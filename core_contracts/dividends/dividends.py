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

from .utils.checks import *
from .utils.consts import *
from .utils.arraydb_helpers import *

TAG = 'Balanced Dividends'

UNITS_PER_TOKEN = 10 ** 18


class DistPercentDict(TypedDict):
    category: str
    dist_percent: int


# An interface of token to get balances.
class TokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass


# An interface tp the Loans SCORE to get the collateral token addresses.
class LoansInterface(InterfaceScore):
    @interface
    def getCollateralTokens(self) -> dict:
        pass

    @interface
    def getAssetTokens(self) -> dict:
        pass

    @interface
    def getDebts(self, _address_list: List[str], _day: int) -> dict:
        pass

    @interface
    def getDay(self) -> int:
        pass


class DexInterface(InterfaceScore):
    @interface
    def getTotalValue(self, _name: str, _snapshot_id: int) -> int:
        pass

    @interface
    def getBalnSnapshot(self, _name: str, _snapshot_id: int) -> int:
        pass

    @interface
    def getDataBatch(self, _name: str, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        pass


class BalnTokenInterface(InterfaceScore):

    @interface
    def getStakeUpdates(self) -> dict:
        pass

    @interface
    def clearYesterdaysStakeChanges(self) -> bool:
        pass

    @interface
    def switchStakeUpdateDB(self) -> None:
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass


class IRC2Interface(InterfaceScore):

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


class Dividends(IconScoreBase):

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, destination: Address, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def TokenTransfer(self, recipient: Address, amount: int, note: str):
        pass

    _GOVERNANCE = 'governance'
    _ADMIN = 'admin'
    _LOANS_SCORE = 'loans_score'
    _DAOFUND = 'daofund'
    _BALN_SCORE = "baln_score"
    _DEX_SCORE = "dex_score"

    _ACCEPTED_TOKENS = "accepted_tokens"
    _AMOUNT_TO_DISTRIBUTE = "amount_to_distribute"
    _AMOUNT_BEING_DISTRIBUTED = "amount_being_distributed"

    _BALN_DIST_INDEX = "baln_dist_index"

    _STAKED_BALN_HOLDERS = "staked_baln_holders"
    _STAKED_DIST_INDEX = "staked_dist_index"

    _BALN_IN_DEX = "baln_in_dex"
    _TOTAL_LP_TOKENS = "total_lp_tokens"
    _LP_HOLDERS_INDEX = "lp_holders_index"

    _USERS_BALANCE = "users_balance"

    _DIVIDENDS_DISTRIBUTION_STATUS = "dividends_distribution_status"

    _SNAPSHOT_ID = "snapshot_id"

    _AMOUNT_RECEIVED_STATUS = "amount_received_status"
    _DAILY_FEES = "daily_fees"

    _MAX_LOOP_COUNT = "max_loop_count"
    _MINIMUM_ELIGIBLE_DEBT = "minimum_eligible_debt"

    _DIVIDENDS_CATEGORIES = "dividends_categories"
    _DIVIDENDS_PERCENTAGE = "dividends_percentage"

    _DISTRIBUTION_ACTIVATE = "distribution_activate"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

        # Addresses of other SCORES, that dividends score interacts with
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._loans_score = VarDB(self._LOANS_SCORE, db, value_type=Address)
        self._daofund = VarDB(self._DAOFUND, db, value_type=Address)
        self._baln_score = VarDB(self._BALN_SCORE, db, value_type=Address)
        self._dex_score = VarDB(self._DEX_SCORE, db, value_type=Address)

        # Accepted tokens store all the tokens that dividends can distribute and accept, store cx00.. for ICX
        self._accepted_tokens = ArrayDB(self._ACCEPTED_TOKENS, db, value_type=Address)
        # Amount that comes in between distribution or during the week is recorded here
        self._amount_to_distribute = DictDB(self._AMOUNT_TO_DISTRIBUTE, db, value_type=int)
        # Amount that is being distributed is recorded here
        self._amount_being_distributed = DictDB(self._AMOUNT_BEING_DISTRIBUTED, db, value_type=int)

        self._baln_dist_index = VarDB(self._BALN_DIST_INDEX, db, value_type=str)

        self._staked_dist_index = VarDB(self._STAKED_DIST_INDEX, db, value_type=str)

        self._baln_in_dex = VarDB(self._BALN_IN_DEX, db, value_type=int)
        self._total_lp_tokens = VarDB(self._TOTAL_LP_TOKENS, db, value_type=int)
        self._lp_holders_index = VarDB(self._LP_HOLDERS_INDEX, db, value_type=int)

        self._users_balance = DictDB(self._USERS_BALANCE, db, value_type=int, depth=2)

        self._dividends_distribution_status = VarDB(self._DIVIDENDS_DISTRIBUTION_STATUS, db, value_type=int)

        # Track which snapshot has been used for distribution
        self._snapshot_id = VarDB(self._SNAPSHOT_ID, db, value_type=int)

        self._amount_received_status = VarDB(self._AMOUNT_RECEIVED_STATUS, db, value_type=bool)
        self._daily_fees = DictDB(self._DAILY_FEES, db, value_type=int, depth=2)

        self._max_loop_count = VarDB(self._MAX_LOOP_COUNT, db, value_type=int)
        self._minimum_eligible_debt = VarDB(self._MINIMUM_ELIGIBLE_DEBT, db, value_type=int)

        self._dividends_categories = ArrayDB(self._DIVIDENDS_CATEGORIES, db, value_type=str)
        self._dividends_percentage = DictDB(self._DIVIDENDS_PERCENTAGE, db, value_type=int)

        self._distribution_activate = VarDB(self._DISTRIBUTION_ACTIVATE, db, value_type=bool)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)

        self._accepted_tokens.put(ZERO_SCORE_ADDRESS)
        loans = self.create_interface_score(Address.from_string('cx66d4d90f5f113eba575bf793570135f9b10cece1'),
                                            LoansInterface)
        day = loans.getDay()
        self._snapshot_id.set(day)
        self._max_loop_count.set(MAX_LOOP)
        self._minimum_eligible_debt.set(MINIMUM_ELIGIBLE_DEBT)
        self._add_initial_categories()
        self._distribution_activate.set(False)

    def on_update(self) -> None:
        super().on_update()

    def _add_initial_categories(self):
        self._dividends_categories.put(DAOFUND)
        self._dividends_categories.put(BALN_HOLDERS)
        self._dividends_percentage[DAOFUND] = 4*10**17
        self._dividends_percentage[BALN_HOLDERS] = 6*10**17

    @external(readonly=True)
    def name(self) -> str:
        return "Balanced Dividends"

    @external(readonly=True)
    def getDistributionActivationStatus(self) -> bool:
        return self._distribution_activate.get()

    @external
    @only_owner
    def setDistributionActivationStatus(self, _status: bool) -> None:
        self._distribution_activate.set(_status)

    @external
    @only_owner
    def setGovernance(self, _address: Address) -> None:
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
        self._loans_score.set(_address)

    @external(readonly=True)
    def getLoans(self) -> Address:
        return self._loans_score.get()

    @external
    @only_admin
    def setDaofund(self, _address: Address) -> None:
        self._daofund.set(_address)

    @external(readonly=True)
    def getDaofund(self) -> Address:
        return self._daofund.get()

    @external
    @only_admin
    def setBaln(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is EOA address. Should be a contract address.")
        self._baln_score.set(_address)

    @external(readonly=True)
    def getBaln(self) -> Address:
        return self._baln_score.get()

    @external
    @only_admin
    def setDex(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is EOA address. Should be a contract address.")
        self._dex_score.set(_address)

    @external(readonly=True)
    def getDex(self) -> Address:
        return self._dex_score.get()

    @external(readonly=True)
    def getBalances(self) -> dict:
        loans = self.create_interface_score(self._loans_score.get(), LoansInterface)
        assets = loans.getAssetTokens()
        balances = {}
        for symbol in assets:
            token = self.create_interface_score(Address.from_string(assets[symbol]), TokenInterface)
            balance = token.balanceOf(self.address)
            if balance > 0:
                balances[symbol] = balance
        balance = self.icx.get_balance(self.address)
        balances['ICX'] = balance
        return balances

    @external(readonly=True)
    def getAcceptedTokens(self) -> list:
        """
        Returns the list of accepted tokens for dividends, zero score address represents ICX
        """
        return [token for token in self._accepted_tokens]

    @external(readonly=True)
    def getDividendsCategories(self) -> list:
        return [item for item in self._dividends_categories]

    @external
    @only_admin
    def addDividendsCategory(self, _category: str) -> None:
        if _category in self._dividends_categories:
            revert(f"{TAG}: {_category} is already added")
        self._dividends_categories.put(_category)

    @external
    @only_admin
    def removeDividendsCategory(self, _category: str) -> None:
        if _category not in self._dividends_categories:
            revert(f"{TAG}: {_category} not found in the list of dividends categories")
        if self._dividends_percentage[_category] != 0:
            revert(f"{TAG}: Please make the category percentage to 0 before removing")
        remove_from_arraydb(_category, self._dividends_categories)

    @external(readonly=True)
    def getDividendsPercentage(self) -> dict:
        return {item: self._dividends_percentage[item] for item in self._dividends_categories}

    @external
    @only_admin
    def setDividendsCategoryPercentage(self, _dist_list: List[DistPercentDict]) -> None:
        total_percentage = 0
        if len(_dist_list) != len(self._dividends_categories):
            revert(f"{TAG}: Categories count mismatched!")
        for idx, dist_percent in enumerate(_dist_list):
            category = dist_percent["category"]
            percent = dist_percent["dist_percent"]
            if category not in self._dividends_categories:
                revert(f"{TAG}: {category} is not a valid dividends category")
            self._dividends_percentage[category] = percent
            total_percentage += percent

        if total_percentage != 10**18:
            revert(f"{TAG}: Total percentage doesn't sum up to 100 i.e. 10**18")

    @external
    def distribute(self, _activate: int = 0) -> bool:
        """
        Main method to handle the distribution of tokens to eligible BALN token holders
        :return: True if distribution has completed
        """
        loans_score = self.create_interface_score(self._loans_score.get(), LoansInterface)
        current_snapshot_id = loans_score.getDay()
        if self._snapshot_id.get() < current_snapshot_id:
            self._snapshot_id.set(current_snapshot_id)
        return True

    @external
    def claim(self) -> None:
        """
        Used only to claim all fees generated by the Balanced system.
        """
        pass

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
            self.FundTransfer(_to, amount, msg + f' {amount} ICX sent to {_to}.')
        except BaseException as e:
            revert(f'{amount} ICX not sent to {_to}. '
                   f'Exception: {e}')

    def _send_token(self, _to: Address, _amount: int, _token: Address, _msg: str) -> None:
        """
        Sends IRC2 token to address
        :param _to: Destination address
        :param _amount: amount to distribute
        :param _token: Address of IRC2 token
        :param _msg: Any message to attach with transfer
        """
        try:
            token_score = self.create_interface_score(_token, IRC2Interface)
            token_score.transfer(_to, _amount)
            self.FundTransfer(_to, _amount, _msg + f" {_amount} token sent to {_to}")
        except BaseException as e:
            revert(f"{TAG}: {_amount} token not sent to {_to}. Token: {_token}"
                   f"Reason: {e}")

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used only to receive all fees generated by the Balanced system.
        :param _from: Token origination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        if self.msg.sender not in self._accepted_tokens:
            loans = self.create_interface_score(self._loans_score.get(), LoansInterface)
            available_tokens = loans.getAssetTokens()
            if str(self.msg.sender) not in available_tokens.values():
                revert(f"{TAG}: {self.msg.sender} token is not an accepted token for the dividends")
            else:
                self._accepted_tokens.put(self.msg.sender)
        day = self._snapshot_id.get()
        self._daily_fees[day][str(self.msg.sender)] += _value
        self.DividendsReceived(_value, f"{_value} tokens received as dividends token: {self.msg.sender}")
        self._amount_received_status.set(True)

    @payable
    def fallback(self):
        day = self._snapshot_id.get()
        self._daily_fees[day][str(ZERO_SCORE_ADDRESS)] += self.msg.value
        self.DividendsReceived(self.msg.value, f"{self.msg.value} ICX received as dividends")
        self._amount_received_status.set(True)

    # -------------------------------------------------------------------------------
    #   EVENT LOGS
    # -------------------------------------------------------------------------------

    @eventlog(indexed=1)
    def DividendsReceived(self, _amount: int, _data: str) -> None:
        pass
