from dotenv import load_dotenv
import streamlit as st
from Agents.agents_models import agent_extrator, agent_builder, agent_executor_circuit, agent_metric,agent_synthesizer
from auth.firebase_store import save_quantum_messages, load_quantum_messages

load_dotenv()


def salvar_mensagens_quantum(email, mensagens):
    save_quantum_messages(email, mensagens)


def carregar_mensagens_quantum(email):
    return load_quantum_messages(email)


usuario_email = st.session_state.get("usuario")
historico_owner = st.session_state.get("quantum_messages_owner")
if usuario_email and historico_owner != usuario_email:
    try:
        st.session_state["quantum_messages"] = carregar_mensagens_quantum(usuario_email)
        st.session_state["quantum_messages_owner"] = usuario_email
    except Exception as e:
        st.session_state["quantum_messages"] = []
        st.session_state["quantum_messages_owner"] = usuario_email
        st.warning(f"Nao foi possivel carregar historico do Firebase: {e}")


with st.form("quantum_circuit_form"):
    user_prompt = st.text_input("Descreva o circuito quântico que deseja criar:", key="input")
    image_width = st.slider("Largura da imagem do circuito (px)", min_value=300, max_value=1400, value=700, step=50)
    executar = st.form_submit_button("Executar circuito")

col1, col2 = st.columns(2)
if executar and user_prompt:

    with st.spinner("Processando..."):
        circuit_requirements = agent_extrator(user_prompt) #model dump é um método do pydantic que converte o modelo em um dicionário, facilitando a visualização dos dados estruturados retornados pelo agente_extrator
    st.subheader("Requisitos do Circuito:")
    st.write(circuit_requirements.model_dump()) #model dump é um método do pydantic que converte o modelo em um dicionário, facilitando a visualização dos dados estruturados retornados pelo agente_extrator
   
    with st.spinner("Gerando plano do circuito..."):
        circuit_plan = agent_builder(circuit_requirements)
    st.subheader("Plano do Circuito:")
    st.write(circuit_plan.model_dump()) #model dump é um método do pydantic

    with st.spinner("Executando circuito..."):
        qc, counts, circuit_image_bytes = agent_executor_circuit(circuit_plan)
        
    with st.spinner("Calculando métricas..."):
        metrics = agent_metric(qc, circuit_requirements.target_state, counts)
    st.subheader("Métricas do Circuito:")
    st.write(metrics.model_dump())

    with col1:
        st.subheader("Circuito Executado:")
        st.write(qc)
    with col2:
        if circuit_image_bytes:
            st.image(circuit_image_bytes, caption="Imagem do circuito", width=image_width)
        else:
            st.info("Não foi possível renderizar a imagem do circuito neste ambiente.")
    st.subheader("Resultados:")
    st.write(counts)

    with st.spinner("Resumindo resultados..."):
        summary = agent_synthesizer(
            requirements=circuit_requirements.model_dump(),
            planning=circuit_plan.model_dump(),
            metrics=metrics.model_dump()
        )
    st.subheader("Resumo:")
    st.write(summary)

    if usuario_email:
        message_record = {
            "prompt": user_prompt,
            "requirements": circuit_requirements.model_dump(),
            "planning": circuit_plan.model_dump(),
            "metrics": metrics.model_dump(),
            "results": counts,
            "summary": summary,
        }
        st.session_state.setdefault("quantum_messages", []).append(message_record)
        try:
            salvar_mensagens_quantum(usuario_email, st.session_state["quantum_messages"])
            st.success("Historico salvo no Firebase.")
        except Exception as e:
            st.error(f"Falha ao salvar no Firebase: {e}")

elif executar:
    st.warning("Digite uma descrição do circuito antes de executar.")

if usuario_email and st.session_state.get("quantum_messages"):
    with st.expander("Historico salvo no Firebase", expanded=False):
        st.write(st.session_state["quantum_messages"])



