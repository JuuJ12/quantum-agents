import os
import sys
import io
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Agents_Classes.agents_classes import StructuredCircuit, CircuitPlan, CircuitMetrics, VerificationResult
load_dotenv()

llama = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=(os.getenv("GROQ_API_KEY")),
    temperature= 0.0,
)

groq_comp = ChatGroq(
    model="groq/compound",
    api_key=(os.getenv("GROQ_API_KEY")),
    temperature= 0.0
)

def agent_extrator(input: str) -> StructuredCircuit:
    agent_extrator = llama.with_structured_output(schema=StructuredCircuit)
    prompt_agent_extrator =  ChatPromptTemplate.from_messages([
        ("system", "You are an expert quantum circuit interpreter." \
                                "Extract only structured circuit requirements."),
        ("human", "{input}")
    ])
    chain_agent_extrator = prompt_agent_extrator | agent_extrator
    response = chain_agent_extrator.invoke({'input': input})
    return response

def agent_builder(input: StructuredCircuit) -> CircuitPlan:
    anget_builder = llama.with_structured_output(schema=CircuitPlan)
    prompt_agent_builder = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a quantum circuit designer. "
        "Generate a list of quantum gates to satisfy the objective. "
        "Only use gates: h, x, cx. "
        "Return structured output only."
    ),
    ("human", "{input}")
    ])
    chain_agent_builder = prompt_agent_builder | anget_builder
    response = chain_agent_builder.invoke({'input': input.model_dump()})
    return response


def agent_verifier_plan(
    requirements: StructuredCircuit,
    plan: CircuitPlan
) -> VerificationResult:
    """
    Verifies whether the CircuitPlan is coherent with the StructuredCircuit.
    Returns approved=True if valid, otherwise approved=False with a reason.
    """
    verifier = llama.with_structured_output(schema=VerificationResult)

    prompt_verifier = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a quantum circuit verifier. "
            "Given the user's requirements and a proposed gate plan, "
            "check if the plan is coherent and can achieve the objective. "
            "Verify: correct number of qubits, gates are valid (only h, x, cx), "
            "cx gates have distinct control and target qubits, "
            "and the plan is likely to produce the target state. "
            "Return approved=True if the plan is correct, "
            "or approved=False with a clear reason if something is wrong."
        ),
        (
            "human",
            "Requirements: {requirements}\n"
            "Proposed plan: {plan}"
        )
    ])

    chain = prompt_verifier | verifier
    result = chain.invoke({
        "requirements": requirements.model_dump(),
        "plan": plan.model_dump()
    })
    return result

def agent_executor_circuit(input: CircuitPlan):
    used_qubits = []
    for gate in input.gates:
        used_qubits.extend(gate.target_qubits) # extende serve para adicionar os elementos de uma lista a outra lista, ou seja, ele vai pegar os qubits alvo de cada porta e adicionar na lista de qubits usados
        if gate.control_qubits is not None:
            if isinstance(gate.control_qubits, list): #isistance serve para verificar se o controle de qubits é uma lista ou um único elemento, porque a porta cx pode ter um ou mais qubits de controle
                used_qubits.extend(gate.control_qubits)
            else:
                used_qubits.append(gate.control_qubits)

    num_qubits = max(used_qubits) + 1
    qc = QuantumCircuit(num_qubits, num_qubits)

    for gate in input.gates:
        if gate.gate_name == "h":
            for target in gate.target_qubits:
                qc.h(target)

        elif gate.gate_name == "x":
            for target in gate.target_qubits:
                qc.x(target)

        elif gate.gate_name == "cx":
            controls = gate.control_qubits
            if controls is None:
                raise ValueError("Gate 'cx' requer control_qubits.")
            if not isinstance(controls, list):
                controls = [controls]

            for control in controls:
                for target in gate.target_qubits:
                    qc.cx(control, target)

    qc.measure(range(num_qubits), range(num_qubits))

    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    result = simulator.run(compiled_circuit, shots=1024).result()
    counts = result.get_counts(compiled_circuit) #serve para contar quantas vezes cada resultado foi obtido na execução do circuito, ou seja, ele vai contar quantas vezes obteve 00, 01, 10 e 11, por exemplo, se for um circuito de 2 qubits

    circuit_image_bytes = None
    try:
        fig = qc.draw(output="mpl") #serve para desenhar o circuito usando Matplotlib, e o output "mpl" indica que queremos a saída em formato de figura do Matplotlib
        buffer = io.BytesIO() #serve para criar um buffer de bytes em memória, ou seja, ele vai armazenar a imagem do circuito em formato de bytes para que possamos exibir na interface do usuário
        fig.savefig(buffer, format="png", bbox_inches="tight") #serve para salvar a figura do circuito no buffer de bytes, usando o formato PNG e ajustando os limites da figura para que fique mais compacta
        buffer.seek(0) # serve para mover o cursor do buffer para o início, ou seja, ele vai garantir que a leitura dos bytes comece do início da imagem salva no buffer
        circuit_image_bytes = buffer.getvalue() #serve para obter os bytes da imagem do circuito a partir do buffer, ou seja, ele vai ler os bytes da imagem salva no buffer e armazenar na variável circuit_image_bytes para que possamos exibir na interface do usuário
    except Exception:
        circuit_image_bytes = None

    return qc, counts, circuit_image_bytes

def _normalize_target_state(target_state: str) -> str:
    cleaned = target_state.strip().lower().replace("|", "").replace(">", "")
    cleaned = cleaned.replace(" ", "")
    return cleaned


def calculate_fidelity(counts: dict, ideal_state: str) -> float:
    # For measured circuits, use probability mass on expected outcomes.
    if not counts:
        return 0.0

    target = _normalize_target_state(ideal_state)
    total_shots = sum(counts.values())
    if total_shots == 0:
        return 0.0

    # If the target is a descriptive Bell/entangled request, use correlated/anti-correlated outcomes.
    entangled_keywords = ("entangled", "bell", "phi", "psi")
    if any(keyword in target for keyword in entangled_keywords):
        correlated = counts.get("00", 0) + counts.get("11", 0)
        anticorrelated = counts.get("01", 0) + counts.get("10", 0)
        return float(max(correlated, anticorrelated) / total_shots)

    hits = counts.get(target, 0)
    return float(hits / total_shots)

def calculate_depth(circuit: QuantumCircuit) -> int:
    return circuit.depth()  #retorna a profundidade do circuito, ou seja, ele vai contar quantas camadas de portas existem no circuito para dar uma medida da complexidade do circuito

def agent_metric(circuit: QuantumCircuit, ideal_state: str, counts: dict) -> CircuitMetrics:
    fidelity = calculate_fidelity(counts, ideal_state)
    depth = calculate_depth(circuit)
    gate_count = circuit.size() #conta o total de instruções no circuito (incluindo medições), útil como métrica de complexidade
    return CircuitMetrics(fidelity=fidelity, depth=depth, gate_count=gate_count)

def agent_synthesizer(requirements: dict, planning: dict, metrics: dict) -> str:
    agent_synthesizer = llama
    prompt_agent_synthesizer = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an agent who will provide a general summary of the results of the requirements, "
            "planning, and final metrics of the generated quantum circuits."
        ),
        (
            "human",
            "Requirements: {requirements}\n"
            "Planning: {planning}\n"
            "Metrics: {metrics}\n"
            "Write a concise summary in Portuguese."
        ),
    ])
    chain_agent_synthesizer = prompt_agent_synthesizer | agent_synthesizer
    response = chain_agent_synthesizer.invoke({'requirements': requirements, 'planning': planning, 'metrics': metrics})
    return response.content


def agent_verifier_execution(
    counts: dict,
    requirements: StructuredCircuit,
    metrics: "CircuitMetrics"
) -> VerificationResult:
    """
    Verifies whether the simulation counts are compatible with the objective.
    Uses deterministic rules instead of an LLM.
    """
    total_shots = sum(counts.values())
    if total_shots == 0:
        return VerificationResult(
            approved=False,
            reason="Simulação retornou zero shots."
        )

    fidelity_threshold = 0.4

    if metrics.fidelity < fidelity_threshold:
        dominant_state = max(counts, key=counts.get)
        dominant_pct = round(counts[dominant_state] / total_shots * 100, 1)
        return VerificationResult(
            approved=False,
            reason=(
                f"Fidelidade baixa ({metrics.fidelity:.2f}). "
                f"Estado dominante: |{dominant_state}⟩ com {dominant_pct}%. "
                f"Estado alvo esperado: {requirements.target_state}."
            )
        )

    return VerificationResult(approved=True)


def run_quantum_pipeline(
    user_prompt: str,
    max_attempts: int = 3
) -> dict:
    """
    Executes the full pipeline with verification and retry.
    Returns a dict with all results, or raises RuntimeError if a valid
    circuit cannot be produced after max_attempts.
    """

    requirements = agent_extrator(user_prompt)
    last_rejection_reason = None

    for attempt in range(1, max_attempts + 1):
        if last_rejection_reason:
            feedback_input = requirements.model_copy(update={
                "objective": (
                    f"{requirements.objective} "
                    f"[CORREÇÃO NECESSÁRIA - tentativa {attempt}: {last_rejection_reason}]"
                )
            })
            plan = agent_builder(feedback_input)
        else:
            plan = agent_builder(requirements)

        plan_check = agent_verifier_plan(requirements, plan)
        if not plan_check.approved:
            last_rejection_reason = f"Plano inválido: {plan_check.reason}"
            continue

        try:
            qc, counts, image_bytes = agent_executor_circuit(plan)
        except Exception as exc:
            last_rejection_reason = f"Erro na execução do circuito: {str(exc)}"
            continue

        metrics = agent_metric(qc, requirements.target_state, counts)

        exec_check = agent_verifier_execution(counts, requirements, metrics)
        if not exec_check.approved:
            last_rejection_reason = f"Resultado inválido: {exec_check.reason}"
            continue

        summary = agent_synthesizer(
            requirements=requirements.model_dump(),
            planning=plan.model_dump(),
            metrics=metrics.model_dump()
        )

        return {
            "success": True,
            "attempts": attempt,
            "requirements": requirements,
            "plan": plan,
            "qc": qc,
            "counts": counts,
            "image_bytes": image_bytes,
            "metrics": metrics,
            "summary": summary,
        }

    raise RuntimeError(
        f"Não foi possível construir um circuito válido após {max_attempts} tentativas. "
        f"Último problema: {last_rejection_reason}"
    )