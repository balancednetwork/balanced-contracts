from iconservice import *
from .interfaces import *
from .utils.checks import *
from .utils.constants import *


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

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)
        self._fee_processing_interval.set(1800)        

        # Set initial accepted tokens on main net.
        accepted_dividend_tokens = [
            Address.from_string(BALN),
            Address.from_string(BNUSD),
            Address.from_string(SICX)
        ]

        for token in accepted_dividend_tokens:
            self._accepted_dividend_tokens.put(token)

        # Set inital routes on main net.
        initial_routes = [
            {
                'from': Address.from_string(IUSDC),
                'to': Address.from_string(BALN),
                'path': f'[{BNUSD}, {BALN}]'
            },
            {
                'from': Address.from_string(OMM),
                'to': Address.from_string(BALN),
                'path': f'[{SICX}, {BALN}]'
            },
            {
                'from': Address.from_string(USDS),
                'to': Address.from_string(BALN),
                'path': f'[{BNUSD}, {BALN}]'
            },
            {
                'from': Address.from_string(CFT),
                'to': Address.from_string(BALN),
                'path': f'[{SICX}, {BALN}]'
            }
        ]

        for route in initial_routes:
            _from = route['from']
            _to = route['to']
            _path = route['path']
            self._routes[_from][_to] = _path

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return f"Balanced {TAG}"

    @external
    @only_governance
    def setAcceptedDividendTokens(self, _tokens: list[Address]) -> None:
        """
        Specifies which tokens that does not need converting before they are sent to
        the dividends contract.

        :param _tokens: list of token addresses
        """
        if len(_tokens) > 10:
            revert("There can be a maximum of 10 accepted dividend tokens.")

        # Remove all previous tokens.
        while self._accepted_dividend_tokens:
            self._accepted_dividend_tokens.pop()

        # Add tokens.
        for token in _tokens:
            self._accepted_dividend_tokens.put(token)

    @external(readonly=True)
    def getAcceptedDividendTokens(self) -> list[Address]:
        """
        Gets all accepted dividend tokens.

        :param _tokens: list of token addresses
        """
        return [token for token in self._accepted_dividend_tokens]

    @external
    @only_governance
    def setRoute(self, _fromToken: Address, _toToken: Address, _path: str):
        """
        Sets a route to use when converting token A to token B.

        :param _fromToken: The address of the token A
        :param _toToken: The address of token B
        :param _path: The path to take when converting token A to token B.
                      Token A is omitted from this path. E.g. assuming token C and D are 
                      needed for the convertion, the route is specified in the following format:
                      '[<address_token_c>, <address_token_d>, <address_token_b>]'.
        """
        self._routes[_fromToken][_toToken] = _path

    @external
    @only_governance
    def deleteRoute(self, _fromToken: Address, _toToken: Address):
        """
        Deletes the route used when converting token A to token B.

        :param _fromToken: The address of the token A
        :param _toToken: The address of token B         
        """
        del self._routes[_fromToken][_toToken]
    
    @external(readonly=True)
    def getRoute(self, _fromToken: Address, _toToken: Address) -> dict:
        """
        Gets the route used for converting token A to token B.

        :param _fromToken: Address of the token A
        :param _toToken: Address of token B
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

        :param _interval: Number of blocks
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

        :param _from: Token origination address
        :param _value: Number of tokens received
        :param _data: Unused, ignored
        """

        # Only one call to this method per external tx.
        if self._last_txhash.get() == self.tx.hash:
            return

        # Do nothing if not enough blocks has occured since last conversion for this token.
        if not self._timeForFeeProcessing(self.msg.sender):
            return
        else:
            self._last_txhash.set(self.tx.hash)

        # If token is accepted dividend token -> forward to dividends contract.
        if self.msg.sender in self._accepted_dividend_tokens:
            self._transferToken(self.msg.sender, self._getContractAddress("dividends"), self._getTokenBalance(self.msg.sender))
        
        # Else convert to baln and forward to dividends contract.
        else:
            try:
                # Raises JSONDecodeError if trying to decode an empty string.
                path = json_loads(self._routes[self.msg.sender][self._getContractAddress("baln")])
            except:
                path = []
                
            if path:
                # Use router.
                self._transferToken(self.msg.sender, self._getContractAddress("router"), 
                                    self._getTokenBalance(self.msg.sender), 
                                    self._createDataFieldRouter(self._getContractAddress("dividends"), path))
            else:
                # Use dex.
                self._transferToken(self.msg.sender, self._getContractAddress("dex"), self._getTokenBalance(self.msg.sender), 
                                    self._createDataFieldDex(self._getContractAddress("dividends")))

        # Set the block for this fee processing event.
        self._last_fee_processing_block[self.msg.sender] = self.block_height

    def _createDataFieldRouter(self, _receiver: Address, _path: list) -> bytes:
        """
        Constructs the data to pass to the router contract when making a swap.

        :param _receiver: Address to receive the funds when all swaps have completed
        :param _path: Path to use for the swap. List of addresses in string format
        """
        data = {
        'method': "_swap",
        'params': {
            'path': _path,
            'receiver': str(_receiver)
            }
        }
        data = json_dumps(data).encode()
        return data

    def _createDataFieldDex(self, _receiver: Address) -> bytes:
        """
        Constructs the data to pass to the dex contract when making a swap.

        :param _receiver: Address to receive the funds when all swaps have completed
        """
        data = {
            'method': "_swap",
            'params': {
                'receiver': str(_receiver)
            }   
        }
        data = json_dumps(data).encode()
        return data

    def _getContractAddress(self, _contract: str) -> Address:
        """
        Gets a contract address registered in the governance score.

        :param _contract: Name of the contract as specified in the governance contract
        """
        gov = self.create_interface_score(self._governance.get(), GovernanceInterface)
        return gov.getContractAddress(_contract)

    def _timeForFeeProcessing(self, _token: Address) -> bool:
        """
        Check if it's time to process all accumulated fees for the specified token.

        :param _token: Token address
        """
        last_conversion = self._last_fee_processing_block[_token]
        target_block = last_conversion + self._fee_processing_interval.get()

        if not last_conversion:
            return True
        elif self.block_height < target_block:
            return False
        else:
            return True

    def _getTokenBalance(self, _token: Address) -> int:
        token = self.create_interface_score(_token, IRC2Interface)
        return token.balanceOf(self.address)

    def _transferToken(self, _token: Address, _to: Address, _amount: int, _data = None) -> None:
        token = self.create_interface_score(_token, IRC2Interface)
        token.transfer(_to, _amount, _data)

# TODO
# Implement receiver/destination in exchange method in dex contract.  -> Done.
# Implement receiver/destination in _route method in router contract. -> Done.
# Direct origination fees to this contract.                           -> Done.
# Direct swapfees to this contract.                                   -> Done.
# Register feehandler score in governance contract.
# Unit tests for all methods.
# Add Admin functionality?
# (Make RouteDB. Cant use dumps with list of addresses.) ?