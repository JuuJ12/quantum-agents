import os
from dotenv import load_dotenv
import streamlit as st
from streamlit_lottie import st_lottie
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import firebase_admin 
from firebase_admin import credentials, firestore
from Agents.agents_models import agent_extrator, agent_builder, agent_executor_circuit

load_dotenv()


input = st.text_input("Descreva o circuito quântico que deseja criar:", key="input")
if input:
    
    with st.spinner("Processando..."):
        circuit_requirements = agent_extrator(input) #model dump é um método do pydantic que converte o modelo em um dicionário, facilitando a visualização dos dados estruturados retornados pelo agente_extrator
    st.subheader("Requisitos do Circuito:")
    st.write(circuit_requirements.model_dump()) #model dump é um método do pydantic que converte o modelo em um dicionário, facilitando a visualização dos dados estruturados retornados pelo agente_extrator
   
    with st.spinner("Gerando plano do circuito..."):
        circuit_plan = agent_builder(circuit_requirements)
    st.subheader("Plano do Circuito:")
    st.write(circuit_plan.model_dump()) #model dump é um método do pydantic
   
    with st.spinner("Executando circuito..."):
        qc, counts = agent_executor_circuit(circuit_plan)
        st.subheader("Circuito Executado:")
        st.write(qc)
        st.subheader("Resultados:")
        st.write(counts)














if not firebase_admin._apps:
    cred = credentials.Certificate("auth/firebase_key.json")
    firebase_admin.initialize_app(cred)

def salvar_mensagens_conselho(email, mensagens):
    db = firestore.client()
    db.collection("conselho_chats").document(email).set({"mensagens": mensagens})

def carregar_mensagens_conselho(email):
    db = firestore.client()
    doc = db.collection("conselho_chats").document(email).get()
    if doc.exists:
        return doc.to_dict().get("mensagens", [])
    else:
        return []

