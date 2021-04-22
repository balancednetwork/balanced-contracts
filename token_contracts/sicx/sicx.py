from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable
from .utils.checks import *
from .utils.consts import *

TAG = 'sICX'

TOKEN_NAME = 'Staked ICX'
SYMBOL_NAME = 'sICX'

class stakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self):
        pass


class StakedICX(IRC2Mintable, IRC2Burnable):

    _PEG = 'peg'
    _STAKING = 'staking'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._peg = VarDB(self._PEG, db, value_type=str)
        self._staking_address = VarDB(self._STAKING, db, value_type=Address)

    def on_install(self, _admin: Address) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)
        self._admin.set(_admin)
        self._staking_address.set(_admin)
        self._peg.set('sICX')

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def getPeg(self) -> str:
        return self._peg.get()

    @external
    @only_owner
    def setStakingAddress(self, _address: Address) -> None:
        self._staking_address.set(_address)

    @external(readonly=True)
    def getStakingAddress(self) -> Address:
        return self._staking_address.get()

    @external
    def priceInLoop(self) -> int:
        """
        Returns the price of sICX in loop.
        """
        staking_score = self.create_interface_score(self._staking_address.get(), stakingInterface)
        return staking_score.getTodayRate()

    @external(readonly=True)
    def lastPriceInLoop(self) -> int:
        """
        Returns the price of sICX in loop.
        """
        return self.priceInLoop()
