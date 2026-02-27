from qiskit import QuantumCircuit
import matplotlib.pyplot as plt
qc = QuantumCircuit(2) # isso faz um circuito com 2 qubits
qc.h(0) # aplica a porta Hadamard no primeiro qubit (h) de hadamard
qc.cx(0, 1) # aplica a porta CNOT (cx) com o primeiro qubit como controle e o segundo como alvo
fig = qc.draw(output='mpl') # desenha o circuito usando Matplotlib
plt.show()

from qiskit.quantum_info import Pauli #serve para criar operadores de Pauli


