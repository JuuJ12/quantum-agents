import os
import requests
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()
firebaseConfig = {
    'apiKey': os.getenv("FIREBASE_API_KEY"),
    'authDomain': os.getenv("AUTH_DOMAIN"),
    'projectId': os.getenv("PROJECT_ID"),
    'storageBucket': os.getenv("STORAGE_BUCKET"),
    'databaseURL': os.getenv("DATABASE_URL"),
    'messagingSenderId': os.getenv("MESSAGING_SENDER_ID"),
    'appId': os.getenv("APP_ID"),
    'measurementId': os.getenv("MEASUREMENT_ID")
}


def _firebase_auth_request(endpoint: str, payload: dict) -> dict:
    api_key = firebaseConfig.get("apiKey")
    if not api_key:
        raise ValueError("FIREBASE_API_KEY não configurada no arquivo .env")

    url = f"https://identitytoolkit.googleapis.com/v1/{endpoint}?key={api_key}"
    response = requests.post(url, json=payload, timeout=15)
    data = response.json() if response.content else {}

    if response.ok:
        return data

    error_code = data.get("error", {}).get("message", "UNKNOWN_ERROR")
    raise ValueError(error_code)

if not firebase_admin._apps:
    try:
        firebase_credentials = {
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n") if os.getenv("FIREBASE_PRIVATE_KEY") else None,
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com")
        }
        
        # Verifica se as credenciais essenciais estão presentes
        if not all([firebase_credentials["project_id"], firebase_credentials["private_key"], firebase_credentials["client_email"]]):
            raise ValueError("Credenciais Firebase incompletas no arquivo .env")
        
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase inicializado com sucesso usando variáveis de ambiente")
        
    except FileNotFoundError:
        print("⚠️  Arquivo .env não encontrado. Funcionalidade Firebase desabilitada.")
    except ValueError as e:
        print(f"⚠️  Erro nas credenciais Firebase: {e}")
    except Exception as e:
        print(f"⚠️  Erro ao inicializar Firebase: {e}")

def cadastro(email: str, senha: str, nome: str) -> tuple[bool, str]:
    """
    Cadastra um novo usuário no Firebase Authentication usando API REST.
    Salva também o nome do usuário no Firestore.
    Retorna True e uma mensagem de sucesso em caso de sucesso,
    ou False e uma mensagem de erro.
    """
    try:
        _firebase_auth_request(
            "accounts:signUp",
            {
                "email": email,
                "password": senha,
                "returnSecureToken": True,
            },
        )
        # Salva o nome no Firestore
        db = firestore.client()
        db.collection("users").document(email).set({"nome": nome, "email": email})
        return True, "Cadastro realizado com sucesso!"
    except Exception as e:
        error_message = str(e)
        if "EMAIL_EXISTS" in error_message:
            return False, "Este e-mail já está em uso por outro feiticeiro."
        elif "WEAK_PASSWORD" in error_message:
            return False, "A senha é muito fraca. Escolha uma senha mais forte (mínimo 6 caracteres)."
        elif "INVALID_EMAIL" in error_message:
            return False, "Formato de e-mail inválido. Verifique o pergaminho."
        else:
            print(f"Erro inesperado ao cadastrar usuário: {e}")
            return False, f"Ocorreu um erro arcano ao tentar cadastrar: {error_message}"

def login(email: str, senha: str) -> tuple[bool, str | None]:
    """
    Tenta autenticar um usuário no Firebase usando API REST.
    Retorna True e o email do usuário em caso de sucesso,
    ou False e None (ou uma mensagem de erro).
    """
    try:
        _firebase_auth_request(
            "accounts:signInWithPassword",
            {
                "email": email,
                "password": senha,
                "returnSecureToken": True,
            },
        )
        return True, email
    except Exception as e:
        error_message = str(e)
        if "INVALID_LOGIN_CREDENTIALS" in error_message or "EMAIL_NOT_FOUND" in error_message or "INVALID_PASSWORD" in error_message:
            return False, "E-mail ou senha incorretos. As runas não reconhecem esta combinação."
        else:
            print(f"Erro inesperado ao fazer login: {e}")
            return False, None


def recuperar_senha(email: str) -> tuple[bool, str]:
    """
    Envia um e-mail de recuperação de senha para o usuário.
    Retorna True e uma mensagem de sucesso em caso de sucesso,
    ou False e uma mensagem de erro.
    """
    try:
        _firebase_auth_request(
            "accounts:sendOobCode",
            {
                "requestType": "PASSWORD_RESET",
                "email": email,
            },
        )
        return True, "E-mail de recuperação enviado com sucesso!"
    except Exception as e:
        error_message = str(e)
        if "EMAIL_NOT_FOUND" in error_message:
            return False, "Este e-mail não está registrado no grimório."
        else:
            print(f"Erro inesperado ao enviar e-mail de recuperação: {e}")
            return False, f"Ocorreu um erro arcano ao tentar enviar o e-mail: {error_message}"