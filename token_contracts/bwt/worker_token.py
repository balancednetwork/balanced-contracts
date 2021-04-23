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
from .tokens.IRC2 import IRC2
from .utils.checks import *

TAG = 'BALW'

TOKEN_NAME = 'Balanced Worker Token'
SYMBOL_NAME = 'BALW'
INITIAL_SUPPLY = 100
DECIMALS = 6

# An interface of token to distribute daily BALN
class TokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


class WorkerToken(IRC2):

    _ACCOUNTS = 'accounts'
    _GOVERNANCE = 'governance'
    _BALN_TOKEN = 'baln_token'
    _BALN = 'baln'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)
        self._baln_token = VarDB(self._BALN_TOKEN, db, value_type=Address)
        self._baln = VarDB(self._BALN, db, value_type=int)

    def on_install(self, _governance: Address) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME, INITIAL_SUPPLY, DECIMALS)
        self._governance.set(_governance)

    def on_update(self) -> None:
        super().on_update()

    @external
    @only_owner
    def setGovernance(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
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
    @only_admin
    def setBaln(self, _address: Address) -> None:
        self._baln_token.set(_address)

    @external(readonly=True)
    def getBaln(self) -> Address:
        return self._baln_token.get()

    @external
    @only_admin
    def adminTransfer(self, _from: Address, _to: Address, _value: int, _data: bytes = None):
        if _data is None:
            _data = b'None'
        super()._transfer(_from, _to, _value, _data)

    @external
    def distribute(self) -> None:
        length = len(self._addresses)
        tokens = self.totalSupply()
        baln = self.create_interface_score(self._baln_token.get(), TokenInterface)
        dist = baln.balanceOf(self.address)
        for i in range(length):
            address = self._addresses[i]
            balance = self._balances[address]
            if balance > 0:
                amount = (dist * balance // tokens)
                dist -= amount
                tokens -= balance
                try:
                    baln.transfer(address, amount)
                except BaseException as e:
                    revert(f'{TAG}: {amount} BALN not sent to {address}. '
                           f'Exception: {e}')

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used to receive BALN tokens.

        :param _from: Token origination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        if self.msg.sender == self._baln_token.get():
            self._baln.set(self._baln.get() + _value)
        else:
            revert(f'The Worker Token contract can only accept BALN tokens. '
                   f'Deposit not accepted from {self.msg.sender} '
                   f'Only accepted from BALN = {self._baln_token.get()}')
