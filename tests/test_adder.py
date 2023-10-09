import pytest
import numpy as np

from qmpa.circuit import Circuit

n_qubits = 10
n_tests = 1000

def test_addition():
    for _ in range(n_tests):
        x, y = np.random.randint(2 ** n_qubits, size=(2))

        c = Circuit()
        r_a = c.register(n_qubits, 'A', x)
        r_b = c.register(n_qubits + 1, 'B', y)
        c.add(r_a, r_b)

        assert(x + y == c.readout(r_b)[0])

def test_addition_preallocated_carry():
    for _ in range(n_tests):
        x, y = np.random.randint(2 ** n_qubits, size=(2))

        c = Circuit()
        reg_carry = c.register(1, 'carry')
        r_a = c.register(n_qubits, 'A', x)
        r_b = c.register(n_qubits + 1, 'B', y)
        c.add(r_a, r_b, reg_carry=reg_carry)
        c.free(reg_carry)
        
        assert(x + y == c.readout(r_b)[0])

def test_addition_reverse():
    for _ in range(n_tests):
        x, y = np.random.randint(2 ** n_qubits, size=(2))

        c = Circuit()
        reg_carry = c.register(1, 'carry')
        r_a = c.register(n_qubits, 'A', x)
        r_b = c.register(n_qubits + 1, 'B', y)
        c.add(r_a, r_b)
        FAILED_DUE_TO_ALLOC = True
        try:
            # This should fail
            c.reverse(c.add, r_a, r_b)
            FAILED_DUE_TO_ALLOC = False
        except:
            assert FAILED_DUE_TO_ALLOC
            c.reverse(c.add, r_a, r_b, reg_carry=reg_carry)
        c.free(reg_carry)
                

if __name__ == '__main__':
    pytest.main()
