from iconservice import *
from .tokens.IRC2 import IRC2
from .utils.checks import *

TAG = 'BWT'

TOKEN_NAME = 'BalancedWorkerToken'
SYMBOL_NAME = 'BWT'
INITIAL_SUPPLY = 100
DECIMALS = 6


class WorkerToken(IRC2):

    _GOVERNANCE = 'governance'
    _BALN_TOKEN = 'baln_token'
    _BALN = 'baln'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)
        self._baln_token = VarDB(self._BALN_TOKEN, db, value_type=Address)
        self._baln = VarDB(self._BALN, db, value_type=int)

    def on_install(self, _governance: Address) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME, INITIAL_SUPPLY, DECIMALS)
        self._governance.set(_governance)

    def on_update(self) -> None:
        super().on_update()

    @external
    @only_owner
    def setGovernance(self, _address: Address) -> None:
        self._governance.set(_address)

    @external(readonly=True)
    def getGovernance(self) -> Address:
        return self._governance.get()

    @external
    @only_governance
    def setAdmin(self, _admin: Address) -> None:
        """
        Sets the authorized address.

        :param _admin: The authorized admin address.
        """
        return self._admin.set(_admin)

    @external
    @only_admin
    def setBaln(self, _address: Address) -> None:
        self._baln_token.set(_address)

    @external(readonly=True)
    def getBaln(self) -> Address:
        return self._baln_token.get()

    @external
    @only_admin
    def admin_transfer(self, _from: Address, _to: Address, _value: int, _data: bytes = None):
        if _data is None:
            _data = b'None'
        super()._transfer(_from, _to, _value, _data)

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
