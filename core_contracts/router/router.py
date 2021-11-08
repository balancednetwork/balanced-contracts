#### Simple transaction router for Balanced  #####

from .scorelib.utils import *
from .utils.checks import *
from iconservice import *

TAG = 'Balanced Router'


class Router(IconScoreBase):
    _DEX_ADDRESS = 'dex_address'
    _SICX_ADDRESS = 'sicx_address'
    _STAKING_ADDRESS = 'staking_address'
    _GOVERNANCE_ADDRESS = 'governance_address'
    _ADMIN = 'admin'
    _JAECHANG_LIMIT = 4 # Unbounded iterations won't pass audit
    _MINT_ADDRESS = Address.from_string('hx0000000000000000000000000000000000000000')

    ####################################
    # System
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

        # Linked Addresses
        self._governance = VarDB(self._GOVERNANCE_ADDRESS, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._sicx = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._staking = VarDB(
            self._STAKING_ADDRESS, db, value_type=Address)
        self._dex = VarDB(self._DEX_ADDRESS, db, value_type=Address)



    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)
        self._admin.set(_governance)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return TAG

    @external(readonly=True)
    def getAdmin(self) -> Address:
        """
        Gets the current admin address. This user can call using the
        `@only_admin` decorator.
        """
        return self._admin.get()

    @only_governance
    @external
    def setAdmin(self, _admin: Address) -> None:
        """
        :param _admin: The new admin address to set.
        Can make calls with the `@only_admin` decorator.
        Should be called before DEX use.
        """
        self._admin.set(_admin)

    @external(readonly=True)
    def getDex(self) -> Address:
        """
        Gets the address of the DEX SCORE.
        """
        return self._dex.get()

    @only_governance
    @external
    def setDex(self, _dex: Address) -> None:
        """
        :param _dex: the new DEX address to set.
        """
        self._dex.set(_dex)


    @external(readonly=True)
    def getSicx(self) -> Address:
        """
        Gets the address of the Sicx contract.
        """
        return self._sicx.get()

    @only_admin
    @external
    def setSicx(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new SICX address. Should be called before DEX use.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._sicx.set(_address)

    @only_admin
    @external
    def setStaking(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new Staking contract address. Should be called before dex use.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._staking.set(_address)

    @external(readonly=True)
    def getStaking(self) -> Address:
        """
        Gets the address of the Staking contract.
        """
        return self._staking.get()

    @only_owner
    @external
    def setGovernance(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new Governance contract address. Should be called before dex use.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._governance.set(_address)

    @external(readonly=True)
    def getGovernance(self) -> Address:
        """
        Gets the address of the Governance contract.
        """
        return self._governance.get()

    def _swap(self, _fromToken: Address, _toToken: Address):

        if _fromToken == None:
            if _toToken == self._sicx.get():
                # Stake ICX
                balance = self.icx.get_balance(self.address)
                self.icx.transfer(self._staking.get(), balance)
                return
            else:
                revert("{TAG}: ICX can only be traded for sICX")

        elif _fromToken == self._sicx.get() and _toToken == None:
            # Call swap ICX
            token = self.create_interface_score(_fromToken, TokenInterface)
            balance = token.balanceOf(self.address)
            token.transfer(self._dex.get(), balance, b'{"method":"_swap_icx"}')
            return

        else:
            token = self.create_interface_score(_fromToken, TokenInterface)
            balance = token.balanceOf(self.address)
            token.transfer(self._dex.get(), balance, b'{"method":"_swap","params":{"toToken":"' + str(_toToken).encode('utf-8') + b'"}}')

    def _route(self, _from: Address, _startToken: Address, _path: List[Address], _minReceive: int):
        current_token = _startToken

        for token in _path:
            self._swap(current_token, token)
            current_token = token

        if current_token == None:
            balance = self.icx.get_balance(self.address)
            if balance < _minReceive:
                revert(f"{TAG}: Below minimum receive amount of {_minReceive}")
            self.icx.transfer(_from, balance)

        else:
            token = self.create_interface_score(current_token, TokenInterface)
            balance = token.balanceOf(self.address)
            if balance < _minReceive:
                revert(f"{TAG}: Below minimum receive amount of {_minReceive}")
            token.transfer(_from, balance)

    @payable
    @external
    def route(self, _path: List[Address], _minReceive: int = 0):
        if len(_path) > self._JAECHANG_LIMIT:
            revert(f"Passed max swaps of {self._JAECHANG_LIMIT}")

        self._route(self.msg.sender, None, _path, _minReceive)

    @payable
    def fallback(self):
        pass


    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        """
        :param _from: The address calling `transfer` on the other contract
        :param _value: Amount of token transferred
        :param _data: Data called by the transfer, json object expected.

        This is invoked when a token is transferred to this score.
        It expects a JSON object with the following format:
        ```
        {"method": "METHOD_NAME", "params":{...}}
        ```

        Token transfers to this contract are rejected unless any of the
        following methods are passed in the object:

        1) `_deposit` - Calls the `_deposit()` function
        2) `_swap_icx` - Calls the `_swap_icx()` function
        3) `_swap` - Calls the `_swap()` function

        All calls to this function update snapshots and process dividends.
        """

        # We receive token transfers from balanced DEX and staking, mid route
        if _from == self._dex.get() or _from == self._MINT_ADDRESS:
            return

        unpacked_data = json_loads(_data.decode('utf-8'))
        _fromToken = self.msg.sender

        if unpacked_data["method"] == "_swap":
            minimum_receive = 0

            if "minimumReceive" in unpacked_data["params"]:
                minimum_receive = int(unpacked_data["params"]["minimumReceive"])

                if minimum_receive < 0:
                    revert(f"{TAG}: Must specify a positive number for minimum to receive")
            
            if "receiver" in unpacked_data["params"]:
                receiver = Address.from_string(unpacked_data["params"]["receiver"])
            else:
                receiver = _from

            if len(unpacked_data["params"]["path"]) > self._JAECHANG_LIMIT:
                revert(f"Passed max swaps of {self._JAECHANG_LIMIT}")

            path = []
            for address in unpacked_data["params"]["path"]:

                if address is not None:
                    path.append(Address.from_string(address))
                else:
                    path.append(None)

            self._route(receiver, _fromToken, path, minimum_receive)

        else:
            revert(f"{TAG}: Fallback directly not allowed.")
