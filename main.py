import streamlit as st
import bcrypt
import json
import os
import time
from dotenv import load_dotenv  
import os  
from groq import Groq  
from auth.authentication import exibir_tela_login_registro

load_dotenv()

# Inicializa o estado de autenticação antes da configuração da página
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None

# Configuração da página com sidebar colapsado para usuários não autenticados
sidebar_state = "expanded" if st.session_state.get('autenticado', False) else "collapsed"

st.set_page_config(
    page_title='Mentorium',
    layout="wide",
    initial_sidebar_state=sidebar_state,
)

css_file_path = "style/style.css"
try:
    with open(css_file_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error(f"Erro: O arquivo CSS '{css_file_path}' não foi encontrado. Verifique o caminho.")
except UnicodeDecodeError:
    st.error(f"Erro de codificação ao ler o arquivo CSS '{css_file_path}'. Verifique se ele está salvo como UTF-8.")

exibir_tela_login_registro()

if st.session_state.get('login_sucesso', False):
    mensagem_container = st.empty()
    with mensagem_container.container():
        st.success(f"🎉 Bem-vindo ao Mentorium, {st.session_state.usuario}! Sua jornada mágica começa agora!")
    
    time.sleep(3)
    mensagem_container.empty()
    
    del st.session_state.login_sucesso

# Controla a exibição do sidebar baseado na autenticação
if st.session_state.get('autenticado', False):
    st.sidebar.text('Mentorium')
    if st.session_state.get('usuario_nome'):
        st.sidebar.success(f"Bem-vindo, {st.session_state['usuario_nome']}!")
    elif st.session_state.get('usuario'):
        st.sidebar.success(f"Bem-vindo, {st.session_state['usuario']}!")
    else:
        st.sidebar.info("Usuário não identificado.")

    if st.sidebar.button("Logout"):
        # Limpa todos os estados relacionados ao usuário
        keys_to_clear = [
            'autenticado', 'usuario', 'usuario_nome', 'login_sucesso',
            'active_tab', 'registration_errors', 'registration_inputs',
            'show_login_after_register', 'mensagem_erro_login',
            'limpar_senha_login', 'login_email', 'login_senha', 'senha_counter'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Reinicia os estados essenciais
        st.session_state.autenticado = False
        st.session_state.usuario = None
        st.rerun()

# Só mostra as páginas se o usuário estiver autenticado
if st.session_state.get('autenticado', False):
    # pag1 = st.Page(
    #     page= "paginas/page_1.py",
    #     title="Iniciando a Jornada",
    #     icon='🧙‍♂️',
    #     default=True
    # )

    # pag2 = st.Page(
    #     page= "paginas/page_2.py",
    #     title="Alto Conselho do Mentorium",
    #     icon='🧙‍♂️'
    # )

    pag3 = st.Page(
        page ='Agents/quantum_agents_page.py'
    )
    paginas = st.navigation({
        # "Jornada": [pag1],
        # "Àgora": [pag2],
        "Agentes": [pag3]
    })

    paginas.run()
