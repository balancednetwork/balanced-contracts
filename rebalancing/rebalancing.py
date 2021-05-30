from iconservice import *

TAG = 'Rebalancing'


class sICXTokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


class bnUSDTokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

class loansTokenInterface(InterfaceScore):
    @interface
    def getMaxRetireAmount(self, _symbol: str) -> int:
        pass

    @interface
    def returnAsset(self, _symbol: str, _value: int, _repay: bool = True) -> None:
        pass

class Rebalancing(IconScoreBase):
    _bnUSD_ADDRESS = 'bnUSD_address'
    _SICX_ADDRESS = 'sicx_address'
    _DEX_ADDRESS = 'dex_address'
    _LOANS_ADDRESS = 'loans_address'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._bnUSD = VarDB(
            self._bnUSD_ADDRESS, db, value_type=Address)
        self._sicx = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._dex = VarDB(self._DEX_ADDRESS, db, value_type=Address)
        self._loans = VarDB(self._DEX_ADDRESS, db, value_type=Address)

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
    def rebalance(self) -> None:
        data = {"method": "_swap", "params": {"toToken": str(self._bnUSD.get())}}
        data_string = json_dumps(data)
        data_bytes = str.encode(data_string)
        self._sICX_score = self.create_interface_score(self._sicx.get(), sICXTokenInterface)
        self.bnUSD_score = self.create_interface_score(self._bnUSD.get(), bnUSDTokenInterface)
        self.loans_score = self.create_interface_score(self._loans.get(), loansTokenInterface)
        self._sICX_score.transfer(self._dex.get(), 1000 * 10 ** 18, data_bytes)
        max_retire_amount = self.loans_score.getMaxRetireAmount("bnUSD")
        self.loans_score.returnAsset("bnUSD",max_retire_amount)
