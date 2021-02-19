from iconservice import *
from .utils.checks import *
from .utils.consts import *
from .scorelib import *

TAG = 'Governance'

# An interface to the Loans SCORE
class LoansInterface(InterfaceScore):
    @interface
    def setTimeOffset(self, _time_delta: int) -> None:
        pass

    @interface
    def turnLoansOn(self) -> None:
        pass


class Governance(IconScoreBase):
    """
    The Governance SCORE will have control of all parameters in BalancedDAO.
    All other SCOREs and external queries will be able to get SCORE addresses
    and parameter values here.
    """

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._launch_day = VarDB('launch_day', db, int)
        self._launched = VarDB('launched', db, bool)
        self._loans_score = VarDB('loans', db, Address)

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
            loans = self.create_interface_score(self._loans_score.get(), LoansInterface)
            self.set_launch_day(0)
            self.set_launch_day(self.getDay())
            time_delta = DAY_START + U_SECONDS_DAY * (DAY_ZERO + self._launch_day.get())
            loans.setTimeOffset(time_delta)
            loans.turnLoansOn()

    @external
    @only_owner
    def setLoansScore(self, _address: Address) -> None:
        self._loans_score.set(_address)

    @external(readonly=True)
    def getLoansScore(self) -> Address:
        self._loans_score.get()

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
# EVENT LOGS
#-------------------------------------------------------------------------------
