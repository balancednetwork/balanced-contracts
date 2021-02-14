from iconservice import *
from .utils.checks import *
from .utils.consts import *


# An interface to the Loans SCORE
class LoansInterface(InterfaceScore):
    @interface
    def setTimeOffset(self, _time_delta: int) -> None:
        pass

    @interface
    def turnLoansOn(self) -> None:
        pass

    @interface
    def addAsset(self, _token_address: Address,
                       _active: bool = True,
                       _collateral: bool = False) -> None:
        pass

    @interface
    def toggleAssetActive(self, _symbol) -> None:
        pass

    @interface
    def setAdmin(self, _address: Address) -> None:
        pass

    @interface
    def setRewards(self, _address: Address) -> None:
        pass

    @interface
    def setStaking(self, _address: Address) -> None:
        pass

    @interface
    def setDividends(self, _address: Address) -> None:
        pass

    @interface
    def setReserve(self, _address: Address) -> None:
        pass


# An interface to the Loans SCORE
class DexInterface(InterfaceScore):
    @interface
    def setTimeOffset(self, _time_delta: int) -> None:
        pass

    @interface
    def turnDexOn(self) -> None:
        pass

    @interface
    def setAdmin(self, _address: Address) -> None:
        pass

    @interface
    def setRewards(self, _address: Address) -> None:
        pass

    @interface
    def setStaking(self, _address: Address) -> None:
        pass

    @interface
    def setDividends(self, _address: Address) -> None:
        pass

    @interface
    def setSicx(self, _address: Address) -> None:
        pass

    @interface
    def setIcd(self, _address: Address) -> None:
        pass


# An interface to the Rewards SCORE
class RewardsInterface(InterfaceScore):
    @interface
    def setTimeOffset(self, _time_delta: int) -> None:
        pass

    @interface
    def setReserve(self, _address: Address) -> None:
        pass

    @interface
    def setBaln(self, _address: Address) -> None:
        pass

    @interface
    def setBwt(self, _address: Address) -> None:
        pass


# An interface to call the setAddress methods on each SCORE.
class SetAddressesInterface(InterfaceScore):

    @interface
    def setAdmin(self, _address: Address) -> None:
        pass

    @interface
    def setLoans(self, _address: Address) -> None:
        pass

    @interface
    def setDex(self, _address: Address) -> None:
        pass

    @interface
    def setRewards(self, _address: Address) -> None:
        pass

    @interface
    def setStaking(self, _address: Address) -> None:
        pass

    @interface
    def setDividends(self, _address: Address) -> None:
        pass

    @interface
    def setReserve(self, _address: Address) -> None:
        pass

    @interface
    def setOracle(self, _address: Address) -> None:
        pass

    @interface
    def setSicx(self, _address: Address) -> None:
        pass

    @interface
    def setIcd(self, _address: Address) -> None:
        pass

    @interface
    def setBaln(self, _address: Address) -> None:
        pass

    @interface
    def setBwt(self, _address: Address) -> None:
        pass
