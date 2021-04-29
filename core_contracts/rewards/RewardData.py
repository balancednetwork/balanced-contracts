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
from .utils.consts import *


class DataSourceInterface(InterfaceScore):
    @interface
    def precompute(self, _snapshot_id: int, batch_size: int) -> str:
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

    def _distribute(self, batch_size: int) -> None:
        """
        The calculation and distribution of rewards proceeds in two stages
        """
        day = self.day.get()
        data_source = self._rewards.create_interface_score(self.contract_address.get(), DataSourceInterface)
        precomp_done = data_source.precompute(day, batch_size)
        if not self.precomp.get() and precomp_done:
            self.precomp.set(True)
            self.total_value[day] = data_source.getTotalValue(self.name.get(), day)

        if self.precomp.get():
            data_batch = data_source.getDataBatch(self.name.get(), day, batch_size, self.offset.get())
            self.offset.set(self.offset.get() + batch_size)
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
                        f'{TAG}: zero or negative divisor for {self.name.get()}, '
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
            self._rewards.Report(day, self.name.get(), remaining, shares)

    def set_day(self, _day: int) -> None:
        self.day.set(_day)

    def set_dist_percent(self, _dist_percent: int) -> None:
        self.dist_percent.set(_dist_percent)

    def get_value(self) -> int:
        data_source = self._rewards.create_interface_score(self.contract_address.get(), DataSourceInterface)
        return data_source.getBnusdValue(self.name.get())

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
