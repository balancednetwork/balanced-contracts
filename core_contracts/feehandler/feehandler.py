from iconservice import *
from .interfaces import *
from .utils.checks import *

TAG = 'FeeHandler'


class FeeHandler(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._accepted_dividend_tokens = ArrayDB("dividend_tokens", db, Address)
        self._last_fee_processing_block = DictDB("last_block", db, int)
        self._fee_processing_interval = VarDB("block_interval", db, int)
        self._last_txhash = VarDB("last_txhash", db, bytes)
        self._routes = DictDB("routes", db, str, depth=2)
        self._governance = VarDB("governance", db, Address)
        self._enabled = VarDB("enabled", db, bool)
        self._allowed_addresses = ArrayDB("allowed_address", db, Address)
        self._next_allowed_addresses_index = VarDB("_next_allowed_addresses_index", db, int)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return f"Balanced {TAG}"

    @external
    @only_governance
    def enable(self) -> None:
        self._enabled.set(True)

    @external
    @only_governance
    def disable(self) -> None:
        self._enabled.set(False)

    @external
    @only_governance
    def setAcceptedDividendTokens(self, _tokens: List[Address]) -> None:
        """
        Specifies which tokens that does not need converting before they are sent to
        the dividends contract.

        :param _tokens: List of token addresses.
        """
        if len(_tokens) > 10:
            revert("There can be a maximum of 10 accepted dividend tokens.")

        for address in _tokens:
            if not address.is_contract:
                revert(f"{TAG}: Address provided is an EOA address. Only contract addresses are allowed.")

        # Remove all previous tokens.
        while self._accepted_dividend_tokens:
            self._accepted_dividend_tokens.pop()

        # Add tokens.
        for token in _tokens:
            self._accepted_dividend_tokens.put(token)

    @external(readonly=True)
    def getAcceptedDividendTokens(self) -> list:
        """
        Gets all accepted dividend tokens.
        """
        return [token for token in self._accepted_dividend_tokens]

    @external
    @only_governance
    def setRoute(self, _fromToken: Address, _toToken: Address, _path: List[Address]) -> None:
        """
        Sets a route to use when converting from token A to token B.

        :param _fromToken: Address of token A.
        :param _toToken: Address of token B.
        :param _path: The path to take when converting from token A to token B.
                      Token A is omitted from this path. E.g. assuming token C and D are
                      needed for the convertion, the path is specified in the following format:
                      [<address_token_c>, <address_token_d>, <address_token_b>].
        """
        for address in _path:
            if not address.is_contract:
                revert(f"{TAG}: Address provided is an EOA address. Only contract addresses are allowed.")
        _path = [str(address) for address in _path]
        self._routes[_fromToken][_toToken] = json_dumps(_path)

    @external
    @only_governance
    def deleteRoute(self, _fromToken: Address, _toToken: Address) -> None:
        """
        Deletes the route used when converting from token A to token B.

        :param _fromToken: Address of the token A.
        :param _toToken: Address of token B.
        """
        del self._routes[_fromToken][_toToken]

    @external(readonly=True)
    def getRoute(self, _fromToken: Address, _toToken: Address) -> dict:
        """
        Gets the route used for converting token A to token B.

        :param _fromToken: Address of token A.
        :param _toToken: Address of token B.
        """
        path = self._routes[_fromToken][_toToken]
        if not path:
            return {}

        route = {
            "fromToken": _fromToken,
            "toToken": _toToken,
            "path": json_loads(path)
        }

        return route

    @external
    @only_governance
    def setFeeProcessingInterval(self, _interval: int) -> None:
        """
        Sets the number of blocks that must occur before a particular
        incomming token can trigger the contract to process all fees
        accumulated in that token.

        :param _interval: Number of blocks.
        """
        self._fee_processing_interval.set(_interval)

    @external(readonly=True)
    def getFeeProcessingInterval(self) -> int:
        """
        Gets the number of blocks that must occur before a particular
        incomming token can trigger the contract to process all fees
        accumulated in that token.
        """
        return self._fee_processing_interval.get()

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used only to receive all fees generated by the Balanced system. Fees
        are processed and forwarded to it's intended destination.

        :param _from: Token origination address.
        :param _value: Number of tokens received.
        :param _data: Unused, ignored.
        """

        # Only one call to this method per external tx.
        if self._last_txhash.get() == self.tx.hash:
            return

        # Do nothing if not enough blocks has occured since last conversion for this token.
        if not self._timeForFeeProcessing(self.msg.sender):
            return
        else:
            self._last_txhash.set(self.tx.hash)

        # If token is accepted dividend token -> forward total token balance to dividends contract.
        if self.msg.sender in self._accepted_dividend_tokens:
            self._transferToken(self.msg.sender, self._getContractAddress("dividends"),
                                self._getTokenBalance(self.msg.sender))

        # Set the block for this fee processing event.
        self._last_fee_processing_block[self.msg.sender] = self.block_height

    @only_owner
    @external
    def add_allowed_address(self, address: Address) -> None:
        """
        Adds address into  allowed address list
        :param address: Address to be added
        :return:
        """
        if not address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._allowed_addresses.put(address)

    @external(readonly=True)
    def get_allowed_address(self, offset: int = 0) -> List:
        """
        Returns 20 allowed address
        :param offset: Offset
        :return:
        """
        start = offset
        end = min(len(self._allowed_addresses), offset + 20) - 1
        return [self._allowed_addresses[i] for i in range(start, end + 1)]

    @external
    def route_contract_balances(self) -> None:
        """
        Converts and sends fees held by the fee handler to destination contract
        :return:
        """
        starting_index = self._next_allowed_addresses_index.get()
        current_index = starting_index
        loop_flag = False

        allowed_addresses_length = len(self._allowed_addresses)
        if not allowed_addresses_length:
            revert(f"{TAG}: No allowed addresses.")

        while True:
            if current_index >= allowed_addresses_length:
                current_index = 0

            address = self._allowed_addresses[current_index]
            balance = self._getTokenBalance(address)

            if balance:
                break
            else:
                if loop_flag and (starting_index == current_index):
                    revert("No fees on the contract")
                current_index += 1
                if not loop_flag:
                    loop_flag = True
                continue
        self._next_allowed_addresses_index.set(current_index + 1)

        try:
            # Raises JSONDecodeError if trying to decode an empty string.
            path = json_loads(self._routes[address][self._getContractAddress("baln")])
        except:
            path = []

        try:
            if path:
                # Use router.
                self._transferToken(address, self._getContractAddress("router"), balance,
                                    self._createDataFieldRouter(self._getContractAddress("dividends"), path))

            else:
                # Use dex.
                self._transferToken(address, self._getContractAddress("dex"), balance,
                                    self._createDataFieldDex(self._getContractAddress("baln"),
                                                             self._getContractAddress("dividends")))

        except BaseException as e:
            revert(f'Fee conversion for {address} failed, {repr(e)}')

    def _createDataFieldRouter(self, _receiver: Address, _path: list) -> bytes:
        """
        Constructs the data to pass to the router contract when making a swap.

        :param _receiver: Address to receive the funds when all swaps have completed.
        :param _path: Path to use for the swap. List of addresses in string format.
        """

        # Convert the path to a bytestring.
        temp = []
        length = len(_path)
        counter = 0
        for address in _path:
            if counter != length - 1:
                temp.append(b'"' + address.encode() + b'", ')
            else:
                temp.append(b'"' + address.encode() + b'"')
            counter += 1
        path = b'[' + b''.join(temp) + b']'

        # Construct data as a bytestring and return it.
        data = (
                b'{"method": "_swap", "params": {"path": ' + path +
                b', "receiver": "' + str(_receiver).encode() + b'"}}'
        )
        return data

    def _createDataFieldDex(self, _toToken: Address, _receiver: Address) -> bytes:
        """
        Constructs the data to pass to the dex contract when making a swap.

        :param _toToken: Token to swap to.
        :param _receiver: Address to receive the funds when all swaps have completed.
        """
        data = (
                b'{"method": "_swap", "params": {"toToken": "' + str(_toToken).encode() +
                b'", "receiver": "' + str(_receiver).encode() + b'"}}'
        )
        return data

    def _getContractAddress(self, _contract: str) -> Address:
        """
        Gets a contract address registered in the governance contract.

        :param _contract: Name of the contract as specified in the governance contract.
        """
        gov = self.create_interface_score(self._governance.get(), GovernanceInterface)
        return gov.getContractAddress(_contract)

    def _timeForFeeProcessing(self, _token: Address) -> bool:
        """
        Check if it's time to process all accumulated fees for the specified token.

        :param _token: Token address.
        """

        # Hold on processing fees until governance allows it
        if not self._enabled.get():
            return False

        last_conversion = self._last_fee_processing_block[_token]
        target_block = last_conversion + self._fee_processing_interval.get()

        if not last_conversion:
            return True
        elif self.block_height < target_block:
            return False
        else:
            return True

    def _getTokenBalance(self, _token: Address) -> int:
        """
        Gets this contract's balance for the specified IRC2 token.

        :param _token: Address of token.
        """
        token = self.create_interface_score(_token, IRC2Interface)
        return token.balanceOf(self.address)

    def _transferToken(self, _token: Address, _to: Address, _amount: int, _data: bytes = None) -> None:
        """
        Transfers an IRC2 token from this contract.

        :param _token: Token to transfer.
        :param _to: Token recipient.
        :param _amount: Number of tokens to transfer.
        :param _data: Extra data to be sent.
        """
        token = self.create_interface_score(_token, IRC2Interface)
        token.transfer(_to, _amount, _data)
