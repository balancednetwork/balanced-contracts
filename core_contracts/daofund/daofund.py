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
from .utils.checks import *
from .utils.enumerable_set import *

TAG = 'DAOfund'


# TypedDict for disbursement specs
class Disbursement(TypedDict):
    address: Address
    amount: int
    symbol: str


# An interface of token to get balances.
class TokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def symbol(self) -> str:
        pass


# An interface tp the Loans SCORE to get the collateral token addresses.
class LoansInterface(InterfaceScore):
    @interface
    def getCollateralTokens(self) -> dict:
        pass

    @interface
    def getAssetTokens(self) -> dict:
        pass


class DAOfund(IconScoreBase):

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, destination: Address, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def TokenTransfer(self, recipient: Address, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def InsufficientFunds(self, recipient: Address, symbol: str, note: str):
        pass

    _GOVERNANCE = 'governance'
    _ADMIN = 'admin'
    _LOANS_SCORE = 'loans_score'
    _SYMBOL = "symbol"
    _FUND = 'fund'
    _AWARDS = 'awards'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._loans_score = VarDB(self._LOANS_SCORE, db, value_type=Address)
        self._fund = DictDB(self._FUND, db, value_type=int)
        self._symbol = EnumerableSetDB(self._SYMBOL, db, value_type=str)
        self._awards = DictDB(self._AWARDS, db, value_type=int, depth=2)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)

    def on_update(self) -> None:
        super().on_update()
        self._add_symbol_to_setdb()

    def _add_symbol_to_setdb(self) -> None:
        loans = self.create_interface_score(self._loans_score.get(), LoansInterface)
        assets = loans.getAssetTokens()
        for symbol in assets:
            self._symbol.add(symbol)

    @external(readonly=True)
    def name(self) -> str:
        return "Balanced DAOfund"

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
    def setAdmin(self, _address: Address) -> None:
        self._admin.set(_address)

    @external(readonly=True)
    def getAdmin(self) -> Address:
        return self._admin.get()

    @external
    @only_admin
    def setLoans(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._loans_score.set(_address)

    @external(readonly=True)
    def getLoans(self) -> Address:
        return self._loans_score.get()

    @external(readonly=True)
    def getBalances(self) -> dict:
        balances = {}
        for symbol in self._symbol.range(0, len(self._symbol)):
            balances[symbol] = self._fund[symbol]
        balances['ICX'] = self._fund['ICX']
        return balances

    @external
    @only_governance
    def disburse(self, _recipient: Address, _amounts: List[Disbursement]) -> bool:
        """
        Disbursement method will be called from the governance SCORE when a
        vote passes approving an expenditure by the DAO.

        :param _recipient: Disbursement recipient address.
        :type _recipient: :class:`iconservice.base.address.Address`
        :param _amounts: Amounts of each asset type to disburse.
        :type _amounts: List[dict]
        """
        for asset in _amounts:
            if self._fund[asset['symbol']] < asset['amount']:
                revert(f'{TAG}: Insufficient balance of asset {asset["symbol"]} in DAOfund.')
            self._awards[_recipient][asset['symbol']] += asset['amount']
            self._fund[asset['symbol']] -= asset['amount']
        return True

    @external
    def claim(self) -> None:
        """
        Any funds that are authorized for disbursement through Balanced Governance
        may be claimed using this method.
        """
        disbursement = self._awards[self.msg.sender]
        loans = self.create_interface_score(self._loans_score.get(), LoansInterface)
        assets = loans.getAssetTokens()
        for symbol in assets:
            amount = disbursement[symbol]
            if amount > 0:
                disbursement[symbol] = 0
                self._send_token(symbol, Address.from_string(assets[symbol]), self.msg.sender,
                                 amount, 'Balanced DAOfund disbursement')
        amount = disbursement['ICX']
        if amount > 0:
            disbursement['ICX'] = 0
            self._send_ICX(self.msg.sender, amount, 'Balanced DAOfund disbursement')

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used only to receive portion of fees allocated to the DAOfund.
        :param _from: Token origination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        loans = self.create_interface_score(self._loans_score.get(), LoansInterface)
        assets = loans.getAssetTokens()
        address = str(self.msg.sender)
        for symbol in assets:
            if assets[symbol] == address:
                self._fund[symbol] += _value
                return
        token_contract = self.create_interface_score(self.msg.sender, TokenInterface)
        symbol = token_contract.symbol()
        if symbol not in self._symbol:
            self._symbol.add(symbol)
        self._fund[symbol] += _value

    def _send_ICX(self, _to: Address, amount: int, msg: str) -> None:
        """
        Sends ICX to an address.
        :param _to: ICX destination address.
        :type _to: :class:`iconservice.base.address.Address`
        :param amount: Number of ICX sent.
        :type amount: int
        :param msg: Message for the event log.
        :type msg: str
        """
        try:
            self.icx.transfer(_to, amount)
            self.FundTransfer(_to, amount, f'{msg} {amount} ICX sent to {_to}.')
        except BaseException as e:
            revert(f'{TAG}: {amount} ICX not sent to {_to}. '
                   f'Exception: {e}')

    def _send_token(self, _symbol: str, _token: Address, _to: Address,
                    _amount: int, msg: str) -> None:
        """
        Sends IRC2 token to an address.
        :param _symbol: Token symbol.
        :type _symbol: str
        :param _token: Token SCORE address.
        :type _token: str
        :param _to: Token destination address.
        :type _to: :class:`iconservice.base.address.Address`
        :param _amount: Number of tokens sent.
        :type _amount: int
        :param msg: Message for the event log.
        :type msg: str
        """
        try:
            token_score = self.create_interface_score(_token, TokenInterface)
            token_score.transfer(_to, _amount)
            self.TokenTransfer(_to, _amount, f'{msg} {_amount} {_symbol} sent to {_to}.')
        except BaseException as e:
            revert(f'{TAG}: {_amount} {_symbol} not sent to {_to}. '
                   f'Exception: {e}')

    @payable
    def fallback(self):
        self._fund['ICX'] += self.msg.value
