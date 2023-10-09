import numpy as np
from qmpa.virtual_chunk import Virtual_QChunk

class QArgs():
    def __init__(self, regs, indices):
        self.regs = regs
        self.indices = indices
    def __call__(self):
        return [reg[index] for reg, index in zip(regs, indices)]

class QAllocator():
    '''
        Manages memory for quantum registers
    '''
    def __init__(self):
        self.chunks = [QChunk(0, 0, 0, None, None, allocator=self, name='HEAD')]
        self.max_mem = 0
               
    def __call__(self, *args, **kwargs):
        return self.alloc(*args, **kwargs)
    
    def anc_alloc(self, fn, *args, **kwargs):
        return self.alloc(*args, anc_chunk=fn, **kwargs)
    
    def alloc(self, size, name=None, padding=0, anc_chunk=False):
        
        # For higher methods that need to add additional qubits to a register
        size += padding
        
        # See if there's free space in the existing region of memory
        for i, chunk in enumerate(self.chunks):
            if chunk.trailing_free >= size: # Found unallocated space
                
                # Allocate the memory
                start = chunk.end
                new_chunk = QChunk(
                    start,
                    size,
                    chunk.trailing_free - size,
                    chunk, chunk.next_chunk,
                    allocator=self,
                    name=name,
                    anc_chunk=anc_chunk
                )
                self.chunks.insert(i + 1, new_chunk)
                chunk.trailing_free = 0
                
                # Fix connections
                if chunk.next_chunk is not None:
                    chunk.next_chunk.prev_chunk = new_chunk
                chunk.next_chunk = new_chunk
                return new_chunk
        
        # No free space, increase mem and go from there
        
        trailing_free = self.chunks[-1].trailing_free
        self.chunks[-1].trailing_free = 0
        
        start = self.max_mem - trailing_free
        
        
        self.max_mem += size - trailing_free
        new_chunk = QChunk(start, size, 0, self.chunks[-1], None, allocator=self, name=name, anc_chunk=anc_chunk)
        self.chunks[-1].next_chunk = new_chunk
        self.chunks.append(new_chunk)
        return new_chunk
                
        
    def free(self, chunk):
        if chunk.anc_chunk:
            raise Exception(f"Ancillae register: {chunk} should be freed using anc_free")
        
        if chunk not in self.chunks:
            raise Exception(f"Double free on chunk: {str(chunk)}")
        
        if chunk is self.chunks[0]:
            raise Exception(f"Attempting to free head!")
        
        chunk.prev_chunk.next_chunk = chunk.next_chunk
        if chunk.next_chunk is not None:
            chunk.next_chunk.prev_chunk = chunk.prev_chunk
        
        # Tally free space
        chunk.prev_chunk.trailing_free += chunk.size + chunk.trailing_free
        
        # Remove the chunk
        self.chunks.remove(chunk)
    
    def anc_free(self, chunk, fn):
        if chunk.anc_chunk == fn:
            chunk.anc_chunk = False
            self.free(chunk)
    
    def qubit_allocated(self, n):
        # Check if this qubit is currently allocated
        
        # Quick check if it's already off the end, this will catch most things
        if n > self.chunks[-1].end:
            return False
        
        for curr_chunk in self.chunks:
            if n >= curr_chunk.start and n <= curr_chunk.end:
                return True
            if n < curr_chunk.start:
                return False
        return False
        
        
    def partial_free_start(self, chunk, size):
        if size > chunk.size:
            raise Exception(f"Cannot partial free {size} on chunk {chunk.name} of size {chunk.size}")
        
        chunk.prev_chunk.trailing_free += size
        chunk.start += size
        chunk.size -= size
    
    def partial_free_end(self, chunk, size):
        if size > chunk.size:
            raise Exception(f"Cannot partial free {size} on chunk {chunk.name} of size {chunk.size}")
        
        chunk.trailing_free += size
        chunk.size -= size
        chunk.end -= size
        
    def __getitem__(self, i):
        return self.chunks[i]

    def __iter__(self, i):
        return self.chunks.__iter__()
        
    def __repr__(self):
        return f"{self.max_mem} : {str(self.chunks)}"
    
class QChunk():
    def __init__(self, 
                 start, 
                 size, 
                 trailing_free, 
                 prev_chunk, 
                 next_chunk, 
                 allocator=None, 
                 name=None, 
                 anc_chunk=False):
        self.start = start
        self.size = size
        self.end = self.start + self.size
        self.trailing_free = trailing_free
        self.prev_chunk = prev_chunk
        self.next_chunk = next_chunk
        self.allocator = allocator
        self.name = name
        self.anc_chunk = anc_chunk
    
    def anc_free(self, fn):
        self.allocator.anc_free(self, fn)
    
    def free(self):
        self.allocator.free(self)
        
    def __repr__(self):
        if self.trailing_free > 0:
            return f"[{self.name} {str(self.size)}][FREE : {self.trailing_free}]"
        else:
            return f"[{self.name} {str(self.size)}]"
    
    def __iter__(self):
        return list(range(self.start, self.end)).__iter__()
    
    def __getitem__(self, *keys, name=None):
        indices = []
        for key in keys:                
            if isinstance(key, slice):
                start = [key.start, 0][key.start is None]
                stop = [key.stop, self.size][key.stop is None]
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
            else:
                raise Exception("Unknown type of Key")
        return self.idx(*indices, name=name)

    
    def idx(self, *indices, name=None):
        return Virtual_QChunk(self, *indices, name=name)
    
    def virt(self, name=None):
        return self.idx(*list(range(self.size)), name=name)
    
    def __call__(self, *indices):
        if len(indices) == 0:
            return self(*list(range(self.size)))
        
        for idx in indices:
            if idx > self.size:
                raise Exception(f"Index {idx} out of bounds on register {self.name}")
        return np.array([self.start + idx for idx in indices])

    def __len__(self):
        return self.size
