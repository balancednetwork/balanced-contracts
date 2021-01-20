from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable
from .utils.checks import *

TAG = 'BALN'

MIN_UPDATE_TIME = 20000000 # 2 seconds

TOKEN_NAME = 'BalanceToken'
SYMBOL_NAME = 'BALN'

# An interface to the Balanced DEX
class DEXInterface(InterfaceScore):
	@interface
	def get_price_data(self, _base: str, _quote: str) -> dict:
		pass


class BalanceToken(IRC2Mintable, IRC2Burnable):

	_DEX_ADDRESS = 'DEX_address'
	_PRICE_UPDATE_TIME = 'price_update_time'
	_LAST_PRICE = 'last_price'
	_MIN_INTERVAL = 'min_interval'

	def __init__(self, db: IconScoreDatabase) -> None:
		super().__init__(db)
		self._DEX_address = VarDB(self._DEX_ADDRESS, db, value_type=Address)
		self._price_update_time = VarDB(self._PRICE_UPDATE_TIME, db, value_type=int)
		self._last_price = VarDB(self._LAST_PRICE, db, value_type=int)
		self._min_interval = VarDB(self._MIN_INTERVAL, db, value_type=int)

	def on_install(self) -> None:
		super().on_install(TOKEN_NAME, SYMBOL_NAME)
		self._last_price.set(10**17)

	def on_update(self) -> None:
		super().on_update()

	@external
	@only_owner
	def set_DEX_address(self, _address: Address) -> None:
		self._DEX_address.set(_address)

	@external(readonly=True)
	def get_DEX_address(self) -> Address:
		return self._DEX_address.get()

	@external
	@only_owner
	def set_min_interval(self, _interval: int) -> None:
		self._min_interval.set(_interval)

	@external
	def priceInLoop(self) -> int:
		"""
		Returns the price of the asset in loop. Makes a call to the DEX if
		the last recorded price is not recent enough.
		"""
		# if self.now() - self._price_update_time.get() > MIN_UPDATE_TIME:
		# 	self.update_asset_value()
		return self._last_price.get()

	@external(readonly=True)
	def lastPriceInLoop(self) -> int:
		"""
		Returns the latest price of the asset in loop.
		"""
		return self._last_price.get()

	def update_asset_value(self) -> None:
		"""
		Updates the last price of BALN in loop.
		"""
		dex = self.create_interface_score(self._DEX_address.get(), DEXInterface)
		priceData = dex.get_price_data('BALN', 'ICD')
		self._last_price.set(priceData['rate'])
		self._price_update_time.set(self.now())
		self.DEXPrice("BALNICD", priceData['rate'], self.now())

	# --------------------------------------------------------------------------
	# EVENTS
	# --------------------------------------------------------------------------

	@eventlog(indexed=3)
	def DEXPrice(self, market: str, price: int, time: int):
		pass
