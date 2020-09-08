from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable

TAG = 'sICX'

TOKEN_NAME = 'StakedICX'
SYMBOL_NAME = 'sICX'
INITIAL_SUPPLY = 0
DECIMALS = 18

class StakedICX(IRC2Mintable, IRC2Burnable):

	def on_install(self) -> None:
		super().on_install(TOKEN_NAME, SYMBOL_NAME, INITIAL_SUPPLY, DECIMALS)
