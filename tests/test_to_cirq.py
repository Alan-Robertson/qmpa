import qmpa

import numpy as np

from qmpa.circuit import Circuit
from qmpa import adapters_cirq 

n_qubits = 4 
n_tests = 100

def test_initial_value(n_qubits=4):
    for _ in range(n_tests):
       x, y = np.random.randint(2 ** n_qubits, size=(2))

       c = Circuit()
       r_a = c.register(n_qubits, 'A', x)
       r_b = c.register(n_qubits + 1, 'B', y)

       joint_value = (y << n_qubits) | x 

       cirq_circuit = adapters_cirq.to_cirq(c) 
       qmpa_circuit = adapters_cirq.from_cirq(cirq_circuit, n_qubits=(2 * n_qubits + 1), initial_value=joint_value)
       assert (c() == qmpa_circuit()).all()

def test_addition(n_qubits=e):
    for _ in range(n_tests):
        x, y = np.random.randint(2 ** n_qubits, size=(2))

        c = Circuit()
        r_a = c.register(n_qubits, 'A', x)
        r_b = c.register(n_qubits + 1, 'B', y)
        c.add(r_a, r_b)

        joint_value = (y << n_qubits) | x 

        cirq_circuit = adapters_cirq.to_cirq(c) 
        qmpa_circuit = adapters_cirq.from_cirq(cirq_circuit, initial_value=joint_value)
      
        out_register = qmpa_circuit.allocator[1]
        out_value = qmpa_circuit.readout(out_register)[0]
        out_r_a = out_value & ((1 << n_qubits) - 1)
        out_r_b = out_value >> n_qubits 

        assert (c() == qmpa_circuit()).all() 

        assert x == out_r_a
        assert x + y == out_r_b

