import pytest
import numpy as np

from qmpa.circuit import Circuit

n_qubits = 10
n_tests = 1000

def test_subtraction():
    # Test with implicit carry
    for _ in range(n_tests):
        x, y = np.random.randint(2 ** n_qubits, size=(2))

        c = Circuit()
        r_a = c.register(n_qubits, 'A', x)
        r_b = c.register(n_qubits + 1, 'B', y)
        c.subtract(r_a, r_b)

        assert((y - x) % (2 ** (r_b.size)) == c.readout(r_b)[0])

def test_subtraction_preallocated_carry():
# Test with pre-alloced carry
    for _ in range(n_tests):
        x, y = np.random.randint(2 ** n_qubits, size=(2))

        c = Circuit()
        reg_carry = c.register(1, 'carry')
        r_a = c.register(n_qubits, 'A', x)
        r_b = c.register(n_qubits + 1, 'B', y)
        c.subtract(r_a, r_b)
        c.free(reg_carry)

        assert((y - x) % (2 ** (r_b.size)) == c.readout(r_b)[0])
   
def test_subtraction_reverse():
    # Test Reversible Subtract
    for _ in range(n_tests):
        x, y = np.random.randint(2 ** n_qubits, size=(2))

        c = Circuit()
        reg_carry = c.register(1, 'carry')
        r_a = c.register(n_qubits, 'A', x)
        r_b = c.register(n_qubits + 1, 'B', y)
        c.subtract(r_a, r_b)
        c.reverse(c.subtract, r_a, r_b, reg_carry=reg_carry)
        c.free(reg_carry)

        assert(y == c.readout(r_b)[0])

if __name__ == '__main__':
    pytest.main()
