from functools import partial
'''
Draft of the constraints system
'''
def constrain(*assert_strs):
    def wrapper(fn):
        for assert_str in assert_strs:
            # TODO pattern matching
            var, val = assert_str.split('=')
            # TODO parse language
            val = int(val)
            var = var.split('|')[1]
            if '*' not in var:
                var = int(var.split('$')[1]) - 1
            
            def equality(fn, *args, **kwargs):
                if var == '*':
                    for arg in args:
                        assert len(arg) == val, f"Failed Constraint: {assert_str}"
                else:
                    assert len(args[var]) == val, f"Failed Constraint: {assert_str}"
                return fn(*args, **kwargs)
            
            fn = partial(equality, fn)
            
        return fn
    return wrapper
        
