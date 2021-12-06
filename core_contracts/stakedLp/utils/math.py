
EXA = 10 ** 18
halfEXA = EXA // 2
SECONDS_PER_YEAR = 31536000
# 365 days = (365 days) × (24 hours/day) × (3600 seconds/hour) = 31536000 seconds


def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a*b)) // EXA


def exaDiv(a: int, b: int) -> int:
    halfB = b // 2
    return (halfB + (a * EXA)) // b


def exaPow(x: int, n: int) -> int:
    if n % 2 != 0:
        z = x
    else:
        z = EXA

    n = n // 2
    while n != 0:
        x = exaMul(x, x)

        if n % 2 != 0:
            z = exaMul(z, x)

        n = n // 2
        
    return z
    
def convertToExa(_amount:int,_decimals:int)-> int:
    if _decimals >= 0:
        return _amount * EXA // (10 ** _decimals)

def convertExaToOther(_amount:int,_decimals:int)->int:
    if _decimals >= 0:
        return _amount * (10 ** _decimals) // EXA