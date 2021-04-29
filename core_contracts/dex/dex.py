#### Balanced DEX is a open source software developed by balanced network #####
#### Forked from icon pool, developed from blockdevs.co #####
#### The content of this project itself is licensed under the Creative Commons Attribution 3.0 Unported license,  #####
#### and the underlying source code used to format and display that content is licensed under the GNU AGLPL license.  #####
##### Check the LICENSE file for more info #####

from .scorelib.iterable_dict import *
from .scorelib.linked_list import *
from .scorelib.utils import *
from .utils.checks import *
from .utils.consts import *
from .lp_metadata import *
from .utils.scoremath import *

TAG = 'Balanced DEX'


# An interface to the Rewards SCORE
class Rewards(InterfaceScore):
    @interface
    def distribute(self) -> bool:
        pass

    @interface
    def addNewDataSource(self, _data_source_name: str, _contract_address: Address) -> None:
        pass


# An interface to the Dividends SCORE


class Dividends(InterfaceScore):
    @interface
    def distribute(self) -> bool:
        pass


class stakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self):
        pass


class DEX(IconScoreBase):
    _ACCOUNT_BALANCE_SNAPSHOT = 'account_balance_snapshot'
    _TOTAL_SUPPLY_SNAPSHOT = 'total_supply_snapshot'
    _QUOTE_COINS = 'quote_coins'
    _ICX_QUEUE_TOTAL = 'icx_queue_total'
    _SICX_ADDRESS = 'sicx_address'
    _bnUSD_ADDRESS = 'bnUSD_address'
    _BALN_ADDRESS = 'baln_address'
    _STAKING_ADDRESS = 'staking_address'
    _DIVIDENDS_ADDRESS = 'dividends_address'
    _REWARDS_ADDRESS = 'rewards_address'
    _GOVERNANCE_ADDRESS = 'governance_address'
    _NAMED_MARKETS = 'named_markets'
    _ADMIN = 'admin'
    _DEX_ON = 'dex_on'
    _SICXICX_MARKET_NAME = 'sICX/ICX'
    _CURRENT_DAY = 'current_day'
    _TIME_OFFSET = 'time_offset'
    _REWARDS_DONE = 'rewards_done'
    _DIVIDENDS_DONE = 'dividends_done'
    _SICXICX_POOL_ID = 1

    ####################################
    # Events
    @eventlog(indexed=2)
    def Swap(self, _id: int, _baseToken: Address, _fromToken: Address, _toToken: Address,
             _sender: Address, _receiver: Address, _fromValue: int, _toValue: int,
             _timestamp: int, _lpFees: int, _balnFees: int, _poolBase: int,
             _poolQuote: int, _endingPrice: int, _effectiveFillPrice: int): pass

    @eventlog(indexed=3)
    def MarketAdded(self, _id: int, _baseToken: Address,
                    _quoteToken: Address, _baseValue: int, _quoteValue: int): pass

    @eventlog(indexed=3)
    def Add(self, _id: int, _owner: Address, _value: int, _base: int, _quote: int): pass

    @eventlog(indexed=3)
    def Remove(self, _id: int, _owner: Address, _value: int, _base: int, _quote: int): pass

    @eventlog(indexed=2)
    def Deposit(self, _token: Address, _owner: Address, _value: int): pass

    @eventlog(indexed=2)
    def Withdraw(self, _token: Address, _owner: Address, _value: int): pass

    @eventlog(indexed=2)
    def ClaimSicxEarnings(self, _owner: Address, _value: int): pass

    @eventlog(indexed=3)
    def TransferSingle(self, _operator: Address, _from: Address, _to: Address, _id: int, _value: int):
        """
        Must trigger on any successful token transfers, including zero value transfers as well as minting or burning.
        When minting/creating tokens, the `_from` must be set to zero address.
        When burning/destroying tokens, the `_to` must be set to zero address.

        :param _operator: the address of an account/contract that is approved to make the transfer
        :param _from: the address of the token holder whose balance is decreased
        :param _to: the address of the recipient whose balance is increased
        :param _id: ID of the token
        :param _value: the amount of transfer
        """

    @eventlog(indexed=2)
    def ApprovalForAll(self, _owner: Address, _operator: Address, _approved: bool):
        """
        Must trigger on any successful approval (either enabled or disabled) for a third party/operator address
        to manage all tokens for the `_owner` address.

        :param _owner: the address of the token holder
        :param _operator: the address of authorized operator
        :param _approved: true if the operator is approved, false to revoke approval
        """

    @eventlog(indexed=1)
    def URI(self, _id: int, _value: str):
        """
        Must trigger on any successful URI updates for a token ID.
        URIs are defined in RFC 3986.
        The URI MUST point to a JSON file that conforms to the "ERC-1155 Metadata URI JSON Schema".

        :param _id: ID of the token
        :param _value: the updated URI string
        """

    @eventlog(indexed=1)
    def Snapshot(self, _id: int):
        """
        Emitted as a new snapshot is generated.
        :param _id: ID of the snapshot.
        """

    ####################################
    # System
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

        # Linked Addresses
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._sicx = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._staking = VarDB(
            self._STAKING_ADDRESS, db, value_type=Address)
        self._dividends = VarDB(
            self._DIVIDENDS_ADDRESS, db, value_type=Address)
        self._governance = VarDB(
            self._GOVERNANCE_ADDRESS, db, value_type=Address)
        self._rewards = VarDB(
            self._REWARDS_ADDRESS, db, value_type=Address)
        self._bnUSD = VarDB(
            self._bnUSD_ADDRESS, db, value_type=Address)
        self._baln = VarDB(
            self._BALN_ADDRESS, db, value_type=Address)

        # DEX Activation (can be set by governance only)
        self._dex_on = VarDB(self._DEX_ON, db, value_type=bool)

        # deposited irc not locked in pool
        # deposit[TokenAddress][UserAddress] = intValue
        self._deposit = DictDB('deposit', db, value_type=int, depth=2)

        # PoolId
        # poolId[token1Address][token2Address] = nonce 1 to n
        self._pool_id = DictDB('poolId', db, value_type=int, depth=2)

        # Top Nonce count == n = (1,n) pools
        self._nonce = VarDB('nonce', db, value_type=int)

        # Total amount of tokens in pool
        # poolTotal[nonce][tokenAddress] = intAmount
        self._pool_total = DictDB('poolTotal', db, value_type=int, depth=2)

        # Total number of pool LP tokens
        # total[nonce] = intValue
        self._total = DictDB('poolLPTotal', db, value_type=int)

        # Balance of LP Tokens of nonce
        # balance[nonce][userAddress]
        self._balance = DictDB('balances', db, value_type=int, depth=2)

        # Pool Balance History for snapshots
        self._account_balance_snapshot = DictDB(
            self._ACCOUNT_BALANCE_SNAPSHOT, db, value_type=int, depth=4)
        self._total_supply_snapshot = DictDB(
            self._TOTAL_SUPPLY_SNAPSHOT, db, value_type=int, depth=3)

        # BALN token snapshot for use in dividends SCORE
        self._baln_snapshot = DictDB('balnSnapshot', db, value_type=int, depth=3)

        # Rewards/timekeeping logic
        self._current_day = VarDB(self._CURRENT_DAY, db, value_type=int)
        self._time_offset = VarDB(self._TIME_OFFSET, db, value_type=int)
        self._rewards_done = VarDB(self._REWARDS_DONE, db, value_type=bool)
        self._dividends_done = VarDB(self._DIVIDENDS_DONE, db, value_type=bool)

        self._active_addresses = LPMetadataDB(db)

        # Pools must use one of these as a quote currency
        self._quote_coins = SetDB(self._QUOTE_COINS, db, value_type=Address)

        # All fees are divided by `FEE_SCALE` in consts
        self._pool_lp_fee = VarDB('pool_lp_fee', db, value_type=int)
        self._pool_baln_fee = VarDB('pool_baln_fee', db, value_type=int)
        self._icx_conversion_fee = VarDB(
            'icx_conversion_fee', db, value_type=int)
        self._icx_baln_fee = VarDB('icx_baln_fee', db, value_type=int)

        # pid to tokens
        # poolTn[nonce] = tokenAddress
        self._pool_base = DictDB('baseToken', db, value_type=Address)
        self._pool_quote = DictDB('quoteToken', db, value_type=Address)
        # pid permissions
        # active[pool] = bool
        self.active = DictDB('activePool', db, value_type=bool)

        # Swap queue for sicxicx
        self._icx_queue = LinkedListDB(
            'icxQueue', db, value1_type=int, value2_type=Address)
        self._icx_queue_order_id = DictDB(
            'icxQueueOrderId', db, value_type=int)
        # Map (address => int)
        self._sicx_earnings = DictDB('sicxEarnings', db, value_type=int)

        # Total ICX Balance available for conversion
        self._icx_queue_total = VarDB(
            self._ICX_QUEUE_TOTAL, db, value_type=int)

        # Approvals for token transfers (map[grantor][grantee] = T/F)
        self._approvals = DictDB('approvals', db, value_type=bool, depth=2)

        self._named_markets = IterableDictDB(
            self._NAMED_MARKETS, db, value_type=int, key_type=str, order=True)

        self._markets_to_names = DictDB('marketsToNames', db, value_type=str)

        # Cache of token precisions, filled on first call of `deposit`
        self._token_precisions = DictDB('token_precisions', db, value_type=int)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)
        self._pool_lp_fee.set(15)
        self._pool_baln_fee.set(15)
        self._icx_conversion_fee.set(70)
        self._icx_baln_fee.set(30)
        # 0 = null PID
        # 1 = SICXICX Swap Queue
        # 2+ = pools
        self._nonce.set(2)
        self._current_day.set(1)
        self._named_markets[self._SICXICX_MARKET_NAME] = self._SICXICX_POOL_ID
        self._markets_to_names[self._SICXICX_POOL_ID] = self._SICXICX_MARKET_NAME

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
        self._quote_coins.add(_address)

    @only_admin
    @external
    def setDividends(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new Dividends address. Should be called before DEX use.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._dividends.set(_address)

    @external(readonly=True)
    def getDividends(self) -> Address:
        """
        Gets the address of the Dividends contract.
        """
        return self._dividends.get()

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

    @only_admin
    @external
    def setRewards(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new Rewards contract address. Should be called before dex use.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._rewards.set(_address)

    @external(readonly=True)
    def getRewards(self) -> Address:
        """
        Gets the address of the Rewards contract.
        """
        return self._rewards.get()

    @only_admin
    @external
    def setbnUSD(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new bnUSD contract address. Should be called before dex use.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._bnUSD.set(_address)
        self._quote_coins.add(_address)

    @external(readonly=True)
    def getbnUSD(self) -> Address:
        """
        Gets the address of the bnUSD contract.
        """
        return self._bnUSD.get()

    @only_admin
    @external
    def setBaln(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new BALN contract address. Should be called before dex use.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._baln.set(_address)

    @external(readonly=True)
    def getBaln(self) -> Address:
        """
        Gets the address of the BALN contract.
        """
        return self._baln.get()

    @only_governance
    @external
    def setMarketName(self, _id: int, _name: str) -> None:
        """
        :param _id: Pool ID to map to the name
        :param _name: Name to associate
        Links a pool ID to a name, so users can look up platform-defined
        markets more easily.
        """
        self._named_markets[_name] = _id
        self._markets_to_names[_id] = _name

    @only_governance
    @external
    def turnDexOn(self) -> None:
        """
        Called by the Governance contract to trigger the DEX to activate.
        """
        self._dex_on.set(True)

    @external(readonly=True)
    def getDexOn(self) -> bool:
        """
        Returns `True` if the DEX is currently active. Users cannot trade
        if the DEX is not yet active.
        """
        return self._dex_on.get()

    @only_governance
    @external
    def addQuoteCoin(self, _address: Address) -> None:
        """
        :param _address: Address of token to add as an allowed quote coin
        """
        self._quote_coins.add(_address)

    @external(readonly=True)
    def isQuoteCoinAllowed(self, _address: Address) -> bool:
        """
        :param _address: address of to check as allowable quote
        """
        return _address in self._quote_coins

    @external(readonly=True)
    def getDay(self) -> int:
        """
        Returns the current day (floored). Used for snapshotting,
        paying rewards, and paying dividends.
        """
        return (self.now() - self._time_offset.get()) // U_SECONDS_DAY

    @external
    @only_governance
    def setTimeOffset(self, _delta_time: int) -> None:
        """
        :param _delta_time: is timestamp offset from epoch.
        Sets the time offset from the governance contract. Used in
        internal timekeeping.
        """
        self._time_offset.set(_delta_time)

    @external(readonly=True)
    def getTimeOffset(self) -> int:
        """
        Returns current us timestamp offset.
        """
        return self._time_offset.get()

    @payable
    @dex_on
    def fallback(self):
        """
        Payable method called by sending ICX directly into the SCORE.
        This places it on the SICXICX swap queue, which is a one-sided
        orderbook to transact ICX for SICX.

        All orders are transacted at the SICXICX price as defined by
        the staking contract. Users selling SICX will pay a 1% fee,
        split 0.7% to the buyer and 0.3% to balanced token holders.

        SICX buyers (ICX sellers calling this payable method) receive
        time precedence in the queue based on the time that their order
        was submitted. A user may have a single order in the queue at
        one time. Sending additional ICX will increase the order size,
        and shift it to the back of the queue.

        Each time an order is placed or increased, it cannot be changed
        for 24 hours. Order placement updates the snapshots of the queue.
        """
        self._take_new_day_snapshot()
        self._check_distributions()

        self._revert_on_incomplete_rewards()

        if self.msg.value < 10 * EXA:
            revert(f"{TAG}: Minimum pool contribution is 10 ICX.")

        order_id = self._icx_queue_order_id[self.msg.sender]
        order_value = self.msg.value

        if order_id:
            # TODO: Modify instead of cancel/replace, after debugging scorelib
            node = self._icx_queue._get_node(order_id)
            order_value += node.get_value1()
            self._icx_queue.remove(order_id)

        order_id = self._icx_queue.append(order_value, self.msg.sender)
        self._icx_queue_order_id[self.msg.sender] = order_id

        current_icx_total = self._icx_queue_total.get() + self.msg.value
        self._icx_queue_total.set(current_icx_total)

        if order_value >= self._get_rewardable_amount(None):
            self._active_addresses[self._SICXICX_POOL_ID].add(self.msg.sender)

        self._update_account_snapshot(self.msg.sender, self._SICXICX_POOL_ID)
        self._update_total_supply_snapshot(self._SICXICX_POOL_ID)

    @dex_on
    @external
    def cancelSicxicxOrder(self):
        """
        Cancels user's order in the sICX/ICX queue.
        Cannot be called within 24h of the last place/modify time.

        Order cancellation updates the snapshots of the queue.
        """
        self._take_new_day_snapshot()
        self._check_distributions()

        self._revert_on_incomplete_rewards()

        if not self._icx_queue_order_id[self.msg.sender]:
            revert(f"{TAG}: No open order in sICX/ICX queue.")

        order_id = self._icx_queue_order_id[self.msg.sender]
        order = self._icx_queue._get_node(order_id)
        withdraw_amount = order.get_value1()

        current_icx_total = self._icx_queue_total.get() - withdraw_amount
        self._icx_queue_total.set(current_icx_total)

        self._icx_queue.remove(order_id)
        del self._icx_queue_order_id[self.msg.sender]

        self.icx.transfer(self.msg.sender, withdraw_amount)

        self._active_addresses[self._SICXICX_POOL_ID].remove(self.msg.sender)

        self._update_account_snapshot(self.msg.sender, self._SICXICX_POOL_ID)
        self._update_total_supply_snapshot(self._SICXICX_POOL_ID)

    @dex_on
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
        # if user sends some irc token to score
        Logger.info("called token fallback", TAG)

        # Update snapshots if necessary and notify the rewards score
        self._take_new_day_snapshot()
        self._check_distributions()

        unpacked_data = json_loads(_data.decode('utf-8'))
        _fromToken = self.msg.sender

        if unpacked_data["method"] == "_deposit":
            self._deposit[_fromToken][_from] += _value
            self.Deposit(_fromToken, _from, _value)

            if _fromToken not in self._token_precisions:
                from_token_score = self.create_interface_score(_fromToken, TokenInterface)
                self._token_precisions[_fromToken] = from_token_score.decimals()

        elif unpacked_data["method"] == "_swap_icx":
            if _fromToken == self._sicx.get():
                self._swap_icx(_from, _value)
            else:
                revert(f"{TAG}: InvalidAsset: _swap_icx can only be called with sICX")

        elif unpacked_data["method"] == "_swap":
            minimum_receive = 0

            if "minimumReceive" in unpacked_data["params"]:
                minimum_receive = int(unpacked_data["params"]["minimumReceive"])

                if minimum_receive < 0:
                    revert(f"{TAG}: Must specify a positive number for minimum to receive")

            self.exchange(_fromToken, Address.from_string(
                unpacked_data["params"]["toToken"]), _from, _from, _value, minimum_receive)

        else:
            revert(f"{TAG}: Fallback directly not allowed.")

    @external
    def precompute(self, snap: int, batch_size: int) -> bool:
        """
        Required by the rewards score data source API, but unused.
        Returns `True` to match the required workflow.
        """
        return True

    @dex_on
    @external
    def transfer(self, _to: Address, _value: int, _id: int, _data: bytes = None):
        """
        Used to transfer LP tokens from sender to another address.
        Calls the internal method `_transfer()` with a default
        `_data` if none is submitted.

        :param _to: Address to transfer to
        :param _value: Amount of units to transfer
        :param _id: Pool ID of token to transfer
        :param _data: data to include with transfer
        """
        revert(f"{TAG}: MethodDisabled: This method has been temporarily disabled")

        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _id, _data)

    def _transfer(self, _from: Address, _to: Address, _value: int, _id: int, _data: bytes):
        """
        Used to transfer LP IRC-31 tokens from one address to another.
        Invoked by `transfer(...)`.
        """
        if _value < 0:
            revert(f"{TAG}: Transferring value cannot be less than 0.")
        if self._balance[_id][_from] < _value:
            revert(f"{TAG}: Out of balance.")

        self._balance[_id][_from] -= _value
        self._balance[_id][_to] += _value

        self.TransferSingle(self.msg.sender, _from, _to, _id, _value)

        self._update_account_snapshot(_from, _id)
        self._update_account_snapshot(_to, _id)

        pool_quote_coin = self.getPoolQuote(_id)

        if self._balance[_id][_to] >= self._get_rewardable_amount(pool_quote_coin):
            self._active_addresses[_id].add(_to)

        if self._balance[_id][_from] < self._get_rewardable_amount(pool_quote_coin):
            self._active_addresses[_id].remove(_from)

        # TODO: Implement token fallback for multi-token score

    ####################################
    # Read
    @external(readonly=True)
    def getDeposit(self, _tokenAddress: Address, _user: Address) -> int:
        """
        Returns the amount of tokens of address `_tokenAddress` that a
        user with Address `_user` has on deposit. Tokens currently
        committed to a LP pool are excluded.

        :param _tokenAddress: IIC2 token to check balance of
        :param _user: User address to check balance of
        """
        return self._deposit[_tokenAddress][_user]

    @external(readonly=True)
    def getSicxEarnings(self, _user: Address) -> int:
        """
        Returns sICX earnings from the ICX queue

        :param _user: User address to check balance of
        """
        return self._sicx_earnings[_user]


    @external(readonly=True)
    def getPoolId(self, _token1Address: Address, _token2Address: Address) -> int:
        """
        Returns the pool ID mapped to this token pair. The following holds:
        ```
        getPoolId(A, B) == getPoolID(B,A)
        ```
        """
        return self._pool_id[_token1Address][_token2Address]

    @external(readonly=True)
    def getNonce(self) -> int:
        """
        Returns the current nonce nonce of liquidity provider pools.
        This is a monotonically increasing value.
        """
        return self._nonce.get()

    @external(readonly=True)
    def getNamedPools(self) -> list:
        """
        Returns a list of all named pools in the contract, set by the admin.
        These pools are used by:
        1) The `rewards` score when calling `getDataBatch(...)`
        2) Users who want to lookup a pool id using `lookupPid(...)`
        """
        rv = []
        for pool in self._named_markets.keys():
            rv.append(pool)
        return rv

    @external(readonly=True)
    def lookupPid(self, _name: str) -> int:
        return self._named_markets[_name]

    @external(readonly=True)
    def getPoolTotal(self, _id: int, _token: Address) -> int:
        return self._pool_total[_id][_token]

    @external(readonly=True)
    def totalSupply(self, _id: int) -> int:
        if _id == self._SICXICX_POOL_ID:
            return self._icx_queue_total.get()
        return self._total[_id]

    @external(readonly=True)
    def balanceOf(self, _owner: Address, _id: int) -> int:
        """
        Returns the balance of the owner's tokens.
        NOTE: ID 0 will return SICXICX balance
        :param _owner: the address of the token holder
        :param _id: ID of the token/pool
        :return: the _owner's balance of the token type requested
        """
        if _id == self._SICXICX_POOL_ID:
            order_id = self._icx_queue_order_id[self.msg.sender]
            if not order_id:
                return 0
            return self._icx_queue._get_node(order_id).get_value1()
        else:
            return self._balance[_id][_owner]

    @external(readonly=True)
    def getFees(self) -> dict:
        """
        Gets fees on the balanced platform. There are presently 4 fees:
        - `icx_conversion_fee` - This goes to the ICX holder in SICXICX
        - `icx_baln_fee` - This is the fee on SICXICX trades that goes to BALN holders
        - `pool_lp_fee` - This is the fee on pool fees that go to the LPs
        - `pool_baln_fee` -  This is the fee on pool trades that goes BALN holders

        All fees are divided by the `FEE_SCALE` constant
        """

        icx_baln_fee = self._icx_baln_fee.get()
        icx_conversion_fee = self._icx_conversion_fee.get()
        pool_baln_fee = self._pool_baln_fee.get()
        pool_ip_fee = self._pool_lp_fee.get()

        return {
            'icx_total': icx_baln_fee + icx_conversion_fee,
            'pool_total': pool_baln_fee + pool_ip_fee,
            'pool_lp_fee': pool_ip_fee,
            'pool_baln_fee': pool_baln_fee,
            'icx_conversion_fee': icx_conversion_fee,
            'icx_baln_fee': icx_baln_fee
        }

    @external(readonly=True)
    def getPoolBase(self, _id: int) -> Address:
        return self._pool_base[_id]

    @external(readonly=True)
    def getPoolQuote(self, _id: int) -> Address:
        return self._pool_quote[_id]

    @external(readonly=True)
    def getQuotePriceInBase(self, _id: int) -> int:
        """
        e.g. USD/BTC, this is the inverse of the most common way to express price.
        """
        if self._nonce.get() < _id < 1:
            revert(f"{TAG}: Invalid pool id.")

        if _id == self._SICXICX_POOL_ID:
            return EXA * EXA // self._get_sicx_rate()

        return (self._pool_total[_id][self._pool_base[_id]] * EXA) // self._pool_total[_id][self._pool_quote[_id]]

    @external(readonly=True)
    def getBasePriceInQuote(self, _id: int) -> int:
        """
        e.g. BTC/USD, this is the most common way to express price.
        """
        if self._nonce.get() < _id < 1:
            revert(f"{TAG}: Invalid pool id.")

        if _id == self._SICXICX_POOL_ID:
            return self._get_sicx_rate()

        return (self._pool_total[_id][self._pool_quote[_id]] * EXA) // self._pool_total[_id][self._pool_base[_id]]

    @external(readonly=True)
    def getPrice(self, _id: int) -> int:
        """
        This method is an alias to the most common form of price.
        """
        return self.getBasePriceInQuote(_id)

    @external(readonly=True)
    def getBalnPrice(self) -> int:
        """
        This method is an alias to the current price of BALN tokens
        """
        return self.getBasePriceInQuote(self._pool_id[self._baln.get()][self._bnUSD.get()])

    @external(readonly=True)
    def getSicxBnusdPrice(self) -> int:
        """
        This method is an alias to the current price of sICX tokens in bnUSD
        """
        return self.getBasePriceInQuote(self._pool_id[self._sicx.get()][self._bnUSD.get()])

    @external(readonly=True)
    def getBnusdValue(self, _name: str) -> int:
        """
        Gets the approximate bnUSD value of a pool.
        :param _name: name
        """
        _id = self._named_markets[_name]

        if _id == self._SICXICX_POOL_ID:
            icx_total = self._icx_queue_total.get()
            return icx_total * self.getSicxBnusdPrice() // self._get_sicx_rate()
        elif self._pool_quote[_id] == self._sicx.get():
            sicx_total =  self._pool_total[_id][self._sicx.get()] * 2
            return self.getSicxBnusdPrice() * sicx_total
        elif self._pool_quote[_id] == self._bnUSD.get():
            return self._pool_total[_id][self._bnUSD.get()] * 2
        else:
            # No support for arbitrary pathing yet
            return 0

    @external(readonly=True)
    def getPriceByName(self, _name: str) -> int:
        return self.getPrice(self._named_markets[_name])

    @external(readonly=True)
    def getICXBalance(self, _address: Address) -> int:
        order_id = self._icx_queue_order_id[_address]
        if not order_id:
            return 0
        return self._icx_queue._get_node(order_id).get_value1()

    @external(readonly=True)
    def getPoolStats(self, _id: int) -> dict:

        if self._nonce.get() < _id < 1:
            return {TAG: "Invalid pool id."}

        if _id == self._SICXICX_POOL_ID:
            return {
                'base_token': self._sicx.get(),
                'quote_token': None,
                'base': 0,
                'quote': self._icx_queue_total.get(),
                'total_supply': self._icx_queue_total.get(),
                'price': self.getPrice(_id),
                'name': self._SICXICX_MARKET_NAME
            }

        else:
            base_token = self._pool_base[_id]
            quote_token = self._pool_quote[_id]
            name = self._markets_to_names[_id] if _id in self._markets_to_names else None

            return {
                'base': self._pool_total[_id][base_token],
                'quote': self._pool_total[_id][quote_token],
                'base_token': base_token,
                'quote_token': quote_token,
                'total_supply': self._total[_id],
                'price': self.getPrice(_id),
                'name': name
            }

    ####################################
    # Token Functionality

    @dex_on
    @external
    def setApprovalForAll(self, _operator: Address, _approved: bool):
        """
        Enables or disables approval for a third party ("operator") to manage all of the caller's tokens,
        and must emit `ApprovalForAll` event on success.

        :param _operator: address to add to the set of authorized operators
        :param _approved: true if the operator is approved, false to revoke approval
        """
        revert(f"{TAG}: MethodDisabled: This method has been temporarily disabled")

        self._approvals[self.msg.sender][_operator] = _approved
        self.ApprovalForAll(self.msg.sender, _operator, _approved)

    @external(readonly=True)
    def isApprovedForAll(self, _owner: Address, _operator: Address) -> bool:
        """
        Returns the approval status of an operator for a given owner.

        :param _owner: the owner of the tokens
        :param _operator: the address of authorized operator
        :return: true if the operator is approved, false otherwise
        """
        if self._approvals[_owner][_operator]:
            return self._approvals[_owner][_operator]
        else:
            return False

    @dex_on
    @external
    def transferFrom(self, _from: Address, _to: Address, _id: int, _value: int, _data: bytes = None):
        """
        Transfers `_value` amount of an token `_id` from one address to another address,
        and must emit `TransferSingle` event to reflect the balance change.
        When the transfer is complete, this method must invoke `onIRC31Received(Address,Address,int,int,bytes)` in `_to`,
        if `_to` is a contract. If the `onIRC31Received` method is not implemented in `_to` (receiver contract),
        then the transaction must fail and the transfer of tokens should not occur.
        If `_to` is an externally owned address, then the transaction must be sent without trying to execute
        `onIRC31Received` in `_to`.
        Additional `_data` can be attached to this token transaction, and it should be sent unaltered in call
        to `onIRC31Received` in `_to`. `_data` can be empty.
        Throws unless the caller is the current token holder or the approved address for the token ID.
        Throws if `_from` does not have enough amount to transfer for the token ID.

        :param _from: source address
        :param _to: target address
        :param _id: ID of the token
        :param _value: the amount of transfer
        :param _data: additional data that should be sent unaltered in call to `_to`
        """
        revert(f"{TAG}: MethodDisabled: This method has been temporarily disabled")

        if _data is None:
            _data = b'None'
        self._transfer_from(_from, _to, _id, _value, _data)

    def _transfer_from(self, _from: Address, _to: Address, _id: int, _value: int, _data: bytes):
        if not self.isApprovedForAll(_from, self.msg.sender):
            revert(f"{TAG}: Not approved for transfer.")
        if _value < 0:
            revert(f"{TAG}: Transferring value cannot be less than 0.")
        if self._balance[_id][_from] < _value:
            revert(f"{TAG}: Out of balance.")

        self._balance[_id][_from] -= _value
        self._balance[_id][_to] += _value
        self.TransferSingle(self.msg.sender, _from, _to, _id, _value)

        pool_quote_coin = self.getPoolQuote(_id)

        if self._balance[_id][_to] >= self._get_rewardable_amount(pool_quote_coin):
            self._active_addresses[_id].add(_to)

        if self._balance[_id][_from] < self._get_rewardable_amount(pool_quote_coin):
            self._active_addresses[_id].remove(_from)

        self._update_account_snapshot(_from, _id)
        self._update_account_snapshot(_to, _id)

        # TODO: Implement onIRC31Received function

    @external(readonly=True)
    def isEarningRewards(self, _address: Address, _id: int) -> bool:
        """
        Returns whether an address is currently eligible to earn rewards.

        :param _address: Address to check
        :param _id: PoolId
        """
        return _address in self._active_addresses[_id]

    @external(readonly=True)
    def totalDexAddresses(self, _id: int) -> int:
        """
        Returns total number of users that have used the dex.
        """
        return len(self._active_addresses[_id])

    def _get_exchange_rate(self) -> int:
        """
        Internal function for use in SICXICX pools.
        Gets the current exchange rate (expressed in units 1 = 1e18).
        Requires that the _staking_address property is set via the contract admin.
        """
        staking_score = self.create_interface_score(
            self._staking.get(), stakingInterface)
        return staking_score.getTodayRate()

    def _revert_on_incomplete_rewards(self):
        """
        Until the cursor release of Balanced is complete, this is a stop-gap
        function that prevents contract lockup.
        """
        if not self._rewards_done.get():
            revert(f"{TAG} Rewards distribution in progress, please try again shortly")

    ####################################
    # Internal exchange function

    def exchange(self, _fromToken: Address, _toToken: Address, _sender: Address, _receiver: Address, _value: int, _minimum_receive: int = 0):

        # All fees are scaled to FEE_SCALE
        lp_fees = (_value * self._pool_lp_fee.get()) // FEE_SCALE
        baln_fees = (_value * self._pool_baln_fee.get()) // FEE_SCALE
        fees = lp_fees + baln_fees

        original_value = _value
        _value -= fees

        is_sell = False

        _id = self._pool_id[_fromToken][_toToken]

        if _id <= 0:
            revert(f"{TAG}: Pool does not exist.")

        if _id == self._SICXICX_POOL_ID:
            revert(f"{TAG}: Not supported on this API, use the ICX swap API.")

        if _fromToken == self.getPoolBase(_id):
            is_sell = True

        if not self.active[_id]:
            revert(f"{TAG}: Pool is not active.")

        new_token1 = self._pool_total[_id][_fromToken] + _value

        new_token2 = int(
            self._pool_total[_id][_fromToken] * self._pool_total[_id][_toToken] / new_token1)

        send_amt = self._pool_total[_id][_toToken] - new_token2

        if send_amt < _minimum_receive:
            revert(f"{TAG}: MinimumReceiveError: Receive amount {send_amt} below supplied minimum")

        new_token1 += lp_fees

        self._pool_total[_id][_fromToken] = new_token1
        self._pool_total[_id][_toToken] = new_token2

        total_base = new_token1 if is_sell else new_token2
        total_quote = new_token2 if is_sell else new_token1

        send_price = (EXA * _value) // send_amt

        # Send the trader their funds
        to_token_score = self.create_interface_score(_toToken, TokenInterface)
        to_token_score.transfer(_receiver, send_amt)

        # Send the dividends share to the dividends SCORE
        from_token_score = self.create_interface_score(
            _fromToken, TokenInterface)
        from_token_score.transfer(self._dividends.get(), baln_fees)

        # Broadcast pool ending price
        ending_price = self.getPrice(_id)
        effective_fill_price = send_price
        if not is_sell:
            effective_fill_price = (EXA * send_amt) // _value

        if (_fromToken == self._baln.get()) or (_toToken == self._baln.get()):
            self._update_baln_snapshot(_id)

        self.Swap(_id, self._pool_base[_id], _fromToken, _toToken, _sender,
                  _receiver, original_value, send_amt, self.now(), lp_fees,
                  baln_fees, total_base, total_quote, ending_price, effective_fill_price)

    def _get_sicx_rate(self) -> int:
        staking_score = self.create_interface_score(
            self._staking.get(), stakingInterface)
        return staking_score.getTodayRate()

    def _get_rewardable_amount(self, _token_address: Address = None) -> int:
        """
        Gets the minimum rewardable amount for a given coin.
        Assumes that the pool is balanced, so the price at time of insert is the real price.
        This won't be sensitive to 'impermanent losses', so use at your own risk.

        :param _token_address: Token SCORE to check (None = ICX)
        """
        if self._sicx == _token_address:
            return (50 * EXA * EXA) // self._get_sicx_rate()
        elif self._bnUSD == _token_address:
            return 25 * EXA
        elif None == _token_address:
            return 50 * EXA
        elif _token_address in self._token_precisions:
            # default to 25 units of precision 1, if we have the coin on deposit
            return 25 * (10 ** self._token_precisions[_token_address])
        else:
            # Fallback to 18 digits of precision
            return 25 * EXA

    def _swap_icx(self, _sender: Address, _value: int):
        """
        Perform an instant conversion from SICX to ICX.
        Gets orders from SICXICX queue by price time precedence.
        """
        self._revert_on_incomplete_rewards()

        # Amount of ICX in one unit sICX
        sicx_icx_price = self._get_sicx_rate()

        sicx_score = self.create_interface_score(
            self._sicx.get(), TokenInterface)

        # subtract out fees to LPs
        baln_fees = _value * self._icx_baln_fee.get() // FEE_SCALE
        conversion_fees = _value * self._icx_conversion_fee.get() // FEE_SCALE

        # effective initial order size. We check the ICX price of order after fees.
        order_size = _value - (baln_fees + conversion_fees)
        order_icx_value = order_size * sicx_icx_price // EXA

        # ICX LPs earn a proportionate amount of order + fees
        lp_sicx_size = order_size + conversion_fees

        if order_icx_value > self._icx_queue_total.get():
            revert(f"{TAG}: InsufficientLiquidityError: Not enough ICX suppliers.")

        # Start order at order_icx_value, fill against queue until none remaining
        filled = False
        order_remaining_icx = order_icx_value

        iterations = 0

        # Tune this to maximum available on the ICON chain
        while not filled:

            iterations += 1

            if (len(self._icx_queue) == 0) or iterations > ICX_QUEUE_FILL_DEPTH:
                revert(f"{TAG}: InsufficientLiquidityError: Unable to fill {order_remaining_icx} ICX.")

            # Get next order from the queue
            counterparty_order = self._icx_queue._get_head_node()
            counterparty_address = counterparty_order.get_value2()
            counterparty_icx = counterparty_order.get_value1()
            counterparty_filled = False


            # Perform match. Matched amount is up to order size
            matched_icx = min(counterparty_icx, order_remaining_icx)
            order_remaining_icx -= matched_icx

            # Check for a full fill of the order
            if matched_icx == counterparty_icx:
                counterparty_filled = True

            # Counterparty earns a proportional amount of order + fees (lp_sicx_size)
            lp_sicx_earnings = lp_sicx_size * matched_icx // order_icx_value
            self._sicx_earnings[counterparty_address] += lp_sicx_earnings

            if counterparty_filled:
                self._icx_queue.remove_head()
                del self._icx_queue_order_id[counterparty_address]
                self._active_addresses[self._SICXICX_POOL_ID].remove(counterparty_address)

            else:
                new_counterparty_value = counterparty_order.get_value1() - matched_icx
                counterparty_order.set_value1(new_counterparty_value)

                if new_counterparty_value < self._get_rewardable_amount(None):
                    self._active_addresses[self._SICXICX_POOL_ID].remove(counterparty_address)

            self._update_account_snapshot(counterparty_address, self._SICXICX_POOL_ID)

            # If no more remaining ICX, the order is fully filled
            if not order_remaining_icx:
                filled = True

        # Subtract the filled ICX from the queue
        self._icx_queue_total.set(self._icx_queue_total.get() - order_icx_value)
        self._update_total_supply_snapshot(self._SICXICX_POOL_ID)

        # Settle fees to dividends and ICX converted to the sender
        sicx_score.transfer(self._dividends.get(), baln_fees)
        self.icx.transfer(_sender, order_icx_value)

    # Snapshotting
    def _take_new_day_snapshot(self) -> None:
        day = self.getDay()
        if day > self._current_day.get():
            self._current_day.set(day)
            self.Snapshot(day)
            self._rewards_done.set(False)
            if day % 7 == 0:
                self._dividends_done.set(False)

    def _check_distributions(self) -> None:
        if not self._rewards_done.get():
            rewards = self.create_interface_score(self._rewards.get(), Rewards)
            self._rewards_done.set(rewards.distribute())
        elif not self._dividends_done.get():
            dividends = self.create_interface_score(
                self._dividends.get(), Dividends)
            self._dividends_done.set(dividends.distribute())

    @external(readonly=True)
    def inspectBalanceSnapshot(self, _account: Address, _id: int, _snapshot_id: int) -> dict:
        return {
            'ids': self._account_balance_snapshot[_id][_account]['ids'][_snapshot_id],
            'values': self._account_balance_snapshot[_id][_account]['values'][_snapshot_id],
            'avgs': self._account_balance_snapshot[_id][_account]['avgs'][_snapshot_id],
            'time': self._account_balance_snapshot[_id][_account]['time'][_snapshot_id],
            'length': self._account_balance_snapshot[_id][_account]['length'][0]
        }

    def _update_account_snapshot(self, _account: Address, _id: int) -> None:
        """
        Updates a user's balance 24h avg snapshot

        :param _account: Address to update
        :param _id: pool id to update

        Note that an average contains 3 fields for each snapshot:
        1. the current value
        2. The weighted average up to that time, for the given window
        3. The timestamp of the last update

        The average value holds the expected average at the end of the day,
        if nothing else changes
        """
        current_id = self._current_day.get()
        current_time = self.now()
        current_value = self.balanceOf(_account, _id)

        length = self._account_balance_snapshot[_id][_account]['length'][0]
        last_snapshot_id = 0

        day_start_us = self._time_offset.get() + (U_SECONDS_DAY * current_id)
        day_elapsed_us = current_time - day_start_us
        day_remaining_us = U_SECONDS_DAY - day_elapsed_us

        if length == 0:
            average = (current_value * day_remaining_us) // U_SECONDS_DAY

            self._account_balance_snapshot[_id][_account]['ids'][length] = current_id
            self._account_balance_snapshot[_id][_account]['values'][length] = current_value
            self._account_balance_snapshot[_id][_account]['avgs'][length] = average
            self._account_balance_snapshot[_id][_account]['time'][length] = current_time
            self._account_balance_snapshot[_id][_account]['length'][0] += 1
            return
        else:
            last_snapshot_id = self._account_balance_snapshot[_id][_account]['ids'][length - 1]

        # If there is a snapshot existing, it either falls before or in the current window.
        if last_snapshot_id < current_id:
            # If the snapshot is before the current window, we should create a new entry
            previous_value = self._account_balance_snapshot[_id][_account]['values'][length - 1]

            average = ((day_elapsed_us * previous_value) + (day_remaining_us * current_value)) // U_SECONDS_DAY

            self._account_balance_snapshot[_id][_account]['ids'][length] = current_id
            self._account_balance_snapshot[_id][_account]['values'][length] = current_value
            self._account_balance_snapshot[_id][_account]['avgs'][length] = average
            self._account_balance_snapshot[_id][_account]['time'][length] = current_time
            self._account_balance_snapshot[_id][_account]['length'][0] += 1
        else:
            # If the snapshot is in the current window, we should update the current entry
            previous_average = self._account_balance_snapshot[_id][_account]['avgs'][length - 1]

            average = ((previous_average * day_elapsed_us) + (current_value * day_remaining_us)) // U_SECONDS_DAY

            self._account_balance_snapshot[_id][_account]['values'][length - 1] = current_value
            self._account_balance_snapshot[_id][_account]['avgs'][length - 1] = average
            self._account_balance_snapshot[_id][_account]['time'][length - 1] = current_time

    def _update_baln_snapshot(self, _id: int) -> None:
        """
        The application tracks the amount of BALN in particular pools,
        in order to give awards. At the time of launch, it will be
        BALN/bnUSD as the tracked pool.

        :param _id: pool id to update

        TODO: This better, it is a last minute requirement.
        """
        current_id = self._current_day.get()
        current_time = self.now()
        current_value = self._pool_total[_id][self._baln.get()]
        length = self._baln_snapshot[_id]['length'][0]
        last_snapshot_id = 0

        day_start_us = self._time_offset.get() + (U_SECONDS_DAY * current_id)
        day_elapsed_us = current_time - day_start_us
        day_remaining_us = U_SECONDS_DAY - day_elapsed_us

        if length == 0:
            average = (current_value * day_remaining_us) // U_SECONDS_DAY

            self._baln_snapshot[_id]['ids'][length] = current_id
            self._baln_snapshot[_id]['values'][length] = current_value
            self._baln_snapshot[_id]['avgs'][length] = average
            self._baln_snapshot[_id]['time'][length] = current_time
            self._baln_snapshot[_id]['length'][0] += 1
            return
        else:
            last_snapshot_id = self._baln_snapshot[_id]['ids'][length - 1]

        # If there is a snapshot existing, it either falls before or in the current window.
        if last_snapshot_id < current_id:
            # If the snapshot is before the current window, we should create a new entry
            previous_value = self._baln_snapshot[_id]['values'][length - 1]

            average = ((day_elapsed_us * previous_value) + (day_remaining_us * current_value)) // U_SECONDS_DAY

            self._baln_snapshot[_id]['ids'][length] = current_id
            self._baln_snapshot[_id]['values'][length] = current_value
            self._baln_snapshot[_id]['avgs'][length] = average
            self._baln_snapshot[_id]['time'][length] = current_time

            self._baln_snapshot[_id]['length'][0] += 1
        else:
            # If the snapshot is in the current window, we should update the current entry
            previous_average = self._baln_snapshot[_id]['avgs'][length - 1]

            average = ((previous_average * day_elapsed_us) + (current_value * day_remaining_us)) // U_SECONDS_DAY

            self._baln_snapshot[_id]['values'][length - 1] = current_value
            self._baln_snapshot[_id]['avgs'][length - 1] = average
            self._baln_snapshot[_id]['time'][length - 1] = current_time

    def _update_total_supply_snapshot(self, _id: int) -> None:
        """
        Updates an asset's 24h avg total supply snapshot

        :param _id: pool id to update
        """
        current_id = self._current_day.get()
        current_time = self.now()
        current_value = self.totalSupply(_id)
        length = self._total_supply_snapshot[_id]['length'][0]
        last_snapshot_id = 0

        day_start_us = self._time_offset.get() + (U_SECONDS_DAY * current_id)
        day_elapsed_us = current_time - day_start_us
        day_remaining_us = U_SECONDS_DAY - day_elapsed_us

        if length == 0:
            average = (current_value * day_remaining_us) // U_SECONDS_DAY

            self._total_supply_snapshot[_id]['ids'][length] = current_id
            self._total_supply_snapshot[_id]['values'][length] = current_value
            self._total_supply_snapshot[_id]['avgs'][length] = average
            self._total_supply_snapshot[_id]['time'][length] = current_time
            self._total_supply_snapshot[_id]['length'][0] += 1
            return
        else:
            last_snapshot_id = self._total_supply_snapshot[_id]['ids'][length - 1]

        # If there is a snapshot existing, it either falls before or in the current window.
        if last_snapshot_id < current_id:
            # If the snapshot is before the current window, we should create a new entry
            previous_value = self._total_supply_snapshot[_id]['values'][length - 1]

            average = ((day_elapsed_us * previous_value) + (day_remaining_us * current_value)) // U_SECONDS_DAY

            self._total_supply_snapshot[_id]['ids'][length] = current_id
            self._total_supply_snapshot[_id]['values'][length] = current_value
            self._total_supply_snapshot[_id]['avgs'][length] = average
            self._total_supply_snapshot[_id]['time'][length] = current_time

            self._total_supply_snapshot[_id]['length'][0] += 1
        else:
            # If the snapshot is in the current window, we should update the current entry
            previous_average = self._total_supply_snapshot[_id]['avgs'][length - 1]

            average = ((previous_average * day_elapsed_us) + (current_value * day_remaining_us)) // U_SECONDS_DAY

            self._total_supply_snapshot[_id]['values'][length - 1] = current_value
            self._total_supply_snapshot[_id]['avgs'][length - 1] = average
            self._total_supply_snapshot[_id]['time'][length - 1] = current_time

    @external(readonly=True)
    def balanceOfAt(self, _account: Address, _id: int, _snapshot_id: int) -> int:
        matched_index = 0
        if _snapshot_id < 0:
            revert(f"{TAG}: Snapshot id is equal to or greater then Zero.")
        low = 0
        high = self._account_balance_snapshot[_id][_account]['length'][0]

        while low < high:
            mid = (low + high) // 2
            if self._account_balance_snapshot[_id][_account]['ids'][mid] > _snapshot_id:
                high = mid
            else:
                low = mid + 1

        if self._account_balance_snapshot[_id][_account]['ids'][0] == _snapshot_id:
            # If the most recent snapshot is the requested snapshot, return the last average
            return self._account_balance_snapshot[_id][_account]['avgs'][0]
        elif low == 0:
            return 0
        else:
            matched_index = low - 1

        # If we matched the day before, weighted avg will be same as ending value.
        # If we matched the day of, return the actual weighted average
        if self._account_balance_snapshot[_id][_account]['ids'][matched_index] == _snapshot_id:
            return self._account_balance_snapshot[_id][_account]['avgs'][matched_index]
        else:
            return self._account_balance_snapshot[_id][_account]['values'][matched_index]

    @external(readonly=True)
    def totalSupplyAt(self, _id: int, _snapshot_id: int) -> int:
        matched_index = 0
        if _snapshot_id < 0:
            revert(f"{TAG}: Snapshot id is equal to or greater then Zero.")
        low = 0
        high = self._total_supply_snapshot[_id]['length'][0]

        while low < high:
            mid = (low + high) // 2
            if self._total_supply_snapshot[_id]['ids'][mid] > _snapshot_id:
                high = mid
            else:
                low = mid + 1

        if self._total_supply_snapshot[_id]['ids'][0] == _snapshot_id:
            return self._total_supply_snapshot[_id]['avgs'][0]
        elif low == 0:
            return 0
        else:
            matched_index = low - 1

        if self._total_supply_snapshot[_id]['ids'][matched_index] == _snapshot_id:
            return self._total_supply_snapshot[_id]['avgs'][matched_index]
        else:
            return self._total_supply_snapshot[_id]['values'][matched_index]

    @external(readonly=True)
    def totalBalnAt(self, _id: int, _snapshot_id: int) -> int:
        matched_index = 0
        if _snapshot_id < 0:
            revert(f'Snapshot id is equal to or greater then Zero')
        low = 0
        high = self._baln_snapshot[_id]['length'][0]

        while low < high:
            mid = (low + high) // 2
            if self._baln_snapshot[_id]['ids'][mid] > _snapshot_id:
                high = mid
            else:
                low = mid + 1

        if self._baln_snapshot[_id]['ids'][0] == _snapshot_id:
            return self._baln_snapshot[_id]['avgs'][0]
        elif low == 0:
            return 0
        else:
            matched_index = low - 1

        if self._baln_snapshot[_id]['ids'][matched_index] == _snapshot_id:
            return self._baln_snapshot[_id]['avgs'][matched_index]
        else:
            return self._baln_snapshot[_id]['values'][matched_index]


    @external(readonly=True)
    def getTotalValue(self, _name: str, _snapshot_id: int) -> int:
        return self.totalSupplyAt(self._named_markets[_name], _snapshot_id)

    @external(readonly=True)
    def getBalnSnapshot(self, _name: str, _snapshot_id: int) -> int:
        return self.totalBalnAt(self._named_markets[_name], _snapshot_id)

    @external(readonly=True)
    def loadBalancesAtSnapshot(self, _id: int, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        if _snapshot_id < 0:
            revert(f"{TAG}: Snapshot id is equal to or greater then Zero.")
        if _id < 0:
            revert(f"{TAG}: Pool id must be equal to or greater than Zero.")
        if _offset < 0:
            revert(f"{TAG}: Offset must be equal to or greater than Zero.")
        rv = {}
        for addr in self._active_addresses[_id].range(_offset, _offset + _limit):
            snapshot_balance = self.balanceOfAt(addr, _id, _snapshot_id)
            if snapshot_balance:
                rv[str(addr)] = snapshot_balance
        return rv

    @external(readonly=True)
    def getDataBatch(self, _name: str, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        pid = self._named_markets[_name]
        total = self.totalDexAddresses(pid)
        clamped_offset = min(_offset, total)
        clamped_limit = min(_limit, total - clamped_offset)
        rv = self.loadBalancesAtSnapshot(
            pid, _snapshot_id, clamped_limit, clamped_offset)
        Logger.info(len(rv), TAG)
        return rv

    ####################################
    # Owner permission for new pools

    @external
    @only_governance
    def permit(self, _id: int, _permission: bool):
        """
        :param _id: Pool ID to manage trading enabled/disabled on
        :param _permission: True = trading enabled, False = disabled

        This function is used to enable or disable trading on a particular pair.
        It should be used by the governance score. If a situation arises such
        as an actively fraudulent market being listed, the community could
        choose to cancel it here.
        """
        self.active[_id] = _permission

    @dex_on
    @external
    def withdraw(self, _token: Address, _value: int):
        """
        :param _token: Address of the token the user wishes to withdraw
        :param _value: Amount of token the users wishes to withdraw

        This function is used to withdraw funds deposited to the DEX, but
        not currently committed to a pool.
        """
        if _value > self._deposit[_token][self.msg.sender]:
            revert(f"{TAG}: Insufficient balance.")

        if _value <= 0:
            revert(f"{TAG}: InvalidAmountError: Please send a positive amount.")

        self._deposit[_token][self.msg.sender] -= _value
        token_score = self.create_interface_score(_token, TokenInterface)
        token_score.transfer(self.msg.sender, _value)
        self.Withdraw(_token, self.msg.sender, _value)

    @dex_on
    @external
    def remove(self, _id: int, _value: int, _withdraw: bool = False):
        """
        :param _id: The pool ID the user wishes to stop contributing to
        :param _value: Amount of LP tokens the user wishes to withdraw
        :param _withdraw: Switch for withdrawing directly to wallet or contract

        This method can withdraw up to a user's holdings in a pool, but it cannot
        be called if the user has not passed their withdrawal lock time period.
        """

        self._take_new_day_snapshot()
        self._check_distributions()

        self._revert_on_incomplete_rewards()

        balance = self._balance[_id][self.msg.sender]

        if not self.active[_id]:
            revert(f"{TAG}: Pool is not active.")

        if _value <= 0:
            revert(f"{TAG}: Invalid input")

        if _value > balance:
            revert(f"{TAG}: Insufficient balance")

        base_token = self._pool_base[_id]
        quote_token = self._pool_quote[_id]

        base_withdraw = self._pool_total[_id][base_token] * _value // self._total[_id]
        quote_withdraw = self._pool_total[_id][quote_token] * _value // self._total[_id]

        self._pool_total[_id][base_token] -= base_withdraw
        self._pool_total[_id][quote_token] -= quote_withdraw
        self._balance[_id][self.msg.sender] -= _value
        self._total[_id] -= _value

        if self._total[_id] < MIN_LIQUIDITY:
            minimum_possible = _value - (MIN_LIQUIDITY - self._total[_id])
            revert(f"{TAG}: MinimumLiquidityError: {minimum_possible} max withdraw size.")

        self.Remove(_id, self.msg.sender, _value, base_withdraw, quote_withdraw)
        self.TransferSingle(self.msg.sender, self.msg.sender, Address.from_string(
            DEX_ZERO_SCORE_ADDRESS), _id, _value)

        self._deposit[base_token][self.msg.sender] += base_withdraw
        self._deposit[quote_token][self.msg.sender] += quote_withdraw

        user_quote_holdings = self._balance[_id][self.msg.sender] \
            * self._pool_total[_id][quote_token] // self.totalSupply(_id)

        if user_quote_holdings < self._get_rewardable_amount(quote_token):
            self._active_addresses[_id].remove(self.msg.sender)

        self._update_account_snapshot(self.msg.sender, _id)
        self._update_total_supply_snapshot(_id)
        if base_token == self._baln.get():
            self._update_baln_snapshot(_id)

        if _withdraw:
            self.withdraw(base_token, base_withdraw)
            self.withdraw(quote_token, quote_withdraw)

    @dex_on
    @external
    def add(self, _baseToken: Address, _quoteToken: Address, _baseValue: int, _quoteValue: int, _withdraw_unused: bool = True):
        """
        Adds liquidity to a pool for trading, or creates a new pool. Rules:
        - The quote coin of the pool must be one of the allowed quote currencies.
        - Tokens must be deposited in the pool's ratio.
        - If ratio is incorrect, it is advisable to call `swap` first.
        - The pool will attempt to maximize the base and quote tokens to fit the pools ratio
        - If there is no deposits, the initial ratio will equal the deposit

        :param _baseToken: Base Token to apply to the pool
        :param _quoteToken: Quote Token to apply to the pool
        :param _baseValue: Amount of base token (at most) to commit to the pool
        :param _quoteValue: Amount of quote token (at most) to commit to the pool
        """

        self._take_new_day_snapshot()
        self._check_distributions()

        self._revert_on_incomplete_rewards()

        _owner = self.msg.sender
        _id = self._pool_id[_baseToken][_quoteToken]

        if _baseToken == _quoteToken:
            revert(f"{TAG}: Pool must contain two token contracts.")
        if _baseValue <= 0:
            revert(f"{TAG}: Invalid base currency value")
        if _quoteValue <= 0:
            revert(f"{TAG}: Invalid quote currency value")
        if self._deposit[_baseToken][self.msg.sender] < _baseValue:
            revert(f"{TAG}: Insufficient base asset funds deposited.")
        if self._deposit[_quoteToken][self.msg.sender] < _quoteValue:
            revert(f"{TAG}: insufficient quote asset funds deposited.")

        # By default on new pools, use the supplied parameters
        # If a pool id already exists (non-zero), apply in the pool ratio instead
        base_to_commit = _baseValue
        quote_to_commit = _quoteValue

        if _id == 0:

            if _quoteToken not in self._quote_coins:
                revert(f"{TAG}: QuoteNotAllowed: Supplied quote token not in permitted set.")

            self._pool_id[_baseToken][_quoteToken] = self._nonce.get()
            self._pool_id[_quoteToken][_baseToken] = self._nonce.get()
            _id = self._nonce.get()

            self._nonce.set(self._nonce.get() + 1)
            self.active[_id] = True

            self._pool_base[_id] = _baseToken
            self._pool_quote[_id] = _quoteToken

            liquidity = sqrt(_baseValue * _quoteValue)

            if liquidity < MIN_LIQUIDITY:
                revert(f"{TAG}: InsufficientInitialLiquidity: Initial LP tokens must exceed {MIN_LIQUIDITY}.")

            self.MarketAdded(_id, _baseToken, _quoteToken,
                             _baseValue, _quoteValue)

        else:

            # We will commit up to the supplied assets, and refund the rest
            base_from_quote = (_quoteValue * self._pool_total[_id][self._pool_base[_id]]) // (self._pool_total[_id][self._pool_quote[_id]])

            quote_from_base = (_baseValue * self._pool_total[_id][self._pool_quote[_id]]) // (self._pool_total[_id][self._pool_base[_id]])

            Logger.info(f"Pre Total Base: {self._pool_total[_id][_baseToken]}, quote: {self._pool_total[_id][_quoteToken]}", TAG)

            Logger.info(f"Base: {_baseValue} (supplied), {base_from_quote} (computed); Quote: {_quoteValue} (supplied), {quote_from_base} (computed)", TAG)

            if quote_from_base <= _quoteValue:
                quote_to_commit = quote_from_base

            else:
                base_to_commit = base_from_quote

            liquidity_from_base = (self._total[_id] * base_to_commit) // self._pool_total[_id][_baseToken]
            liquidity_from_quote = (self._total[_id] * quote_to_commit) // self._pool_total[_id][_quoteToken]

            liquidity = min(liquidity_from_base, liquidity_from_quote)

        # Apply the funds to the pool and add LP tokens
        self._pool_total[_id][_baseToken] += base_to_commit
        self._pool_total[_id][_quoteToken] += quote_to_commit

        Logger.info(f"Committing: {base_to_commit} base, {quote_to_commit} quote for {liquidity} LP tokens", TAG)

        self._deposit[_baseToken][self.msg.sender] -= base_to_commit
        self._deposit[_quoteToken][self.msg.sender] -= quote_to_commit

        self._balance[_id][_owner] += liquidity
        self._total[_id] += liquidity

        self.Add(_id, _owner, liquidity, base_to_commit, quote_to_commit)

        self.TransferSingle(_owner, Address.from_string(
            DEX_ZERO_SCORE_ADDRESS), _owner, _id, liquidity)

        user_quote_holdings = self._balance[_id][self.msg.sender] \
            * self._pool_total[_id][_quoteToken] // self.totalSupply(_id)

        if user_quote_holdings >= self._get_rewardable_amount(_quoteToken):
            self._active_addresses[_id].add(self.msg.sender)

        self._update_account_snapshot(_owner, _id)
        self._update_total_supply_snapshot(_id)
        if _baseToken == self._baln.get():
            self._update_baln_snapshot(_id)

        Logger.info(f"Post Total Base: {self._pool_total[_id][_baseToken]}, quote: {self._pool_total[_id][_quoteToken]}", TAG)

        # If set to withdraw unused funds, check if any are left on deposit
        # If yes, then send back to the msg.sender address
        if _withdraw_unused:
            remaining_base = self._deposit[_baseToken][self.msg.sender]

            if remaining_base > 0:
                self.withdraw(_baseToken, remaining_base)

            remaining_quote = self._deposit[_quoteToken][self.msg.sender]

            if remaining_quote > 0:
                self.withdraw(_quoteToken, remaining_quote)

    @dex_on
    @external
    def withdrawSicxEarnings(self, _value: int = 0):
        """
        :param _value: Amount of token the users wishes to withdraw

        This function is used to withdraw funds deposited to the DEX, but
        not currently committed to a pool.
        """
        if _value == 0:
            _value = self._sicx_earnings[self.msg.sender]

        if _value > self._sicx_earnings[self.msg.sender]:
            revert(f"{TAG}: Insufficient balance.")

        if _value <= 0:
            revert(f"{TAG}: InvalidAmountError: Please send a positive amount.")

        self._sicx_earnings[self.msg.sender] -= _value
        token_score = self.create_interface_score(self._sicx.get(), TokenInterface)
        token_score.transfer(self.msg.sender, _value)
        self.ClaimSicxEarnings(self.msg.sender, _value)
