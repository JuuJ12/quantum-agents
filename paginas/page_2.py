import streamlit as st
from PIL import Image

# if "pagina" not in st.session_state or st.session_state.pagina != "principal":
#     st.switch_page("paginas/tela_login_e_cadastro.py")

from Agents.quantum_agents_page import chat
from Agents.quantum_agents_page import respostass

# Configurar imagem de fundo


st.title('titulo')
st.write('''
   descrição de algo  
''')


defaults = {
    'assunto': '',
    'respostas_agentes': [],
    'respostas_mago1': [],
    'respostas_mago2': [],
    'respostas_mago3': []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
st.session_state.assunto = st.text_input('Assunto',  help='Escreva o que você deseja, uma duvida, um problema, qualquer coisa !',value=st.session_state.assunto)
button = st.button('Iniciar Conversa')

if button:
    # Resetar respostas antigas
    st.session_state.respostas_agentes = []
    st.session_state.respostas_mago1 = []
    st.session_state.respostas_mago2 = []
    st.session_state.respostas_mago3 = []

    # Criar 3 colunas para os magos
    col1, col2, col3 = st.columns(3)
    
    # Configurar as colunas com imagens e títulos
    with col1:
        st.subheader("🔮 Feiticeiro")
        placeholder_mago1 = st.empty()
        
    with col2:
        st.subheader("📚 Wizard")
        placeholder_mago2 = st.empty()
        
    with col3:
        st.subheader("🌙 Bruxo")
        placeholder_mago3 = st.empty()

    with st.spinner('Aguarde um momento, os agentes estão batendo um papo 🗣...'):
        for resultado in chat(st.session_state.assunto):
            # Determinar qual mago está falando baseado no nome
            if "Feiticeiro" in resultado:
                st.session_state.respostas_mago1.append(resultado)
                with placeholder_mago1:
                    st.markdown("**Respostas:**")
                    for resposta in st.session_state.respostas_mago1:
                        st.write(resposta)
            elif "Wizard" in resultado:
                st.session_state.respostas_mago2.append(resultado)
                with placeholder_mago2:
                    st.markdown("**Respostas:**")
                    for resposta in st.session_state.respostas_mago2:
                        st.write(resposta)
            elif "Bruxo" in resultado:
                st.session_state.respostas_mago3.append(resultado)
                with placeholder_mago3:
                    st.markdown("**Respostas:**")
                    for resposta in st.session_state.respostas_mago3:
                        st.write(resposta)

# Exibir respostas anteriores se existirem
if ('respostas_mago1' in st.session_state and st.session_state.respostas_mago1) or \
   ('respostas_mago2' in st.session_state and st.session_state.respostas_mago2) or \
   ('respostas_mago3' in st.session_state and st.session_state.respostas_mago3):
    
    st.subheader("💬 Última conversa dos magos:")
    
    # Criar 3 colunas para exibir as respostas anteriores
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🔮 Feiticeiro")
        if 'respostas_mago1' in st.session_state:
            for resposta in st.session_state.respostas_mago1:
                st.write(resposta)
                
    with col2:
        st.subheader("📚 Wizard")
        if 'respostas_mago2' in st.session_state:
            for resposta in st.session_state.respostas_mago2:
                st.write(resposta)
                
    with col3:
        st.subheader("🌙 Bruxo")
        if 'respostas_mago3' in st.session_state:
            for resposta in st.session_state.respostas_mago3:
                st.write(resposta)

# st.write(respostass(st.session_state.assunto))
