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

    _ELIGIBLE_BALN_HOLDERS = "eligible_baln_holders"
    _ELIGIBLE_BALN_BALANCES = "eligible_baln_balances"
    _TOTAL_ELIGIBILE_BALN_TOKENS = "total_eligible_baln_tokens"
    _BALN_DIST_INDEX = "baln_dist_index"

    _STAKED_BALN_HOLDERS = "staked_baln_holders"
    _STAKED_BALN_BALANCES = "staked_baln_balances"
    _STAKED_DIST_INDEX = "staked_dist_index"

    _BALN_IN_DEX = "baln_in_dex"
    _TOTAL_LP_TOKENS = "total_lp_tokens"
    _LP_HOLDERS_INDEX = "lp_holders_index"

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
        self._dex_score = VarDB(self._DEX_SCORE, db, value_type=Address)

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
        self._lp_holders_index = VarDB(self._LP_HOLDERS_INDEX, db, value_type=int)

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

    @external
    @only_admin
    def setBalnTokenAddress(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is EOA address. Should be a contract address.")
        self._baln_score.set(_address)

    @external(readonly=True)
    def getBalnTokenAddress(self) -> Address:
        return self._baln_score.get()

    @external
    @only_admin
    def setDexAddress(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is EOA address. Should be a contract address.")
        self._dex_score.set(_address)

    @external(readonly=True)
    def getDexAddress(self) -> Address:
        return self._dex_score.get()

    @external
    @only_admin
    def setMaxLoopCount(self, _loop: int) -> None:
        if not 100 <= _loop <= 1000:
            revert(f"{TAG}: Please provide loop in the range of 100 and 1000")
        self._max_loop_count.set(_loop)

    @external(readonly=True)
    def getMaxLoopCount(self) -> int:
        return self._max_loop_count.get()

    @external
    @only_admin
    def setMinimumEligibleDebt(self, _debt: int) -> None:
        if _debt < 0:
            revert(f"{TAG}: Negative value for _debt can't be provided")
        self._minimum_eligible_debt.set(_debt)

    @external(readonly=True)
    def getMinimumEligibleDebt(self) -> int:
        return self._minimum_eligible_debt.get()

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
    def getUserDividends(self, _account: Address) -> dict:
        return {token: self._users_balance[str(_account)][str(token)] for token in self._accepted_tokens}

    @external(readonly=True)
    def getAmountToDistribute(self) -> dict:
        """
        Returns the amount of tokens that will be distributed in the next div cycle. zero score address refers to ICX
        """
        return {token: self._amount_to_distribute[str(token)] for token in self._accepted_tokens}

    @external(readonly=True)
    def getAmountBeingDistributed(self) -> dict:
        """
        Returns the amount of tokens being distributed currently. In the middle of distribution it only shows the
        remaining amount to distribute.
        """
        return {token: self._amount_being_distributed[str(token)] for token in self._accepted_tokens}

    @external
    def distribute(self) -> bool:
        """
        Main method to handle the distribution of tokens to eligible BALN token holders
        :return: True if distribution has completed
        """
        baln_score = self.create_interface_score(self._baln_score.get(), BalnTokenInterface)

        if self._dividends_distribution_status.get() == Status.DIVIDENDS_DISTRIBUTION_COMPLETE:
            loans_score = self.create_interface_score(self._loans_score.get(), LoansInterface)
            current_snapshot_id = loans_score.getDay()

            increased_snapshot = self._snapshot_id.get() + DAYS_IN_A_WEEK
            if increased_snapshot <= current_snapshot_id:
                # week has passed
                self._snapshot_id.set(increased_snapshot)
                # week has also advanced as well as there is amount to distribute
                if self._amount_received_status.get():
                    self._dividends_distribution_status.set(Status.COMPLETE_STAKED_BALN_UPDATES)
                    self._sweep_amount_for_distribution()
                    baln_score.switchStakeUpdateDB()
            else:
                self._update_stake_balances()
                baln_score.clearYesterdaysStakeChanges()
                return True

        elif self._dividends_distribution_status.get() == Status.COMPLETE_STAKED_BALN_UPDATES:
            # If the week has changed but the dividends distribution contract has not pulled all the staking data from
            # baln token contract, it continues to pull the data
            if self._update_stake_balances():
                self._dividends_distribution_status.set(Status.FILTER_ELIGIBLE_STAKED_BALN_HOLDERS)

        elif self._dividends_distribution_status.get() == Status.FILTER_ELIGIBLE_STAKED_BALN_HOLDERS:
            self._check_eligibility_against_debt_value()

        elif self._dividends_distribution_status.get() == Status.TOTAL_DATA_FROM_BALN_LP_POOL:
            self._update_total_lp_tokens()

        elif self._dividends_distribution_status.get() == Status.COMPUTE_BALN_FOR_LP_HOLDER:
            self._update_lp_holders_balance()

        elif self._dividends_distribution_status.get() == Status.DAOFUND_DISTRIBUTION:
            pass
        elif self._dividends_distribution_status.get() == Status.DISTRIBUTE_FUND_TO_HOLDERS:
            pass
        else:
            pass
        return False

    def _sweep_amount_for_distribution(self) -> None:
        for token in self._accepted_tokens:
            token_key = str(token)
            self._amount_being_distributed[token_key] += self._amount_to_distribute[token_key]
            self._amount_to_distribute[token_key] = 0

    def _update_stake_balances(self) -> bool:
        """
        Updates the staked balances of BALN token
        """
        baln_score = self.create_interface_score(self._baln_score.get(), BalnTokenInterface)
        staked_baln_balances = baln_score.getStakeUpdates()
        if len(staked_baln_balances) == 0:
            return True
        for address, balance in staked_baln_balances.items():
            if address not in self._staked_baln_holders:
                self._staked_baln_holders.put(address)
            self._staked_baln_balances[address] = balance
        return False

    def _check_eligibility_against_debt_value(self) -> None:
        # Checks if the staked BALN token holders still maintain the debt criteria
        # get debt data in batch and process only those addresses
        baln_stake_holders = get_array_items(self._staked_baln_holders, self._staked_dist_index.get(),
                                             self._max_loop_count.get())

        count_of_remaining_baln_stake_holders = len(baln_stake_holders)
        dist_index = self._staked_dist_index.get() + count_of_remaining_baln_stake_holders
        if dist_index >= len(self._staked_baln_holders):
            # Filter process has been complete, can be changed to next state
            self._staked_dist_index.set(0)
            self._dividends_distribution_status.set(Status.TOTAL_DATA_FROM_BALN_LP_POOL)
            return
        else:
            self._staked_dist_index.set(dist_index)

        loan_score = self.create_interface_score(self._loans_score.get(), LoansInterface)
        baln_stake_holders_debts = loan_score.getDebts(baln_stake_holders, self._snapshot_id.get() - 1)
        for address, debt in baln_stake_holders_debts.items():
            if debt >= self._minimum_eligible_debt.get():
                if address not in self._eligible_baln_holders:
                    self._eligible_baln_holders.put(address)
                baln_token = self._staked_baln_balances[address]
                self._eligible_baln_balances[address] = baln_token
                self._total_eligible_baln_tokens.set(self._total_eligible_baln_tokens.get() + baln_token)

    def _update_total_lp_tokens(self) -> None:
        # update the total lp tokens and baln tokens in the pool
        dex_score = self.create_interface_score(self._dex_score.get(), DexInterface)
        baln_in_dex = dex_score.getBalnSnapshot(BALNBNUSD, self._snapshot_id.get() - 1)
        total_lp_tokens = dex_score.getTotalValue(BALNBNUSD, self._snapshot_id.get() - 1)
        self._baln_in_dex.set(baln_in_dex)
        self._total_lp_tokens.set(total_lp_tokens)
        self._dividends_distribution_status.set(Status.COMPUTE_BALN_FOR_LP_HOLDER)

    def _update_lp_holders_balance(self) -> None:
        # Update the lp holders balance of baln tokens
        # name: BALNbnUSD
        pass

    def _update_stake_balances(self) -> bool:
        """
        Updates the staked balances of BALN token
        """
        baln_score = self.create_interface_score(self._baln_score.get(), BalnTokenInterface)
        staked_baln_balances = baln_score.getStakeUpdates()
        if len(staked_baln_balances) == 0:
            return True
        for address, balance in staked_baln_balances.items():
            if address not in self._staked_baln_holders:
                self._staked_baln_holders.put(address)
            self._staked_baln_balances[address] = balance
        return False

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
