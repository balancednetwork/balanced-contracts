from iconservice import *
from .RewardData import *

TAG = 'Rewards'

DAY_IN_MICROSECONDS = 86400 * 10**6

class DistPercentDict(TypedDict):
    data_source_name : str
    bal_token_dist_percent: int

class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass
   
class Rewards(IconScoreBase):
    
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._start_timestamp = VarDB('start_timestamp', db, value_type = int)
        self._batch_size = VarDB('batch_size', db, value_type = int)
        self._token_holdings = DictDB('token_holdings', db, value_type = int)
        self._token_address = DictDB('token_address', db, value_type = Address)
        self._data_source_names = ArrayDB('data_source_names', db, value_type = str)
        self._data_source_db = DataSourceDB(db,self)

    def on_install(self) -> None:
        super().on_install()
        
    def on_update(self) -> None:
        super().on_update()

    @external(readonly = True)
    def name(self) -> str:
        return "Rewards"

    @external
    def setTokenAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f"Only owner can set the token address")
        self._token_address.set(_address)

    @external(readonly = True)
    def getTokenAddress() -> Address:
        self._token_address.get()

    @external
    def setBatchSize(self, _batch_size: int) -> None:
        if self.msg.sender != self.owner:
            revert(f"Only owner can set the token address")
        self._batch_size.set(_batch_size)

    @external(readonly = True)
    def getBatchSize() -> int:
        self._batch_size.get()

    @external
    def setStartTimestamp(self, _timestamp: int) -> None:
        if self.msg.sender != self.owner:
            revert(f"Only owner can set the token address")
        self._start_timestamp.set(_timestamp)

    @external(readonly = True)
    def getStartTimestamp() -> int:
        self._start_timestamp.get()
    
    # Methods to update the states of a data_source_name object
    @external
    def updateBalTokenDistPercentage(self, _data_source_dict_list : List[DistPercentDict]):
        if len(_data_source_dict_list) != len(self._data_source_names):
            revert(f"Data sources length mismatched!")
        total_percentage = 0
        for data_source_dict in _data_source_dict_list:
            if data_source_dict['data_source_name'] not in self._data_source_names:
                revert(f"Data source {data_source_dict['data_source_name']} doesn't exists")
            self._data_source_db[data_source_dict['data_source_name']].bal_token_dist_percent.set(data_source_dict['bal_token_dist_percent'])
            total_percentage += data_source_dict['bal_token_dist_percent'] 

        if total_percentage != 10**18:
            revert(f"Total percentage doesn't sum upto 100")
    
    @external(readonly=True)
    def getDataSourceNames(self) -> list:
        data_source_names = []
        for data_source_name in self._data_source_names:
            data_source_names.append(data_source_name)
        return data_source_names

    @external
    def addNewDataSource(self, _data_source_name: str, _contract_address: Address):
        data_source_dict = {'contract_address': _contract_address, 'bal_token_dist_percent': 0}
        data_source_obj = create_data_source_object(data_source_dict)
        if _data_source_name not in self._data_source_names:
            self._data_source_names.put(_data_source_name)
        add_data_to_data_source(_data_source_name, self._data_source_db, data_source_obj)

    @external(readonly = True)
    def getDataSources(self, _data_source_name: str) -> dict:
        response = {}
        if _data_source_name in self._data_source_names:
            response = get_data_from_data_source(_data_source_name, self._data_source_db)
        return response

    def _reward_distribution(self, _data_source_name: str, _batch_size: int) -> None:
        self._data_source_db[_data_source_name]._distribute(_batch_size)

    @external
    def distribute(self) -> bool:
        distribution_complete = True
        for data_source_name in self._data_source_names:
            data_source = self.get_data_sources(data_source_name)
            if data_source[day] < self._get_day():
                self._reward_distribution(data_source_name, self._batch_size.get())
                distribution_complete = False
        return distribution_complete
                
        
    @external
    def claimRewards(self) -> None:
        if self._token_holdings[self.msg.sender]:
            token_contract = self.create_interface_score(self._token_address.get(), TokenInterface)
            token_contract.transfer(self.msg.sender, self._token_holdings[self.msg.sender])

    def _get_day(self) -> int:
        today = (self.now() - self._start_timestamp.get()) // DAY_IN_MICROSECONDS 
        return today 
    
            


    

    