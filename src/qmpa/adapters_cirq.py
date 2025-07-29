import cirq
import qmpa

def to_cirq_X(qmpa_gate, register):
    args = qmpa_gate.qargs()
    cirq_args = list(map(register.__getitem__, args))
    gate = cirq.X(*cirq_args)
    return gate

def to_cirq_CNOT(qmpa_gate, register):
    args = qmpa_gate.qargs()
    cirq_args = list(map(register.__getitem__, args))
    gate = cirq.CNOT(*cirq_args)
    return gate

def to_cirq_Toffoli(qmpa_gate, register):
    args = qmpa_gate.qargs()
    cirq_args = list(map(register.__getitem__, args))
    gate = cirq.CCX(*cirq_args)
    return gate

def from_cirq_X(cirq_gate, register):
    args = cirq_gate.qubits 
    qmpa_args = list(map(register.__getitem__, args)) 
    gate = qmpa.gates.X(*qmpa_args) 
    return gate

def from_cirq_CNOT(cirq_gate, register):
    args = cirq_gate.qubits 
    qmpa_args = list(map(register.__getitem__, args)) 
    gate = qmpa.gates.CNOT(*qmpa_args) 
    return gate


def from_cirq_Toffoli(cirq_gate, register):
    args = cirq_gate.qubits 
    qmpa_args = list(map(register.__getitem__, args))
    gate = qmpa.gates.Toffoli(*qmpa_args) 
    return gate


to_cirq_adapter = {
    qmpa.gates.X : to_cirq_X,
    qmpa.gates.CNOT : to_cirq_CNOT,
    qmpa.gates.Toffoli : to_cirq_Toffoli,
}

from_cirq_adapter = {
    cirq.ops.common_gates.XPowGate: from_cirq_X, 
    cirq.ops.pauli_gates._PauliX: from_cirq_X, 
    cirq.ops.common_gates.CXPowGate: from_cirq_CNOT,
    cirq.ops.three_qubit_gates.CCXPowGate: from_cirq_Toffoli,
}

def to_cirq(circ: qmpa.circuit.Circuit) -> cirq.Circuit:
    '''
        Maps a QMPA circuit to cirq
    '''

    n_qubits = circ.allocator.max_mem 
    cirq_circuit = cirq.Circuit()
    register = [cirq.NamedQubit(str(i)) for i in range(n_qubits)]

    for gate in circ.circuit:
        cirq_gate_constructor = to_cirq_adapter.get(type(gate), None)
        if cirq_gate_constructor is not None:
            cirq_gate = cirq_gate_constructor(gate, register) 
            cirq_circuit.append(cirq_gate)
    return cirq_circuit
     

def from_cirq(
        circ: cirq.Circuit,
        *,
        n_qubits: int = None,
        initial_value: int = 0
        ) -> qmpa.circuit.Circuit: 
    '''
        From cirq adapter
        :: circ : cirq.Circuit :: Cirq circuit 
        :: n_qubits : int :: Manual override for number of qubits 
        :: initial_value : int :: Sets the initial value of the qmpa object 
        Returns a qmpa circuit
    '''

    circ = decompose_qmpa(circ)

    if n_qubits is None:
        n_qubits = len(circ.all_qubits())
    
    qmpa_circ = qmpa.circuit.Circuit()

    register = qmpa_circ.register(n_qubits, 'cirq_register', initial_value)

    cirq_register = list(circ.all_qubits())
    cirq_register.sort(key=key_cirq_qubits)
    register_map = {qubit: register[i] for i, qubit in enumerate(cirq_register)}
    print(register_map)

    for layer in circ:
        for gate in layer:
            qmpa_gate_constructor = from_cirq_adapter.get(type(gate.gate), None) 
            qmpa_gate = qmpa_gate_constructor(gate, register_map)
            if qmpa_gate is not None:
                qmpa_circ.add_gate(qmpa_gate)

    return qmpa_circ


cirq_op_table = (type(cirq.CCX), type(cirq.CNOT), type(cirq.X)) 
def keep_qmpa(op):
    '''
        Cirq decomposition helper
        Only keeps classical gates
    '''
    return isinstance(op.gate, cirq_op_table)

def decompose_qmpa(cirq_circuit):
    '''
        Cirq decomposition helper
        Wraps the keep function and decomposes into qmpa gates
    '''
    return cirq.Circuit(cirq.decompose(cirq_circuit, keep=keep_qmpa))


def key_cirq_qubits(qubit):
    '''
        Sorting primitive for qubits
    '''

    if isinstance(qubit, cirq.devices.line_qubit.LineQubit):
        return qubit.x
    else:
        return 1e20 + qubit.id 
