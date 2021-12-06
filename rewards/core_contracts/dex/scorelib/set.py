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

from .bag import *


class SetDB(BagDB):
    """
    SetDB is an iterable collection of *unique* items.
    Order of retrieval is *optionally* significant (*not* significant by default)
    """

    _NAME = '_SETDB'

    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type, order=False):
        name = var_key + SetDB._NAME
        super().__init__(name, db, value_type, order)
        self._name = name
        self._db = db

    def add(self, item) -> None:
        """ Adds an element to the set 
            If it already exists, it *does not raise* any exception
        """
        if item not in self._items:
            super().add(item)

    def remove(self, item) -> None:
        """ This operation removes element x from the set.
            If element x does not exist, it raises a ItemNotFound.
        """
        if item not in self._items:
            raise ItemNotFound(self._name, str(item))
        super().remove(item)

    def discard(self, item) -> None:
        """ This operation also removes element x from the set.
            If element x does not exist, it *does not raise* a ItemNotFound.
        """
        if item in self._items:
            super().remove(item)

    def pop(self):
        """ Removes an element from the set and returns it """
        return self._items.pop()

    def difference(self, other: set):
        """ Returns a set containing the difference between two or more sets """
        return self._to_set().difference(other)

    def intersection(self, other: set):
        """ Returns a set, that is the intersection of two other sets """
        return self._to_set().intersection(other)

    def isdisjoint(self, other: set) -> bool:
        """ Returns whether two sets have a intersection or not """
        return self._to_set().isdisjoint(other)

    def issubset(self, other: set) -> bool:
        """ Returns whether another set contains this set or not """
        return self._to_set().issubset(other)

    def issuperset(self, other: set) -> bool:
        """ Returns whether this set contains another set or not """
        return self._to_set().issuperset(other)

    def symmetric_difference(self, other: set):
        """ Returns a set with the symmetric differences of two sets """
        return self._to_set().symmetric_difference(other)

    def union(self, other: set):
        """ Return a set containing the union of sets """
        return self._to_set().union(other)

    def update(self, *others) -> None:
        """ Update the set with the union of this set and others """
        self._to_set().update(others)

    def _to_set(self) -> set:
        result = set()
        for item in self:
            result.add(item)
        return result
