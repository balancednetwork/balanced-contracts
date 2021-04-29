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
from .RewardData import *


class DistPercentDict(TypedDict):
    recipient_name: str
    dist_percent: int


class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def mint(self, _amount: int, _data: bytes = None) -> None:
        pass


class Rewards(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._governance = VarDB('governance', db, value_type=Address)
        self._admin = VarDB('admin', db, value_type=Address)
        self._baln_address = VarDB('baln_address', db, value_type=Address)
        self._bwt_address = VarDB('bwt_address', db, value_type=Address)
        self._reserve_fund = VarDB('reserve_fund', db, value_type=Address)
        self._daofund = VarDB('dao_fund', db, value_type=Address)
        self._start_timestamp = VarDB('start_timestamp', db, value_type=int)
        self._batch_size = VarDB('batch_size', db, value_type=int)
        self._baln_holdings = DictDB('baln_holdings', db, value_type=int)
        self._recipient_split = DictDB('recipient_split', db, value_type=int)
        self._recipients = ArrayDB('recipients', db, value_type=str)
        self._platform_recipients = {'Worker Tokens': self._bwt_address,
                                     'Reserve Fund': self._reserve_fund,
                                     'DAOfund': self._daofund}
        self._total_dist = VarDB('total_dist', db, value_type=int)
        self._platform_day = VarDB('platform_day', db, value_type=int)
        self._data_source_db = DataSourceDB(db, self)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)
        self._platform_day.set(1)
        self._batch_size.set(DEFAULT_BATCH_SIZE)
        self._recipient_split['Worker Tokens'] = 0
        self._recipients.put('Worker Tokens')
        self._recipient_split['Reserve Fund'] = 0
        self._recipients.put('Reserve Fund')
        self._recipient_split['DAOfund'] = 0
        self._recipients.put('DAOfund')

    def on_update(self) -> None:
        super().on_update()
        self._data_source_db['sICX/bnUSD'].precomp.set(0)
        self._data_source_db['sICX/bnUSD'].offset.set(0)

    @external
    @only_governance
    def setDay(self, _day: int) -> None:
        for name in self._data_source_db:
            total_dist = self._data_source_db[name].total_dist[_day - 1]
            total_value = self._data_source_db[name].total_value[_day - 1]
            self.Report(_day - 1, name, total_dist, total_value)
            self._data_source_db[name].set_day(_day)

    @external(readonly=True)
    def name(self) -> str:
        return "Balanced Rewards"

    @external(readonly=True)
    def getEmission(self, _day: int = -1) -> int:
        if _day < 1:
            _day += self._get_day() + 1
        if _day < 1:
            revert(f'{TAG}: Invalid day.')
        return self._daily_dist(_day)

    @external(readonly=True)
    def getBalnHoldings(self, _holders: List[str]) -> dict:
        return {holder: self._baln_holdings[holder] for holder in _holders}

    @external(readonly=True)
    def getBalnHolding(self, _holder: str) -> int:
        return self._baln_holdings[_holder]

    @external(readonly=True)
    def distStatus(self) -> dict:
        return {
            'platform_day': self._platform_day.get(),
            'source_days': {
                source: self._data_source_db[source].day.get()
                for source in self._data_source_db
            }
        }

    # Methods to update the states of a data_source_name object
    @external
    @only_governance
    def updateBalTokenDistPercentage(self, _recipient_list: List[DistPercentDict]) -> None:
        """
        This method provides a means to adjust the allocation of rewards tokens.
        To maintain consistency a change to these percentages will only be
        accepted if they sum to 100%, with 100% represented by the value 10**18.
        This method must only be called when rewards are fully up to date.

        :param _recipient_list: List of dicts containing the allocation spec.
        :type _recipient_list: List[TypedDict]
        """
        if len(_recipient_list) != len(self._recipients):
            revert(f'{TAG}: Recipient lists lengths mismatched!')
        total_percentage = 0
        day = self._get_day()
        for recipient in _recipient_list:
            name = recipient['recipient_name']
            if name not in self._recipients:
                revert(f'{TAG}: Recipient {name} does not exist.')

            percent = recipient['dist_percent']
            self._recipient_split[name] = percent

            source = self._data_source_db[name]
            if source.get_data()['dist_percent'] == 0:
                source.set_day(day)
            source.set_dist_percent(percent)
            total_percentage += percent

        if total_percentage != 10 ** 18:
            revert(f'{TAG}: Total percentage does not sum up to 100.')

    @external(readonly=True)
    def getDataSourceNames(self) -> list:
        """
        Returns a list of the data source names.

        :return: list of data source names
        :rtype list
        """
        return [name for name in self._data_source_db]

    @external(readonly=True)
    def getRecipients(self) -> list:
        """
        Returns a list of the rewards token recipients.

        :return: list of recipient names
        :rtype list
        """
        return [recipient for recipient in self._recipients]

    @external(readonly=True)
    def getRecipientsSplit(self) -> dict:
        """
        Returns a dict of the rewards token recipients.

        :return: dict of recipient {names: percent}
        :rtype dict
        """
        return {recipient: self._recipient_split[recipient] for recipient in self._recipients}

    @external
    @only_governance
    def addNewDataSource(self, _name: str, _address: Address) -> None:
        """
        Sources for data on which to base incentive rewards are added with this
        method. Data source contracts must provide an API of precompute(),
        totalValue() and getDataBatch(). Newly added data sources will start
        with zero share (0%) of the rewards token distribution. The intention
        is to allow for the addition of new incentivized markets on the DEX.

        :param _name: Identifying name for the data source.
        :type _name: str
        :param _address: Address of the data source.
        :type _address: :class:`iconservice.base.address.Address`
        """
        if _name in self._recipients:
            return
        if not _address.is_contract:
            revert(f'{TAG}: Data source must be a contract.')
        self._recipients.put(_name)
        self._recipient_split[_name] = 0
        self._data_source_db.new_source(_name, _address)

    @external(readonly=True)
    def getDataSources(self) -> dict:
        result = {}
        for name in self._data_source_db:
            source = self._data_source_db[name]
            result[name] = source.get_data()
        return result

    @external(readonly=True)
    def getSourceData(self, _name: str) -> dict:
        source = self._data_source_db[_name]
        return source.get_data()

    @external
    def distribute(self) -> bool:
        platform_day = self._platform_day.get()
        day = self._get_day()
        if platform_day < day:
            if self._total_dist.get() == 0:
                distribution = self._daily_dist(platform_day)
                baln_token = self.create_interface_score(self._baln_address.get(), TokenInterface)
                baln_token.mint(distribution)
                self._total_dist.set(distribution)
                shares = EXA
                remaining = distribution
                for name in self._recipients:
                    split = self._recipient_split[name]
                    share = remaining * split // shares
                    if name in self._data_source_db:
                        self._data_source_db[name].total_dist[platform_day] = share
                    else:
                        baln_token.transfer(self._platform_recipients[name].get(), share)
                    remaining -= share
                    shares -= split
                    if shares == 0:
                        break
                self._total_dist.set(remaining) # remaining will be == 0 at this point.
                self._platform_day.set(platform_day + 1)
                return False
        batch_size = self._batch_size.get()
        for name in self._data_source_db:
            source_data = self.getSourceData(name)
            if source_data['day'] < day:
                source = self._data_source_db[name]
                source._distribute(batch_size)
                return False
        return True

    @external
    def claimRewards(self) -> None:
        address = str(self.msg.sender)
        amount = self._baln_holdings[address]
        if amount:
            baln_token = self.create_interface_score(self._baln_address.get(), TokenInterface)
            self._baln_holdings[address] = 0
            baln_token.transfer(self.msg.sender, amount)
            self.RewardsClaimed(self.msg.sender, amount)

    def _get_day(self) -> int:
        today = (self.now() - self._start_timestamp.get()) // DAY_IN_MICROSECONDS
        return today

    def _daily_dist(self, _day: int) -> int:
        if _day <= 60:
            return 10 ** 23
        else:
            index = _day - 60
            return max(((995 ** index) * 10 ** 23) // (1000 ** index), 1250 * 10 ** 18)

    @external(readonly=True)
    def getAPY(self, _name: str) -> int:
        """
        Returns an approximate APY for miners.

        :param _name: Data source name.
        :type _name: str

        :return: APY * 10**18
        :rtype int
        """
        dex = self._data_source_db['sICX/ICX']
        dex_score = self.create_interface_score(dex.contract_address.get(), DataSourceInterface)
        source = self._data_source_db[_name]
        emission = self.getEmission(-1)
        baln_price = dex_score.getBalnPrice()
        percent = source.dist_percent.get()
        return 365 * emission * percent * baln_price // (EXA * source.get_value())

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
        if self.msg.sender != self._baln_address.get():
            revert(f'{TAG}: The Rewards SCORE can only accept BALN tokens. '
                   f'Deposit not accepted from {self.msg.sender} '
                   f'Only accepted from BALN = {self._baln_address.get()}')

    # -------------------------------------------------------------------------------
    #   SETTERS AND GETTERS
    # -------------------------------------------------------------------------------

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
    def setBaln(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._baln_address.set(_address)

    @external(readonly=True)
    def getBaln(self) -> Address:
        return self._baln_address.get()

    @external
    @only_admin
    def setBwt(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._bwt_address.set(_address)

    @external(readonly=True)
    def getBwt(self) -> Address:
        return self._bwt_address.get()

    @external
    @only_admin
    def setReserve(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._reserve_fund.set(_address)

    @external(readonly=True)
    def getReserve(self) -> Address:
        return self._reserve_fund.get()

    @external
    @only_admin
    def setDaofund(self, _address: Address) -> None:
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._daofund.set(_address)

    @external(readonly=True)
    def getDaofund(self) -> Address:
        return self._daofund.get()

    @external
    @only_admin
    def setBatchSize(self, _batch_size: int) -> None:
        self._batch_size.set(_batch_size)

    @external(readonly=True)
    def getBatchSize(self) -> int:
        return self._batch_size.get()

    @external
    @only_governance
    def setTimeOffset(self, _timestamp: int) -> None:
        self._start_timestamp.set(_timestamp)

    @external(readonly=True)
    def getTimeOffset(self) -> int:
        return self._start_timestamp.get()

    # -------------------------------------------------------------------------------
    #   EVENT LOGS
    # -------------------------------------------------------------------------------

    @eventlog(indexed=1)
    def RewardsClaimed(self, _address: Address, _amount: int):
        pass

    @eventlog(indexed=2)
    def Report(self, _day: int, _name: str, _dist: int, _value: int):
        pass

    @eventlog(indexed=2)
    def Diagnostic(self, _day: int, _name: str, _note: str):
        pass
