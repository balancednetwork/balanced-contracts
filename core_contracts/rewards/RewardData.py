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
from .utils.consts import *


class DataSourceInterface(InterfaceScore):
    @interface
    def precompute(self, _snapshot_id: int, batch_size: int) -> bool:
        pass

    @interface
    def getTotalValue(self, _name: str, _snapshot_id: int) -> int:
        pass

    @interface
    def getBnusdValue(self, _name: str) -> int:
        pass

    @interface
    def getDataBatch(self, _name: str, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        pass

    @interface
    def getBalnPrice(self) -> int:
        pass

    @interface
    def getBalanceAndSupply(self, _name: str, _owner: Address) -> dict:
        pass

class RewardsDataEntry(TypedDict):
    _user: Address
    _balance: int

class BatchRewardsData(TypedDict):
    _name: str
    _totalSupply: int
    _data: List[RewardsDataEntry]

class RewardsData(TypedDict):
    _user: Address
    _name: str
    _balance: int
    _totalSupply: int


class DataSource(object):

    def __init__(self, db: IconScoreDatabase, rewards: IconScoreBase) -> None:
        self._rewards = rewards
        self.contract_address = VarDB('contract_address', db, value_type=Address)
        self.name = VarDB('name', db, value_type=str)
        self.day = VarDB('day', db, value_type=int)
        self.precomp = VarDB('precomp', db, value_type=bool)
        self.offset = VarDB('offset', db, value_type=int)
        self.total_value = DictDB('total_value', db, value_type=int)
        self.total_dist = DictDB('total_dist', db, value_type=int)
        self.dist_percent = VarDB('dist_percent', db, value_type=int)

        # map: address -> user weight
        # user weight is defined as user supply * emission
        # Upon claim, a user conults many data sources to get their rewards
        self.user_weight = DictDB('user_weight', db, value_type=int)

        # Timestamp the rewards were last updated
        self.last_update_time_us = VarDB('last_update_us', db, value_type=int)

        # Running total reward weight
        # Reward weight is supply * emission
        self.total_weight = VarDB('running_total', db, value_type=int)

        # Current total supply, the total quantity of asset against which
        # rewards are assessed
        self.total_supply = VarDB('total_supply', db, value_type=int)
    
    def load_current_supply(self, _owner: Address) -> dict:
        data_source = self._rewards.create_interface_score(self.contract_address.get(), DataSourceInterface)
        return data_source.getBalanceAndSupply(self.name.get(), _owner)
    
    def _compute_total_weight(self, previous_total_weight: int, emission: int, total_supply: int, last_update_time: int, current_time: int) -> int:
        # Return if there is no supply to emit based on or no emission
        if emission == 0 or total_supply == 0:
            return previous_total_weight
        
        time_delta = current_time - last_update_time

        # We may decide to increase the max time delta to drop writes
        if time_delta == 0:
            return previous_total_weight
        
        weight_delta = (emission * time_delta * EXA) // (DAY_IN_MICROSECONDS * total_supply)
        new_total_weight = previous_total_weight + weight_delta

        return new_total_weight

    def _update_total_weight(self, current_time: int, total_supply: int) -> int:
        previous_running_total = self.total_weight.get()
        last_update_timestamp = self.last_update_time_us.get()

        # Special case for the day1s
        if last_update_timestamp == 0:
            last_update_timestamp = current_time
            self.last_update_time_us.set(current_time)

        # If the current time is equal to the last update time, don't emit any new rewards
        if current_time == last_update_timestamp:
            return previous_running_total
        
        # Emit rewards based on the time delta * reward rate
        start_timestamp_us = self._rewards._start_timestamp.get()
        previous_rewards_day = 0
        previous_day_end_us = 0

        while last_update_timestamp < current_time:
            # Play forward all days
            previous_rewards_day = (last_update_timestamp - start_timestamp_us) // DAY_IN_MICROSECONDS
            previous_day_end_us = start_timestamp_us + (DAY_IN_MICROSECONDS *  (previous_rewards_day + 1))

            end_compute_timestamp_us = min(previous_day_end_us, current_time)

        
            emission = self.total_dist[previous_rewards_day]
            new_total = self._compute_total_weight(previous_running_total, emission, total_supply, last_update_timestamp, end_compute_timestamp_us)

            # Debug code, remove before a live launch
            if new_total < previous_running_total:
                revert(f"Reward computation error, new_weight={new_total}, old_weight={previous_running_total}, emission={emission}")
            
            last_update_timestamp = end_compute_timestamp_us
        
        # Write new total weight to disk if it has changed
        if new_total > previous_running_total:
            self.total_weight.set(new_total)
            self.last_update_time_us.set(current_time)
        
        return new_total
    
    def _compute_user_rewards(self, prev_user_balance: int, total_weight: int, user_weight: int) -> int:
        # User rewards = weight change * last known balance
        delta_weight = total_weight - user_weight
        return delta_weight * prev_user_balance
    
    def compute_single_user_data(self, current_time, prev_total_supply: int, user: Address, prev_balance: int) -> int:
        current_user_weight = self.user_weight[user]
        # Then, check the current weight of the pool, updating if necessary via the helper function
        total_weight = self._compute_total_weight(self.total_weight.get(), self.total_dist[self._rewards._get_day()], prev_total_supply, self.last_update_time_us.get(), current_time)

        accrued_rewards = 0

        # If the user's current weight is less than the total, update their weight and issue rewards
        if current_user_weight < total_weight:
            # Don't do unnecessary writes - only reward the user if their previous balance was nonzero
            if prev_balance > 0:
                accrued_rewards = self._compute_user_rewards(prev_balance, total_weight, current_user_weight) // EXA

        return accrued_rewards

    def update_single_user_data(self, current_time: int, prev_total_supply: int, user: Address, prev_balance: int) -> int:
        # First, get the current user's weight
        current_user_weight = self.user_weight[user]
        # Then, check the current weight of the pool, updating if necessary via the helper function
        total_weight = self._update_total_weight(current_time, prev_total_supply)

        accrued_rewards = 0

        # If the user's current weight is less than the total, update their weight and issue rewards
        if current_user_weight < total_weight:
            # Don't do unnecessary writes - only reward the user if their previous balance was nonzero
            if prev_balance > 0:
                accrued_rewards = self._compute_user_rewards(prev_balance, total_weight, current_user_weight) // EXA
            # Update the user's weight to the current total weight regardless of reward
            self.user_weight[user] = total_weight
        
        return accrued_rewards

    def _distribute(self, batch_size: int) -> None:
        """
        The calculation and distribution of rewards proceeds in two stages
        """
        day = self.day.get()
        name = self.name.get()
        data_source = self._rewards.create_interface_score(self.contract_address.get(), DataSourceInterface)
        precomp_done = data_source.precompute(day, batch_size)
        if not self.precomp.get() and precomp_done:
            self.precomp.set(True)
            self.total_value[day] = data_source.getTotalValue(name, day)

        if self.precomp.get():
            offset = self.offset.get()
            data_batch = data_source.getDataBatch(name, day, batch_size, offset)
            self.offset.set(offset + batch_size)
            if not data_batch:
                self.day.set(day + 1)
                self.offset.set(0)
                self.precomp.set(False)
                return
            remaining = self.total_dist[day]  # Amount remaining of the allocation to this source
            shares = self.total_value[day]  # The sum of all mining done by this data source
            original_shares = shares
            batch_sum = sum(data_batch.values())
            for address in data_batch:
                token_share = remaining * data_batch[address] // shares
                if shares <= 0:
                    revert(
                        f'{TAG}: zero or negative divisor for {name}, '
                        f'sum: {batch_sum}, '
                        f'total: {shares}, '
                        f'remaining: {remaining}, '
                        f'token_share: {token_share}, '
                        f'starting: {original_shares}'
                    )
                remaining -= token_share
                shares -= data_batch[address]
                self._rewards._baln_holdings[address] += token_share
            self.total_dist[day] = remaining
            self.total_value[day] = shares
            self._rewards.Report(day, name, remaining, shares)

    def set_day(self, _day: int) -> None:
        self.day.set(_day)

    def set_dist_percent(self, _dist_percent: int) -> None:
        self.dist_percent.set(_dist_percent)

    def get_value(self) -> int:
        data_source = self._rewards.create_interface_score(self.contract_address.get(), DataSourceInterface)
        return data_source.getBnusdValue(self.name.get())
    
    def get_data_at(self, _day: int = -1) -> dict:
        return {
            'day': _day,
            'contract_address': self.contract_address.get(),
            'dist_percent': self.dist_percent.get(),
            'precomp': self.precomp.get(),
            'offset': self.offset.get(),
            'total_value': self.total_value[_day],
            'total_dist': self.total_dist[_day]
        }

    def get_data(self) -> dict:
        day = self.day.get()
        return {
            'day': day,
            'contract_address': self.contract_address.get(),
            'dist_percent': self.dist_percent.get(),
            'precomp': self.precomp.get(),
            'offset': self.offset.get(),
            'total_value': self.total_value[day],
            'total_dist': self.total_dist[day]
        }


class DataSourceDB:
    """
    Holds DataSource objects
    """

    def __init__(self, db: IconScoreDatabase, rewards: IconScoreBase):
        self._db = db
        self._rewards = rewards
        self._names = ArrayDB('names', db, value_type=str)
        self._items = {}

    def __getitem__(self, _name: str) -> DataSource:
        prefix = b'|'.join([DATASOURCE_DB_PREFIX, str(_name).encode()])
        if _name not in self._items:
            sub_db = self._db.get_sub_db(prefix)
            self._items[_name] = DataSource(sub_db, self._rewards)
        return self._items[_name]

    def __setitem__(self, key, value):
        revert(f'{TAG}: Illegal access.')

    def __iter__(self):
        for name in self._names:
            yield name

    def __len__(self) -> int:
        return len(self._names)

    def new_source(self, _name: str, _address: Address) -> None:
        self._names.put(_name)
        source = self.__getitem__(_name)
        source.name.set(_name)
        source.day.set(self._rewards._get_day())
        source.contract_address.set(_address)

    def remove_source(self, _name: str) -> None:
        if _name not in self._names:
            return
        source = self.__getitem__(_name)
        source.name.remove()
        source.day.remove()
        source.contract_address.remove()
        top = self._names.pop()
        if top != _name:
            for i in range(len(self._names)):
                if self._names[i] == _name:
                    self._names[i] = top