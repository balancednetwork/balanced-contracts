from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable
from .utils.checks import *

TAG = 'ICD'

TOKEN_NAME = 'ICONDollar'
SYMBOL_NAME = 'ICD'
DEFAULT_PEG = 'USD'
DEFAULT_ORACLE_ADDRESS = 'cx61a36e5d10412e03c907a507d1e8c6c3856d9964'
DEFAULT_ORACLE_NAME = 'BandChain'
INITIAL_PRICE_ESTIMATE = 125 * 10**16
MIN_UPDATE_TIME = 30000000 # 30 seconds

# An interface to the Band Price Oracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class ICONDollar(IRC2Mintable, IRC2Burnable):

    _PEG = 'peg'
    _ORACLE_ADDRESS = 'oracle_address'
    _ORACLE_NAME = 'oracle_name'
    _PRICE_UPDATE_TIME = 'price_update_time'
    _LAST_PRICE = 'last_price'
    _MIN_INTERVAL = 'min_interval'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._peg = VarDB(self._PEG, db, value_type=str)
        self._oracle_address = VarDB(self._ORACLE_ADDRESS, db, value_type=Address)
        self._oracle_name = VarDB(self._ORACLE_NAME, db, value_type=str)
        self._price_update_time = VarDB(self._PRICE_UPDATE_TIME, db, value_type=int)
        self._last_price = VarDB(self._LAST_PRICE, db, value_type=int)
        self._min_interval = VarDB(self._MIN_INTERVAL, db, value_type=int)

    def on_install(self) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)
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
    def getOracle(self) -> dict:
        return {"name": self._oracle_name.get(), "address": str(self._oracle_address.get())}

    @external
    @only_owner
    def setMinInterval(self, _interval: int) -> None:
        self._min_interval.set(_interval)

    @external(readonly=True)
    def getMinInterval(self) -> int:
        return self._min_interval.get()

    @external(readonly=True)
    def getPriceUpdateTime(self) -> int:
        return self._price_update_time.get()

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

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        if self.msg.sender != self.address:
            revert(f'Only accepts ICD tokens.')

    # ------------------------------------------------------------------------------------------------------------------
    # EVENTS
    # ------------------------------------------------------------------------------------------------------------------

    @eventlog(indexed=3)
    def OraclePriceUpdateFailed(self, market: str, oracle_name: str, oracle_address: Address, msg: str):
        pass

    @eventlog(indexed=3)
    def OraclePrice(self, market: str, oracle_name: str, oracle_address: Address, price: int):
        pass
