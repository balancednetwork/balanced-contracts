from iconservice import *

TAG = 'Rebalancing'

POINTS = 10000


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
    def priceInLoop(self) -> int:
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

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._bnUSD = VarDB(self._bnUSD_ADDRESS, db, value_type=Address)
        self._sicx = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._dex = VarDB(self._DEX_ADDRESS, db, value_type=Address)
        self._loans = VarDB(self._LOANS_ADDRESS, db, value_type=Address)
        self._oracle = VarDB(self._ORACLE_ADDRESS, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def setbnUSD(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new bnUSD contract address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._bnUSD.set(_address)

    @external
    def setLoans(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new bnUSD contract address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._loans.set(_address)

    @external
    def setSicx(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new SICX address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._sicx.set(_address)

    @external
    def setOracle(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new Oracle address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._oracle.set(_address)

    @external
    def setDex(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new DEX address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._dex.set(_address)

    def _calculate_sicx_to_retire(self) -> int:
        self.oracle_score = self.create_interface_score(self._oracle.get(), oracleTokenInterface)
        self.dex_score = self.create_interface_score(self._dex.get(), dexTokenInterface)
        oracle_price = self.oracle_score.get_reference_data("ICX", "USD")
        oracle_rate = oracle_price["rate"]
        pool_stats = self.dex_score.getPoolStats(2)
        sicx_supply = int(pool_stats['base'], 16)
        bnusd_supply = int(pool_stats['quote'], 16)
        value = ((((oracle_rate * 10 ** 18 * sicx_supply * bnusd_supply) ** 0.5) // 10 ** 18) - sicx_supply)
        return value

    @external(readonly=True)
    def getRebalancingStatus(self) -> tuple:
        self.sICX_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)
        self.bnUSD_score = self.create_interface_score(self._bnUSD.get(), bnUSDTokenInterface)
        self.loans_score = self.create_interface_score(self._loans.get(), loansTokenInterface)
        self.dex_score = self.create_interface_score(self._dex.get(), dexTokenInterface)
        price = self.bnUSD_score.priceInLoop()
        sicx_rate = self.sICX_score.priceInLoop()
        params_loan = self.loans_score.getParameters()
        redemption_fee = params_loan["redemption fee"]
        sicx_from_lenders = 1 * 10 ** 18 * price * (POINTS - redemption_fee) // (sicx_rate * POINTS)
        pool_price_dex = self.dex_score.getPriceByName("sICX/bnUSD")
        if (sicx_from_lenders * pool_price_dex) // 10 ** 18 > 10 ** 18:
            return True, self._calculate_sicx_to_retire()


    @external
    def rebalance(self, ) -> None:
        data = {"method": "_swap", "params": {"toToken": str(self._bnUSD.get())}}
        data_string = json_dumps(data)
        data_bytes = str.encode(data_string)
        self.sICX_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)
        sicx_in_contract = self.sICX_score.balanceOf(self.address)
        rebalancing_status = self.getRebalancingStatus()
        if rebalancing_status[0]:
            sicx_to_retire = rebalancing_status[1]
            if sicx_to_retire > sicx_in_contract:
                self.sICX_score.transfer(self._dex.get(), sicx_in_contract, data_bytes)
                bnusd_in_contract = self.bnUSD_score.balanceOf(self.address)
                self.loans_score.retireRedeem("bnUSD", bnusd_in_contract,1000*10**18)

    @external
    def tokenFallback(self, _from: Address, value: int, _data: bytes) -> None:
        pass
