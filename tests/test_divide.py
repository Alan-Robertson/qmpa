import pytest
import numpy as np

from qmpa.circuit import Circuit

n_qubits = 10
n_tests = 1000

def test_division():
    for i in range(n_tests):

        # Test divsion
        for i in range(n_tests):
            x, y = np.random.randint(2 ** n_qubits, size=(2))
            obj = [x + 1, y + 1] # Avoiding div zero
            obj.sort(reverse=True)
            x, y = obj
        c = Circuit()

        x_len = int(np.floor(np.log2(x)) + 1)
        y_len = int(np.floor(np.log2(y)) + 1)

        reg_a = c.register(x_len, 'A', x)
        reg_b = c.register(y_len, 'B', y)
        reg_r, reg_q = c.divide(reg_a, reg_b)

        assert (c.readout(reg_r)[0] + c.readout(reg_q)[0] * y == x)

if __name__ == '__main__':
    pytest.main()
