import numpy as np 

class QArgsGroup():
    '''
    Group of QArgs object
    Used when passing to functions
    '''
    def __init__(self, *qargs, name=None):
        self.qargs=qargs
        self.name=name
    def __call__(self, idx=None):
        if idx is None:
            return np.array([i() for i in self.qargs]).flatten()
        return np.array([i() for i in self.qargs]).flatten()[idx]
    def __len__(self):
        return sum([len(i) for i in self.qargs])
    def __iter__(self):
        return iter(self())
    def __getitem__(self, *keys, name=None):
        indices = []
        for key in keys:
            if isinstance(key, slice):
                start = [key.start, 0][key.start is None]
                stop = [key.stop, len(self)][key.stop is None]
                if key.step is None:
                    key = (start, stop)
                else:
                    key = (start, stop, step)
                indices += list(range(*key))
            elif isinstance(key, list) or isinstance(key, tuple) or isinstance(key, np.ndarray):
                indices += list(key)
            elif isinstance(key, int):
                indices += [key]
            else:
                raise Exception("Unknown type of Key")
        return self.idx(*indices, name=name)
    
    def idx(self, *indices, name=None):
        return QArgsGroup(*[self.qargs[i] for i in indices], name=name)   
