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


def get_array_items(arraydb, start: int = 0, max_count: int = 100) -> list:
    items = []
    length = len(arraydb)
    if start < 0:
        start = 0
    elif start >= length:
        return items

    end = start + max_count
    end = length if end > length else end

    for idx in range(start, end):
        items.append(arraydb[idx])

    return items
