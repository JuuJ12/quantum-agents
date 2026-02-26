import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

llamaChatModel = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5,
)

def salvar_mensagens_chat(email, mensagens):
    db = firestore.client()
    db.collection("chats").document(email).set({"mensagens": mensagens})

def carregar_mensagens_chat(email):
    db = firestore.client()
    doc = db.collection("chats").document(email).get()
    if doc.exists:
        return doc.to_dict().get("mensagens", [])
    else:
        return []
    
def chat_bot():
    st.title("Chatbot")

    email_usuario = st.session_state.get("usuario")  # ou "usuario_nome" se preferir

    if "messages" not in st.session_state:
        if email_usuario:
            st.session_state.messages = carregar_mensagens_chat(email_usuario)
            if not st.session_state.messages:
                st.session_state.messages = [
                    {"role": "system", "content": "Você é um mago supremo que guiará o usuário na jornada dele. Fale de forma sábia e amigável."}
                ]
        else:
            st.session_state.messages = [
                {"role": "system", "content": "Você é um mago supremo que guiará o usuário na jornada dele. Fale de forma sábia e amigável."}
            ]

    user_input = st.chat_input("Digite sua mensagem:")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        messages_for_model = [
            (msg["role"], msg["content"]) for msg in st.session_state.messages
        ]
        response = llamaChatModel.invoke(messages_for_model)
        st.session_state.messages.append({"role": "assistant", "content": response.content})

        # Salva as mensagens no Firestore
        if email_usuario:
            salvar_mensagens_chat(email_usuario, st.session_state.messages)

    for msg in st.session_state.messages[1:]:
        if msg["role"] == "user":
            with st.chat_message('👤'):
                st.markdown(f"**Você:** {msg['content']}")
        else:
            with st.chat_message('🧙‍♂️'):
                st.markdown(f"**Mago:** {msg['content']}")

if __name__ == "__main__":
    if not firebase_admin._apps:
        cred = credentials.Certificate("auth/firebase_key.json")
        firebase_admin.initialize_app(cred)
    chat_bot()
