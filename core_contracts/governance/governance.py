from iconservice import *
from .utils.checks import *
from .utils.consts import *
from .scorelib import *
from .data_objects import *

TAG = 'Governance'


class BalancedAddresses(TypedDict):
    loans: Address
    dex: Address
    staking: Address
    rewards: Address
    reserve_fund: Address
    dividends: Address
    oracle: Address
    sicx: Address
    icd: Address
    baln: Address
    bwt: Address


class Governance(IconScoreBase):
    """
    The Governance SCORE will have control of all parameters in BalancedDAO.
    All other SCOREs and external queries will be able to get SCORE addresses
    and parameter values here.
    """

    _ADMIN = 'admin'
    _LAUNCH_DAY = 'launch_day'
    _LAUNCHED = 'launched'


    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self.addresses = Addresses(db)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._launch_day = VarDB('launch_day', db, int)
        self._launched = VarDB('launched', db, bool)

    def on_install(self) -> None:
        super().on_install()
        self._launched.set(False)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Governance"

    @external
    @only_owner
    def launchBalanced(self) -> None:
        if not self._launched.get():
            loans = self.create_interface_score(self.addresses._loans.get(), LoansInterface)
            dex = self.create_interface_score(self.addresses._dex.get(), LoansInterface)
            rewards = self.create_interface_score(self.addresses._rewards.get(), LoansInterface)
            self.set_launch_day(0)
            self.set_launch_day(self.getDay())
            time_delta = DAY_START + U_SECONDS_DAY * (DAY_ZERO + self._launch_day.get())
            loans.setTimeOffset(time_delta)
            loans.turnLoansOn()
            # dex.setTimeOffset(time_delta)
            # dex.turnDexOn()
            rewards.setTimeOffset(time_delta)

    @external
    @only_owner
    def setAddresses(self, _addresses: BalancedAddresses) -> None:
        self.addresses.setAddresses(_addresses)

    @external(readonly=True)
    def getAddresses(self) -> dict:
        self.addresses.getAddresses()

    @external
    @only_owner
    def toggleBalancedOn(self) -> None:
        loans = self.create_interface_score(self._loans_score.get(), LoansInterface)
        loans.toggleLoansOn()

    def set_launch_day(self, _day: int) -> None:
        self._launch_day.set(_day)

    @external(readonly=True)
    def getLaunchDay(self) -> int:
        self._launch_day.get()

    @external
    def getDay(self) -> int:
        offset = DAY_ZERO + self._launch_day.get()
        return (self.now() - DAY_START) // U_SECONDS_DAY - offset

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used only to receive sICX for unstaking.
        :param _from: Token orgination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        revert("The Balanced Governance SCORE does not accept tokens.")

    @payable
    def fallback(self):
        pass


#-------------------------------------------------------------------------------
# Interfaces
#-------------------------------------------------------------------------------

# An interface to the Loans SCORE
class LoansInterface(InterfaceScore):
    @interface
    def setTimeOffset(self, _time_delta: int) -> None:
        pass

    @interface
    def turnLoansOn(self) -> None:
        pass


# An interface to the Loans SCORE
class DexInterface(InterfaceScore):
    @interface
    def setTimeOffset(self, _time_delta: int) -> None:
        pass

    @interface
    def turnDexOn(self) -> None:
        pass


# An interface to the Loans SCORE
class RewardsInterface(InterfaceScore):
    @interface
    def setTimeOffset(self, _time_delta: int) -> None:
        pass



#-------------------------------------------------------------------------------
# EVENT LOGS
#-------------------------------------------------------------------------------
