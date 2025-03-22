import re
import requests
import jwt  # Biblioteca para gerar o token JWT
import boto3  # SDK da AWS para interagir com o Cognito

def validate_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or not cpf.isdigit():
        return False
    if cpf == cpf[0] * 11:
        return False
    return True

def check_cpf_in_test_api(cpf):
    api_url = "https://jsonplaceholder.typicode.com/users"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            return {"name": "Teste Usuario", "cpf": cpf}
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar à API de teste: {e}")
        return None

def generate_jwt(payload, secret="abacaxi"):
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token

def create_user_in_cognito(username):
    client = boto3.client('cognito-idp')
    try:
        response = client.admin_create_user(
            UserPoolId='us-east-1_bjgWk97QO',
            Username=username,  
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': f"{username}@exemplo.com"  # Cria um email válido com base no CPF ou identificador
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'  # Opcional: marca o email como verificado
                }
            ]
        )
        print("Usuário criado com sucesso no Cognito.")
        return response
    except Exception as e:
        print(f"Erro ao criar o usuário no Cognito: {e}")
        raise



def store_token_in_cognito(username, token):
    client = boto3.client('cognito-idp')
    try:
        # Tenta atualizar os atributos do usuário
        response = client.admin_update_user_attributes(
            UserPoolId='us-east-1_bjgWk97QO',
            Username=username,
            UserAttributes=[
                {
                    'Name': 'custom:jwtToken',
                    'Value': token
                }
            ]
        )
        print("Token armazenado com sucesso no Cognito.")
        return response
    except client.exceptions.UserNotFoundException:
        # Cria o usuário se ele não existir
        print("Usuário não encontrado. Criando usuário...")
        create_user_in_cognito(username)
        # Tenta novamente atualizar os atributos
        return store_token_in_cognito(username, token)
    except Exception as e:
        print(f"Erro ao armazenar o token no Cognito: {e}")
        raise



def lambda_handler(event, context):
    cpf = event.get("queryStringParameters", {}).get("cpf")
    if not cpf:
        return {"statusCode": 400, "body": "CPF não fornecido"}

    if not validate_cpf(cpf):
        return {"statusCode": 401, "body": "CPF inválido"}

    client_data = check_cpf_in_test_api(cpf)
    if client_data:
        token = generate_jwt(client_data)
        store_token_in_cognito(client_data["cpf"], token)  # Armazena o token no Cognito
        return {"statusCode": 200, "body": f"Token JWT: {token}"}
    else:
        return {"statusCode": 404, "body": "CPF não encontrado"}
