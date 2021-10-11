from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable
from .utils.checks import *

TAG = 'bnXLM'

TOKEN_NAME = 'Balanced Lumens'
SYMBOL_NAME = 'bnXLM'
DEFAULT_PEG = 'XLM'
EXA = 10 ** 18


class BalancedLumens(IRC2Mintable, IRC2Burnable):
    _PEG = 'peg'
    _GOVERNANCE = 'governance'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._peg = VarDB(self._PEG, db, value_type=str)
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)

    def on_install(self, _governance: Address) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)
        self._governance.set(_governance)
        self._peg.set(DEFAULT_PEG)

    def on_update(self) -> None:
        super().on_update()

        _ORACLE_ADDRESS = 'oracle_address'
        _ORACLE_NAME = 'oracle_name'
        _PRICE_UPDATE_TIME = 'price_update_time'
        _LAST_PRICE = 'last_price'
        _MIN_INTERVAL = 'min_interval'
        VarDB(_ORACLE_ADDRESS, self.db, value_type=Address).remove()
        VarDB(_ORACLE_NAME, self.db, value_type=str).remove()
        VarDB(_PRICE_UPDATE_TIME, self.db, value_type=int).remove()
        VarDB(_LAST_PRICE, self.db, value_type=int).remove()
        VarDB(_MIN_INTERVAL, self.db, value_type=int).remove()

    @external(readonly=True)
    def getPeg(self) -> str:
        return self._peg.get()

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
