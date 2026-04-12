from dotenv import load_dotenv
import base64
import re
import streamlit as st
from Agents.agents_models import run_quantum_pipeline
from auth.firebase_store import save_quantum_messages, load_quantum_messages

load_dotenv()


def salvar_mensagens_quantum(email, mensagens):
    save_quantum_messages(email, mensagens)


def carregar_mensagens_quantum(email):
    return load_quantum_messages(email)


def _encode_image_to_base64(image_bytes):
    if not image_bytes:
        return None
    return base64.b64encode(image_bytes).decode("ascii")


def _decode_image_from_base64(image_base64):
    if not image_base64:
        return None
    try:
        return base64.b64decode(image_base64)
    except Exception:
        return None


def _planning_to_text(planning):
    if not planning:
        return None

    gates = planning.get("gates") if isinstance(planning, dict) else None
    if not gates:
        return None

    lines = ["Circuito (fallback pelo plano):"]
    for idx, gate in enumerate(gates, start=1):
        gate_name = gate.get("gate_name")
        targets = gate.get("target_qubits")
        controls = gate.get("control_qubits")
        lines.append(f"{idx}. gate={gate_name} targets={targets} controls={controls}")
    return "\n".join(lines)


def _is_quantum_circuit_prompt(prompt):
    if not prompt:
        return False

    normalized = prompt.lower()
    keywords = [
        "quantum", "quantico", "qubit", "qubits", "circuit", "circuito",
        "qiskit", "hadamard", "entanglement", "entangled", "bell",
        "superposition", "medicao", "measurement", "cx", "h ", " x ",
    ]
    if any(word in normalized for word in keywords):
        return True

    # Heuristica adicional para gate+qubit no texto.
    has_gate = bool(re.search(r"\b(h|x|cx|cz|swap)\b", normalized))
    has_qubit_index = bool(re.search(r"q\d+|qubit\s*\d+", normalized))
    return has_gate and has_qubit_index


def _build_off_topic_response():
    return (
        "Posso ajudar apenas com pedidos sobre circuitos quanticos. "
        "Exemplos: criar circuito Bell, aplicar H no qubit 0 e CX(0,1), "
        "ou gerar circuito para superposicao e medir resultados."
    )


def _render_chat_message(message, image_width, index):
    user_prompt = message.get("prompt")
    if user_prompt:
        with st.chat_message("user"):
            st.write(user_prompt)

    with st.chat_message("assistant"):
        is_off_topic = message.get("message_type") == "off_topic"
        if not is_off_topic:
            circuit_text = message.get("circuit_text") or _planning_to_text(message.get("planning"))
            if circuit_text:
                st.code(circuit_text, language="text")
            else:
                st.info("Circuito textual nao disponivel neste item do historico.")

            image_bytes = _decode_image_from_base64(message.get("circuit_image_base64"))
            if image_bytes:
                st.image(image_bytes, caption="Imagem do circuito", width=image_width)
            else:
                st.caption("Imagem do circuito indisponivel para este item.")

        summary = message.get("summary")
        if summary:
            st.markdown(f"**Resumo do sintetizador:** {summary}")

    has_technical_data = any([
        message.get("requirements") is not None,
        message.get("planning") is not None,
        message.get("metrics") is not None,
        message.get("results") is not None,
    ])
    if has_technical_data:
        with st.expander(f"Saidas tecnicas da mensagem {index} (fora do chat)", expanded=False):
            st.subheader("Prompt")
            st.write(message.get("prompt"))
            st.subheader("Requisitos do Circuito")
            st.write(message.get("requirements"))
            st.subheader("Plano do Circuito")
            st.write(message.get("planning"))
            st.subheader("Metricas do Circuito")
            st.write(message.get("metrics"))
            st.subheader("Resultados")
            st.write(message.get("results"))


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


image_width = st.session_state.get("image_width", 700)

st.subheader("Chat")
if st.session_state.get("quantum_messages"):
    for idx, message in enumerate(st.session_state["quantum_messages"], start=1):
        _render_chat_message(message, image_width, idx)
else:
    st.info("Nenhuma mensagem no chat ainda.")


with st.form("quantum_circuit_form"):
    user_prompt = st.text_input("Descreva o circuito quântico que deseja criar:", key="input")
    executar = st.form_submit_button("Executar circuito")

if executar and user_prompt:
    if not _is_quantum_circuit_prompt(user_prompt):
        message_record = {
            "prompt": user_prompt,
            "summary": _build_off_topic_response(),
            "message_type": "off_topic",
        }
        st.session_state.setdefault("quantum_messages", []).append(message_record)

        if usuario_email:
            try:
                salvar_mensagens_quantum(usuario_email, st.session_state["quantum_messages"])
                st.success("Historico salvo no Firebase.")
            except Exception as e:
                st.error(f"Falha ao salvar no Firebase: {e}")

        st.rerun()

    with st.spinner("Processando circuito quântico..."):
        try:
            result = run_quantum_pipeline(user_prompt, max_attempts=5)

            circuit_text = str(result["qc"].draw(output="text"))
            circuit_image_base64 = _encode_image_to_base64(result["image_bytes"])

            if result["attempts"] >=1:
                st.info(
                    f"Circuito gerado com sucesso após {result['attempts']} tentativas de refinamento."
                )

            message_record = {
                "prompt": user_prompt,
                "requirements": result["requirements"].model_dump(),
                "planning": result["plan"].model_dump(),
                "metrics": result["metrics"].model_dump(),
                "results": result["measurement_counts"],
                "summary": result["summary"],
                "circuit_text": circuit_text,
                "circuit_image_base64": circuit_image_base64,
                "message_type": "circuit_response",
            }

        except RuntimeError as e:
            message_record = {
                "prompt": user_prompt,
                "summary": str(e),
                "message_type": "off_topic",
            }

    st.session_state.setdefault("quantum_messages", []).append(message_record)

    if usuario_email:
        try:
            salvar_mensagens_quantum(usuario_email, st.session_state["quantum_messages"])
        except Exception as e:
            st.error(f"Falha ao salvar no Firebase: {e}")

    st.rerun()

elif executar:
    st.warning("Digite uma descrição do circuito antes de executar.")



