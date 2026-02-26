import os
from autogen import ConversableAgent
from dotenv import load_dotenv
import streamlit as st
from streamlit_lottie import st_lottie
import numpy as np
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

if not firebase_admin._apps:
    cred = credentials.Certificate("auth/firebase_key.json")
    firebase_admin.initialize_app(cred)

defaults = {
    'funcao_agente1': '''Feiticeiro (Sorcerer), Usa magia de forma inata, como se fosse um dom natural ou herdado por linhagem mágica (ex: sangue de dragão). 
    Você responderar sempre de forma temática de acordo com sua função e com sabedoria, responda de uma forma enigmática, mas que ainda seja compreensível.
    Sua resposta será enviada para outros magos.''',

    'funcao_agente2': '''Mago (Wizard), Estuda magia profundamente em grimórios e academias arcanas.
    Tem uma vasta variedade de feitiços, mas precisa preparar e memorizar magias com antecedência.
    Você responderar sempre de forma temática de acordo com sua função e com sabedoria, responda de uma forma enigmática, mas que ainda seja compreensível.
    Sua resposta será enviada para outros magos.''',

    'funcao_agente3': '''Bruxo (Warlock), Faz um pacto com uma entidade poderosa (como um demônio, fada ou antigo deus) para obter magia.
    Recebe poderes únicos e misteriosos, muitas vezes com um preço.
    Você responderar sempre de forma temática de acordo com sua função e com sabedoria, responda de uma forma enigmática, mas que ainda seja compreensível.
    Sua resposta será enviada para outros magos.''',
    'nome_mago1': 'Feiticeiro',
    'nome_mago2': 'Wizard',
    'nome_mago3': 'Bruxo',
    'modelo_agente_1': 'llama-3.3-70b-versatile',
    'modelo_agente_2': 'llama-3.3-70b-versatile',
    'modelo_agente_3': 'llama-3.3-70b-versatile',
    'idioma': 'Português',
    'assunto': '',
    'resposta_sintetizador': "",
    'respostas_agentes': [],
    'resposta_mago1': '',
    'resposta_mago2': '',
    'resposta_mago3': '',
}




# Funções auxiliares
def distance(state, goal_state):
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([state, goal_state])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return 1 - similarity
    except Exception as e:
        print(f"Erro ao calcular a distância: {e}")
        return 1.0

def calculate_reward(state, goal_state):
    try:
        dist = distance(state, goal_state)
        return -dist
    except Exception as e:
        print(f"Erro ao calcular a recompensa: {e}")
        return -np.inf

q_table = {}
epsilon = 0.1

def update_q_value(state, action, reward, next_state, alpha=0.1, gamma=0.9):
    try:
        state_action = (state, action)
        if state_action not in q_table:
            q_table[state_action] = 0.0
        current_q = q_table[state_action]
        next_q_values = [q_table.get((next_state, a), 0.0) for a in range(6)]
        max_next_q = max(next_q_values) if next_q_values else 0.0
        new_q = current_q + alpha * (reward + gamma * max_next_q - current_q)
        if not np.isnan(new_q):
            q_table[state_action] = new_q
    except Exception as e:
        print(f"Erro ao atualizar valor Q: {e}")

def get_best_action(state):
    if random.uniform(0, 1) < epsilon:
        return "Exploração Aleatória"
    q_values = {action: q_value for (s, action), q_value in q_table.items() if s == state}
    if q_values:
        best_action = max(q_values, key=q_values.get)
        return f"Ação mais promissora no estado '{state}'"
    else:
        return "Nenhuma ação registrada"


# Criação dos agentes
def criar_agente(nome, funcao, modelo):
    return ConversableAgent(
        name=nome,
        system_message=(f'Você vai responder sempre em {defaults["idioma"]}, sempre vai atacar e tentar resolver o problema e sua função é {funcao}.'),
        llm_config={
            "model": modelo,
            "api_key": os.getenv("GROQ_API_KEY"),
            "api_type": "groq",
            "temperature": 0
        }
    )

agentes = [criar_agente(f'{defaults[f"nome_mago{i+1}"]}', defaults[f'funcao_agente{i+1}'], defaults[f'modelo_agente_{i+1}']) for i in range(3)]

def respostass(assuntos):
    for agente in agentes:
        chat_result = agente.generate_reply(messages=[{"role": "user", "content": assuntos}])
        resposta = chat_result['content']
        yield f"\n🤖 **{agente.name}** respondeu: {resposta}"

# Chat
def chat(assunto):
    state = "inicio"

    previous_response = assunto

    respostas_individuais = []

    st.subheader("💬 Respostas Individuais")

    for agente in agentes:

        chat_result = agente.generate_reply(messages=[{"role": "user", "content": assunto}])
        resposta = chat_result['content']
        respostas_individuais.append(resposta)
        yield f"\n **{agente.name}** respondeu: {resposta}"
    st.write("__________________________________________________________")
    ultima_resposta = respostas_individuais[-1]

    st.subheader("Conversa")
    for idx, agente in enumerate(agentes):

        chat_result = agente.generate_reply(messages=[{"role": "user", "content": ultima_resposta}])
        resposta = chat_result['content']
        next_state = f"debate-{idx+1}"
        reward = calculate_reward(resposta, "objetivo")
        update_q_value(state, resposta, reward, next_state)
        best_action = get_best_action(state)


        ultima_resposta = resposta


        yield f"\n **{agente.name}** respondeu: {resposta}"
        state = next_state

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

def conselho_dos_magos():
    st.title("Conselho dos Magos 🧙‍♂️🧙‍♀️")
    email_usuario = st.session_state.get("usuario")

    if "conselho_messages" not in st.session_state:
        if email_usuario:
            st.session_state.conselho_messages = carregar_mensagens_conselho(email_usuario)
            if not st.session_state.conselho_messages:
                st.session_state.conselho_messages = [
                    {"role": "system", "content": "Você está diante do conselho dos magos. Faça sua pergunta e receba respostas enigmáticas dos três magos."}
                ]
        else:
            st.session_state.conselho_messages = [
                {"role": "system", "content": "Você está diante do conselho dos magos. Faça sua pergunta e receba respostas enigmáticas dos três magos."}
            ]

    user_input = st.chat_input("Pergunte ao conselho:")

    if user_input:
        st.session_state.conselho_messages.append({"role": "user", "content": user_input})
        respostas = []
        for agente in agentes:
            chat_result = agente.generate_reply(messages=[{"role": "user", "content": user_input}])
            resposta = chat_result['content']
            respostas.append({"role": agente.name, "content": resposta})
            st.session_state.conselho_messages.append({"role": agente.name, "content": resposta})

        # Salva as mensagens no Firestore
        if email_usuario:
            salvar_mensagens_conselho(email_usuario, st.session_state.conselho_messages)

    # Exibe o histórico (pulando a mensagem system)
    for msg in st.session_state.conselho_messages[1:]:
        if msg["role"] == "user":
            with st.chat_message('👤'):
                st.markdown(f"**Você:** {msg['content']}")
        else:
            with st.chat_message('🧙‍♂️'):
                st.markdown(f"**{msg['role']}:** {msg['content']}")

