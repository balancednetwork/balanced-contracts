from iconservice import *
from .utils.checks import *
from .scorelib import *
from .utils.consts import *
from .utils.arraydb_helpers import *

TAG = 'Dividends'

UNITS_PER_TOKEN = 1000000000000000000


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


class DexInterface(InterfaceScore):
    @interface
    def getTotalValue(self, _name: str, _snapshot_id: int) -> int:
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

    _ACCEPTED_TOKENS = "accepted_tokens"
    _AMOUNT_TO_DISTRIBUTE = "amount_to_distribute"
    _AMOUNT_BEING_DISTRIBUTED = "amount_being_distributed"

    _ELIGIBLE_BALN_HOLDERS = "eligible_baln_holders"
    _ELIGIBLE_BALN_BALANCES = "eligible_baln_balances"
    _TOTAL_ELIGIBILE_BALN_TOKENS = "total_eligible_baln_tokens"
    _BALN_DIST_INDEX = "baln_dist_index"

    _STAKED_BALN_HOLDERS = "staked_baln_holders"
    _STAKED_BALN_BALANCES = "staked_baln_balances"
    _STAKED_DIST_INDEX = "staked_dist_index"

    _BALN_IN_DEX = "baln_in_dex"
    _TOTAL_LP_TOKENS = "total_lp_tokens"

    _USERS_BALANCE = "users_balance"

    _DIVIDENDS_DISTRIBUTION_STATUS = "dividends_distribution_status"

    _SNAPSHOT_ID = "snapshot_id"

    _AMOUNT_RECEIVED_STATUS = "amount_received_status"

    _MAX_LOOP_COUNT = "max_loop_count"
    _MINIMUM_ELIGIBLE_DEBT = "minimum_eligible_debt"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

        # Addresses of other SCORES, that dividends score interacts with
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._loans_score = VarDB(self._LOANS_SCORE, db, value_type=Address)
        self._daofund = VarDB(self._DAOFUND, db, value_type=Address)
        self._baln_score = VarDB(self._BALN_SCORE, db, value_type=Address)

        # Accepted tokens store all the tokens that dividends can distribute and accept, store cx00.. for ICX
        self._accepted_tokens = ArrayDB(self._ACCEPTED_TOKENS, db, value_type=Address)
        # Amount that comes in between distribution or during the week is recorded here
        self._amount_to_distribute = DictDB(self._AMOUNT_TO_DISTRIBUTE, db, value_type=int)
        # Amount that is being distributed is recorded here
        self._amount_being_distributed = DictDB(self._AMOUNT_BEING_DISTRIBUTED, db, value_type=int)

        # Eligible baln token holders retrieved from staked baln token and from baln pool
        self._eligible_baln_holders = ArrayDB(self._ELIGIBLE_BALN_HOLDERS, db, value_type=str)
        self._eligible_baln_balances = DictDB(self._ELIGIBLE_BALN_BALANCES, db, value_type=int)
        self._total_eligible_baln_tokens = VarDB(self._TOTAL_ELIGIBILE_BALN_TOKENS, db, value_type=int)
        self._baln_dist_index = VarDB(self._BALN_DIST_INDEX, db, value_type=int)

        # Staked baln token holders and their balance retrieved from baln token contract
        self._staked_baln_holders = ArrayDB(self._STAKED_BALN_HOLDERS, db, value_type=str)
        self._staked_baln_balances = DictDB(self._STAKED_BALN_BALANCES, db, value_type=int)
        self._staked_dist_index = VarDB(self._STAKED_DIST_INDEX, db, value_type=int)

        self._baln_in_dex = VarDB(self._BALN_IN_DEX, db, value_type=int)
        self._total_lp_tokens = VarDB(self._TOTAL_LP_TOKENS, db, value_type=int)

        self._users_balance = DictDB(self._USERS_BALANCE, db, value_type=int, depth=2)

        self._dividends_distribution_status = VarDB(self._DIVIDENDS_DISTRIBUTION_STATUS, db, value_type=int)

        # Track which snapshot has been used for distribution
        self._snapshot_id = VarDB(self._SNAPSHOT_ID, db, value_type=int)

        self._amount_received_status = VarDB(self._AMOUNT_RECEIVED_STATUS, db, value_type=bool)

        self._max_loop_count = VarDB(self._MAX_LOOP_COUNT, db, value_type=int)
        self._minimum_eligible_debt = VarDB(self._MINIMUM_ELIGIBLE_DEBT, db, value_type=int)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)

        self._accepted_tokens.put(Address.from_string(ZERO_SCORE_ADDRESS))
        self._snapshot_id.set(1)
        self._max_loop_count.set(MAX_LOOP)
        self._minimum_eligible_debt.set(MINIMUM_ELIGIBLE_DEBT)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Dividends"

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

    @external
    def distribute(self) -> bool:
        """
        A placeholder until BalancedDAO community decides how to handle fee revenue.
        """
        return True

    @external
    def claim(self) -> None:
        """
        A placeholder until BalancedDAO community decides how to handle fee revenue.
        """
        pass

    def _send_ICX(self, _to: Address, amount: int, msg: str) -> None:
        """
        Sends ICX to an address.
        :param _to: ICX destination address.
        :type _to: :class:`iconservice.base.address.Address`
        :param _amount: Number of ICX sent.
        :type _amount: int
        :param msg: Message for the event log.
        :type msg: str
        """
        try:
            self.icx.transfer(_to, amount)
            self.FundTransfer(_to, amount, msg + f' {amount} ICX sent to {_to}.')
        except BaseException as e:
            revert(f'{amount} ICX not sent to {_to}. '
                   f'Exception: {e}')

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used only to receive all fees generated by the Balanced system.
        :param _from: Token orgination address.
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
        self._amount_to_distribute[str(self.msg.sender)] += _value
        self.DividendsReceived(_value, f"{_value} tokens received as dividends token: {self.msg.sender}")
        self._amount_received_status.set(True)

    @payable
    def fallback(self):
        self._amount_to_distribute[ZERO_SCORE_ADDRESS] += self.msg.value
        self.DividendsReceived(self.msg.value, f"{self.msg.value} ICX received as dividends")
        self._amount_received_status.set(True)

    # -------------------------------------------------------------------------------
    #   EVENT LOGS
    # -------------------------------------------------------------------------------

    @eventlog(indexed=1)
    def DividendsReceived(self, _amount: int, _data: str) -> None:
        pass
