from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable

TAG = 'BAL'

TOKEN_NAME = 'BalanceToken'
SYMBOL_NAME = 'BAL'
INITIAL_SUPPLY = 0
DECIMALS = 18

class BalanceToken(IRC2Mintable, IRC2Burnable):

	def on_install(self) -> None:
		super().on_install(TOKEN_NAME, SYMBOL_NAME, INITIAL_SUPPLY, DECIMALS)
