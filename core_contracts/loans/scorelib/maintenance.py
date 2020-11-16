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
from .exception import *
from .auth import *
from .utils import *
from .state import *


class ScoreInMaintenanceException(Exception):
    pass


class IconScoreMaintenanceStatus:
    UNINITIALIZED = 0
    DISABLED = 1
    ENABLED = 2


class IconScoreMaintenance:

    _NAME = 'SCORE_MAINTENANCE'

    # ================================================
    #  Fields
    # ================================================
    @property
    def _status(self):
        return StateDB(f'{IconScoreMaintenance._NAME}_MODE', self.db, IconScoreMaintenanceStatus)

    # ================================================
    #  Internal methods
    # ================================================
    def on_install_maintenance_manager(self, status: int = IconScoreMaintenanceStatus.DISABLED) -> None:
        self._status.set(status)

    # ================================================
    #  Private methods
    # ================================================
    def _maintenance_is_enabled(self) -> bool:
        return self._status.get() == IconScoreMaintenanceStatus.ENABLED

    def _maintenance_is_disabled(self) -> bool:
        return self._status.get() == IconScoreMaintenanceStatus.DISABLED

    # ================================================
    #  External methods
    # ================================================
    @catch_exception
    @external
    @only_owner
    def maintenance_enable(self) -> None:
        self._status.set(IconScoreMaintenanceStatus.ENABLED)

    @catch_exception
    @external
    @only_owner
    def maintenance_disable(self) -> None:
        self._status.set(IconScoreMaintenanceStatus.DISABLED)

    @catch_exception
    @external(readonly=True)
    def maintenance_status(self) -> str:
        return Utils.get_enum_name(IconScoreMaintenanceStatus, self._status.get())


# --- Wrapper ---
def check_maintenance(func):
    if not isfunction(func):
        raise NotAFunctionError

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self._maintenance_is_enabled():
            raise ScoreInMaintenanceException

        return func(self, *args, **kwargs)
    return __wrapper
