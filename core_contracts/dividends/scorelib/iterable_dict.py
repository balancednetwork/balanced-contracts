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
from .set import *
from .consts import *


class IterableDictDB(object):
    """
    Utility class wrapping the state DB.
    IterableDictDB behaves like a DictDB, but supports iterator operation at a higher step cost.
    Order of retrieval during iteration is *optionally* significant (*not* significant by default)
    """

    _NAME = '_ITERABLE_DICTDB'

    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type, order=False):
        self._name = var_key + IterableDictDB._NAME
        self._keys = SetDB(f'{self._name}_keys', db, value_type, order)
        self._values = DictDB(f'{self._name}_values', db, value_type)
        self._db = db

    def __iter__(self):
        for key in self._keys:
            yield key, self._values[key]

    def keys(self):
        for key in self._keys:
            yield key

    def values(self):
        for key in self._keys:
            yield self._values[key]

    def __contains__(self, key) -> bool:
        return key in self._keys

    def __len__(self) -> int:
        return len(self._keys)

    def __setitem__(self, key, value) -> None:
        self._keys.add(key)
        self._values[key] = value

    def __getitem__(self, key):
        return self._values[key]

    def __delitem__(self, key):
        del self._values[key]
        self._keys.remove(key)

    def select(self, offset: int, cond=None, **kwargs) -> dict:
        """ Returns a limited amount of items in the IterableDictDB that optionally fulfills a condition """
        keys = iter(self._keys)
        result = []

        # Skip N items until offset
        try:
            for _ in range(offset):
                next(keys)
        except StopIteration:
            # Offset is bigger than the size of the bag
            raise StopIteration(self._name)

        # Do a maximum iteration count of MAX_ITERATION_LOOP
        for _ in range(MAX_ITERATION_LOOP):
            try:
                key = next(keys)
                item = (key, self._values[key])
                if cond:
                    if cond(self._db, item, **kwargs):
                        result.append(item)
                else:
                    result.append(item)
            except StopIteration:
                # End of array : stop here
                break

        return {k: v for k, v in result}

    def clear(self):
        """ Remove all key,value pairs in the dict """
        # Removes values
        for key in self.keys():
            del self._values[key]
        # Remove keys
        self._keys.clear()
