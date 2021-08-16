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

TAG = 'bnUSD'

TOKEN_NAME = 'Balanced Dollar'
SYMBOL_NAME = 'bnUSD'
DEFAULT_PEG = 'USD'
DEFAULT_ORACLE_NAME = 'BandChain'
INITIAL_PRICE_ESTIMATE = 125 * 10**16
MIN_UPDATE_TIME = 30_000_000 # 30 seconds

# An interface to the Band Price Oracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class BalancedDollar(IRC2Mintable, IRC2Burnable):

    _PEG = 'peg'
    _GOVERNANCE = 'governance'
    _ORACLE_ADDRESS = 'oracle_address'
    _ORACLE_NAME = 'oracle_name'
    _PRICE_UPDATE_TIME = 'price_update_time'
    _LAST_PRICE = 'last_price'
    _MIN_INTERVAL = 'min_interval'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._peg = VarDB(self._PEG, db, value_type=str)
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)
        self._oracle_address = VarDB(self._ORACLE_ADDRESS, db, value_type=Address)
        self._oracle_name = VarDB(self._ORACLE_NAME, db, value_type=str)
        self._price_update_time = VarDB(self._PRICE_UPDATE_TIME, db, value_type=int)
        self._last_price = VarDB(self._LAST_PRICE, db, value_type=int)
        self._min_interval = VarDB(self._MIN_INTERVAL, db, value_type=int)

    def on_install(self, _governance: Address) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)
        self._governance.set(_governance)
        self._peg.set(DEFAULT_PEG)
        self._oracle_name.set(DEFAULT_ORACLE_NAME)
        self._last_price.set(INITIAL_PRICE_ESTIMATE)
        self._min_interval.set(MIN_UPDATE_TIME)

    def on_update(self) -> None:
        super().on_update()
        old_div_address = Address.from_string('cx13f08df7106ae462c8358066e6d47bb68d995b6d')
        new_div_address = Address.from_string('cx203d9cd2a669be67177e997b8948ce2c35caffae')
        old_div_balance = self._balances[old_div_address]
        self._transfer(old_div_address, new_div_address, old_div_balance, b'')

    @external(readonly=True)
    def getPeg(self) -> str:
        return self._peg.get()

    @external
    @only_owner
    def setGovernance(self, _address: Address) -> None:
        self._governance.set(_address)

    @external(readonly=True)
    def getGovernance(self) -> Address:
        return self._governance.get()

    @external
    @only_governance
    def setAdmin(self, _admin: Address) -> None:
        """
        Sets the authorized address.

        :param _admin: The authorized admin address.
        """
        return self._admin.set(_admin)

    @external
    @only_governance
    def setOracle(self, _address: Address) -> None:
        self._oracle_address.set(_address)

    @external(readonly=True)
    def getOracle(self) -> dict:
        return self._oracle_address.get()

    @external
    @only_governance
    def setOracleName(self, _name: str) -> None:
        self._oracle_name.set(_name)

    @external(readonly=True)
    def getOracleName(self) -> dict:
        return self._oracle_name.get()

    @external
    @only_governance
    def setMinInterval(self, _interval: int) -> None:
        self._min_interval.set(_interval)

    @external(readonly=True)
    def getMinInterval(self) -> int:
        return self._min_interval.get()

    @external(readonly=True)
    def getPriceUpdateTime(self) -> int:
        return self._price_update_time.get()

    @external
    def priceInLoop(self) -> int:
        """
        Returns the price of the asset in loop. Makes a call to the oracle if
        the last recorded price is not recent enough.
        """
        if self.now() - self._price_update_time.get() > self._min_interval.get():
            self.update_asset_value()
        return self._last_price.get()

    @external(readonly=True)
    def lastPriceInLoop(self) -> int:
        """
        Returns the latest price of the asset in loop.
        """
        base = self._peg.get()
        quote = "ICX"
        oracle_address = self._oracle_address.get()
        oracle = self.create_interface_score(oracle_address, OracleInterface)
        priceData = oracle.get_reference_data(base, quote)
        return priceData['rate']

    @external
    @only_governance
    def govTransfer(self, _from: Address, _to: Address, _value: int, _data: bytes = None) -> None:
        if _data is None:
			_data = b'None'
        self._transfer(_from, _to, _value, _data)

    def update_asset_value(self) -> None:
        """
        Calls the oracle method for the asset and updates the asset
        value in loop.
        """
        base = self._peg.get()
        quote = "ICX"
        oracle_address = self._oracle_address.get()
        try:
            oracle = self.create_interface_score(oracle_address, OracleInterface)
            priceData = oracle.get_reference_data(base, quote)
            self._last_price.set(priceData['rate'])
            self._price_update_time.set(self.now())
            self.OraclePrice(base + quote, self._oracle_name.get(), oracle_address, priceData['rate'])
        except BaseException as e:
            revert(f'{base + quote}, {self._oracle_name.get()}, {oracle_address}, Exception: {e}')

    # ------------------------------------------------------------------------------------------------------------------
    # EVENTS
    # ------------------------------------------------------------------------------------------------------------------

    @eventlog(indexed=3)
    def OraclePrice(self, market: str, oracle_name: str, oracle_address: Address, price: int):
        pass
