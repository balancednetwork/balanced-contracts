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

from .tokens.IRC2 import IRC2
from .utils.checks import *
from .utils.consts import *


# An interface to the Band Price Oracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


# An interface to the Balanced DEX
class DexInterface(InterfaceScore):
    @interface
    def getPrice(self, _id: int) -> int:
        pass

    @interface
    def getPoolId(self, _token1Address: Address, _token2Address: Address) -> int:
        pass

    @interface
    def getBalnPrice(self) -> int:
        pass

    @interface
    def getTimeOffset(self) -> int:
        pass


class StakedBalnTokenSnapshots(TypedDict):
    address: Address
    amount: int
    day: int


class TotalStakedBalnTokenSnapshots(TypedDict):
    amount: int
    day: int


class BalancedToken(IRC2):
    _PRICE_UPDATE_TIME = "price_update_time"
    _LAST_PRICE = "last_price"
    _MIN_INTERVAL = "min_interval"

    _EVEN_DAY_STAKE_CHANGES = "even_day_stake_changes"
    _ODD_DAY_STAKE_CHANGES = "odd_day_stake_changes"

    _INDEX_STAKE_ADDRESS_CHANGES = "index_stake_address_changes"
    _INDEX_UPDATE_STAKE = "index_update_stake"
    _STAKE_UPDATE_DB = "stake_update_db"
    _STAKE_ADDRESS_UPDATE_DB = "stake_address_update_db"

    _STAKING_ENABLED = "staking_enabled"

    _STAKED_BALANCES = "staked_balances"
    _MINIMUM_STAKE = "minimum_stake"
    _UNSTAKING_PERIOD = "unstaking_period"
    _TOTAL_STAKED_BALANCE = "total_staked_balance"

    _DIVIDENDS_SCORE = "dividends_score"
    _GOVERNANCE = "governance"

    _DEX_SCORE = "dex_score"
    _BNUSD_SCORE = "bnUSD_score"
    _ORACLE = "oracle"
    _ORACLE_NAME = "oracle_name"

    _TIME_OFFSET = "time_offset"
    _STAKE_SNAPSHOTS = "stake_snapshots"
    _TOTAL_SNAPSHOTS = "total_snapshots"
    _TOTAL_STAKED_SNAPSHOT = "total_staked_snapshot"
    _TOTAL_STAKED_SNAPSHOT_COUNT = "total_staked_snapshot_count"

    _ENABLE_SNAPSHOTS = "enable_snapshots"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._dex_score = VarDB(self._DEX_SCORE, db, value_type=Address)
        self._bnusd_score = VarDB(self._BNUSD_SCORE, db, value_type=Address)
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)
        self._oracle = VarDB(self._ORACLE, db, value_type=Address)
        self._oracle_name = VarDB(self._ORACLE_NAME, db, value_type=str)
        self._price_update_time = VarDB(self._PRICE_UPDATE_TIME, db, value_type=int)
        self._last_price = VarDB(self._LAST_PRICE, db, value_type=int)
        self._min_interval = VarDB(self._MIN_INTERVAL, db, value_type=int)

        self._even_day_stake_changes = ArrayDB(self._EVEN_DAY_STAKE_CHANGES, db, value_type=Address)
        self._odd_day_stake_changes = ArrayDB(self._ODD_DAY_STAKE_CHANGES, db, value_type=Address)
        self._stake_changes = [self._even_day_stake_changes, self._odd_day_stake_changes]

        self._index_update_stake = VarDB(self._INDEX_UPDATE_STAKE, db, value_type=int)
        self._index_stake_address_changes = VarDB(self._INDEX_STAKE_ADDRESS_CHANGES, db, value_type=int)

        self._stake_update_db = VarDB(self._STAKE_UPDATE_DB, db, value_type=int)
        self._stake_address_update_db = VarDB(self._STAKE_ADDRESS_UPDATE_DB, db, value_type=int)

        self._staking_enabled = VarDB(self._STAKING_ENABLED, db, value_type=bool)

        self._staked_balances = DictDB(self._STAKED_BALANCES, db, value_type=int, depth=2)
        self._minimum_stake = VarDB(self._MINIMUM_STAKE, db, value_type=int)
        self._unstaking_period = VarDB(self._UNSTAKING_PERIOD, db, value_type=int)
        self._total_staked_balance = VarDB(self._TOTAL_STAKED_BALANCE, db, value_type=int)

        self._dividends_score = VarDB(self._DIVIDENDS_SCORE, db, value_type=Address)

        self._time_offset = VarDB(self._TIME_OFFSET, db, value_type=int)

        # [address][snapshot_id]["ids" || "amount"]
        self._stake_snapshots = DictDB(self._STAKE_SNAPSHOTS, db, value_type=int, depth=3)
        # [address] = total_number_of_snapshots_taken
        self._total_snapshots = DictDB(self._TOTAL_SNAPSHOTS, db, value_type=int)

        # [snapshot_id]["ids" || "amount"]
        self._total_staked_snapshot = DictDB(self._TOTAL_STAKED_SNAPSHOT, db, value_type=int, depth=2)
        self._total_staked_snapshot_count = VarDB(self._TOTAL_STAKED_SNAPSHOT_COUNT, db, value_type=int)

        self._enable_snapshots = VarDB(self._ENABLE_SNAPSHOTS, db, value_type=bool)

    def on_install(self, _governance: Address) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)
        self._governance.set(_governance)
        self._staking_enabled.set(False)
        self._index_update_stake.set(0)
        self._index_stake_address_changes.set(0)
        self._stake_update_db.set(0)
        self._stake_address_update_db.set(0)
        self._oracle_name.set(DEFAULT_ORACLE_NAME)
        self._last_price.set(INITIAL_PRICE_ESTIMATE)
        self._min_interval.set(MIN_UPDATE_TIME)
        self._minimum_stake.set(MINIMUM_STAKE)
        self._unstaking_period.set(DEFAULT_UNSTAKING_PERIOD)

    def on_update(self) -> None:
        super().on_update()
        self.setTimeOffset()
        self._enable_snapshots.set(False)

    @external(readonly=True)
    def getPeg(self) -> str:
        return TAG

    @external
    @only_governance
    def setbnUSD(self, _address: Address) -> None:
        self._bnusd_score.set(_address)

    @external(readonly=True)
    def getbnUSD(self) -> dict:
        return self._bnusd_score.get()

    @external
    @only_governance
    def setOracle(self, _address: Address) -> None:
        self._oracle.set(_address)

    @external(readonly=True)
    def getOracle(self) -> dict:
        return self._oracle.get()

    @external
    @only_governance
    def setDex(self, _address: Address) -> None:
        self._dex_score.set(_address)

    @external(readonly=True)
    def getDex(self) -> dict:
        return self._dex_score.get()

    @external
    @only_governance
    def setOracleName(self, _name: str) -> None:
        self._oracle_name.set(_name)

    @external(readonly=True)
    def getOracleName(self) -> dict:
        return self._oracle_name.get()

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
    def setMinInterval(self, _interval: int) -> None:
        self._min_interval.set(_interval)

    @external(readonly=True)
    def getMinInterval(self) -> int:
        return self._min_interval.get()

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
        dex_score = self._dex_score.get()
        oracle_address = self._oracle.get()
        dex = self.create_interface_score(dex_score, DexInterface)
        oracle = self.create_interface_score(oracle_address, OracleInterface)
        price = dex.getBalnPrice()
        priceData = oracle.get_reference_data('USD', 'ICX')

        return priceData['rate'] * price // EXA

    def update_asset_value(self) -> None:
        """
        Calls the oracle method for the asset and updates the asset
        value in loop.
        """
        base = "BALN"
        quote = "bnUSD"
        dex_score = self._dex_score.get()
        oracle_address = self._oracle.get()
        try:
            dex = self.create_interface_score(dex_score, DexInterface)
            oracle = self.create_interface_score(oracle_address, OracleInterface)
            price = dex.getBalnPrice()
            priceData = oracle.get_reference_data('USD', 'ICX')
            self._last_price.set(priceData['rate'] * price // EXA)
            self._price_update_time.set(self.now())
            self.OraclePrice(base + quote, self._oracle_name.get(), dex_score, price)
        except Exception:
            revert(f'{base + quote}, {self._oracle_name.get()}, {dex_score}.')

    @external(readonly=True)
    def detailsBalanceOf(self, _owner: Address) -> dict:
        if self._staked_balances[_owner][Status.UNSTAKING_PERIOD] < self.now():
            curr_unstaked: int = self._staked_balances[_owner][Status.UNSTAKING]
        else:
            curr_unstaked: int = 0

        if self._first_time(_owner):
            available_balance = self.balanceOf(_owner)
        else:
            available_balance = self._staked_balances[_owner][Status.AVAILABLE]

        unstaking_amount = self._staked_balances[_owner][Status.UNSTAKING] - curr_unstaked
        unstaking_time = 0 if unstaking_amount == 0 else self._staked_balances[_owner][Status.UNSTAKING_PERIOD]

        return {
            "Total balance": self._balances[_owner],
            "Available balance": available_balance + curr_unstaked,
            "Staked balance": self._staked_balances[_owner][Status.STAKED],
            "Unstaking balance": unstaking_amount,
            "Unstaking time (in microseconds)": unstaking_time
        }

    def _first_time(self, _from: Address) -> bool:
        return (
                self._staked_balances[_from][Status.AVAILABLE] == 0
                and self._staked_balances[_from][Status.STAKED] == 0
                and self._staked_balances[_from][Status.UNSTAKING] == 0
                and self._balances[_from] != 0
        )

    @external(readonly=True)
    def unstakedBalanceOf(self, _owner: Address) -> int:
        detail_balance = self.detailsBalanceOf(_owner)
        return detail_balance["Unstaking balance"]

    @external(readonly=True)
    def stakedBalanceOf(self, _owner: Address) -> int:
        return self._staked_balances[_owner][Status.STAKED]

    @external(readonly=True)
    def availableBalanceOf(self, _owner: Address) -> int:
        detail_balance = self.detailsBalanceOf(_owner)
        return detail_balance["Available balance"]

    @external(readonly=True)
    def getStakingEnabled(self) -> bool:
        return self._staking_enabled.get()

    @external(readonly=True)
    def totalStakedBalance(self) -> int:
        return self._total_staked_balance.get()

    @external(readonly=True)
    def getMinimumStake(self) -> int:
        return self._minimum_stake.get()

    @external(readonly=True)
    def getUnstakingPeriod(self) -> int:
        time_in_microseconds = self._unstaking_period.get()
        time_in_days = time_in_microseconds // DAY_TO_MICROSECOND
        return time_in_days

    def _check_first_time(self, _from: Address):
        # If first time copy the balance to available staked balances
        if self._first_time(_from):
            self._staked_balances[_from][Status.AVAILABLE] = self._balances[_from]

    def staking_enabled_only(self):
        if not self._staking_enabled.get():
            revert(f"{TAG}: Staking must first be enabled.")

    @external
    @only_owner
    def toggleEnableSnapshot(self) -> None:
        self._enable_snapshots.set(not self._enable_snapshots.get())

    @external(readonly=True)
    def getSnapshotEnabled(self) -> bool:
        return self._enable_snapshots.get()

    @external
    @only_governance
    def toggleStakingEnabled(self) -> None:
        self._staking_enabled.set(not self._staking_enabled.get())

    def _make_available(self, _from: Address):
        if self._staked_balances[_from][Status.UNSTAKING_PERIOD] <= self.now():
            curr_unstaked = self._staked_balances[_from][Status.UNSTAKING]
            self._staked_balances[_from][Status.UNSTAKING] = 0
            self._staked_balances[_from][Status.AVAILABLE] += curr_unstaked

    @external
    def stake(self, _value: int) -> None:
        self.staking_enabled_only()
        _from = self.msg.sender
        if _value < 0:
            revert(f"{TAG}: Staked BALN value can't be less than zero.")
        if _value > self._balances[_from]:
            revert(f"{TAG}: Out of BALN balance.")
        if _value < self._minimum_stake.get() and _value != 0:
            revert(f"{TAG}: Staked BALN must be greater than the minimum stake amount and non zero.")

        self._check_first_time(_from)
        self._make_available(_from)

        old_stake = self._staked_balances[_from][Status.STAKED] + self._staked_balances[_from][Status.UNSTAKING]
        new_stake = _value
        stake_increment = _value - self._staked_balances[_from][Status.STAKED]
        unstake_amount: int = 0
        if new_stake > old_stake:
            offset: int = new_stake - old_stake
            self._staked_balances[_from][Status.AVAILABLE] = self._staked_balances[_from][Status.AVAILABLE] - offset
        else:
            unstake_amount = old_stake - new_stake

        self._staked_balances[_from][Status.STAKED] = _value
        self._staked_balances[_from][Status.UNSTAKING] = unstake_amount
        self._staked_balances[_from][Status.UNSTAKING_PERIOD] = self.now() + self._unstaking_period.get()
        self._total_staked_balance.set(self._total_staked_balance.get() + stake_increment)

        if self._enable_snapshots.get():
            self._update_snapshot_for_address(self.msg.sender, _value)
            self._update_total_staked_snapshot(self._total_staked_balance.get())

    @external
    @only_governance
    def setMinimumStake(self, _amount: int) -> None:
        if _amount < 0:
            revert(f"{TAG}: Amount cannot be less than zero.")

        total_amount = _amount * 10 ** self._decimals.get()
        self._minimum_stake.set(total_amount)

    @external
    @only_governance
    def setUnstakingPeriod(self, _time: int) -> None:
        if _time < 0:
            revert(f"{TAG}: Time cannot be negative.")
        total_time = _time * DAY_TO_MICROSECOND
        self._unstaking_period.set(total_time)

    @external
    @only_governance
    def setDividends(self, _score: Address) -> None:
        self._dividends_score.set(_score)

    @external(readonly=True)
    def getDividends(self) -> Address:
        return self._dividends_score.get()

    def dividends_only(self):
        if self.msg.sender != self._dividends_score.get():
            revert(f"{TAG}: This method can only be called by the dividends distribution contract.")

    @external
    def getStakeUpdates(self) -> dict:
        self.dividends_only()
        self.staking_enabled_only()

        stake_changes = self._stake_changes[self._stake_update_db.get()]
        length_list = len(stake_changes)

        start = self._index_update_stake.get()
        if start == length_list:
            if self._stake_update_db.get() != self._stake_address_update_db.get():
                self._stake_update_db.set(self._stake_address_update_db.get())
                self._index_update_stake.set(self._index_stake_address_changes.get())
            return {}

        end = min(start + MAX_LOOP, length_list)
        detailed_stake_balances = {
            str(stake_changes[i]): self.stakedBalanceOf(stake_changes[i]) for i in range(start, end)
        }
        self._index_update_stake.set(end)
        return detailed_stake_balances

    @external
    def clearYesterdaysStakeChanges(self) -> bool:
        self.dividends_only()
        self.staking_enabled_only()

        yesterday = (self._stake_address_update_db.get() + 1) % 2
        yesterdays_changes = self._stake_changes[yesterday]
        length_list = len(yesterdays_changes)

        if length_list == 0:
            return True

        loop_count = min(length_list, MAX_LOOP)
        for _ in range(loop_count):
            yesterdays_changes.pop()

        return not len(yesterdays_changes) > 0

    @external
    def switchStakeUpdateDB(self) -> None:
        self.dividends_only()
        self.staking_enabled_only()

        new_day = (self._stake_address_update_db.get() + 1) % 2
        self._stake_address_update_db.set(new_day)
        stake_changes = self._stake_changes[new_day]
        self._index_stake_address_changes.set(len(stake_changes))

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):

        _from = self.msg.sender
        self._check_first_time(_from)
        self._check_first_time(_to)
        self._make_available(_from)
        self._make_available(_to)

        if self._staked_balances[_from][Status.AVAILABLE] < _value:
            revert(f"{TAG}: Out of available balance. Please check staked and total balance.")

        self._staked_balances[_from][Status.AVAILABLE] = self._staked_balances[_from][Status.AVAILABLE] - _value
        self._staked_balances[_to][Status.AVAILABLE] = self._staked_balances[_to][Status.AVAILABLE] + _value

        super().transfer(_to, _value, _data)

    @external
    def mint(self, _amount: int, _data: bytes = None) -> None:
        """
        Creates `_amount` number of tokens, and assigns to caller account.
        Increases the balance of that account and total supply.
        See {IRC2-_mint}

        :param _amount: Number of tokens to be created at the account.
        :param _data: data to mint
        """
        if _data is None:
            _data = b'None'

        _to = self.msg.sender
        self._check_first_time(_to)
        self._make_available(_to)
        self._staked_balances[_to][Status.AVAILABLE] = self._staked_balances[_to][Status.AVAILABLE] + _amount

        self._mint(_to, _amount, _data)

    @external
    def mintTo(self, _account: Address, _amount: int, _data: bytes = None) -> None:
        """
        Creates `_amount` number of tokens, assigns to self, then transfers to `_account`.
        Increases the balance of that account and total supply.
        See {IRC2-_mint}

        :param _account: The account at which token is to be created.
        :param _amount: Number of tokens to be created at the account.
        :param _data: data to mint
        """
        if _data is None:
            _data = b'None'

        self._check_first_time(_account)
        self._make_available(_account)
        self._staked_balances[_account][Status.AVAILABLE] = self._staked_balances[_account][Status.AVAILABLE] + _amount

        self._mint(_account, _amount, _data)

    @external
    def burn(self, _amount: int) -> None:
        """
        Destroys `_amount` number of tokens from the caller account.
        Decreases the balance of that account and total supply.
        See {IRC2-_burn}

        :param _amount: Number of tokens to be destroyed.
        """
        _from = self.msg.sender
        self._check_first_time(_from)
        self._make_available(_from)

        if self._staked_balances[_from][Status.AVAILABLE] < _amount:
            revert(f"{TAG}: Out of available balance. Please check staked and total balance.")
        self._staked_balances[_from][Status.AVAILABLE] = self._staked_balances[_from][Status.AVAILABLE] - _amount

        self._burn(_from, _amount)

    @external
    def burnFrom(self, _account: Address, _amount: int) -> None:
        """
        Destroys `_amount` number of tokens from the specified `_account` account.
        Decreases the balance of that account and total supply.
        See {IRC2-_burn}

        :param _account: The account at which token is to be destroyed.
        :param _amount: Number of tokens to be destroyed at the `_account`.
        """
        self._check_first_time(_account)
        self._make_available(_account)

        if self._staked_balances[_account][Status.AVAILABLE] < _amount:
            revert(f"{TAG}: Out of available balance. Please check staked and total balance.")
        self._staked_balances[_account][Status.AVAILABLE] = self._staked_balances[_account][Status.AVAILABLE] - _amount

        self._burn(_account, _amount)

    @external
    @only_owner
    def setTimeOffset(self) -> None:
        _dex = self.create_interface_score(self._dex_score.get(), DexInterface)
        _delta_time = _dex.getTimeOffset()
        self._time_offset.set(_delta_time)

    @external(readonly=True)
    def getTimeOffset(self) -> int:
        return self._time_offset.get()

    @external(readonly=True)
    def getDay(self) -> int:
        """
        Returns the current day (floored). Used for snapshotting,
        paying rewards, and paying dividends.
        """
        return (self.now() - self._time_offset.get()) // DAY_TO_MICROSECOND

    # ----------------------------------------------------------
    # Snapshots
    # ----------------------------------------------------------

    def _update_snapshot_for_address(self, _account: Address, _amount: int) -> None:
        if self._time_offset.get() == 0:
            self.setTimeOffset()
        current_id = self.getDay()
        total_snapshots_taken = self._total_snapshots[_account]

        if total_snapshots_taken > 0 and self._stake_snapshots[_account][total_snapshots_taken - 1][IDS] == current_id:
            self._stake_snapshots[_account][total_snapshots_taken - 1][AMOUNT] = _amount
        else:
            self._stake_snapshots[_account][total_snapshots_taken][IDS] = current_id
            self._stake_snapshots[_account][total_snapshots_taken][AMOUNT] = _amount
            self._total_snapshots[_account] = total_snapshots_taken + 1

    def _update_total_staked_snapshot(self, _amount: int):

        if self._time_offset.get() == 0:
            self.setTimeOffset()
        current_id = self.getDay()
        total_snapshots_taken = self._total_staked_snapshot_count.get()

        if total_snapshots_taken > 0 and self._total_staked_snapshot[total_snapshots_taken - 1][IDS] == current_id:
            self._total_staked_snapshot[total_snapshots_taken - 1][AMOUNT] = _amount
        else:
            self._total_staked_snapshot[total_snapshots_taken][IDS] = current_id
            self._total_staked_snapshot[total_snapshots_taken][AMOUNT] = _amount
            self._total_staked_snapshot_count.set(total_snapshots_taken + 1)

    @external(readonly=True)
    def stakedBalanceOfAt(self, _account: Address, _day: int) -> int:
        current_day = self.getDay()
        if _day > current_day:
            revert(f'{TAG}: Asked _day is greater than current day')

        total_snapshots_taken = self._total_snapshots[_account]
        if total_snapshots_taken == 0:
            return 0

        if self._stake_snapshots[_account][total_snapshots_taken - 1][IDS] <= _day:
            return self._stake_snapshots[_account][total_snapshots_taken - 1][AMOUNT]

        if self._stake_snapshots[_account][0][IDS] > _day:
            return 0

        low = 0
        high = total_snapshots_taken - 1
        while high > low:
            mid = high - (high - low)//2
            mid_value = self._stake_snapshots[_account][mid]
            if mid_value[IDS] == _day:
                return mid_value[AMOUNT]
            elif mid_value[IDS] < _day:
                low = mid
            else:
                high = mid - 1

        return self._stake_snapshots[_account][low][AMOUNT]

    @external(readonly=True)
    def totalStakedBalanceOfAt(self, _day: int) -> int:
        current_day = self.getDay()

        if _day > current_day:
            revert(f"{TAG}: Asked _day is greater than current day")

        total_snapshots_taken = self._total_staked_snapshot_count.get()
        if total_snapshots_taken == 0:
            return 0

        if self._total_staked_snapshot[total_snapshots_taken - 1][IDS] <= _day:
            return self._total_staked_snapshot[total_snapshots_taken - 1][AMOUNT]

        if self._total_staked_snapshot[0][IDS] > _day:
            return 0

        low = 0
        high = total_snapshots_taken - 1
        while high > low:
            mid = high - (high-low)//2
            mid_value = self._total_staked_snapshot[mid]
            if mid_value[IDS] == _day:
                return mid_value[AMOUNT]
            elif mid_value[IDS] < _day:
                low = mid
            else:
                high = mid - 1

        return self._total_staked_snapshot[low][AMOUNT]

    @external
    @only_owner
    def loadBalnStakeSnapshot(self, _data: List[StakedBalnTokenSnapshots]) -> None:
        if self._time_offset.get() == 0:
            self.setTimeOffset()
        for _stake in _data:
            current_id = int(_stake.get('day'))
            if current_id <= self.getDay():
                _account = _stake.get('address')
                length = self._total_snapshots[_account]
                self._stake_snapshots[_account][length][IDS] = current_id
                self._stake_snapshots[_account][length][AMOUNT] = int(_stake.get('amount'))
                self._total_snapshots[_account] += 1
            else:
                pass

    @external
    @only_owner
    def loadTotalStakeSnapshot(self, _data: List[TotalStakedBalnTokenSnapshots]) -> None:
        if self._time_offset.get() == 0:
            self.setTimeOffset()
        for _id in _data:
            current_id = int(_id.get('day'))
            if current_id <= self.getDay():
                amount = int(_id.get('amount'))
                length = self._total_staked_snapshot_count.get()
                self._total_staked_snapshot[length][IDS] = current_id
                self._total_staked_snapshot[length][AMOUNT] = amount
                self._total_staked_snapshot_count.set(self._total_staked_snapshot_count.get() + 1)

            else:
                pass

    # --------------------------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------------------------

    @eventlog(indexed=3)
    def OraclePrice(self, market: str, oracle_name: str, oracle_address: Address, price: int):
        pass
