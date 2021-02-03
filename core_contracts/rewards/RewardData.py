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
    def getDataBatch(self, _name: str, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        pass


class DataSource(object):

    def __init__(self, db: IconScoreDatabase, rewards: IconScoreBase) -> None:
        self._rewards = rewards
        self.day = VarDB('day', db, int)
        self.name = VarDB('name', db, str)
        self.offset = VarDB('offset', db, int)
        self.precomp = VarDB('precomp', db, bool)
        self.total_value = VarDB('total_value', db, int)
        self.total_dist = VarDB('total_dist', db, int)
        self.contract_address = VarDB('contract_address', db, Address)
        self.bal_token_dist_percent = VarDB('bal_token_dist_percent', db, int)

    def _distribute(self, batch_size: int) -> None:
        """
        The calculation and distribution of rewards proceeds in two stages
        """
        wallets = []
        data_source = self._rewards.create_interface_score(self.contract_address.get(), DataSourceInterface)
        if not self.precomp.get() and data_source.precompute(self.day.get(), batch_size):
            self.precomp.set(True)
            self.total_value.set(data_source.getTotalValue(self.name.get(), self.day.get()))

        if self.precomp.get():
            data_batch = data_source.getDataBatch(self.name.get(), self.day.get(), self.offset.get(), batch_size)
            self.offset.set(self.offset.get() + batch_size)
            if not data_batch:
                self.day.set(self.day.get() + 1)
                self.offset.set(0)
                self.precomp.set(False)
                return
            remaining = self.total_dist.get() # Amount remaining of the allocation to this source
            shares = self.total_value.get() # The sum of all mining done by this data source
            for address in data_batch:
                token_share =  remaining * data_batch[address] // shares
                remaining -= token_share
                shares -= data_batch[address]
                self._rewards._token_holdings[address] += token_share
            self.total_dist.set(remaining)
            self.total_value.set(shares)


class DataSourceDB:
    """

    """
    def __init__(self, db: IconScoreDatabase, rewards: IconScoreBase):
        self._db = db
        self._rewards = rewards
        self._names = ArrayDB('names', db, value_type = str)
        self._items = {}

    def __getitem__(self, data_source_name: str) -> DataSource:
        prefix = b'|'.join([DATASOURCE_DB_PREFIX, str(data_source_name).encode()])
        if data_source_name not in self._items:
            sub_db = self._db.get_sub_db(prefix)
            self._items[data_source_name] = DataSource(sub_db, self._rewards)

        return self._items[data_source_name]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self) -> int:
        return len(self._names)

def add_data_to_data_source(name: str, data_source: 'DataSourceDB', data_source_obj: 'DataSourceObject'):
    data_source[name].contract_address.set(data_source_obj.contract_address)
    data_source[name].bal_token_dist_percent.set(data_source_obj.bal_token_dist_percent)
    data_source[name].name.set(name)

def get_data_from_data_source(name: str, data_source: 'DataSourceDB') -> dict:
    day = data_source[name].day.get()
    contract_address = data_source[name].contract_address.get()
    bal_token_dist_percent = data_source[name].bal_token_dist_percent.get()

    return {
        'day' : day,
        'contract_address' : contract_address,
        'bal_token_dist_percent' : bal_token_dist_percent
    }

def create_data_source_object(data_source_dict: dict) -> 'DataSourceObject':
    return DataSourceObject( contract_address = data_source_dict['contract_address'],
                             bal_token_dist_percent = data_source_dict['bal_token_dist_percent']
                            )


class DataSourceObject(object):

    def __init__(self, **kwargs) -> None:
        self.contract_address = kwargs.get('contract_address')
        self.bal_token_dist_percent = kwargs.get('bal_token_dist_percent')
