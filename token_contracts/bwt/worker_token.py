from iconservice import *
from .tokens.IRC2 import IRC2

TAG = 'BWT'

TOKEN_NAME = 'WorkerToken'
SYMBOL_NAME = 'BWT'
INITIAL_SUPPLY = 100
DECIMALS = 6

class WorkerToken(IRC2):

	_GOVERNANCE_ADDRESS = 'governance_address'

	def __init__(self, db: IconScoreDatabase) -> None:
		"""
		Varible Definition
		"""
		super().__init__(db)

		self._governance_address = VarDB(self._GOVERNANCE_ADDRESS, db, value_type=Address)

	def on_install(self) -> None:
		super().on_install(TOKEN_NAME, SYMBOL_NAME, INITIAL_SUPPLY, DECIMALS)

	def transfer(self, _from: Address, _to: Address) -> None:
		if self.msg.sender != self._governance_address.get():
			revert(f'BWT can only be transferred according to a vote, and '
					'called by the governance contract.')
		super().transfer(_from, _to)
