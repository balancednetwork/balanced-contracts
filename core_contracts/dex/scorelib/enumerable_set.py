# Copyright 2021 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from iconservice import *


class ItemNotFound(Exception):
    pass


class ValueTypeMismatchException(Exception):
    pass


class EnumerableSetDB(object):

    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type):
        self._entries = ArrayDB(f'{var_key}_es_entries', db, value_type=value_type)
        self._indexes = DictDB(f'{var_key}_es_indexes', db, value_type=int)
        self._value_type = value_type

    def __get_size(self) -> int:
        return len(self._entries)

    def __get_index(self, value) -> int:
        return self._indexes[value]

    def __len__(self) -> int:
        return self.__get_size()

    def __contains__(self, value):
        return self.__get_index(value) != 0

    def __getitem__(self, index: int):
        size = self.__get_size()
        if 0 <= index < size:
            return self._entries.get(index)
        else:
            raise ItemNotFound()

    def add(self, value):
        if type(value) != self._value_type:
            raise ValueTypeMismatchException()

        index = self.__get_index(value)
        if index == 0:
            # add new value
            self._entries.put(value)
            # index 0 is sentinel value, so store len(_entries)
            self._indexes[value] = len(self._entries)

    def remove(self, value):
        if type(value) != self._value_type:
            raise ValueTypeMismatchException()

        value_index = self.__get_index(value)
        if value_index != 0:
            # pop and swap with the last entry
            last_index = len(self._entries)
            last_entry = self._entries.pop()
            self._indexes.remove(value)
            if value_index != last_index:
                self._entries[value_index-1] = last_entry
                self._indexes[last_entry] = value_index
                # returns the swapped item
                return last_entry
        # value not in the set or the value is the last item
        return None

    def range(self, start: int, stop: int):
        size = self.__get_size()
        if 0 <= start < size and start < stop:
            end = stop if stop <= size else size
            for i in range(start, end):
                yield self._entries.get(i)
