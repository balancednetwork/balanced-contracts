from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable
from .utils.checks import *

TAG = 'ICD'

MIN_UPDATE_TIME = 30000000 # 30 seconds

TOKEN_NAME = 'ICONDollar'
SYMBOL_NAME = 'ICD'
DEFAULT_PEG = 'USD'
BAND_PRICE_ORACLE_ADDRESS = 'cx61a36e5d10412e03c907a507d1e8c6c3856d9964'


# An interface to the Band Price Oracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class ICONDollar(IRC2Mintable, IRC2Burnable):

    _PEG = 'peg'
    _ORACLE = 'oracle'
    _PRICE_UPDATE_TIME = 'price_update_time'
    _LAST_PRICE = 'last_price'
    _MIN_INTERVAL = 'min_interval'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._peg = VarDB(self._PEG, db, value_type=str)
        self._oracle_address = VarDB(self._ORACLE, db, value_type=Address)
        self._price_update_time = VarDB(self._PRICE_UPDATE_TIME, db, value_type=int)
        self._last_price = VarDB(self._LAST_PRICE, db, value_type=int)
        self._min_interval = VarDB(self._MIN_INTERVAL, db, value_type=int)

    def on_install(self) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)
        self._peg.set(DEFAULT_PEG)
        self._oracle_address.set(Address.from_string(BAND_PRICE_ORACLE_ADDRESS))

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def get_peg(self) -> str:
        return self._peg.get()

    @external
    @only_owner
    def set_oracle_address(self, _address: Address) -> None:
        self._oracle_address.set(_address)

    @external(readonly=True)
    def get_oracle_address(self) -> Address:
        return self._oracle_address.get()

    @external
    @only_owner
    def set_min_interval(self, _interval: int) -> None:
        self._min_interval.set(_interval)

    @external
    def price_in_icx(self) -> int:
        """
        Returns the price of the asset in loop. Makes a call to the oracle if
        the last recorded price is not recent enough.
        """
        if self.now() - self._price_update_time.get() > MIN_UPDATE_TIME:
            self.update_asset_value()
        return self._last_price.get()

    def update_asset_value(self) -> None:
        """
        Calls the oracle method for the asset and updates the asset
        value in the _assets_ DictDB.
        """
        oracle = self.create_interface_score(self._oracle_address.get(), OracleInterface)
        priceData = oracle.get_reference_data(self._peg.get(), 'ICX')
        self._last_price.set(priceData['rate'])
        self._price_update_time.set(self.now())
