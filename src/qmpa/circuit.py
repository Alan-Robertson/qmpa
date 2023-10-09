import inspect
import copy
import numpy as np

from qmpa.virtual_chunk import Virtual_QChunk
from qmpa.allocator import QAllocator
from qmpa.gates import Gate, X, CNOT, Toffoli, Space, Alloc, Free

def vwrap(fn):
    def inner(*args, **kwargs):
        return fn(*[arg[:] for arg in args], **kwargs)
    return inner
    
# TODO: 
# - Register conversion
# - Non-local registers
# - Realloc
# - Symbolic resolution at execution

class Circuit():
    
    def __init__(self, debug=False):
        
        self.allocator = QAllocator()
        self.circuit = []
        
        self.toffoli_count = 0
        self.cnot_count = 0
        self.non_clifford_count = 0
        self.debug = debug
            
    def __call__(self, *regs, debug=False):
        vec = np.zeros(self.allocator.max_mem, dtype=np.int32)
        
        for gate in self.circuit:
            vec = gate(vec)
            
        if len(regs) > 0:
            return [vec[reg()] for reg in regs]
        
        return vec
    
    def readout(self, *regs):
        vals = self.__call__()
        return [int(''.join(map(str, vals[reg()]))[::-1], 2) for reg in regs]
    
    '''
        Display Functions
    '''
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return self.circuit_print()
    
    def circuit_to_latex(self):
        alloced_qubits = np.zeros(self.allocator.max_mem)
        
        latex_circuit = [[] for i in range(self.allocator.max_mem)]
        
        for gate in self.circuit:
            
            if type(gate) is Alloc:
                for i in gate.qargs():
                    alloced_qubits[i] = True
            if type(gate) is Free:
                for i in gate.qargs():
                    alloced_qubits[i] = False
                    
            for qarg, representation in zip(gate.qargs(), gate.representation()):
                latex_circuit[qarg].append(representation)
            self.latex_circuit_pad(latex_circuit, *gate.qargs, alloced_qubits=alloced_qubits)
        return latex_circuit
         
    def circuit_print(self):
        latex_circuit = self.circuit_to_latex()
        circ_str = ""
        for i in latex_circuit:
            circ_str += '&'
            for j in i:
                circ_str += "{} & ".format(j)
            circ_str += '\\\\\n'
        return circ_str

    def latex_circuit_pad(self, latex_circuit, *args, n=1, padding='\\qw', alloced_qubits=None):
        '''
            Pad non participating elements of the circuit
        '''
        for index, elements in enumerate(latex_circuit):
            if index not in args:
                if alloced_qubits is not None:
                    if alloced_qubits[index]:
                        elements += [padding] * n
                    else:
                        elements += [' '] * n
                else:
                    elements += [padding] * n
        return 
    
    '''
        Properties
    '''
    def circuit_len(self):
        return len(self.circuit)

    def counts(self):
        return (self.toffoli_count, self.cnot_count, self.non_clifford_count)
    
    
    '''
        Base Gate Operations
    '''
    def register(self, n_qubits, name=None, initial_value=0, **kwargs):
        reg = self.allocator.alloc(n_qubits, name=name, **kwargs)
        self.add_gate(Alloc(reg, name=name, initial_value=initial_value))
        return reg.virt()
    
    def anc_register(self, n_qubits, reg=None, name=None, initial_value=0, **kwargs):
        # Get stack frame from caller
        if reg is None:
            fn = id(inspect.currentframe().f_back)
            reg = self.allocator.anc_alloc(fn, n_qubits, name=name, **kwargs)
            self.add_gate(Alloc(reg, name=name, initial_value=initial_value))
        return reg

    def anc_free(self, reg, *args, **kwargs):
        fn = id(inspect.currentframe().f_back)
        if reg.anc_chunk == fn:
            self.allocator.anc_free(reg, fn)
            self.add_gate(Free(reg, *args, **kwargs))
        return
    
    def free(self, reg, end=None, start=None, final_value=0):
        if end is None and start is None:
            self.add_gate(Free(reg, final_value=final_value))
            reg.free()
            return
        if end > 0:
            self.add_gate(Free(reg[-end:], final_value=final_value))
            self.allocator.partial_free_end(reg, end)
        if start > 0:
            self.add_gate(Free(reg[:start], final_value=final_value))
            self.allocator.partial_free_start(reg, start)
        return
            
        
    def add_gate(self, gate):
        self.circuit.append(gate)
        self.toffoli_count += gate.toffoli_count
        self.cnot_count += gate.cnot_count
        self.non_clifford_count += gate.non_clifford_count
    
    
    def reverse(self, fn, *args, permit_rev_alloc=False, **kwargs):
        circuit_pt = len(self.circuit)
        fn(*args, **kwargs)
        for i, gate in enumerate(self.circuit[circuit_pt:]):
            if not permit_rev_alloc and type(gate) in (Free, Alloc):
                raise Exception(f"Cannot reverse function {fn}, contains Alloc or Free")
                
            if type(gate) is Free:
                circuit[circuit_pt + i] = Alloc(*gate.qargs, name=gate.name, initial_value=gate.final_value)
            if type(gate) is Alloc:
                circuit[circuit_pt + i] = Free(*gate.qargs, name=gate.name, final_value=gate.initial_value)
                
        self.circuit[circuit_pt:] = self.circuit[circuit_pt:][::-1]
        return
    
    '''
        Singular Gates
    '''
    def X(self, targ):
        self.add_gate(X(targ))
    
    def cnot(self, ctrl, targ):
        self.add_gate(CNOT(ctrl, targ))
    
    def toffoli(self, ctrl_a, ctrl_b, targ):
        self.add_gate(Toffoli(ctrl_a, ctrl_b, targ))

    '''
        Macros
    '''
    def Ccpy(self, ctrl, targ, cpy_reg=None, **kwargs):
        '''
        :: blank_alloc :: Allocated qubits that are not copied to
        Currently this only works because we guarantee the target of the mult is constructed
        From lowest to highest order and hence there are no high carries.
        '''
        
        if cpy_reg is None:
            cpy_reg = self.register(len(targs), **kwargs)
            
        for i in range(len(targ)):
            self.toffoli(ctrl, targ[i], cpy_reg[i])
        return cpy_reg

    def cpy(self, src, dst, **kwargs):
        '''
        :: cpy :: 
        Performs CNOTs from the control to the target
        '''
        
        for i in range(src.size):
            self.cnot(src[i], dst[i])
        return

    def MAJ(self, a, b, carry):
        '''
            Injects a MAJ gadget
        '''
        self.cnot(a, b)
        self.cnot(a, carry)
        self.toffoli(carry, b, a)
        return
  
    def UMA(self, a, b, carry):
        '''
            Injects a UMA gadget
        '''
        self.toffoli(carry, b, a)
        self.cnot(a, carry)
        self.cnot(carry, b)
        return
        
##################################
        
    def add(self,
            reg_a,
            reg_b,
            reg_carry = None,
            carry=True):
        '''
        reg_a(a_n)[i]     ->  reg_a(a_n)[i]
        reg_b(b_n)[i + 1] ->  reg_b(a_n + b_n)[i + 1]
        {reg_carry(0)[1]} ->  {reg_carry(0)[1]}
        '''
        n_qubits = len(reg_a)
        
        # Conditional alloc on reg_carry
        reg_carry = self.anc_register(1, reg=reg_carry, name='carry')
        
        # MAJ with carry
        self.MAJ(reg_a[0], reg_b[0], reg_carry[0])
        
        # MAJ sequence
        for i in range(1, n_qubits):
            self.MAJ(reg_a[i], reg_b[i], reg_a[i - 1])

        # Carry Bit
        if carry:
            self.cnot(reg_a[n_qubits - 1], reg_b[n_qubits])

        # UMA Sequence
        for i in range(n_qubits - 1, 0, -1):
            self.UMA(reg_a[i], reg_b[i], reg_a[i - 1])
        
        # UMA with carry
        self.UMA(reg_a[0], reg_b[0], reg_carry[0])
        
        # Conditional free on reg_carry
        self.anc_free(reg_carry)

        return 
    
    def subtract(self, 
                reg_a, 
                reg_b, 
                reg_carry = None, 
                carry=True):
        
        reg_carry = self.anc_register(1, reg=reg_carry, name='carry')
            
        self.reverse(self.add, reg_a, reg_b, reg_carry=reg_carry, carry=carry)
        
        self.anc_free(reg_carry)
    
    def multiply(self,
                 reg_a,
                 reg_b,
                 precision=None,
                 target_reg=None,
                 cpy_target_reg=None,
                 reg_carry=None,
                 name='MUL',
                 **kwargs):
        
        if precision is not None:
            assert precision > 0
        
        target_reg = self.anc_register(reg_a.size + reg_b.size + 1, reg=target_reg, name=name, **kwargs)
        cpy_target_reg = self.anc_register(reg_a.size + reg_b.size, reg=cpy_target_reg, name='MULCPY')
        reg_carry = self.anc_register(1, reg=reg_carry, name='carry')
            
        for i in range(reg_a.size):
            self.Ccpy(reg_a[i], reg_b, cpy_reg=cpy_target_reg)
            self.add(
                cpy_target_reg[:len(cpy_target_reg) - i],
                target_reg[i:],
                reg_carry=reg_carry
            )
            self.Ccpy(reg_a[i], reg_b, cpy_reg=cpy_target_reg)
            
        if precision is not None:
            precision_bit = target_reg.size - precision + 1
            for i in range(reg_a.size - 1, -1, -1):
                #precision_bit = i + reg_b.size + 1
                adder_high_bit = i + reg_b.size + 1 
                
                # Limit 
                if i > precision_bit:
                    continue
                
                if adder_high_bit > precision_bit:
                    adder_size = reg_b.size - (adder_high_bit - precision_bit)
                    
                    self.Ccpy(reg_a[i], reg_b[:adder_size], cpy_reg=cpy_target_reg[:adder_size])
                    self.subtract(
                        cpy_target_reg[:len(cpy_target_reg) - i],
                        target_reg[i:],
                        reg_carry=reg_carry,
                        carry=False
                    )
                    self.Ccpy(reg_a[i], reg_b[:adder_size], cpy_reg=cpy_target_reg[:adder_size])
                    
                else:
                                
                    self.Ccpy(reg_a[i], reg_b, cpy_reg=cpy_target_reg)
                    self.subtract(
                        cpy_target_reg[:len(cpy_target_reg) - i],
                        target_reg[i:],
                        reg_carry=reg_carry,
                    )
                    self.Ccpy(reg_a[i], reg_b, cpy_reg=cpy_target_reg)
            
        
        self.anc_free(cpy_target_reg)
        self.anc_free(reg_carry)
            
        return target_reg
    
    # TODO Register Realloc
    
    def divide(self, 
               reg_a,
               reg_b, 
               cpy_target_reg=None,
               reg_carry=None):
        reg_r = self.register(reg_a.size + 1, name='Remainder') # Remainder, high bit needed
        reg_q = self.register(reg_a.size - reg_b.size + 1, name='Quotient') # Quotient
        
        cpy_target_reg = self.anc_register(reg_a.size + 1, name='DIVANC', reg=cpy_target_reg)
        reg_carry = self.anc_register(reg_a.size + 1, name='Carry', reg=reg_carry)

        # Initial copy to the remainder column
        self.cpy(reg_a[reg_a.size - reg_b.size:], reg_r[reg_a.size - reg_b.size:])
        for i in range(reg_a.size - reg_b.size + 1):
            
            targ_index = reg_a.size - reg_b.size - i
            
            if i > 0:
                self.cpy(reg_a[targ_index], cpy_target_reg[0])
                self.add(cpy_target_reg[:reg_r.size - targ_index - 1], reg_r[targ_index:], reg_carry=reg_carry)
                self.cpy(reg_a[targ_index], cpy_target_reg[0])

            self.subtract(reg_b, reg_r[reg_a.size - reg_b.size - i: reg_r.size - i], reg_carry=reg_carry)
            self.cnot(reg_r[-1 - i], reg_q[-1 - i])

            self.Ccpy(reg_q[-1 - i], reg_b, cpy_reg=cpy_target_reg)
            self.add(cpy_target_reg[:reg_b.size], reg_r[reg_a.size - reg_b.size - i: reg_r.size - i], reg_carry=reg_carry)
            self.Ccpy(reg_q[-1 - i], reg_b, cpy_reg=cpy_target_reg)
            self.X(reg_q[-1 - i])
            
        self.anc_free(cpy_target_reg)
        self.anc_free(reg_carry)

        return reg_r, reg_q
