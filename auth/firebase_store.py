import os
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv


load_dotenv()


def _resolve_credentials_file() -> str | None:
    credentials_file = os.getenv("FIREBASE_CREDENTIALS_FILE")
    if not credentials_file:
        return None

    if os.path.isabs(credentials_file):
        return credentials_file

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(project_root, credentials_file)


def _build_firebase_credentials() -> dict[str, str | None]:
    return {
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
        "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com"),
    }


def ensure_firebase_initialized() -> None:
    if firebase_admin._apps:
        return

    credentials_file = _resolve_credentials_file()
    if credentials_file and os.path.exists(credentials_file):
        cred = credentials.Certificate(credentials_file)
        firebase_admin.initialize_app(cred)
        return

    firebase_credentials = _build_firebase_credentials()
    if not all([
        firebase_credentials["project_id"],
        firebase_credentials["private_key"],
        firebase_credentials["client_email"],
    ]):
        raise ValueError("Credenciais Firebase incompletas no arquivo .env")

    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)


def get_firestore_client() -> firestore.Client:
    ensure_firebase_initialized()
    return firestore.client()


def save_messages(collection_name: str, doc_id: str, messages: list[dict[str, Any]]) -> None:
    db = get_firestore_client()
    db.collection(collection_name).document(doc_id).set({"mensagens": messages})


def load_messages(collection_name: str, doc_id: str) -> list[dict[str, Any]]:
    db = get_firestore_client()
    doc = db.collection(collection_name).document(doc_id).get()
    if not doc.exists:
        return []
    return doc.to_dict().get("mensagens", [])


def save_quantum_messages(email: str, messages: list[dict[str, Any]]) -> None:
    save_messages("quantum_chats", email, messages)


def load_quantum_messages(email: str) -> list[dict[str, Any]]:
    return load_messages("quantum_chats", email)
