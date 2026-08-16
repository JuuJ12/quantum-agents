from enum import Enum #serve para criar um tipo de dado enumerado, ou seja, um tipo de dado que pode assumir um conjunto finito de valores, nesse caso, os tipos de circuitos que o agente construtor pode criar
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class CircuitType(str, Enum):
    COMPUTATIONAL = "computational"
    BELL = "bell"
    GHZ = "ghz"
    SUPERPOSITION = "superposition"


class StructuredCircuit(BaseModel): 
    objective: str = Field(description="The objective of the circuit")
    num_qubits: int = Field(description="Number of qubits in the circuit")
    target_state: str = Field(description="Desired final quantum state")
    circuit_type: CircuitType = Field(
        default=CircuitType.COMPUTATIONAL,
        description="Type of target circuit/state: computational, bell, ghz or superposition",
    )


class Gate(BaseModel): 
    gate_name: Literal["h", "x", "cx", "rz"] = Field(description="Name of the quantum gate (h, x, cx, rz)")
    target_qubits: List[int] = Field(description="List of target qubits for the gate")
    control_qubits: Optional[int | List[int]] = Field(
        default=None,
        description="Control qubit index (or list) if needed",
    )
    theta: Optional[float] = Field(
        default=None,
        description="Rotation angle in radians used only when gate_name is rz",
    )


class CircuitPlan(BaseModel): 
    gates: List[Gate] = Field(
        description="List of quantum gates to be applied in the circuit"
    )

class CircuitMetrics(BaseModel):
    fidelity: float = Field(description="Fidelity of the executed circuit compared to the target state")
    depth: int = Field(description="Depth of the executed circuit")
    gate_count: int = Field(description="Total number of gates used in the executed circuit")
    attempts: int = Field(description="Number of attempts made to execute the circuit")


class VerificationResult(BaseModel):
    approved: bool
    reason: Optional[str] = None


class IsQuantumAwnser(BaseModel):
    is_quantum: bool
