from qmpa.constraints import constrain
from qmpa.qargs import QArgsGroup

int_to_bin = lambda x : list(map(int, list(bin(x)[2:])[::-1]))
bin_to_int = lambda x : int(''.join(map(str, x))[::-1], 2)

class Gate():
    def __init__(self, *qargs,
                cnot_count = 0,
                toffoli_count = 0,
                non_clifford_count = 0,
                ident_rep = None,
                validate=True):
        self.qargs = QArgsGroup(*qargs)
        self.cnot_count = cnot_count
        self.toffoli_count = toffoli_count
        self.non_clifford_count = non_clifford_count
        self.ident_rep = ident_rep # Number of sequential identical gates to identity
        if validate:
            self.validate()
    
    def validate(self):
        self.qargs()
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return str(self.representation())
    
    def representation(self):
        return [""]
    
    def __call__(self, vec):
        return vec
    
    def __len__(self):
        return len(self.qargs)
    
    
class X(Gate):
    def __init__(self, targ):
        super().__init__(
            targ,
            ident_rep = 2
        )
        self.targ = self.qargs
        
    def __call__(self, vec):
        vec[self.targ()] ^= 1
        return vec

    def representation(self):
        return ['\\targ{}'] * len(self.targ())
    
class CNOT(Gate):
    #@constrain('|$1| = 1', '|$2| = 1')
    def __init__(self, ctrl, targ):
        super().__init__(
            ctrl, targ,
            cnot_count = 1,
            ident_rep = 2
        )
        self.ctrl = self.qargs[0]
        self.targ = self.qargs[1]
        
    def representation(self):
        return ["\\ctrl{{{x}}}".format(x=self.targ()[0] - self.ctrl()[0]), '\\targ{}']
    
    def __call__(self, vec):
        vec[self.targ()] ^= vec[self.ctrl()]
        return vec

                                           
        
class Toffoli(Gate):
    #@constrain('|$1| = 1', '|$2| = 1', '|$3| = 1')
    def __init__(self, ctrl_a, ctrl_b, targ):
        super().__init__(
            ctrl_a, ctrl_b, targ,
            # Different constructions of this gate will vary with these counts
            cnot_count = 6,
            toffoli_count = 1,
            non_clifford_count = 7,
            ident_rep = 2
        )
        self.ctrl_a = self.qargs[0]
        self.ctrl_b = self.qargs[1]
        self.targ = self.qargs[2]
        
    def representation(self):
        return ["\\ctrl{{{x}}}".format(x=self.targ()[0] - self.ctrl_a()[0]),
             "\\ctrl{{{x}}}".format(x=self.targ()[0] - self.ctrl_b()[0]),
             '\\targ{}']
    
    def __call__(self, vec):
        vec[self.targ()] ^= vec[self.ctrl_a()] & vec[self.ctrl_b()]
        return vec

class Space(Gate):
    def __init__(self, *args, **kwargs):
        super().__init__([])
    def __call__(self, vec, *args, **kwargs):
        return vec 
    
    
class Alloc(Gate):
    def __init__(self, *args, name='', initial_value=0):
        self.initial_value = initial_value
        super().__init__(*args, validate=False)
        alloced_mem = args
        self.name = name
        
    def __call__(self, vec):
        for i, val in enumerate(int_to_bin(self.initial_value)):
            vec[self.qargs(i)] ^= val
        return vec
    
    def representation(self):
        return ([f"\lstick[wires={len(self)}]{{$\ket{{{self.initial_value}}}_{{\\text{{{self.name}}}}}$}} \setwiretype{{q}}"] 
                + ([" "] * (len(self) - 1)))
        
class Free(Gate):
    def __init__(self, *args, final_value=0, assert_cleanup=True):
        self.final_value = final_value
        self.assert_cleanup = assert_cleanup
        super().__init__(*args)
        
    def __call__(self, vec):
        if self.assert_cleanup:
            assert(bin_to_int([vec[i] for i in self.qargs()]) == self.final_value)
        for i in self.qargs:
            vec[i] = 0    
        return vec
    def representation(self):
            return [f"\\trash{{\ket{{{self.final_value}}}}}\setwiretype{{n}}"] * len(self)
        
