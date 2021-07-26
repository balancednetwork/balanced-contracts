from iconservice import *
from .utils.checks import *

TAG = 'Rebalancing'

EXA = 10 ** 18
data_for_loans = b'{"_asset": "bnUSD", "_amount": ""}'

class sICXTokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def lastPriceInLoop(self) -> int:
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass


class BnusdTokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def lastPriceInLoop(self) -> int:
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass


class DexTokenInterface(InterfaceScore):
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
    _GOVERNANCE_ADDRESS = 'governance_address'
    _SICX_RECEIVABLE = 'sicx_receivable'
    _ADMIN = 'admin'
    _PRICE_THRESHOLD = '_price_threshold'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._bnUSD = VarDB(self._bnUSD_ADDRESS, db, value_type=Address)
        self._sicx = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._dex = VarDB(self._DEX_ADDRESS, db, value_type=Address)
        self._loans = VarDB(self._LOANS_ADDRESS, db, value_type=Address)
        self._governance = VarDB(self._GOVERNANCE_ADDRESS, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._sicx_receivable = VarDB(self._SICX_RECEIVABLE, db, value_type=int)
        self._price_threshold = VarDB(self._PRICE_THRESHOLD, db, value_type=int)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._admin.set(_governance)

    def on_update(self) -> None:
        super().on_update()

    @external
    @only_admin
    def setBnusd(self, _address: Address) -> None:
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
    @only_owner
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

    def _calculate_tokens_to_retire(self, price: int, base_supply: int, quote_supply: int) -> int:
        """
        :param price: Oracle price.
        :param base_supply: base token supply.
        :param quote_supply: quote token supply.
        Returns the amount of sICX required for rebalancing the price.
        """
        value = (self._sqrt(price * base_supply * quote_supply) // 10 ** 9) - base_supply
        return value

    @external
    @only_governance
    def setPriceChangeThreshold(self, _value: int) -> None:
        """
        :param _value: It is the minimum price deviation between oracle and dex pool .
        Sets the threshold and if the deviation is more than threshold, then rebalancing is triggered.
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
        Sets the sICX amount to receive by rebalancing contract from the loans contract.
        """
        self._sicx_receivable.set(_value)

    @external(readonly=True)
    def getSicxReceivable(self) -> int:
        """
        Returns the sICX amount to receive by rebalancing contract.
        """
        return self._sicx_receivable.get()

    @external(readonly=True)
    def getRebalancingStatus(self) -> list0:
        """
        Checks the Rebalancing status of the pool i.e. whether the difference between
        oracle price and dex pool price are more than threshold or not and if it is more
        than the threshold then the function returns total sICX value that needs to be converted
        to bnUSD and retires to reduce the price difference.
        """
        self.bnUSD_score = self.create_interface_score(self._bnUSD.get(), BnusdTokenInterface)
        self.dex_score = self.create_interface_score(self._dex.get(), DexTokenInterface)
        self.sICX_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)
        price = self.bnUSD_score.lastPriceInLoop() * EXA // self.sICX_score.lastPriceInLoop()
        pool_stats = self.dex_score.getPoolStats(2)
        dex_price = pool_stats['base'] * EXA // pool_stats['quote']
        diff = (price - dex_price) * EXA // price
        max_diff = self._price_threshold.get()
        if diff > max_diff:
            return [True, self._calculate_tokens_to_retire(price, pool_stats['base'], pool_stats['quote']),
                    "sICX"]
        return [False, self._calculate_tokens_to_retire(price, pool_stats['base'], pool_stats['quote'])]

    @external
    def rebalance(self) -> None:
        """
           Calls the retireRedeem function of loans and retire the value of bnUSD.
           Rebalances only if the rate of change in dex pool price and oracle price is greater than the threshold set.
        """
        self.sICX_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)
        rebalancing_status = self.getRebalancingStatus()
        sicx_to_receive = self._sicx_receivable.get()
        if rebalancing_status[0]:
            sicx_to_retire = rebalancing_status[1]
            if sicx_to_retire > sicx_to_receive:
                self.sICX_score.transfer(self._loans.get(), sicx_to_receive, data_for_loans)

    @external
    def tokenFallback(self, _from: Address, value: int, _data: bytes) -> None:
        pass