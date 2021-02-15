from iconservice import *
from .utils.checks import *
from .utils.consts import *
from .RewardData import *

TAG = 'Rewards'


class DistPercentDict(TypedDict):
    recipient_name : str
    bal_token_dist_percent: int


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
        self._baln_address = VarDB('baln_address', db, value_type = Address)
        self._bwt_address = VarDB('bwt_address', db, value_type = Address)
        self._reserve_fund = VarDB('reserve_fund', db, value_type = Address)
        self._start_timestamp = VarDB('start_timestamp', db, value_type = int)
        self._batch_size = VarDB('batch_size', db, value_type = int)
        self._baln_holdings = DictDB('baln_holdings', db, value_type = int)
        self._recipient_split = DictDB('recipient_split', db, value_type = int)
        self._recipients = ArrayDB('recipients', db, value_type = str)
        self._platform_recipients = {'Worker Tokens': self._bwt_address,
                                     'Reserve Fund': self._reserve_fund}
        self._total_dist = VarDB('total_dist', db, int)
        self._platform_day = VarDB('platform_day', db, value_type = int)
        self._data_source_db = DataSourceDB(db,self)

    def on_install(self) -> None:
        super().on_install()
        self._platform_day.set(1)
        self._batch_size.set(DEFAULT_BATCH_SIZE)
        self._recipient_split['Worker Tokens'] = 0
        self._recipients.put('Worker Tokens')
        self._recipient_split['Reserve Fund'] = 0
        self._recipients.put('Reserve Fund')

    def on_update(self) -> None:
        super().on_update()

    @external(readonly = True)
    def name(self) -> str:
        return "Rewards"

    @external(readonly = True)
    def getBalnHoldings(self, _holders: List[Address]) -> dict:
        holdings = {}
        for holder in _holders:
            holdings[str(holder)] = self._baln_holdings[holder]
        return holdings

    @external(readonly = True)
    def distStatus(self) -> dict:
        status = {}
        status['platform_day'] = self._platform_day.get()
        status['source_days'] = {}
        for source in self._data_source_db._names:
            status['source_days'][source] = self._data_source_db[source].day.get()
        return status

    # Methods to update the states of a data_source_name object
    @external
    def updateBalTokenDistPercentage(self, _recipient_list : List[DistPercentDict]) -> None:
        """
        This method provides a means to adjust the allocation of rewards tokens.
        To maintain consistency a change to these percentages will only be
        accepted if they sum to 100%, with 100% represented by the value 10**18.

        :param _recipient_list: List of dicts containing the allocation spec.
        :type _recipient_list: List[TypedDict]
        """
        if len(_recipient_list) != len(self._recipients):
            revert(f"Recipient lists lengths mismatched!")
        total_percentage = 0
        for recipient in _recipient_list:
            self._recipient_split[recipient['recipient_name']] = recipient['bal_token_dist_percent']
            if recipient['recipient_name'] not in self._recipients:
                revert(f"Recipient {recipient['recipient_name']} doesn't exist")
            source = self._data_source_db[recipient['recipient_name']]
            if source.bal_token_dist_percent.get() == 0:
                source.day.set(self._get_day())
            source.bal_token_dist_percent.set(recipient['bal_token_dist_percent'])
            total_percentage += recipient['bal_token_dist_percent']

        if total_percentage != 10**18:
            revert(f"Total percentage doesn't sum up to 100")

    @external(readonly=True)
    def getDataSourceNames(self) -> list:
        """
        Returns a list of the data source names.

        :return: list of data source names
        :rtype list
        """
        data_source_names = []
        for data_source_name in self._data_source_db._names:
            data_source_names.append(data_source_name)
        return data_source_names

    @external(readonly=True)
    def getRecipients(self) -> list:
        """
        Returns a list of the rewards token recipients.

        :return: list of recipient names
        :rtype list
        """
        recipients = []
        for recipient in self._recipients:
            recipients.append(recipient)
        return recipients

    @external(readonly=True)
    def getRecipientsSplit(self) -> dict:
        """
        Returns a dict of the rewards token recipients.

        :return: dict of recipient {names: percent}
        :rtype dict
        """
        recipients = {}
        for recipient in self._recipients:
            recipients[recipient] = self._recipient_split[recipient]
        return recipients

    @external
    def addNewDataSource(self, _data_source_name: str, _contract_address: Address) -> None:
        """
        Sources for data on which to base incentive rewards are added with this
        method. Data source contracts must provide an API of precompute(),
        totalValue() and getDataBatch(). Newly added data sources will start
        with zero share (0%) of the rewards token distribution. The intention
        is to allow for the addition of new incentivized markets on the DEX.

        :param _data_source_name: Identifying name for the data source.
        :type _data_source_name: str
        :param _contract_address: Address of the data source.
        :type _contract_address: :class:`iconservice.base.address.Address`
        """
        data_source_dict = {'contract_address': _contract_address, 'bal_token_dist_percent': 0}
        data_source_obj = create_data_source_object(data_source_dict)
        if _data_source_name not in self._data_source_db._names and _data_source_name not in self._recipients:
            self._data_source_db._names.put(_data_source_name)
            self._recipients.put(_data_source_name)
            self._recipient_split[_data_source_name] = 0
        add_data_to_data_source(_data_source_name, self._data_source_db, data_source_obj)

    @external(readonly=True)
    def getDataSources(self, _data_source_name: str) -> dict:
        response = {}
        if _data_source_name in self._data_source_db._names:
            response = get_data_from_data_source(_data_source_name, self._data_source_db)
        return response

    def _reward_distribution(self, _data_source_name: str, _batch_size: int) -> None:
        self._data_source_db[_data_source_name]._distribute(_batch_size)

    @external
    def distribute(self) -> bool:
        if self._platform_day.get() < self._get_day():
            if self._total_dist.get() == 0:
                distribution = self._bal_token_dist_per_day(self._platform_day.get())
                baln_token = self.create_interface_score(self._baln_address.get(), TokenInterface)
                baln_token.mint(distribution)
                self._total_dist.set(distribution)
                shares = EXA
                remaining = distribution
                for name in self._recipients:
                    split = self._recipient_split[name]
                    share =  remaining * split // shares
                    if name in self._data_source_db._names:
                        self._data_source_db[name].total_dist[self._data_source_db[name].day.get()] = share
                    else:
                        baln_token.transfer(self._platform_recipients[name].get(), share)
                    remaining -= share
                    shares -= split
                self._total_dist.set(remaining) # remaining will be == 0 at this point.
                self._platform_day.set(self._platform_day.get() + 1)
                return False
        distribution_complete = True
        for name in self._data_source_db._names:
            data_source = self.getDataSources(name)
            if data_source['day'] < self._get_day():
                source = self._data_source_db[name]
                percent = source.dist_percent_dict
                if percent[data_source['day']] == 0:
                    percent[data_source['day']] = source.bal_token_dist_percent.get()
                self._reward_distribution(name, self._batch_size.get())
                distribution_complete = False
        return distribution_complete

    @external
    def claimRewards(self) -> None:
        if self._baln_holdings[self.msg.sender]:
            baln_token = self.create_interface_score(self._baln_address.get(), TokenInterface)
            baln_token.transfer(self.msg.sender, self._baln_holdings[self.msg.sender])
            self._baln_holdings[self.msg.sender] = 0

    def _get_day(self) -> int:
        today = (self.now() - self._start_timestamp.get()) // DAY_IN_MICROSECONDS
        return today

    def _bal_token_dist_per_day(self, _day: int) -> int:
        if _day <= 60:
            return 10**23
        else:
            index = _day - 60
            return max(((995 ** index) * 10**23) // (1000 ** index), 1250 * 10**18)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used to receive BALN tokens.

        :param _from: Token orgination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        if self.msg.sender != self._baln_address.get():
            revert(f'The Rewards SCORE can only accept BALN tokens. '
                   f'Deposit not accepted from {str(self.msg.sender)} '
                   f'Only accepted from BALN = {str(self._baln_address.get())}')


#-------------------------------------------------------------------------------
#   SETTERS AND GETTERS
#-------------------------------------------------------------------------------

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
    def setBaln(self, _address: Address) -> None:
        self._baln_address.set(_address)

    @external(readonly=True)
    def getBaln(self) -> Address:
        return self._baln_address.get()

    @external
    @only_admin
    def setBwt(self, _address: Address) -> None:
        self._bwt_address.set(_address)

    @external(readonly=True)
    def getBwt(self) -> Address:
        return self._bwt_address.get()

    @external
    @only_admin
    def setReserve(self, _address: Address) -> None:
        self._reserve_fund.set(_address)

    @external(readonly=True)
    def getReserve(self) -> Address:
        return self._reserve_fund.get()

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
