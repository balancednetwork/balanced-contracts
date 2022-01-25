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

TAG = 'BalancedReserveFund'


# TypedDict for disbursement specs
class Disbursement(TypedDict):
    address: Address
    amount: int


# An interface of token
class TokenInterface(InterfaceScore):
    @interface
    def symbol(self) -> str:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def balanceOf(self) -> int:
        pass

    @interface
    def priceInLoop(self) -> int:
        pass


# An interface to the Loans SCORE
class LoansInterface(InterfaceScore):
    @interface
    def getCollateralTokens(self) -> dict:
        pass


class ReserveFund(IconScoreBase):

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, destination: Address, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def TokenTransfer(self, recipient: Address, amount: int, note: str):
        pass

    @eventlog(indexed=1)
    def RedeemFail(self, _to: Address, _symbol: str, _value: int):
        pass

    _GOVERNANCE = 'governance'
    _ADMIN = 'admin'
    _LOANS_SCORE = 'loans_score'
    _BALN_TOKEN = 'baln_token'
    _SICX_TOKEN = 'sicx_token'
    _BALN = 'baln'
    _SICX = 'sicx'
    _AWARDS = 'awards'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._loans_score = VarDB(self._LOANS_SCORE, db, value_type=Address)
        self._baln_token = VarDB(self._BALN_TOKEN, db, value_type=Address)
        self._sicx_token = VarDB(self._SICX_TOKEN, db, value_type=Address)
        self._baln = VarDB(self._BALN, db, value_type=int)
        self._sicx = VarDB(self._SICX, db, value_type=int)
        self._awards = DictDB(self._AWARDS, db, value_type=int, depth=2)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Balanced Reserve Fund"

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

    @external
    @only_admin
    def setBaln(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._baln_token.set(_address)

    @external(readonly=True)
    def getBaln(self) -> Address:
        return self._baln_token.get()

    @external
    @only_admin
    def setSicx(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._sicx_token.set(_address)

    @external(readonly=True)
    def getSicx(self) -> Address:
        return self._sicx_token.get()

    @external(readonly=True)
    def getBalances(self) -> dict:
        loans = self.create_interface_score(self._loans_score.get(), LoansInterface)
        assets = loans.getCollateralTokens()
        balances = {}
        for symbol in assets:
            token = self.create_interface_score(Address.from_string(assets[symbol]), TokenInterface)
            balance = token.balanceOf(self.address)
            if balance > 0:
                balances[symbol] = balance
        return balances

    @external
    def redeem(self, _to: Address, _amount: int, _sicx_rate: int) -> int:
        if self.msg.sender != self._loans_score.get():
            revert(f'{TAG}: The redeem method can only be called by the Loans SCORE.')
        sicx = self._sicx.get()
        if _amount <= sicx:
            sicx_to_send = _amount
        else:
            sicx_to_send = sicx
            baln_address = self._baln_token.get()
            baln = self.create_interface_score(baln_address, TokenInterface)
            baln_rate = baln.priceInLoop()
            baln_to_send = (_amount - sicx) * _sicx_rate // baln_rate
            baln_remaining = self._baln.get() - baln_to_send
            if baln_remaining < 0:  # Revert in case where there is not enough BALN.
                revert(f'{TAG}: Unable to process request at this time.')
            self._baln.set(baln_remaining)
            self._send_token(baln_address, _to, baln_to_send, 'Redeemed:')
        self._sicx.set(sicx - sicx_to_send)
        if sicx_to_send > 0:
            self._send_token(self._sicx_token.get(), self._loans_score.get(), sicx_to_send, 'To Loans:')
        return sicx_to_send

    @external
    @only_governance
    def disburse(self, _recipient: Address, _amounts: List[Disbursement]) -> bool:
        """
        Disbursement method will be called from the governance SCORE when a
        vote passes approving an expenditure by the Emergency Reserve.

        :param _recipient: Disbursement recipient address.
        :type _recipient: :class:`iconservice.base.address.Address`
        :param _amounts: Amounts of each asset type to disburse.
        :type _amounts: List[dict]
        """
        for asset in _amounts:
            if asset['address'] == self._sicx_token.get():
                sicx = self._sicx.get()
                if sicx < asset['amount']:
                    revert(f'{TAG}: Insufficient balance of asset {asset["address"]} in the reserve fund.')
                self._sicx.set(sicx - asset['amount'])
                self._awards[_recipient][asset['address']] += asset['amount']
            elif asset['address'] == self._baln_token.get():
                baln = self._baln.get()
                if baln < asset['amount']:
                    revert(f'{TAG}: Insufficient balance of asset {asset["address"]} in the reserve fund.')
                self._baln.set(baln - asset['amount'])
                self._awards[_recipient][asset['address']] += asset['amount']
            else:
                revert(f'{TAG}: Unavailable assets in the reserve fund requested.')
        return True

    @external
    def claim(self) -> None:
        """
        Any funds that are authorized for disbursement through Balanced Governance
        may be claimed using this method.
        """
        disbursement = self._awards[self.msg.sender]
        loans = self.create_interface_score(self._loans_score.get(), LoansInterface)
        assets = loans.getCollateralTokens()
        for symbol in assets:
            amount = disbursement[Address.from_string(assets[symbol])]
            if amount > 0:
                disbursement[Address.from_string(assets[symbol])] = 0
                self._send_token(Address.from_string(assets[symbol]), self.msg.sender,
                                 amount, 'Balanced Reserve Fund disbursement.')

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used to receive sICX and BALN tokens.

        :param _from: Token origination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        if self.msg.sender == self._baln_token.get():
            self._baln.set(self._baln.get() + _value)
        elif self.msg.sender == self._sicx_token.get():
            self._sicx.set(self._sicx.get() + _value)
        else:
            revert(f'{TAG}: The Reserve Fund can only accept BALN or sICX tokens. '
                   f'Deposit not accepted from {self.msg.sender}'
                   f'Only accepted from BALN = {self._baln_token.get()}'
                   f'Or sICX = {self._sicx_token.get()}')

    def _send_token(self, _token_address: Address, _to: Address, _amount: int, msg: str) -> None:
        """
        Sends IRC2 token to an address.

        :param _token_address: Token address.
        :type _token_address: :class:`iconservice.base.address.Address`
        :param _to: Token destination address.
        :type _to: :class:`iconservice.base.address.Address`
        :param _amount: Number of tokens sent.
        :type _amount: int
        :param msg: Message for the event log.
        :type msg: str
        """
        symbol = "unknown"
        try:
            token_score = self.create_interface_score(_token_address, TokenInterface)
            symbol = token_score.symbol()
            token_score.transfer(_to, _amount)
            self.TokenTransfer(_to, _amount, f'{msg} {_amount} {symbol} sent to {_to}.')
        except Exception:
            revert(f'{TAG}: {_amount} {symbol} not sent to {_to}.')

    @payable
    def fallback(self):
        pass
