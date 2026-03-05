import os
import requests
from dotenv import load_dotenv
from .firebase_store import get_firestore_client

load_dotenv()


def get_firebase_web_config() -> dict[str, str | None]:
    """Retorna a configuracao Web do Firebase com suporte a aliases legados."""
    return {
        "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyDl2FEsLbxBe4mcA848xgyQzWv6ShDfHMc"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN") or os.getenv("AUTH_DOMAIN") or "quantum-agents-cb893.firebaseapp.com",
        "projectId": os.getenv("FIREBASE_PROJECT_ID") or os.getenv("PROJECT_ID") or "quantum-agents-cb893",
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET") or os.getenv("STORAGE_BUCKET") or "quantum-agents-cb893.firebasestorage.app",
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID") or os.getenv("MESSAGING_SENDER_ID") or "124016539317",
        "appId": os.getenv("FIREBASE_APP_ID") or os.getenv("APP_ID") or "1:124016539317:web:1923cbba500622c9d730fc",
        "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID") or os.getenv("MEASUREMENT_ID") or "G-K8LFYCR19G",
    }


def _firebase_auth_request(endpoint: str, payload: dict) -> dict:
    firebase_config = get_firebase_web_config()
    api_key = firebase_config.get("apiKey")
    if not api_key:
        raise ValueError("FIREBASE_API_KEY nao configurada")

    url = f"https://identitytoolkit.googleapis.com/v1/{endpoint}?key={api_key}"
    response = requests.post(url, json=payload, timeout=15)
    data = response.json() if response.content else {}

    if response.ok:
        return data

    error_code = data.get("error", {}).get("message", "UNKNOWN_ERROR")
    raise ValueError(error_code)

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
        db = get_firestore_client()
        db.collection("users").document(email).set({"nome": nome, "email": email})
        return True, "Cadastro realizado com sucesso!"
    except Exception as e:
        error_message = str(e)
        if "EMAIL_EXISTS" in error_message:
            return False, "Este e-mail já está em uso."
        elif "WEAK_PASSWORD" in error_message:
            return False, "A senha é muito fraca. Escolha uma senha mais forte (mínimo 6 caracteres)."
        elif "INVALID_EMAIL" in error_message:
            return False, "Formato de e-mail inválido."
        else:
            print(f"Erro inesperado ao cadastrar usuário: {e}")
            return False, f"Ocorreu um erro ao tentar cadastrar: {error_message}"

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
            return False, "E-mail ou senha incorretos."
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
            return False, f"Ocorreu um erro ao tentar enviar o e-mail: {error_message}"