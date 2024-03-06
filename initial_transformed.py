from flask import Flask, request, jsonify
import requests
from pegasus import run_pipeline, retorna_conselho
from whatsapp_client import WhatsAppClient
import csv
from datetime import datetime, timedelta
import json

#ngrok http --domain=gobbler-better-specially.ngrok-free.app 8000



#TOKEN E VARIAVEIS ESTATICAS

token = "EAAPM33lAi90BO9H5ByIY2kKw3ZAsb44NmqxueyQafpw9DT9axvwRs1mh44p56OZCEaDiPZC2Gxi9lhyPxuiZBgZBIzl5iaHZBDAIni0MvCGZBNZALT4TGKN36xE82SnqgYHuR4yXnQf5NGfZCJj83cwpgy013p4ZCdVinIZCXqmEuJcZCZCI9belKVwEkX4TEW7NueLFm6iNpfaxHj8uuKjp7vc8ZD"  # Replace with your actual token
verify_token = "token_valida"  # Replace with your actual verify token
processed_message_ids = {}

#################################################################
#
#                           FUNÇÕES
#
#################################################################

#FUNÇÃO PARA VEIFICAR SE O NUMERO JA TEM O 9 NA FRENTE
def modify_number(number):
                    str_number = str(number)
                    if len(str_number) < 13:
                        modified_number = str_number[:4] + '9' + str_number[4:]
                        return int(modified_number)
                    else:
                        return number

# #### antiga
# #FUNÇÃO PARA EXTRAIR OS DADOS DA NOTIFICAÇÃO DO WEBHOOK
# def extract_info(body):
#     try:
#         message_id = body.get('entry')[0].get('changes')[0].get('value').get('messages')[0].get('id')
#         timestamp_str  = body.get('entry')[0].get('changes')[0].get('value').get('messages')[0].get('timestamp')
#         # Convert timestamp to integer
#         timestamp = int(timestamp_str)
#         # Convert Unix timestamp to datetime
#         datetime_obj = datetime.fromtimestamp(timestamp)
        
#         text = body.get('entry')[0].get('changes')[0].get('value').get('messages')[0].get('text')
#         name = body.get('entry')[0].get('changes')[0].get('value').get('contacts')[0].get('profile').get('name')
#         wa_id = body.get('entry')[0].get('changes')[0].get('value').get('contacts')[0].get('wa_id')
        
#         return name, wa_id, message_id,text, datetime_obj
#     except:
#         #print('NOT A MESSAGE*****************************')
#         return None
    
    
######################################################
#
#                  PROCESSA DADOS WEBHOOK
#
######################################################
def process_whatsapp_api_call(payload):
    result = {}
    status = -1  # Default status indicating unknown payload type
    #print(payload)
    if 'changes' in payload[0] and 'value' in payload[0]['changes'][0]:
        
        value = payload[0]['changes'][0]['value']
        if 'statuses' in value:
            status_info = value['statuses'][0]
            if 'status' in status_info:
                if status_info['status'] == 'sent':
                    status = 0
                elif status_info['status'] == 'delivered':
                    status = 1
        elif 'messages' in value:
            message_info = value['messages'][0]
            if 'wa_id' in value['contacts'][0] and 'timestamp' in message_info and 'text' in message_info:
                status = 2
                result['wa_id'] = value['contacts'][0]['wa_id']
                result['timestamp'] = message_info['timestamp']
                result['text'] = message_info['text']['body']
    
    return status, result





#FUNÇÃO PARA RODAR A PIPELINE DE OCR E BUSCA SEMANTICA
def run_data_processing_pipeline(query, field, lang):
    base_path = "/home/gustavo_zitta/Downloads/Source_Code/knowledge pdf biblia"
    top_k_sent = 2

    # Run your data processing pipeline
    response = run_pipeline(base_path, field, lang, query, top_k_sent)

    # Modify or process the response if needed
    # For example, you might want to extract relevant information from the response

    return response
###############################################################################
#     FUNÇÃO QUE VERIFICA SE JA TA CADASTRADO E DIAS DE TESTE GRATUITO
#
###############################################################################
#FUNÇÃO QUE RETORNA SE TEM MAIS DE 7 DIAS OU NAO, SE A PESSOA NAO TIVER ADICIONA
# def update_csv(name, wa_id, datetime_obj):
#     # Verifica se a pessoa já está no CSV
#     #print(f"Received timestamp: {datetime_obj}")
#     with open('seu_arquivo.csv', 'r') as file:
#         csv_reader = csv.reader(file)
#         for row in csv_reader:
#             if row[1] == wa_id:
#                 # A pessoa já está no CSV, calcula a diferença de dias
#                 date_registered = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
#                 current_date = datetime.now()
#                 days_difference = (current_date - date_registered).days

#                 if days_difference > 2:
#                     # Se a diferença for maior que 7 dias, não autoriza
#                     return False
#                 else:
#                     # Se a diferença for menor ou igual a 7 dias, autoriza
#                     return True

#     # Se a pessoa não estiver no CSV, adiciona com a data de hoje
#     with open('seu_arquivo.csv', 'a', newline='') as file:
#         csv_writer = csv.writer(file)
#         csv_writer.writerow([name, wa_id, datetime_obj])

#     return True


##############################################################
#
#               FUNÇÃO CADASTRO 7 DIAS SEM NOME
#
###########################################################

def update_csv(wa_id, datetime_obj):
    csv_filename = 'clientes.csv'

    # Verifica se o wa_id está presente no CSV
    with open(csv_filename, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if row[1] == wa_id:
                # O wa_id já está no CSV, calcula a diferença de dias
                date_registered = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
                current_date = datetime.now()
                days_difference = (current_date - date_registered).days

                # Retorna False se a diferença for maior do que 2 dias, caso contrário, retorna True
                return days_difference <= 20

    # Se o wa_id não estiver no CSV, adiciona uma nova entrada com a data atual
    with open(csv_filename, 'a', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([wa_id, datetime_obj])

    # Como acabamos de adicionar uma nova entrada, retorna True
    return True




##################################################################
#
#                           SERVER
#
##################################################################
app = Flask(__name__)

#TESTE PRA VER SE TA ONLINE
@app.route("/")
def home():
    return "WhatsApp Echo Bot is running!"



# Accepts POST requests at /webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.get_json()
    if not body:
        return jsonify({"message": "Invalid request"}), 400
    
    status, resultado = process_whatsapp_api_call(body['entry'])  # Remove the list brackets around body

    if not resultado:  # Check if resultado is None
        return jsonify({"message": "Invalid data format"}), 401

    wa_id = resultado.get('wa_id')  # Use get to avoid KeyError
    print(resultado)
    timestamp = resultado.get('timestamp')  # Use get to avoid KeyError
    if not wa_id or not timestamp:
        return jsonify({"message": "Missing phone number or timestamp"}), 402

    authorized = update_csv(wa_id, timestamp)

    if authorized and status == 2:
        texto = resultado.get('text')
        if not texto:
            return jsonify({"message": "Missing message text"}), 403

        reply_conselho = retorna_conselho(texto)
        reply_citacoes = run_data_processing_pipeline(texto, "ajuda", "en")

        wtsapp_client = WhatsAppClient()
        wtsapp_client.send_text_message(message='💭'+reply_conselho, phone_number=modify_number(wa_id))
        wtsapp_client.send_text_message(message='🙏'+reply_citacoes+'🙌 ', phone_number=modify_number(wa_id))
        
        return jsonify({"message": "Authorized, and message sent"}), 200
    elif status == 0:
        print('SENT! CHEGOU')
    elif status == 1: 
        print('DELIVERED! ENTREGUE RAPAZ')
    elif not authorized:
        wtsapp_client = WhatsAppClient()
        wtsapp_client.send_text_message(message='🆓 Que pena! O limite gratuito de 2 dias foi atingido, mas você ainda pode ter acesso ao poder da palavra!', phone_number=modify_number(wa_id))
        wtsapp_client.send_text_message(message='✝️ Com menos de R$0,75 centavos por dia, você pode ter os conhecimentos bíblicos milenares na palma da sua mão.🙌', phone_number=modify_number(wa_id))
        wtsapp_client.send_text_message(message='✨🕊️ Faça agora o pagamento em nossa plataforma credenciada! ✨🕊️', phone_number=modify_number(wa_id))
        wtsapp_client.send_text_message_with_link(message='✅ Acesse o link, selecione como pagar e pronto!   https://mpago.la/1aMtx9j  ✅', phone_number=modify_number(wa_id))
        return jsonify({"message": "Unauthorized, 2-day limit reached"}), 400

    return jsonify({"message": "Request processed"}), 200  # Default response if no specific condition is met


        
    
        

    



#VERIFICAÇÃO DO WEBHOOK COM  API DE FACEBOOK
#payload: https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests 
@app.route("/webhook", methods=['GET'])
def verify_webhook():
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode")
    token_param = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # Check if a token and mode were sent
    if mode and token_param:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token_param == verify_token:
            # Respond with 200 OK and challenge token from the request
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            return "Forbidden", 403
    return "Invalid Request", 400







if __name__ == "__main__":
    # Runs the application on the local development server
    app.run(port=8000)
