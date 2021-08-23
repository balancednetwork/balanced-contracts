from iconservice import *
from .utils.checks import *

TAG = 'Rebalancing'

EXA = 10 ** 18
# sICX token address in toToken
data_bytes_sicx = b'{"method": "_swap", "params": {"toToken": "cx2609b924e33ef00b648a409245c7ea394c467824"}}'

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


class Rebalancing(IconScoreBase):
    _bnUSD_ADDRESS = 'bnUSD_address'
    _SICX_ADDRESS = 'sicx_address'
    _DEX_ADDRESS = 'dex_address'
    _LOANS_ADDRESS = 'loans_address'
    _GOVERNANCE_ADDRESS = 'governance_address'
    _SICX_RECEIVABLE = 'sicx_receivable'
    _MAX_RETIRE = '_max_retire'
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
        self._max_retire = VarDB(self._MAX_RETIRE, db, value_type=int)
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

    @external
    @only_governance
    def setMaxRetireAmount(self, _value: int) -> None:
        """
        :param _value: Maximum sICX amount to retire.
        Sets the Maximum sICX amount to retire.
        """
        self._max_retire.set(_value)

    @external(readonly=True)
    def getMaxRetireAmount(self) -> int:
        """
        Returns the Maximum sICX amount to retire.
        """
        return self._max_retire.get()

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
        bnusd_score = self.create_interface_score(self._bnUSD.get(), BnusdTokenInterface)
        dex_score = self.create_interface_score(self._dex.get(), DexTokenInterface)
        sicx_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)

        price = bnusd_score.lastPriceInLoop() * EXA // sicx_score.lastPriceInLoop()
        pool_stats = dex_score.getPoolStats(2)
        dex_price = pool_stats['base'] * EXA // pool_stats['quote']

        # direction = price > dex_price

        diff = (price - dex_price) * EXA // price
        min_diff = self._price_threshold.get()
        required_retire_amount = self._calculate_tokens_to_retire(price, pool_stats['base'], pool_stats['quote'])
        # if direction:
        #     return [diff > min_diff, required_retire_amount]
        # return [diff < -min_diff, required_retire_amount, "sICX"]
        return [diff > min_diff, required_retire_amount, diff < -min_diff]

    @external
    def rebalance(self) -> None:
        """
           Calls the retireRedeem method on loans to balance the bnUSD price on the DEX.
           Rebalances only if the difference between the DEX price and oracle price is greater than the threshold.
        """
        loans = self.create_interface_score(self._loans.get(), LoansInterface)
        bnusd_score = self.create_interface_score(self._bnUSD.get(), BnusdTokenInterface)
        sicx_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)

        rebalance_needed, required_retire_amount, reverse_rebalance = self.getRebalancingStatus()
        sicx_threshold = self._sicx_receivable.get()
        if required_retire_amount > 0:
            if rebalance_needed:
                if required_retire_amount > sicx_threshold:
                    loans.retireRedeem('bnUSD', self._max_retire.get())
        else:
            bnusd_in_contract = bnusd_score.balanceOf(self.address)
            required_retire_amount = abs(required_retire_amount)
            if reverse_rebalance:
                if required_retire_amount > bnusd_in_contract:
                    bnusd_score.transfer(self._dex.get(), bnusd_in_contract, data_bytes_sicx)
                    sicx_in_contract = sicx_score.balanceOf(self.address)
                    data_to_send = {"bnusd_to_receive": self._bnusd_receivable.get(),
                                    "sicx_amount": sicx_in_contract}
                    data_in_string = json_dumps(data_to_send)
                    data_in_bytes = str.encode(data_in_string)
                    sicx_score.transfer(self._loans.get(), sicx_in_contract, data_in_bytes)

    @external
    def tokenFallback(self, _from: Address, value: int, _data: bytes) -> None:
        pass