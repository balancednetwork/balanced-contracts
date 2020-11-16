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
from .utils import *


class InvalidState(Exception):
    pass


class StateUninitialized(Exception):
    pass


class InvalidStateClass(Exception):
    pass


class StateDB:

    _NAME = '_STATEDB'

    # ================================================
    #  Initialization
    # ================================================
    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type):
        self._name = var_key + StateDB._NAME
        self._state = VarDB(f"{self._name}_state", db, value_type=int)
        self._cls = value_type
        self._db = db

        # Check if the class is conform
        if Utils.enum_names(value_type)[0] != "UNINITIALIZED":
            raise InvalidStateClass(f"{value_type} needs an UNINITIALIZED state equals to 0 in its declaration")

    # ================================================
    #  External methods
    # ================================================
    def set(self, value: int) -> None:
        self._state.set(value)

    def get(self) -> int:
        return self._state.get()

    def get_name(self) -> str:
        return Utils.enum_names(self._cls)[self._state.get()]

    # ================================================
    #  Checks
    # ================================================
    def check_exists(self) -> None:
        if self._state.get() == self._cls.UNINITIALIZED:
            raise StateUninitialized(self._name)

    def check(self, state: int) -> None:
        if self._state.get() != state:
            raise InvalidState(
                self._name,
                Utils.enum_names(self._cls)[self._state.get()],
                Utils.enum_names(self._cls)[state])

    def check_not(self, state: int) -> None:
        if self._state.get() == state:
            raise InvalidState(
                self._name,
                Utils.enum_names(self._cls)[self._state.get()],
                Utils.enum_names(self._cls)[state])
