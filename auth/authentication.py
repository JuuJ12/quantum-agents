import streamlit as st
import json
import os
import re
import time
from streamlit_lottie import st_lottie
from .auth_firebase import cadastro, login
from streamlit.components.v1 import html
from paginas.recuperacao_senha import mostrar_recuperacao_senha
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# USUARIOS_FILE = 'usuarios.json' # Não será mais necessário
ALLOWED_DOMAINS = ["gmail.com", "outlook.com", "hotmail.com"] 
MIN_PASSWORD_LENGTH = 6 
MAX_NAME_LENGTH = 100 

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

def is_valid_email_format(email_str):
    """Verifica o formato básico do e-mail e o domínio."""
    if not email_str:
        return False, "O pergaminho do e-mail não pode estar em branco."
    
    email_str = email_str.strip()

    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(regex, email_str):
        return False, "Esse não parece ser um pergaminho válido de comunicação. Verifique teu e-mail, jovem aprendiz." # CT-AUT-13

    domain = email_str.split('@')[1].lower()
    if domain not in ALLOWED_DOMAINS:
        return False, f"Este domínio não é reconhecido pelo Conselho Arcano. Use domínios como: {', '.join(ALLOWED_DOMAINS)}." # CT-AUT-22
    return True, email_str 

def is_strong_password(password_str):
    """Verifica a força da senha."""
    if not password_str:
        return False, "A senha não pode ser um feitiço vazio."
    
    # Verifica se há emojis na senha
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+", flags=re.UNICODE
    )
    
    if emoji_pattern.search(password_str):
        return False, "As runas mágicas não devem conter símbolos encantados (emojis). Use apenas letras, números e símbolos tradicionais."
    
    # A validação de comprimento aqui ainda é útil como uma verificação de frontend,
    # mesmo que o Firebase também valide.
    if len(password_str) < MIN_PASSWORD_LENGTH:
        return False, "A Palavra-Passe deve conter pelo menos 6 runas mágicas." # CT-AUT-14
    return True, ""

def sanitize_full_name(name_str):
    """Sanitiza e trunca o nome completo."""
    if not name_str:
        return "", False 
    
    name_str = name_str.strip()
    name_str = re.sub(r'<script.*?>.*?</script>', '', name_str, flags=re.IGNORECASE)
    
    truncated = False
    if len(name_str) > MAX_NAME_LENGTH:
        name_str = name_str[:MAX_NAME_LENGTH]
        truncated = True 
    return name_str, truncated

def verificar_login(email, senha):
    """
    Verifica as credenciais do usuário usando o método login do Firebase.
    """
    email = email.strip() 
    
    autenticado, message = login(email, senha) 
    
    if autenticado:
        # Busca o nome no Firestore
        db = firestore.client()
        doc = db.collection("users").document(email).get()
        nome = doc.to_dict().get("nome") if doc.exists else ""
        st.session_state["usuario_nome"] = nome
        return True, message 
    else:
        return False, message


def registrar_usuario(nome_completo, email, senha):
    """
    Registra um novo usuário usando o método cadastro do Firebase.
    Retorna (status_code, message_or_data).
    """
    email_original = email 
    is_valid, email_or_error_msg = is_valid_email_format(email)
    if not is_valid: 
        return "validation_error", email_or_error_msg
    email = email_or_error_msg 

    nome_sanitizado, foi_truncado = sanitize_full_name(nome_completo)
    if not nome_sanitizado:
        return "validation_error", "O nome completo não pode ser vazio."

    senha_processada = senha.strip()
    if not is_strong_password(senha_processada)[0]:
        return "validation_error", is_strong_password(senha_processada)[1]
    
    success, message = cadastro(email, senha_processada, nome_sanitizado)

    if success:
        # Se precisar, você pode usar o UID (se o pyrebase retornasse aqui,
        # mas ele retorna apenas True/False para create_user_with_email_and_password)
        # para salvar informações adicionais do usuário (como o nome completo)
        # em um Firestore ou Realtime Database.
        
        success_message = "Inscrição concluída! Teu nome foi gravado nos registros sagrados."
        if foi_truncado: 
            success_message += " (Observação: Teu nome foi abreviado para caber nos registros antigos.)"
        return "success", success_message
    else:
        # A mensagem de erro já vem do auth_firebase.py
        if "e-mail já está em uso" in message:
            return "email_exists", message
        elif "Formato de e-mail inválido" in message:
            return "validation_error", message
        elif "senha é muito fraca" in message:
            return "validation_error", message
        else: # Erro geral do Firebase
            return "firebase_error", message

def load_lottiefile(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def exibir_tela_login_registro():
    """Exibe a tela de login ou registro se o usuário não estiver autenticado."""
    
    if st.session_state.get('autenticado', False):
        return
    

    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Login"
    
    if 'registration_errors' not in st.session_state:
        st.session_state.registration_errors = {}
    
    if 'registration_inputs' not in st.session_state:
        st.session_state.registration_inputs = {"nome": "", "email": "", "senha": "", "conf_senha": ""}

    if not st.session_state.get('autenticado', False):
        st.title("Login Mentorium")
        
        tab_login, tab_registro = st.tabs(["Login", "Registrar"])
        
        with tab_login:
            if st.session_state.get("show_login_after_register"):
                st.success("Registro realizado com sucesso! Por favor, faça o login.")
                del st.session_state.show_login_after_register 

            with st.form("login_form"):
                email_login = st.text_input("Selo Mágico", key="login_email")
                
                # Campo de senha com controle de limpeza usando contador único
                if not hasattr(st.session_state, 'senha_counter'):
                    st.session_state.senha_counter = 0
                
                # Incrementa contador quando deve limpar senha
                if st.session_state.get('limpar_senha_login', False):
                    st.session_state.senha_counter += 1
                    st.session_state.limpar_senha_login = False
                
                # Cria key única para forçar limpeza do campo
                senha_key = f"login_senha_{st.session_state.senha_counter}"
                senha_login = st.text_input("Palavra-Passe", type="password", key=senha_key)
                
                # Botão sempre habilitado no formulário
                enviar_login = st.form_submit_button("Entrar")
                
                # Mostra mensagem de erro se houver
                if st.session_state.get('mensagem_erro_login'):
                    st.error(st.session_state.mensagem_erro_login)
                
                if enviar_login:
                    # Limpa mensagens de erro anteriores
                    if 'mensagem_erro_login' in st.session_state:
                        del st.session_state.mensagem_erro_login
                    
                    # Validação de campos vazios
                    if not email_login.strip() or not senha_login.strip():
                        st.session_state.mensagem_erro_login = "Por favor, complete o pergaminho antes de prosseguir, jovem aprendiz."
                        st.rerun()
                    else:
                        # Validação do formato do email antes de tentar login
                        email_valido, msg_email = is_valid_email_format(email_login)
                        if not email_valido:
                            st.session_state.mensagem_erro_login = "Este selo mágico não é reconhecido. Use o formato: aprendiz@reino.com"
                            st.rerun()
                        # Validação do comprimento da senha
                        elif len(senha_login.strip()) < MIN_PASSWORD_LENGTH:
                            st.session_state.mensagem_erro_login = f"A Palavra-Passe deve conter pelo menos {MIN_PASSWORD_LENGTH} runas mágicas."
                            st.session_state.limpar_senha_login = True
                            st.rerun()
                        else:
                            with st.spinner("Verificando suas credenciais arcanas..."):
                                # Chama a função de login que agora usa o Firebase
                                autenticado, message = verificar_login(email_login, senha_login)
                                
                                if autenticado:
                                    # Mostra spinner de carregamento pós-login
                                    time.sleep(1)  # Pequena pausa para melhor experiência
                                    
                            if autenticado:
                                with st.spinner("Bem-vindo ao Mentorium! Preparando sua jornada..."):
                                    time.sleep(2)  # Simula carregamento da aplicação
                                    
                                st.session_state.autenticado = True
                                st.session_state.usuario = message # O message agora é o email do usuário
                                # Limpa estados de sessão após login bem-sucedido
                                keys_to_delete = [
                                    'active_tab', 
                                    'registration_errors', 
                                    'registration_inputs', 
                                    'show_login_after_register',
                                    'login_email', # Limpa o campo de email do login
                                    'login_senha',  # Limpa o campo de senha do login
                                    'senha_counter', # Limpa o contador de senha
                                    'limpar_senha_login', # Limpa a flag de limpeza
                                    'mensagem_erro_login' # Limpa mensagens de erro
                                ]
                                for key in keys_to_delete:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.rerun()
                            else:
                                # Define flag para limpar campo de senha na próxima execução
                                st.session_state.limpar_senha_login = True
                                # Armazena a mensagem de erro para exibir
                                st.session_state.mensagem_erro_login = "Selo Mágico ou Palavra-Passe inválidos. Tente novamente ou inicie o Ritual de Recuperação."
                                st.rerun()
            
            with st.expander("Esqueci minha senha", expanded=False):
                    mostrar_recuperacao_senha()

        with tab_registro:
            with st.form("register_form"):
                st.subheader("Inscreva-se no Mentorium")
                
                nome_completo_reg = st.text_input("Nome Completo", 
                                                    value=st.session_state.registration_inputs["nome"], 
                                                    key="reg_nome")
                if "nome" in st.session_state.registration_errors:
                    st.error(st.session_state.registration_errors["nome"])

                email_reg = st.text_input("E-mail de Invocação", 
                                                value=st.session_state.registration_inputs["email"], 
                                                key="reg_email",
                                                help=f"Domínios permitidos: {', '.join(ALLOWED_DOMAINS)}")
                if "email" in st.session_state.registration_errors:
                    st.error(st.session_state.registration_errors["email"])

                senha_reg = st.text_input("Senha Arcana", type="password", 
                                                value=st.session_state.registration_inputs["senha"], 
                                                key="reg_senha",
                                                help=f"Mínimo {MIN_PASSWORD_LENGTH} caracteres.")
                if "senha" in st.session_state.registration_errors:
                    st.error(st.session_state.registration_errors["senha"])

                confirmar_senha_reg = st.text_input("Confirmar Senha Arcana", type="password", 
                                                        value=st.session_state.registration_inputs["conf_senha"],
                                                        key="reg_conf_senha")
                if "conf_senha" in st.session_state.registration_errors:
                    st.error(st.session_state.registration_errors["conf_senha"])

                # Atualiza os inputs no session_state para manter os valores no formulário
                st.session_state.registration_inputs["nome"] = nome_completo_reg
                st.session_state.registration_inputs["email"] = email_reg
                st.session_state.registration_inputs["senha"] = senha_reg
                st.session_state.registration_inputs["conf_senha"] = confirmar_senha_reg

                if st.form_submit_button("Concluir Cadastro"):
                    st.session_state.registration_errors = {} # Limpa erros anteriores

                    # Validações locais (antes de chamar o Firebase)
                    if not nome_completo_reg.strip():
                        st.session_state.registration_errors["nome"] = "Até mesmo os magos precisam de um nome... Informe como deseja ser chamado em nossos grimórios."
                    
                    email_valido, msg_email = is_valid_email_format(email_reg)
                    if not email_valido:
                        st.session_state.registration_errors["email"] = msg_email
                    
                    senha_valida, msg_senha = is_strong_password(senha_reg) 
                    if not senha_valida:
                        st.session_state.registration_errors["senha"] = msg_senha
                    elif senha_reg.strip() != confirmar_senha_reg.strip(): 
                        st.session_state.registration_errors["conf_senha"] = "As senhas não se alinham como as constelações."
                    
                    # Se houver erros de validação locais, exibe-os e interrompe.
                    if st.session_state.registration_errors:
                        st.rerun() # Reruns para exibir os erros

                    # Se não houver erros de validação locais, tenta registrar no Firebase
                    if not st.session_state.registration_errors:
                        with st.spinner("O Conselho está inscrevendo teu nome nos registros sagrados..."):
                            time.sleep(1) # Pequena pausa para a experiência do usuário
                            
                            status_code, message = registrar_usuario(nome_completo_reg, email_reg, senha_reg)
                        
                        if status_code == "success":
                            st.success(message) 
                            time.sleep(2)
                            st.session_state.show_login_after_register = True
                            st.session_state.active_tab = "Login" 
                            # Limpa os campos do formulário de registro após sucesso
                            st.session_state.registration_inputs = {"nome": "", "email": "", "senha": "", "conf_senha": ""} 
                            st.session_state.registration_errors = {}
                            st.rerun()
                        else: # Qualquer outro status_code indica erro
                            # Mapeia as mensagens de erro do Firebase para os campos específicos, se aplicável
                            if status_code == "email_exists": 
                                st.session_state.registration_errors["email"] = message
                            elif status_code == "validation_error":
                                if "e-mail" in message:
                                    st.session_state.registration_errors["email"] = message
                                elif "senha" in message:
                                    st.session_state.registration_errors["senha"] = message
                                elif "nome" in message: # Para erros de nome que podem vir de sanitize_full_name
                                    st.session_state.registration_errors["nome"] = message
                            elif status_code == "firebase_error":
                                # Para erros gerais do Firebase, exibe como erro global
                                st.error(message)
                            else: # Catch-all para outros erros inesperados
                                st.error(f"Um contratempo mágico ocorreu: {message}")
                            st.rerun() # Reruns para exibir os erros nos campos ou globalmente
    
    try:
        caminho_do_lottie = "pictures/aventureiros.json"
        lottie_data = load_lottiefile(caminho_do_lottie)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar a animação Lottie: {e}")
        lottie_data = None

    if lottie_data:
        left_column, right_column  = st.columns([2, 1])
        with left_column:
            st.write("")
        with right_column:
            st_lottie(lottie_data, height=150, width=400, key="corner_lottie2")
        
        st.stop()