def hamming_weight(val : int) -> int:
    '''
        Calculates the hamming weight of the value
        :: val : int :: Value to take the hamming weight of
    '''
    count = 0
    while val > 0:
        val &= val - 1
        count += 1
    return count
