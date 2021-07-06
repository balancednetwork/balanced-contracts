from iconservice import *
from .utils.checks import *

TAG = 'Rebalancing'

POINTS = 10000
# bnUSD token address in toToken
data = {"method": "_swap", "params": {"toToken": "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"}}
data_string = json_dumps(data)
data_bytes = str.encode(data_string)

# sICX token address in toToken
data_sicx = {"method": "_swap", "params": {"toToken": "cx2609b924e33ef00b648a409245c7ea394c467824"}}
data_string_sicx= json_dumps(data)
data_bytes_sicx = str.encode(data_string)

class sICXTokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def priceInLoop(self) -> int:
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass


class bnUSDTokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def lastPriceInLoop(self) -> int:
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass


class loansTokenInterface(InterfaceScore):
    @interface
    def getMaxRetireAmount(self, _symbol: str) -> int:
        pass

    @interface
    def retireRedeem(self, _symbol: str, _redeemed: int, _sicx_from_lenders: int) -> None:
        pass

    @interface
    def getParameters(self) -> dict:
        pass


class oracleTokenInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class dexTokenInterface(InterfaceScore):
    @interface
    def getPriceByName(self, _name: str) -> int:
        pass

    @interface
    def getPoolStats(self, _id: int) -> dict:
        pass


class Rebalancing(IconScoreBase):
    _bnUSD_ADDRESS = 'bnUSD_address'
    _SICX_ADDRESS = 'sicx_address'
    _DEX_ADDRESS = 'dex_address'
    _LOANS_ADDRESS = 'loans_address'
    _ORACLE_ADDRESS = 'oracle_address'
    _GOVERNANCE_ADDRESS = 'governance_address'
    _SICX_RECEIVABLE = 'sicx_receivable'
    _BNUSD_RECEIVABLE = 'bnusd_receivable'
    _ADMIN = 'admin'
    _PRICE_THRESHOLD = '_price_threshold'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._bnUSD = VarDB(self._bnUSD_ADDRESS, db, value_type=Address)
        self._sicx = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._dex = VarDB(self._DEX_ADDRESS, db, value_type=Address)
        self._loans = VarDB(self._LOANS_ADDRESS, db, value_type=Address)
        self._oracle = VarDB(self._ORACLE_ADDRESS, db, value_type=Address)
        self._governance = VarDB(self._GOVERNANCE_ADDRESS, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._sicx_receivable = VarDB(self._SICX_RECEIVABLE, db, value_type=int)
        self._bnusd_receivable = VarDB(self._BNUSD_RECEIVABLE, db, value_type=int)
        self._price_threshold = VarDB(self._PRICE_THRESHOLD, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._admin.set(self.msg.sender)

    def on_update(self) -> None:
        super().on_update()

    @external
    @only_admin
    def setbnUSD(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new bnUSD contract address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._bnUSD.set(_address)

    @external
    @only_admin
    def setLoans(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new bnUSD contract address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._loans.set(_address)

    @external
    @only_admin
    def setSicx(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new SICX address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._sicx.set(_address)

    @external
    @only_admin
    def setGovernance(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new SICX address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._governance.set(_address)

    @external
    @only_admin
    def setOracle(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new Oracle address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._oracle.set(_address)

    @external
    @only_admin
    def setDex(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new DEX address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._dex.set(_address)

    def _sqrt(self, x: int) -> int:
        """
        Babylonian Square root implementation
        """
        z = (x + 1) // 2
        y = x

        while z < y:
            y = z
            z = ((x // z) + z) // 2

        return y

    def _calculate_sicx_to_retire(self, dex_score: dexTokenInterface, flag: int) -> int:
        """
        :param dex_score: Interface of dex score.
        Returns the amount of sICX required for rebalancing the price.
        """
        oracle_score = self.create_interface_score(self._oracle.get(), oracleTokenInterface)
        oracle_price = oracle_score.get_reference_data("USD", "ICX")
        oracle_rate = oracle_price["rate"]
        pool_stats = dex_score.getPoolStats(2)
        sicx_supply = pool_stats['base']
        bnusd_supply = pool_stats['quote']
        value = (self._sqrt(oracle_rate * sicx_supply * bnusd_supply) // 10 ** 9) - sicx_supply
        if flag == 1:
            value = (self._sqrt(oracle_rate * sicx_supply * bnusd_supply) // 10 ** 9) - bnusd_supply
        return value


    @external
    @only_governance
    def setPriceChangeThreshold(self, _value: int) -> None:
        """
        :param _value: threshold to set.
        Sets the threshold .
        """
        self._price_threshold.set(_value)

    @external(readonly=True)
    def getPriceChangeThreshold(self) -> int:
        """
        Returns the threshold value set by Governance contract.
        """
        return self._price_threshold.get()

    @external
    @only_governance
    def setSicxReceivable(self, _value: int) -> None:
        """
        :param _value: sICX amount to set.
        Sets the sICX amount to receive by rebalancing contract.
        """
        self._sicx_receivable.set(_value)

    @external
    @only_governance
    def setBnusdReceivable(self, _value: int) -> None:
        """
        :param _value: sICX amount to set.
        Sets the bnUSD amount to receive by rebalancing contract.
        """
        self._bnusd_receivable.set(_value)

    @external(readonly=True)
    def getSicxReceivable(self) -> int:
        """
        Returns the sICX amount to receive by rebalancing contract.
        """
        return self._sicx_receivable.get()

    @external(readonly=True)
    def getBnusdReceivable(self) -> int:
        """
        Returns the bnUSD amount to receive by rebalancing contract.
        """
        return self._bnusd_receivable.get()

    @external(readonly=True)
    def getRebalancingStatus(self) -> list:
        """
        Checks the Rebalancing status of the pool.
        """
        rebalancing_direction = 0
        self.bnUSD_score = self.create_interface_score(self._bnUSD.get(), bnUSDTokenInterface)
        self.dex_score = self.create_interface_score(self._dex.get(), dexTokenInterface)
        self.loans_score = self.create_interface_score(self._loans.get(), loansTokenInterface)
        price = self.bnUSD_score.lastPriceInLoop()
        pool_price_dex = self.dex_score.getPriceByName("sICX/bnUSD")
        difference = price - (10 ** 36 // pool_price_dex)
        if price < (10 ** 36 // pool_price_dex):
            difference = (10 ** 36 // pool_price_dex) - price
            rebalancing_direction = 1
        change_in_percent = self._change_in_percent(price, difference)
        if change_in_percent > self._price_threshold.get():
            if rebalancing_direction == 1:
                return [True, self._calculate_sicx_to_retire(self.dex_score, 1), "bnUSD"]
            return [True, self._calculate_sicx_to_retire(self.dex_score, 0), "sICX"]
        else:
            return [False, 0]

    def _change_in_percent(self, price: int, difference: int) -> int:
        return (difference * 10 ** 18 // price) * 100

    @external
    def rebalance(self) -> None:
        """
           Calls the retireRedeem function of loans and retire the value of bnUSD.
           Rebalances only if the rate of change in dex pool price and oracle price is greater than the threshold set.
        """
        self.sICX_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)
        self.bnUSD_score = self.create_interface_score(self._bnUSD.get(), bnUSDTokenInterface)
        rebalancing_status = self.getRebalancingStatus()
        if rebalancing_status[0]:
            if rebalancing_status[2] == "sICX":
                sicx_to_retire = rebalancing_status[1]
                sicx_in_contract = self.sICX_score.balanceOf(self.address)
                if sicx_to_retire > sicx_in_contract:
                    self.sICX_score.transfer(self._dex.get(), sicx_in_contract, data_bytes)
                    bnusd_in_contract = self.bnUSD_score.balanceOf(self.address) - self._bnusd_receivable.get()
                    self.loans_score.retireRedeem("bnUSD", bnusd_in_contract, self._sicx_receivable.get())
            else:
                bnusd_to_retire = rebalancing_status[1]
                bnusd_in_contract = self.bnUSD_score.balanceOf(self.address)
                if bnusd_to_retire > bnusd_in_contract:
                    self.bnUSD_score.transfer(self._dex.get(), bnusd_in_contract, data_bytes_sicx)
                    sicx_in_contract = self.sICX_score.balanceOf(self.address) - self._sicx_receivable.get()
                    self.loans_score.retireRedeem("sICX", sicx_in_contract, self._bnusd_receivable.get())

    @external
    def tokenFallback(self, _from: Address, value: int, _data: bytes) -> None:
        pass
