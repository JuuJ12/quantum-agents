import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel, Field #usamos o pydantic para dizer que tipo de saída deve ser aceita
                                      #LLms geram textos, mas as aplicações precisam de DADOS eu é com o pydantic que nos estruturamos esses dados
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Agents_Classes.agents_classes import StructuredCircuit, CircuitPlan
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
    return qc, counts