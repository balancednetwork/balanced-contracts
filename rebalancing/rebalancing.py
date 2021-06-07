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
    def returnAsset(self, _symbol: str, _value: int, _repay: bool = True) -> None:
        pass

    @interface
    def getParameters(self) -> dict:
        pass


class dexTokenInterface(InterfaceScore):
    @interface
    def getPriceByName(self, _name: str) -> int:
        pass


class Rebalancing(IconScoreBase):
    _bnUSD_ADDRESS = 'bnUSD_address'
    _SICX_ADDRESS = 'sicx_address'
    _DEX_ADDRESS = 'dex_address'
    _LOANS_ADDRESS = 'loans_address'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._bnUSD = VarDB(self._bnUSD_ADDRESS, db, value_type=Address)
        self._sicx = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._dex = VarDB(self._DEX_ADDRESS, db, value_type=Address)
        self._loans = VarDB(self._LOANS_ADDRESS, db, value_type=Address)

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
    def setDex(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new SICX address.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._dex.set(_address)

    @external
    def rebalance(self, ) -> None:
        data = {"method": "_swap", "params": {"toToken": str(self._bnUSD.get())}}
        data_string = json_dumps(data)
        data_bytes = str.encode(data_string)
        self.sICX_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)
        self.bnUSD_score = self.create_interface_score(self._bnUSD.get(), bnUSDTokenInterface)
        self.loans_score = self.create_interface_score(self._loans.get(), loansTokenInterface)
        self.dex_score = self.create_interface_score(self._dex.get(), dexTokenInterface)
        sicx_in_contract = self.sICX_score.balanceOf(self.address)
        price = self.bnUSD_score.priceInLoop()
        sicx_rate = self.sICX_score.priceInLoop()
        # redeemed = max_retire_amount
        params_loan = self.loans_score.getParameters()
        redemption_fee = params_loan["redemption fee"]
        sicx_from_lenders = 1*10**18 * price * (POINTS - redemption_fee) // (sicx_rate * POINTS)
        pool_price_dex = self.dex_score.getPriceByName("sICX/bnUSD")
        if (sicx_from_lenders * pool_price_dex * 10**18) // 10**36 > 10**18:
            self.sICX_score.transfer(self._dex.get(), sicx_in_contract, data_bytes)
            bnusd_in_contract = self.bnUSD_score.balanceOf(self.address)
            self.loans_score.returnAsset("bnUSD", bnusd_in_contract)

    @external
    def tokenFallback(self, _from: Address, value: int, _data: bytes) -> None:
        pass

    def fallback(self) -> None:
        pass