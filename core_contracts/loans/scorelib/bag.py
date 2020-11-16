# -*- coding: utf-8 -*-

# Copyright 2020 ICONation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from iconservice import *
from .consts import *


class ItemNotFound(Exception):
    """ Cannot find an entry in the collection """
    pass


class BagDBIsNotOrdered(Exception):
    """ The BagDB should be ordered in order to use that operation """
    pass


class BagDB(object):
    """
    BagDB is an iterable collection of items that may have duplicates.
    Order of retrieval is *optionally* significant (*not* significant by default)
    """

    _NAME = '_BAGDB'

    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type, order=False):
        self._name = var_key + BagDB._NAME
        self._items = ArrayDB(f'{self._name}_items', db, value_type=value_type)
        self._order = order
        self._db = db

    def __iter__(self):
        for item in self._items:
            yield item

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int):
        if not self._order:
            raise BagDBIsNotOrdered(self._name)
        return self._items[index]

    def __setitem__(self, index: int, value):
        if not self._order:
            raise BagDBIsNotOrdered(self._name)
        self._items[index] = value

    def first(self):
        if not self._order:
            raise BagDBIsNotOrdered(self._name)
        return self._items[0]

    def last(self):
        if not self._order:
            raise BagDBIsNotOrdered(self._name)
        return self._items[len(self._items) - 1]

    def __contains__(self, item) -> bool:
        return item in self._items

    def check_exists(self, item) -> None:
        if not item in self:
            raise ItemNotFound(self._name, str(item))

    def count(self, item) -> int:
        """ Returns the number of occurences of a given item in the bag """
        count = 0
        for cur in self._items:
            if cur == item:
                count += 1
        return count

    def add(self, item) -> None:
        """ Adds an item in the bag """
        self._items.put(item)

    def clear(self) -> None:
        """ Removes all the items from the bag """
        while self._items:
            self._items.pop()

    def remove(self, item) -> None:
        """ This operation removes a given item from the bag.
            If the item does not exist, it *does not raise* a KeyError.
        """
        if self._order:
            # Remove from the ArrayDB (ordered)
            tmp = []
            while self._items:
                cur = self._items.pop()
                # Keep all the elements until we reach the selected one
                if cur != item:
                    tmp.append(cur)
                # We found the removable element, stop here
                else:
                    break
            # Append the elements next to the removed one in order
            while tmp:
                cur = tmp.pop()
                self._items.put(cur)
        else:
            # Remove from the ArrayDB (unordered)
            length = len(self._items)
            for idx, cur in enumerate(self._items):
                # Look for the item index to be removed
                if cur == item:
                    if idx == length - 1:
                        # Nothing left in the array
                        self._items.pop()
                    else:
                        # Replace the old value with the tail of the array
                        self._items[idx] = self._items.pop()
                    return

    def select(self, offset: int, cond=None, **kwargs) -> list:
        """ Returns a limited amount of items in the BagDB that optionally fulfills a condition """
        items = iter(self._items)
        result = []

        # Skip N items until offset
        try:
            for _ in range(offset):
                next(items)
        except StopIteration:
            # Offset is bigger than the size of the bag
            raise StopIteration(self._name)

        # Do a maximum iteration count of MAX_ITERATION_LOOP
        for _ in range(MAX_ITERATION_LOOP):
            try:
                item = next(items)
                if cond:
                    if cond(self._db, item, **kwargs):
                        result.append(item)
                else:
                    result.append(item)
            except StopIteration:
                # End of array : stop here
                break

        return result
