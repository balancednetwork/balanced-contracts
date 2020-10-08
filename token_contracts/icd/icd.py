from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable

TAG = 'ICD'

TOKEN_NAME = 'ICONDollar'
SYMBOL_NAME = 'ICD'
DEFAULT_PEG = 'USD'

class ICONDollar(IRC2Mintable, IRC2Burnable):

	_PEG = 'peg'

	def __init__(self, db: IconScoreDatabase) -> None:
		super().__init__(db)
		self._peg = VarDB(self._PEG, db, value_type=str)

	def on_install(self) -> None:
		super().on_install(TOKEN_NAME, SYMBOL_NAME)
		self._peg.set(DEFAULT_PEG)

	def on_update(self) -> None:
		super().on_update()

	@external(readonly=True)
	def get_peg(self) -> str:
		return self._peg.get()
