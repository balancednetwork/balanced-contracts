from iconservice import *

DATASOURCE_DB_PREFIX = b'datasource'

class DataSourceInterface(InterfaceScore):
    @interface
    def precompute(self) -> str:
        pass

    @interface
    def getTotalValue(self, snap: int) -> int:
        pass

    @interface
    def getDataBatch(self, snap: int) -> dict:
        pass


class DataSource(object):

    def __init__(self, db: IconScoreDatabase, rewards: IconScoreBase) -> None:
        self._rewards = rewards
        self.day = VarDB('day', db, int)
        self.precomp = VarDB('precomp', db, bool)
        self.total_value = VarDB('total_value', db, int)
        self.total_dist = VarDB('total_dist', db, int)
        self.contract_address = VarDB('contract_address', db, Address)
        self.bal_token_dist_percent = VarDB('bal_token_dist_percent', db, int)

    def _distribute(self) -> None:
        wallets = []
        data_source = self._rewards.create_interface_score(self.contract_address.get(), DataSourceInterface)
        if not self.precomp.get() and data_source.precompute(self.day.get()):
            self.precomp.set(True)
            self.total_value.set(data_source.getTotalValue(self.day.get()))

        if self.precomp.get():
            data_batch = data_source.getDataBatch(self.day.get())
            if not data_batch:
                self.day.set(self.day.get() + 1)
                self.total_dist.set(self.bal_token_dist_percent.get() * self._bal_token_dist_per_day(self.day.get()))
                return

            for data in data_batch:
                token_value = ( self.total_dist.get() * data_batch[data]) // self.total_value.get()
                self.total_dist.set(self.total_dist.get() - token_value)
                self.total_value.set(self.total_value.get()  - data_batch[data])
                self._rewards._token_holdings[data] = token_value

        
    def _bal_token_dist_per_day(self, _day: int) -> int:
        if _day < 60:
            return 10**23
        else:
            index = _day - 59
            return max(((995 ** index) * 10**23) // (1000 ** index), 1250 * 10**18)

class DataSourceDB:

    def __init__(self, db: IconScoreDatabase, rewards: IconScoreBase):
        self._db = db
        self._rewards = rewards
        self._items = {}

    def __getitem__(self, data_source_name: str) -> DataSource:
        prefix = b'|'.join([DATASOURCE_DB_PREFIX, str(data_source_name).encode()])
        if prefix not in self._items:
            sub_db = self._db.get_sub_db(prefix)
            self._items[prefix] = DataSource(sub_db, self._rewards)

        return self._items[prefix]

    def __setitem__(self, key, value):
        revert('illegal access')
          

def add_data_to_data_source(prefix: str, data_source: 'DataSourceDB', data_source_obj: 'DataSourceObject'):
    data_source[prefix].contract_address.set(data_source_obj.contract_address)
    data_source[prefix].bal_token_dist_percent.set(data_source_obj.bal_token_dist_percent)

def get_data_from_data_source(prefix: str, data_source: 'DataSourceDB') -> dict:
    day = data_source[prefix].day.get()
    contract_address = data_source[prefix].contract_address.get()
    bal_token_dist_percent = data_source[prefix].bal_token_dist_percent.get()

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


