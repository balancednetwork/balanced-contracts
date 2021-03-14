from iconservice import *

def remove_from_arraydb(_item, _array: ArrayDB) -> bool:
    length = len(_array)
    if length < 1:
        return False
    top = _array[-1]
    for index in range(length):
        if _array[index] == _item:
            _array[index] = top
            _array.pop()
            return True
    return False
