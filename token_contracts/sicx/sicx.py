from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable
from .utils.checks import *
from .utils.consts import *

TAG = 'sICX'

TOKEN_NAME = 'StakedICX'
SYMBOL_NAME = 'sICX'

class StakedICX(IRC2Mintable, IRC2Burnable):

	_PEG = 'peg'
	_STAKING = 'staking'

	def __init__(self, db: IconScoreDatabase) -> None:
		super().__init__(db)
		self._peg = VarDB(self._PEG, db, value_type=str)
		self._staking_address = VarDB(self._STAKING, db, value_type=Address)

	def on_install(self) -> None:
		super().on_install(TOKEN_NAME, SYMBOL_NAME)
		self._peg.set('sICX')

	def on_update(self) -> None:
		super().on_update()

	@external(readonly=True)
	def get_peg(self) -> str:
		return self._peg.get()

	@external
	@only_owner
	def set_staking_address(self, _address: Address) -> None:
		self._staking_address.set(_address)

	@external(readonly=True)
	def get_staking_address(self) -> Address:
		return self._staking_address.get()

	@external
	def price_in_icx(self) -> int:
		"""
		Returns the price of sICX in loop.
		"""
		pool = self.icx.get_balance(self._staking_address.get())
		rate = EXA * pool // self._total_supply.get()
		return rate
