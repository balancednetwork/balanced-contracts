from iconservice import *
from .utils.checks import *
from .utils.enums import *

TAG = 'Rebalancing'

EXA = 10 ** 18

class StabilityFundInterface(InterfaceScore):
    @interface
    def raisePrice(self, amount) -> None:
        pass
    
    @interface
    def lowerPrice(self, amount) -> None:
        pass


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
    def raisePrice(self, _total_tokens_required: int) -> None:
        pass

    @interface
    def lowerPrice(self, _total_tokens_required: int) -> None:
        pass


class Rebalancing(IconScoreBase):
    _bnUSD_ADDRESS = 'bnUSD_address'
    _SICX_ADDRESS = 'sicx_address'
    _DEX_ADDRESS = 'dex_address'
    _LOANS_ADDRESS = 'loans_address'
    _STABILITY_FUND_ADDRESS = "stability_fund_address"
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
        self._stability_fund = VarDB(self._STABILITY_FUND_ADDRESS, db, value_type=Address)
        self._governance = VarDB(self._GOVERNANCE_ADDRESS, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._sicx_receivable = VarDB(self._SICX_RECEIVABLE, db, value_type=int)
        self._price_threshold = VarDB(self._PRICE_THRESHOLD, db, value_type=int)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._admin.set(_governance)

    def on_update(self) -> None:
        super().on_update()
        self._sicx_receivable.remove()

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
    def setStabilityfund(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new bnUSD contract address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._stability_fund.set(_address)

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

    def _calculate_tokens_to_sell(self, price: int, base_supply: int, quote_supply: int) -> int:
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

    @external(readonly=True)
    def getRebalancingStatus(self) -> list:
        """
        Checks the Rebalancing status of the pool i.e. whether the difference between
        oracle price and dex pool price are more than threshold or not. If it is more
        than the threshold then the function returns a list .
        If the first element of the list is True then it's forward rebalancing and if the
        last element of the list is True, it's the reverse rebalancing .
        The second element of the list specifies the amount of tokens required to balance the pool.
        """
        bnusd_score = self.create_interface_score(self._bnUSD.get(), BnusdTokenInterface)
        dex_score = self.create_interface_score(self._dex.get(), DexTokenInterface)
        sicx_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)

        price = bnusd_score.lastPriceInLoop() * EXA // sicx_score.lastPriceInLoop()
        pool_stats = dex_score.getPoolStats(2)
        dex_price = pool_stats['base'] * EXA // pool_stats['quote']

        diff = (price - dex_price) * EXA // price
        min_diff = self._price_threshold.get()
        tokens_to_sell = self._calculate_tokens_to_sell(price, pool_stats['base'], pool_stats['quote'])
        return [diff > min_diff, tokens_to_sell, diff < -min_diff]

    @external
    def rebalance(self) -> None:
        """
        Balances the sICX/bnUSD price on the DEX. If there are funds in the stability fund, 
        then that is used. If there are no funds in the stability fund, then the loans contract is used. 
        """
        higher, token_amount, lower = self.getRebalancingStatus()
        
        if token_amount > 0:

            if higher:
                try:
                    self._rebalanceUsingStabilityFund(token_amount, RebalancingDirection.FORWARD)
                except StabilityFundOutOfBalance:
                    self._rebalanceUsingLoans(token_amount, RebalancingDirection.FORWARD)

        else:
            token_amount = abs(token_amount)

            if lower:
                try:
                    self._rebalanceUsingStabilityFund(token_amount, RebalancingDirection.REVERSE)
                except StabilityFundOutOfBalance:
                    self._rebalanceUsingLoans(token_amount, RebalancingDirection.REVERSE)

    def _rebalanceUsingLoans(self, _amount: int, _rebalancing_type: RebalancingDirection) -> None:
        """
        :param _amount: Amount of tokens to sell.
        :param _rebalancing_type: Direction of the rebalancing.
        Rebalances the sICX / bnUSD pool on the dex.
        """
        loans = self.create_interface_score(self._loans.get(), LoansInterface)

        if _rebalancing_type == RebalancingDirection.FORWARD:
            loans.raisePrice(_amount)

        elif _rebalancing_type == RebalancingDirection.REVERSE:
            loans.lowerPrice(_amount)

        else:
            revert("Unknown rebalancing error using Loans.")

    def _rebalanceUsingStabilityFund(self, _amount: int, _rebalancing_type: RebalancingDirection) -> None:
        """
        :param _amount: Amount of tokens to sell.
        :param _rebalancing_type: Direction of the rebalancing.
        Rebalances the sICX / bnUSD pool on the dex.
        """
        stability_fund_address = self._stability_fund.get()

        if _rebalancing_type == RebalancingDirection.FORWARD:
            sicx = create_interface_score(self._sicx.get(), sICXTokenInterface)
            sicx_balance = sicx.balanceOf(stability_fund_address)

            if not sicx_balance > 0:
                raise StabilityFundOutOfBalance

            else:
                stability_fund = create_interface_score(self._stability_fund.get(), StabilityFundInterface)
                stability_fund.raisePrice(min(sicx_balance, _amount))

        elif _rebalancing_type == RebalancingDirection.REVERSE:
            bnusd = create_interface_score(self._bnUSD.get(), BnusdTokenInterface)
            bnusd_balance = bnusd.balanceOf(stability_fund_address)
            
            if not bnusd_balance > 0:
                raise StabilityFundOutOfBalance

            else:
                stability_fund = create_interface_score(self._stability_fund.get(), StabilityFundInterface)
                stability_fund.lowerPrice(min(bnusd_balance, _amount))

        else:
            revert("Unknown rebalancing error using the stability fund.")

    @external
    def tokenFallback(self, _from: Address, value: int, _data: bytes) -> None:
        pass

