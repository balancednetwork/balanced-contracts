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


class Utils():

    @staticmethod
    def enum_names(cls):
        return [i for i in cls.__dict__.keys() if i[:1] != '_']

    @staticmethod
    def enum_values(cls):
        return [i[1] for i in cls.__dict__.items() if i[0][0] != '_']

    @staticmethod
    def get_enum_name(cls, index):
        return Utils.enum_names(cls)[index]
