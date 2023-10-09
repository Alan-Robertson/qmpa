import pytest
import numpy as np

from qmpa.circuit import Circuit

n_qubits = 5 
n_tests = 100

def test_multiply():
    # Test multiplication
    for i in range(n_tests):
        x, y = np.random.randint(2 ** n_qubits, size=(2))

        t = i % 2
        
        c = Circuit()
        r_a = c.register(n_qubits, 'A', x)
        r_b = c.register(n_qubits, 'B', y)
        r_d = c.multiply(r_a, r_b)

        assert(x * y == c.readout(r_d)[0])
        
# Test Reversible multiplication
def test_multiply_reverse():
    for i in range(n_tests):
        x, y = np.random.randint(2 ** n_qubits, size=(2))

        t = i % 2
        
        c = Circuit()
        r_a = c.register(n_qubits, 'A', x)
        r_b = c.register(n_qubits, 'B', y)
        r_d = c.multiply(r_a, r_b)
        try:
            r_d = c.reverse(c.multiply, r_a, r_b, target_reg=r_d)
            assert(0 == c.readout(r_d)[0])
        except:
            pass
            

if __name__ == '__main__':
    pytest.main()
