from pydantic import BaseModel, Field
from typing import Optional, List


class StructuredCircuit(BaseModel): # estrutura de dados para requisição do circuito, ou seja, o usuário vai pedir e vai ficar nesse formato
    objective: Optional[str] = Field(description="The objective of the circuit")
    num_qubits: Optional[int] = Field(description="Number of qubits in the circuit")
    target_state: Optional[str] = Field(description="Desired final quantum state")


class Gate(BaseModel): # estrutura de dados para a construção do circuito. Para cada qubit ele vai aplicar uma porta, e essa é a estrutura de dados para cada porta, ou seja, o nome da porta, os qubits alvo e os qubits de controle (se houver)
    gate_name: str = Field(description="Name of the quantum gate (h, x, cx)")
    target_qubits: List[int] = Field(description="List of target qubits for the gate")
    control_qubits: Optional[int] = Field(
        default=None,
        description="Control qubit index if needed",
    )


class CircuitPlan(BaseModel): # esturura da lista de portas que o agente construtor vai retornar, ou seja, a lista de portas que ele vai aplicar no circuito para atingir o objetivo do usuário
    gates: List[Gate] = Field(
        description="List of quantum gates to be applied in the circuit"
    )
