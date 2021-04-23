# Copyright 2021 Balanced DAO
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
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable
from .utils.checks import *
from .utils.consts import *

TAG = 'sICX'

TOKEN_NAME = 'Staked ICX'
SYMBOL_NAME = 'sICX'

class stakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self):
        pass


class StakedICX(IRC2Mintable, IRC2Burnable):

    _PEG = 'peg'
    _STAKING = 'staking'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._peg = VarDB(self._PEG, db, value_type=str)
        self._staking_address = VarDB(self._STAKING, db, value_type=Address)

    def on_install(self, _admin: Address) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)
        self._admin.set(_admin)
        self._staking_address.set(_admin)
        self._peg.set('sICX')

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def getPeg(self) -> str:
        return self._peg.get()

    @external
    @only_owner
    def setStakingAddress(self, _address: Address) -> None:
        self._staking_address.set(_address)

    @external(readonly=True)
    def getStakingAddress(self) -> Address:
        return self._staking_address.get()

    @external
    def priceInLoop(self) -> int:
        """
        Returns the price of sICX in loop.
        """
        staking_score = self.create_interface_score(self._staking_address.get(), stakingInterface)
        return staking_score.getTodayRate()

    @external(readonly=True)
    def lastPriceInLoop(self) -> int:
        """
        Returns the price of sICX in loop.
        """
        return self.priceInLoop()
