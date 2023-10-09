import numpy as np

class Virtual_QChunk():
    def __init__(self, register, *indices, name=None):    
        self.register = register
        self.indices = np.array(indices, dtype=np.int32)
        self.size = len(self)
        self.anc_chunk = None
    
    def __getitem__(self, *keys, name=None):
        indices = []
        for key in keys:
            if isinstance(key, slice):
                start = [key.start, 0][key.start is None]
                stop = [key.stop, len(self)][key.stop is None]
                if start < 0:
                    start = self.size - start
                if stop < 0:
                    stop = self.size - stop
                if key.step is None:
                    key = (start, stop)
                else:
                    key = (start, stop, step)
                indices += list(range(*key))
            elif isinstance(key, list) or isinstance(key, tuple) or isinstance(key, np.ndarray):
                indices += list(key)
            elif isinstance(key, int):
                indices += [key]
            elif isinstance(key, Virtual_QChunk):
                if key.register != self.register:
                    raise Exception("Joint register chunks not yet supported")
                indices += key.indices
            else:
                raise Exception("Unknown type of Key")
        return self.idx(*indices, name=name)
    
    def idx(self, *indices, name=None):
        return Virtual_QChunk(self.register, *self.indices[list(indices)], name=name)
    
    def __call__(self, *indices):
        if len(indices) == 0:
            return self(*list(range(len(self.indices))))
        return self.register(*self.indices[list(indices)])
    
    def __add__(self, reg):
        # Todo support joins between different virtual registers
        if reg.register == self.register:
            return Virtual_QChunk(self.register, *self.indices, *reg.indices)
        else:
            raise Exception("Can only join virtual registers of the same base register")
    
    def __repr__(self):
        return f"{self.register.__repr__()}:{self.indices}"
        
    def __len__(self):
        return len(self.indices)
    
    def free(self):
        pass
    
    def anc_free(self, *args, **kwargs):
        pass
    
    def virt(self):
        return self
