from iconservice import *
from .utils.checks import *
from .utils.contract_addresses import ContractAddresses

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


class LoansInterface(InterfaceScore):
    @interface
    def retireRedeem(self, _symbol: str, _sicx_from_lenders: int) -> None:
        pass


class Rebalancing(ContractAddresses):
    _SICX_RECEIVABLE = 'sicx_receivable'
    _PRICE_THRESHOLD = '_price_threshold'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._sicx_receivable = VarDB(self._SICX_RECEIVABLE, db, value_type=int)
        self._price_threshold = VarDB(self._PRICE_THRESHOLD, db, value_type=int)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self.set_contract_addresses([{"name": "admin", "address": _governance}])

    def on_update(self) -> None:
        super().on_update()

        _bnUSD_ADDRESS = 'bnUSD_address'
        _SICX_ADDRESS = 'sicx_address'
        _DEX_ADDRESS = 'dex_address'
        _LOANS_ADDRESS = 'loans_address'
        _ADMIN = 'admin'
        _GOVERNANCE_ADDRESS = 'governance_address'
        VarDB(_bnUSD_ADDRESS, self.db, value_type=Address).remove()
        VarDB(_SICX_ADDRESS, self.db, value_type=Address).remove()
        VarDB(_DEX_ADDRESS, self.db, value_type=Address).remove()
        VarDB(_LOANS_ADDRESS, self.db, value_type=Address).remove()
        VarDB(_GOVERNANCE_ADDRESS, self.db, value_type=Address).remove()
        VarDB(_ADMIN, self.db, value_type=Address).remove()

    @external
    @only_admin
    def setBnusd(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new bnUSD contract address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._bnUS = _address

    @external
    @only_admin
    def setLoans(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new bnUSD contract address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self.set_contract_addresses([{"name": "loans", "address":_address}])

    @external
    @only_admin
    def setSicx(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new SICX address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self.set_contract_addresses([{"sicx": _address}])

    @external
    @only_owner
    def setGovernance(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new SICX address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self.set_contract_addresses([{"name": "governance", "address":_address}])

    @external
    @only_admin
    def setDex(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new DEX address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self.set_contract_addresses([{"name": "dex", "address":_address}])

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
        return self._sqrt(price * base_supply * quote_supply // EXA) - base_supply

    @external
    @only_governance
    def setPriceDiffThreshold(self, _value: int) -> None:
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
    def getRebalancingStatus(self) -> list:
        """
        Checks the Rebalancing status of the pool i.e. whether the difference between
        oracle price and dex pool price are more than threshold or not. If it is more
        than the threshold then the function returns total sICX value that needs to be
        converted to bnUSD and retired to reduce the price difference.
        """
        bnusd_score = self.create_interface_score(self.get_contract_address("bnusd"), BnusdTokenInterface)
        dex_score = self.create_interface_score(self.get_contract_address("dex"), DexTokenInterface)
        sicx_score = self.create_interface_score(self.get_contract_address("sicx"), sICXTokenInterface)

        price = bnusd_score.lastPriceInLoop() * EXA // sicx_score.lastPriceInLoop()
        pool_stats = dex_score.getPoolStats(2)
        dex_price = pool_stats['base'] * EXA // pool_stats['quote']

        diff = (price - dex_price) * EXA // price
        min_diff = self._price_threshold.get()
        required_retire_amount = self._calculate_tokens_to_retire(price, pool_stats['base'], pool_stats['quote'])

        return [diff > min_diff, required_retire_amount]

    @external
    def rebalance(self) -> None:
        """
           Calls the retireRedeem method on loans to balance the bnUSD price on the DEX.
           Rebalances only if the difference between the DEX price and oracle price is greater than the threshold.
        """
        loans = self.create_interface_score(self.get_contract_address("loans"), LoansInterface)
        rebalance_needed, required_retire_amount = self.getRebalancingStatus()
        sicx_sale_amount = self._sicx_receivable.get()
        if rebalance_needed:
            if required_retire_amount > sicx_sale_amount:
                loans.retireRedeem('bnUSD', sicx_sale_amount)

    @external
    def tokenFallback(self, _from: Address, value: int, _data: bytes) -> None:
        pass
