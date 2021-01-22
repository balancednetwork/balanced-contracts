from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable
from .utils.checks import *
from .utils.consts import *

TAG = 'BALN'

TOKEN_NAME = 'BalanceToken'
SYMBOL_NAME = 'BALN'
DEFAULT_PEG = 'BALN'
DEFAULT_ORACLE_ADDRESS = 'cx31bb0d42d9667fd6acab1bbebcfa3b916f04a3f3'
DEFAULT_ORACLE_NAME = 'BalancedDEX'


# An interface to the Balanced DEX
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class BalanceToken(IRC2Mintable, IRC2Burnable):
    
    _DEX_ADDRESS = "DEX_address"
    _PRICE_UPDATE_TIME = "price_update_time"
    _LAST_PRICE = "last_price"
    _MIN_INTERVAL = "min_interval"
    
    _EVEN_DAY_STAKE_CHANGES = "even_day_stake_changes"
    _ODD_DAY_STAKE_CHANGES = "odd_day_stake_changes"

    _INDEX_STAKE_ADDRESS_CHANGES = "index_stake_address_changes"
    _INDEX_UDPATE_STAKE = "index_update_stake"
    _STAKE_UPDATE_DB = "stake_update_db"
    _STAKE_ADDRESS_UPDATE_DB = "stake_address_update_db"

    _STAKING_ENABLED = "staking_enabled"

    _STAKED_BALANCES = "staked_balances"
    _MINIMUM_STAKE = "minimum_stake"
    _UNSTAKING_PERIOD = "unstaking_period"
    _TOTAL_STAKED_BALANCE = "total_staked_balance"

    _DIVIDENDS_SCORE = "dividends_score"

    _PEG = "peg"
    _ORACLE_ADDRESS = "oracle_address"
    _ORACLE_NAME = "oracle_name"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._DEX_address = VarDB(self._DEX_ADDRESS, db, value_type=Address)
        self._peg = VarDB(self._PEG, db, value_type=str)
        self._oracle_address = VarDB(self._ORACLE_ADDRESS, db, value_type=Address)
        self._oracle_name = VarDB(self._ORACLE_NAME, db, value_type=str)
        self._price_update_time = VarDB(self._PRICE_UPDATE_TIME, db, value_type=int)
        self._last_price = VarDB(self._LAST_PRICE, db, value_type=int)
        self._min_interval = VarDB(self._MIN_INTERVAL, db, value_type=int)

        self._even_day_stake_changes = ArrayDB(self._EVEN_DAY_STAKE_CHANGES, db, value_type=Address)
        self._odd_day_stake_changes = ArrayDB(self._ODD_DAY_STAKE_CHANGES, db, value_type=Address)
        self._stake_changes = [self._even_day_stake_changes, self._odd_day_stake_changes]

        self._index_update_stake = VarDB(self._INDEX_UDPATE_STAKE, db, value_type=int)
        self._index_stake_address_changes = VarDB(self._INDEX_STAKE_ADDRESS_CHANGES, db, value_type=int)

        self._stake_update_db = VarDB(self._STAKE_UPDATE_DB, db, value_type=int)
        self._stake_address_update_db = VarDB(self._STAKE_ADDRESS_UPDATE_DB, db, value_type=int)

        self._staking_enabled = VarDB(self._STAKING_ENABLED, db, value_type=bool)

        self._staked_balances = DictDB(self._STAKED_BALANCES, db, value_type=int, depth=2)
        self._minimum_stake = VarDB(self._MINIMUM_STAKE, db, value_type=int)
        self._unstaking_period = VarDB(self._UNSTAKING_PERIOD, db, value_type=int)
        self._total_staked_balance = VarDB(self._TOTAL_STAKED_BALANCE, db, value_type=int)

        self._dividends_score = VarDB(self._DIVIDENDS_SCORE, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)
        self._staking_enabled.set(False)
        self._index_update_stake.set(0)
        self._index_stake_address_changes.set(0)
        self._stake_update_db.set(0)
        self._stake_address_update_db.set(0)
        self._peg.set(DEFAULT_PEG)
        self._oracle_address.set(Address.from_string(DEFAULT_ORACLE_ADDRESS))
        self._oracle_name.set(DEFAULT_ORACLE_NAME)
        self._last_price.set(INITIAL_PRICE_ESTIMATE)
        self._min_interval.set(MIN_UPDATE_TIME)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def getPeg(self) -> str:
        return self._peg.get()

    @external
    @only_owner
    def setOracle(self, _address: Address, _name: str) -> None:
        self._oracle_address.set(_address)
        self._oracle_name.set(_name)

    @external(readonly=True)
    def getOracle(self, _name: str) -> dict:
        return {"name": self._oracle_name.set(_name), "address": str(self._oracle_address.get())}

    @external
    @only_owner
    def setDEXAddress(self, _address: Address) -> None:
        self._DEX_address.set(_address)

    @external(readonly=True)
    def getDEXAddress(self) -> Address:
        return self._DEX_address.get()

    @external
    @only_owner
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
        return self._last_price.get()

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
            self.OraclePriceUpdateFailed(base + quote, self._oracle_name.get(), oracle_address, f'Exception: {e}')

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
            revert(f"{TAG}: Staking must first be enabled")

    @external
    @only_owner
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
            revert(f"{TAG}: Staked BALN value can't be less than zero")
        if _value > self._balances[_from]:
            revert(f"{TAG}: Out of BALN balance")
        if _value < self._minimum_stake.get() and _value != 0:
            revert(f"{TAG}: Staked TAP must be greater than the minimum stake amount and non zero")

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

        stake_address_changes = self._stake_changes[self._stake_address_update_db.get()]
        stake_address_changes.put(_from)

    @external
    @only_owner
    def setMinimumStake(self, _amount: int) -> None:
        if _amount < 0:
            revert(f"{TAG}: Amount cannot be less than zero")

        total_amount = _amount * 10 ** self._decimals.get()
        self._minimum_stake.set(total_amount)

    @external
    @only_owner
    def setUnstakingPeriod(self, _time: int) -> None:
        if _time < 0:
            revert(f"{TAG}: Time cannot be negative")
        total_time = _time * DAY_TO_MICROSECOND
        self._unstaking_period.set(total_time)

    @external
    @only_owner
    def setDividendsScore(self, _score: Address) -> None:
        self._dividends_score.set(_score)

    @external(readonly=True)
    def getDividendsScore(self) -> Address:
        return self._dividends_score.get()

    def dividends_only(self):
        if self.msg.sender != self._dividends_score.get():
            revert(f"{TAG}: This method can only be called by the dividends distribution contract")

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
            revert(f"{TAG}: Out of available balance. Please check staked and total balance")

        self._staked_balances[_from][Status.AVAILABLE] = self._staked_balances[_from][Status.AVAILABLE] - _value
        self._staked_balances[_from][Status.AVAILABLE] = self._staked_balances[_from][Status.AVAILABLE] + _value

        IRC2Mintable.transfer(self, _to, _value, _data)

    # --------------------------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------------------------

    @eventlog(indexed=3)
    def DEXPrice(self, market: str, price: int, time: int):
        pass

    @eventlog(indexed=3)
    def OraclePriceUpdateFailed(self, market: str, oracle_name: str, oracle_address: Address, msg: str):
        pass

    @eventlog(indexed=3)
    def OraclePrice(self, market: str, oracle_name: str, oracle_address: Address, price: int):
        pass
