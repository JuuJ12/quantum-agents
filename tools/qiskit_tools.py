from qiskit import QuantumCircuit 
from qiskit_aer import AerSimulator, execute 

def criar_circuito(descricao_circuito : dict)-> dict:
    circuito = QuantumCircuit(descricao_circuito['num_qubits'])
    
    for porta in descricao_circuito['portas']:
        if porta['tipo'] == 'H':
            circuito.h(porta['qubits'][0])
        elif porta['tipo'] == 'X':
            circuito.x(porta['qubits'][0])
        elif porta['tipo'] == 'CX':
            circuito.cx(porta['qubits'][0], porta['qubits'][1])
    
    return circuito