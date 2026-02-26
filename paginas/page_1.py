import streamlit as st

# if "pagina" not in st.session_state or st.session_state.pagina != "principal":
#     st.switch_page("paginas/tela_login_e_cadastro.py")

from Agents.chat_bot import chat_bot

chat_bot()