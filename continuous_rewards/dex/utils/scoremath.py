from iconservice import *

def sqrt(x: int) -> int:
    """
    Babylonian Square root implementation
    """
    z = (x + 1) // 2
    y = x
    
    while z < y:
        y = z
        z = ( (x // z) + z) // 2
    
    return y