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


class IdFactory:
    """ IdFactory is able to generate unique identifiers for a collection of items. """

    _NAME = '_ID_FACTORY'

    def __init__(self, var_key: str, db: IconScoreDatabase):
        self._name = var_key + IdFactory._NAME
        self._uid = VarDB(f'{self._name}_uid', db, int)
        self._db = db

    def get_uid(self) -> int:
        # UID = 0 is forbidden in order to prevent conflict with uninitialized uid
        # Starts with UID 1
        self._uid.set(self._uid.get() + 1)
        return self._uid.get()
