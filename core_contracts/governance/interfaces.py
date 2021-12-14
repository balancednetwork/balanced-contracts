from iconservice import *


# TypedDict for disbursement specs
class Disbursement(TypedDict):
    address: Address
    amount: int
    symbol: str


class PrepDelegations(TypedDict):
    _address: Address
    _votes_in_per: int


class DistPercentDict(TypedDict):
    recipient_name: str
    dist_percent: int


# An interface to the Staking Management SCORE
class StakingInterface(InterfaceScore):
    @interface
    def stakeICX(self) -> None:
        pass


class RebalancingInterface(InterfaceScore):
    @interface
    def setPriceDiffThreshold(self, _value: int) -> None:
        pass

    @interface
    def setDex(self, _address: Address) -> None:
        pass

    @interface
    def setLoans(self, _address: Address) -> None:
        pass

    @interface
    def setSicx(self, _address: Address) -> None:
        pass

    @interface
    def setBnusd(self, _address: Address) -> None:
        pass


# An interface to the feeHandler SCORE
class feeHandlerInterface(InterfaceScore):
    @interface
    def setAcceptedDividendTokens(self, _tokens: List[Address]) -> None:
        pass

    @interface
    def setRoute(self, _fromToken: Address, _toToken: Address, _path: List[Address]) -> None:
        pass

    @interface
    def deleteRoute(self, _fromToken: Address, _toToken: Address) -> None:
        pass

    @interface
    def setFeeProcessingInterval(self, _interval: int) -> None:
        pass


# An interface to the Loans SCORE
class LoansInterface(InterfaceScore):
    @interface
    def depositAndBorrow(self, _asset: str = '', _amount: int = 0,
                         _from: Address = None, _value: int = 0) -> None:
        pass

    @interface
    def setRebalance(self, _address: Address):
        pass

    @interface
    def setDex(self, _address: Address):
        pass

    @interface
    def setTimeOffset(self, _time_delta: int) -> None:
        pass

    @interface
    def turnLoansOn(self) -> None:
        pass

    @interface
    def toggleLoansOn(self) -> None:
        pass

    @interface
    def addAsset(self, _token_address: Address,
                 _active: bool = True,
                 _collateral: bool = False) -> None:
        pass

    @interface
    def getAssetTokens(self) -> dict:
        pass

    @interface
    def toggleAssetActive(self, _symbol: str) -> None:
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

    @interface
    def delegate(self, _user_delegations: List[PrepDelegations]) -> None:
        pass

    @interface
    def setRedemptionFee(self, _fee: int) -> None:
        pass

    @interface
    def setMaxRetirePercent(self, _value: int) -> None:
        pass

    @interface
    def setRedeemBatchSize(self, _value: int) -> None:
        pass

    @interface
    def setMiningRatio(self, _value: int) -> None:
        pass

    @interface
    def setLockingRatio(self, _value: int) -> None:
        pass

    @interface
    def setOriginationFee(self, _fee: int) -> None:
        pass

    @interface
    def setLiquidationRatio(self, _ratio: int) -> None:
        pass

    @interface
    def setRetirementBonus(self, _points: int):
        pass

    @interface
    def setLiquidationReward(self, _points: int):
        pass

    @interface
    def setMaxSellAmount(self, _sicx_value: int, _bnusd_value: int) -> None:
        pass


# An interface to the Loans SCORE
class DexInterface(InterfaceScore):
    @interface
    def add(self, _baseToken: Address, _quoteToken: Address, _baseValue: int, _quoteValue: int,
            _withdraw_unused: bool = True):
        pass

    @interface
    def setPoolLpFee(self, _value: int) -> None:
        pass

    @interface
    def setPoolBalnFee(self, _value: int) -> None:
        pass

    @interface
    def setIcxBalnFee(self, _value: int) -> None:
        pass

    @interface
    def setIcxConversionFee(self, _value: int) -> None:
        pass

    @interface
    def setTimeOffset(self, _time_delta: int) -> None:
        pass

    @interface
    def turnDexOn(self) -> None:
        pass

    @interface
    def permit(self, _id: int, _permission: bool):
        pass

    @interface
    def setMarketName(self, _id: int, _name: str) -> None:
        pass

    @interface
    def getPoolId(self, _token1Address: Address, _token2Address: Address) -> int:
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
    def setbnUSD(self, _address: Address) -> None:
        pass

    @interface
    def setBaln(self, _address: Address) -> None:
        pass

    @interface
    def addQuoteCoin(self, _address: Address) -> None:
        pass

    @interface
    def addLpAddresses(self, _poolId: int, _addresses: List[Address]) -> None:
        pass

    @interface
    def balanceOfAt(self, _account: Address, _id: int, _snapshot_id: int, _twa: bool = False) -> int:
        pass

    @interface
    def totalSupplyAt(self, _id: int, _snapshot_id: int, _twa: bool = False) -> int:
        pass

    @interface
    def totalBalnAt(self, _id: int, _snapshot_id: int, _twa: bool = False) -> int:
        pass


# An interface to the Rewards SCORE
class RewardsInterface(InterfaceScore):
    @interface
    def claimRewards(self) -> None:
        pass

    @interface
    def setDay(self, _day: int) -> None:
        pass

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

    @interface
    def addNewDataSource(self, _data_source_name: str, _contract_address: Address) -> None:
        pass

    @interface
    def removeDataSource(self, _name: str) -> None:
        pass

    @interface
    def updateBalTokenDistPercentage(self, _recipient_list: List[DistPercentDict]) -> None:
        pass

    @interface
    def bonusDist(self, _addresses: List[Address], _amounts: List[int]) -> None:
        pass


# An interface to the Dividends SCORE.
class DividendsInterface(InterfaceScore):

    @interface
    def setDistributionActivationStatus(self, _status: bool) -> None:
        pass

    def setDividendsCategoryPercentage(self, _dist_list: List[DistPercentDict]) -> None:
        pass

    @interface
    def addAcceptedTokens(self, _token: Address) -> None:
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
    def setDaofund(self, _address: Address) -> None:
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
    def setbnUSD(self, _address: Address) -> None:
        pass

    @interface
    def setBaln(self, _address: Address) -> None:
        pass

    @interface
    def setBwt(self, _address: Address) -> None:
        pass

    @interface
    def setRouter(self, _address: Address) -> None:
        pass

    @interface
    def setRebalancing(self, _address: Address) -> None:
        pass

    @interface
    def setFeehandler(self, _address: Address) -> None:
        pass

    @interface
    def setStabilityfund(self, _address: Address) -> None:
        pass


class BalancedInterface(InterfaceScore):

    @interface
    def totalSupply(self) -> int:
        pass

    @interface
    def totalStakedBalance(self) -> int:
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def stakedBalanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def stakedBalanceOfAt(self, _account: Address, _day: int) -> int:
        pass

    @interface
    def totalStakedBalanceOfAt(self, _day: int) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def setbnUSD(self, _address: Address) -> None:
        pass

    @interface
    def setDividends(self, _score: Address) -> None:
        pass

    @interface
    def setDex(self, _address: Address) -> None:
        pass

    @interface
    def setOracle(self, _address: Address) -> None:
        pass

    @interface
    def setOracleName(self, _name: str) -> None:
        pass

    @interface
    def toggleStakingEnabled(self) -> None:
        pass

    @interface
    def setMinimumStake(self, _amount: int) -> None:
        pass

    @interface
    def setUnstakingPeriod(self, _time: int) -> None:
        pass

    @interface
    def setMinInterval(self, _interval: int) -> None:
        pass


class DAOfundInterface(InterfaceScore):

    @interface
    def disburse(self, _recipient: Address, _amounts: List[Disbursement]) -> bool:
        pass


class AssetInterface(InterfaceScore):

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def setOracleName(self, _name: str) -> None:
        pass

    @interface
    def setOracle(self, _address: Address) -> None:
        pass

    @interface
    def setMinInterval(self, _interval: int) -> None:
        pass

    @interface
    def setAdmin(self, _admin: Address) -> None:
        pass

    @interface
    def priceInLoop(self) -> int:
        pass


class BalancedWorkerTokenInterface(InterfaceScore):

    @interface
    def adminTransfer(self, _from: Address, _to: Address, _value: int, _data: bytes = None):
        pass


class BnUSDInterface(InterfaceScore):

    @interface
    def govTransfer(self, _from: Address, _to: Address, _value: int, _data: bytes = b'None') -> None:
        pass


# An interface to the Router SCORE
class RouterInterface(InterfaceScore):
    @interface
    def setDex(self, _address: Address):
        pass

    @interface
    def setAdmin(self, _address: Address) -> None:
        pass

    @interface
    def setStaking(self, _address: Address) -> None:
        pass

    @interface
    def setSicx(self, _address: Address) -> None:
        pass


class FeeHandlerInterface(InterfaceScore):
    @interface
    def enable(self):
        pass

    @interface
    def disable(self) -> None:
        pass
