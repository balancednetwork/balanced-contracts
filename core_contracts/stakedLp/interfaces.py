from iconservice import *


class Status:
    STAKED = 1


class SupplyDetails(TypedDict):
    decimals: int
    principalUserBalance: int
    principalTotalSupply: int


class TotalStaked(TypedDict):
    decimals: int
    totalStaked: int


class AddressDetails(TypedDict):
    name: str
    address: Address

class RewardsDataEntry(TypedDict):
    _user: Address
    _balance: int

class AssetConfig(TypedDict):
    _id: int
    asset: Address
    distPercentage: int
    assetName: str
    rewardEntity: str


class RewardInterface(InterfaceScore):
    @interface
    def updateRewardsData(self, _name: str, _totalSupply: int, _user: Address, _balance: int) -> None:
        pass

    @interface
    def updateBatchRewardsData(self, _name: str, _totalSupply: int, _data: List[RewardsDataEntry]) -> None:
        pass


class LiquidityPoolInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address, _id: int) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _id: int, _data: bytes = None):
        pass

    @interface
    def getPoolStats(self, _id: int) -> dict:
        pass

    @interface
    def getPoolName(self, _id: int ) -> str:
        pass
