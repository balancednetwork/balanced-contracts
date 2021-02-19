from iconservice import *
from .tokens.IRC2 import IRC2
from .utils.checks import *

TAG = 'BWT'

TOKEN_NAME = 'WorkerToken'
SYMBOL_NAME = 'BWT'
INITIAL_SUPPLY = 100
DECIMALS = 6

class WorkerToken(IRC2):

    _GOVERNANCE_ADDRESS = 'governance_address'
    _BALN_TOKEN = 'baln_token'
    _BALN = 'baln'

    def __init__(self, db: IconScoreDatabase) -> None:
        """
        Varible Definition
        """
        super().__init__(db)

        self._governance_address = VarDB(self._GOVERNANCE_ADDRESS, db, value_type=Address)
        self._baln_token = VarDB(self._BALN_TOKEN, db, value_type=Address)
        self._baln = VarDB(self._BALN, db, value_type=int)

    def on_install(self) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME, INITIAL_SUPPLY, DECIMALS)

    @external
    @only_owner
    def setBalnToken(self, _address: Address) -> None:
        self._baln_token.set(_address)

    @external(readonly=True)
    def getBalnToken(self) -> Address:
        self._baln_token.get()

    @external
    def transfer(self, _from: Address, _to: Address, _value: int) -> None:
        if self.msg.sender != self._governance_address.get():
            revert(f'BWT can only be transferred according to a vote, and '
                    'called by the governance contract.')
        super()._transfer(_from, _to, _value, b'None')

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used to receive BALN tokens.

        :param _from: Token orgination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        if self.msg.sender == self._baln_token.get():
            self._baln.set(self._baln.get() + _value)
        else:
            revert(f'The Worker Token contract can only accept BALN tokens. '
                   f'Deposit not accepted from {str(self.msg.sender)} '
                   f'Only accepted from BALN = {str(self._baln_token.get())}')
