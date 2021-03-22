#### Balanced DEX is a open source software developed by balanced network #####
#### Forked from icon pool, developed from blockdevs.co #####
#### The content of this project itself is licensed under the Creative Commons Attribution 3.0 Unported license,  #####
#### and the underlying source code used to format and display that content is licensed under the GNU AGLPL license.  #####
##### Check the LICENSE file for more info #####

from .scorelib.utils import *
from .scorelib.id_factory import *
from .scorelib.linked_list import *
from .scorelib.bag import *
from .scorelib.set import *
from .scorelib.iterable_dict import *
from iconservice import *
from .utils.checks import *
from .utils.consts import *


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

    _TAG = 'DEX'
    _ACCOUNT_BALANCE_SNAPSHOT = 'account_balance_snapshot'
    _TOTAL_SUPPLY_SNAPSHOT = 'total_supply_snapshot'
    _FUNDED_ADDRESSES = 'funded_addresses'
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
    _SICXICX_MARKET_NAME = 'SICXICX'
    _CURRENT_DAY = 'current_day'
    _TIME_OFFSET = 'time_offset'
    _REWARDS_DONE = 'rewards_done'
    _DIVIDENDS_DONE = 'dividends_done'
    _NAME = 'BalancedDex'

    ####################################
    # Events
    @eventlog(indexed=2)
    def Swap(self, _fromToken: Address, _toToken: Address, _sender: Address,
             _receiver: Address, _fromValue: int, _toValue: int, _lpFees: int, _balnFees: int): pass

    @eventlog(indexed=3)
    def MarketAdded(self, _pid: int, _baseToken: Address,
                    _quoteToken: Address, _baseValue: int, _quoteValue: int): pass

    @eventlog(indexed=2)
    def Add(self, _pid: int, _owner: Address, _value: int): pass

    @eventlog(indexed=2)
    def Remove(self, _pid: int, _owner: Address, _value: int): pass

    @eventlog(indexed=2)
    def Deposit(self, _token: Address, _owner: Address, _value: int): pass

    @eventlog(indexed=2)
    def Withdraw(self, _token: Address, _owner: Address, _value: int): pass

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

        # Rewards/timekeeping logic
        self._current_day = VarDB(self._CURRENT_DAY, db, value_type=int)
        self._time_offset = VarDB(self._TIME_OFFSET, db, value_type=int)
        self._rewards_done = VarDB(self._REWARDS_DONE, db, value_type=bool)
        self._dividends_done = VarDB(self._DIVIDENDS_DONE, db, value_type=bool)

        # Previously mapped addresses, for iteration purposes
        self._funded_addresses = SetDB(
            self._FUNDED_ADDRESSES, db, value_type=Address, order=True)

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

        # poolTotal[nonce][tokenAddress] = intAmount
        self._pool_total = DictDB('poolTotal', db, value_type=int, depth=2)

        self._withdraw_lock = DictDB(
            'withdrawLock', db, value_type=int, depth=2)

        # Swap queue for sicxicx
        self._icx_queue = LinkedListDB(
            'icxQueue', db, value1_type=int, value2_type=Address)
        self._icx_queue_order_id = DictDB(
            'icxQueueOrderId', db, value_type=int)

        # Total ICX Balance available for conversion
        self._icx_queue_total = VarDB(
            self._ICX_QUEUE_TOTAL, db, value_type=int)

        # Withdraw lock for sicxicx
        self._icx_withdraw_lock = DictDB('icxWithdrawLock', db, value_type=int)

        # Approvals for token transfers (map[grantor][grantee] = T/F)
        self._approvals = DictDB('approvals', db, value_type=bool, depth=2)

        self._named_markets = IterableDictDB(
            self._NAMED_MARKETS, db, value_type=int, key_type=str, order=True)

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
        self._current_day.set(0)
        self._named_markets[self._SICXICX_MARKET_NAME] = 1

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return self._NAME

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
        :param _address: The new admin address to set.
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
        self._sicx.set(_address)

    @only_admin
    @external
    def setDividends(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new Dividends address. Should be called before DEX use.
        """
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
        self._governance.set(_address)

    @external
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
        self._rewards.set(_address)

    @external
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
        self._bnUSD.set(_address)

    @external
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
        self._baln.set(_address)

    @external
    def getBaln(self) -> Address:
        """
        Gets the address of the BALN contract.
        """
        return self._baln.get()

    @only_governance
    @external
    def setMarketName(self, _pid: int, _name: str) -> None:
        """
        :param _pid: Pool ID to map to the name
        :param _name: Name to associate
        Links a pool ID to a name, so users can look up platform-defined
        markets more easily.
        """
        self._named_markets[_name] = _pid

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

    @external
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

        order_id = self._icx_queue_order_id[self.msg.sender]
        if order_id:
            # First, modify our order
            node = self._icx_queue._get_node(order_id)
            node.set_value1(node.get_value1() + self.msg.value)
            # Next, bump the user to the end of the line if it is not the tail
            if self._icx_queue._length.get() > 1:
                self._icx_queue.move_node_tail(order_id)
        else:
            order_id = self._icx_queue.append(self.msg.value, self.msg.sender)
            self._icx_queue_order_id[self.msg.sender] = order_id

        current_icx_total = self._icx_queue_total.get() + self.msg.value
        self._icx_queue_total.set(current_icx_total)

        self._icx_withdraw_lock[self.msg.sender] = self.now()
        if self.msg.sender not in self._funded_addresses:
            self._funded_addresses.add(self.msg.sender)
        self._update_account_snapshot(self.msg.sender, 1)
        self._update_total_supply_snapshot(1)

    @external
    def cancelSicxicxOrder(self):
        """
        Cancels user's order in the SICXICX queue.
        Cannot be called within 24h of the last place/modify time.

        Order cancellation updates the snapshots of the queue.
        """
        self._take_new_day_snapshot()
        self._check_distributions()

        if not self._icx_queue_order_id[self.msg.sender]:
            revert("No open order in SICXICX queue")

        if self._icx_withdraw_lock[self.msg.sender] + WITHDRAW_LOCK_TIMEOUT > self.now():
            revert("Withdraw lock not expired")

        order_id = self._icx_queue_order_id[self.msg.sender]
        order = self._icx_queue._get_node(order_id)
        withdraw_amount = order.get_value1()

        current_icx_total = self._icx_queue_total.get() - withdraw_amount
        self._icx_queue_total.set(current_icx_total)

        self._icx_queue.remove(order_id)
        self.icx.transfer(self.msg.sender, withdraw_amount)
        del self._icx_queue_order_id[self.msg.sender]
        self._update_account_snapshot(self.msg.sender, 1)
        self._update_total_supply_snapshot(1)

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
        Logger.info("called token fallback", self._TAG)

        # Update snapshots if necessary and notify the rewards score
        self._take_new_day_snapshot()
        self._check_distributions()

        unpacked_data = json_loads(_data.decode('utf-8'))
        _fromToken = self.msg.sender
        if unpacked_data["method"] == "_deposit":
            self._deposit[_fromToken][_from] += _value
            self.Deposit(_fromToken, _from, _value)
        elif unpacked_data["method"] == "_swap_icx":
            if _fromToken == self._sicx.get():
                self._swap_icx(_from, _value)
        elif unpacked_data["method"] == "_swap":
            max_slippage = 250
            if "maxSlippage" in unpacked_data["params"]:
                max_slippage = int(unpacked_data["params"]["maxSlippage"])
                if max_slippage > MAX_SLIPPAGE:
                    revert("Slippage cannot exceed 10% (1000 basis points)")
                if max_slippage <= 0:
                    revert("Max slippage must be a positive number")
            self.exchange(_fromToken, Address.from_string(
                unpacked_data["params"]["toToken"]), _from, _from, _value, max_slippage)
        else:
            revert("Fallback directly not allowed")

    @external
    def precompute(self, snap: int, batch_size: int) -> bool:
        """
        Required by the rewards score data source API, but unused.
        Returns `True` to match the required workflow.
        """
        return True

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
        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)

    def _transfer(self, _from: Address, _to: Address, _value: int, _id: int, _data: bytes):
        """
        Used to transfer LP IRC-31 tokens from one address to another.
        Invoked by `transfer(...)`.
        """
        if _value < 0:
            revert("Transferring value cannot be less than 0")
        if self._balance[_id][_from] < _value:
            revert("Out of balance")

        if _to not in self._funded_addresses:
            self._funded_addresses.add(_to)

        self._balance[_id][_from] = self._balance[_from] - _value
        self._balance[_id][_to] = self._balance[_to] + _value

        self.TransferSingle(self.msg.sender, _from, _to, _id, _value)

        self._update_account_snapshot(self.msg.sender, _id)

        # TODO: Implement token fallback for multitoken score

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
    def getPoolTotal(self, _pid: int, _token: Address) -> int:
        return self._pool_total[_pid][_token]

    @external(readonly=True)
    def totalSupply(self, _pid: int) -> int:
        if _pid == 1:
            return self._icx_queue_total.get()
        return self._total[_pid]

    @external(readonly=True)
    def balanceOf(self, _owner: Address, _id: int) -> int:
        """
        Returns the balance of the owner's tokens.
        NOTE: ID 0 will return SICXICX balance
        :param _owner: the address of the token holder
        :param _id: ID of the token/pool
        :return: the _owner's balance of the token type requested
        """
        if _id == 1:
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
        fees = {}
        fees['icx_total'] = self._icx_baln_fee.get() + \
            self._icx_conversion_fee.get()
        fees['pool_total'] = self._pool_baln_fee.get() + \
            self._pool_lp_fee.get()
        fees['pool_lp_fee'] = self._pool_lp_fee.get()
        fees['pool_baln_fee'] = self._pool_baln_fee.get()
        fees['icx_conversion_fee'] = self._icx_conversion_fee.get()
        fees['icx_baln_fee'] = self._icx_baln_fee.get()
        return fees

    @external(readonly=True)
    def getPoolBase(self, _pid: int) -> Address:
        return self._pool_base[_pid]

    @external(readonly=True)
    def getPoolQuote(self, _pid: int) -> Address:
        return self._pool_quote[_pid]

    @external(readonly=True)
    def getQuotePriceInBase(self, _pid: int) -> int:
        """
        e.g. USD/BTC, this is the inverse of the most common way to express price.
        """
        if _pid < 1 or _pid > self._nonce.get():
            return "Invalid pool id"
        if _pid == 1:
            return self._get_sicx_rate()
        return (self._pool_total[_pid][self._pool_base[_pid]] * EXA) // self._pool_total[_pid][self._pool_quote[_pid]]

    @external(readonly=True)
    def getBasePriceInQuote(self, _pid: int) -> int:
        """
        e.g. BTC/USD, this is the most common way to express price.
        """
        if _pid < 1 or _pid > self._nonce.get():
            return "Invalid pool id"
        return (self._pool_total[_pid][self._pool_quote[_pid]] * EXA) // self._pool_total[_pid][self._pool_base[_pid]]

    @external(readonly=True)
    def getPrice(self, _pid: int) -> int:
        """
        This method is an alias to the most common form of price.
        """
        return self.getBasePriceInQuote(_pid)

    @external(readonly=True)
    def getBalnPrice(self, _pid: int) -> int:
        """
        This method is an alias to the current price of BALN tokens
        """
        return self.getBasePriceInQuote(self._pool_id[self._baln.get()][_token2Address])

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
    def getICXWithdrawLock(self) -> int:
        return self._icx_withdraw_lock[self.msg.sender]

    ####################################
    # Token Functionality

    @external
    def setApprovalForAll(self, _operator: Address, _approved: bool):
        """
        Enables or disables approval for a third party ("operator") to manage all of the caller's tokens,
        and must emit `ApprovalForAll` event on success.

        :param _operator: address to add to the set of authorized operators
        :param _approved: true if the operator is approved, false to revoke approval
        """
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

        if _data is None:
            _data = b'None'
        self._transfer_from(self.msg.sender, _from, _to, _id, _value, _data)

    def _transfer_from(self, _from: Address, _to: Address, _id: int, _value: int, _data: bytes):
        if not self.isApprovedForAll(_from, self.msg.sender):
            revert("Not approved for transfer")
        if _value < 0:
            revert("Transferring value cannot be less than 0")
        if self._balance[_id][_from] < _value:
            revert("Out of balance")

        self._balance[_id][_from] = self._balance[_from] - _value
        self._balance[_id][_to] = self._balance[_to] + _value
        self.TransferSingle(self.msg.sender, _from, _to, _id, _value)

        if _to not in self._funded_addresses:
            self._funded_addresses.add(_to)

        self._update_account_snapshot(_from, _id)

        # TODO: Implement onIRC31Received function

    @external(readonly=True)
    def hasUsedDex(self, _user: Address) -> bool:
        """
        Returns whether an address has previously used the dex.

        :param _user: Address to check
        """
        return _user in self._funded_addresses

    @external(readonly=True)
    def totalDexAddresses(self) -> int:
        """
        Returns total number of users that have used the dex.

        :param _user: Address to check
        """
        return self._funded_addresses.__len__()

    def _get_exchange_rate(self) -> int:
        """
        Internal function for use in SICXICX pools.
        Gets the current exchange rate (expressed in units 1 = 1e18).
        Requires that the _staking_address property is set via the contract admin.
        """
        staking_score = self.create_interface_score(
            self._staking.get(), stakingInterface)
        return staking_score.getTodayRate()

    ####################################
    # Internal exchange function

    def exchange(self, _fromToken: Address, _toToken: Address, _sender: Address, _receiver: Address, _value: int, _max_slippage: int = 250):
        lp_fees = (_value * self._pool_lp_fee.get()) // FEE_SCALE
        baln_fees = (_value * self._pool_baln_fee.get()) // FEE_SCALE
        fees = lp_fees + baln_fees
        original_value = _value
        _value -= fees
        _pid = self._pool_id[_fromToken][_toToken]
        if _pid == 0:
            revert("Pool does not exist")
        if _pid == 1:
            revert("Not supported on this API, use the ICX swap API")
        old_price = 0
        if _fromToken == self.getPoolQuote(_pid):
            old_price = self.getBasePriceInQuote(_pid)
        else:
            old_price = self.getQuotePriceInBase(_pid)
        Logger.info("old_price: " + str(old_price), self._TAG)
        if not self.active[_pid]:
            revert("Pool is not active")
        new_token1 = self._pool_total[_pid][_fromToken] + _value
        new_token2 = int(
            self._pool_total[_pid][_fromToken] * self._pool_total[_pid][_toToken] / new_token1)
        send_amt = self._pool_total[_pid][_toToken] - new_token2

        self._pool_total[_pid][_fromToken] = new_token1 + lp_fees
        self._pool_total[_pid][_toToken] = new_token2

        send_price = ((EXA) * _value) // send_amt

        max_slippage_price = (old_price * (10000 + _max_slippage)) // 10000

        Logger.info("send price = " + str(send_price) + ", old price = " +
                    str(old_price) + ", max slippage price = " + str(max_slippage_price), self._TAG)

        if (send_price > max_slippage_price):
            revert("Passed Maximum slippage")

        # Pay each of the user and the dividends score their share of the tokens
        to_token_score = self.create_interface_score(_toToken, TokenInterface)
        to_token_score.transfer(_receiver, send_amt)
        from_token_score = self.create_interface_score(
            _fromToken, TokenInterface)
        from_token_score.transfer(self._dividends.get(), baln_fees)
        self.Swap(_fromToken, _toToken, _sender,
                  _receiver, original_value, send_amt, lp_fees, baln_fees)

    def _get_sicx_rate(self) -> int:
        staking_score = self.create_interface_score(
            self._staking.get(), stakingInterface)
        return staking_score.getTodayRate()

    def _swap_icx(self, _sender: Address, _value: int):
        """
        Perform an instant conversion from SICX to ICX.
        Gets orders from SICXICX queue by price time precedence.
        """
        remaining_sicx = _value
        conversion_factor = self._get_sicx_rate()

        sicx_score = self.create_interface_score(
            self._sicx.get(), TokenInterface)
        filled = False
        filled_icx = 0
        removed_icx = 0

        fee_ratio = FEE_SCALE - \
            (self._icx_baln_fee.get() + self._icx_conversion_fee.get())

        while not filled:

            if self._icx_queue._length.get() == 0:
                Logger.info("Transferring remaining SICX", 'DEX')
                sicx_score.transfer(_sender, remaining_sicx)
                break

            counterparty_order = self._icx_queue._get_head_node()
            counterparty_address = counterparty_order.get_value2()
            order_sicx_value = (int)(counterparty_order.get_value1() * EXA //
                                     conversion_factor)
            # Perform match. Matched amount is up to order size
            matched_sicx = min(order_sicx_value, remaining_sicx)
            matched_icx = (int)(matched_sicx * conversion_factor // EXA)
            filled_icx += (int)((matched_icx * fee_ratio) // FEE_SCALE)
            removed_icx += matched_icx

            dividends_contribution = (int)(
                (matched_icx * self._icx_baln_fee.get()) // FEE_SCALE)
            self.icx.transfer(self._dividends.get(),
                              dividends_contribution)

            sicx_score.transfer(counterparty_address, matched_sicx)
            self.icx.transfer(counterparty_address, (int)
                              ((matched_icx * self._icx_conversion_fee.get()) // FEE_SCALE))

            if matched_icx == counterparty_order.get_value1():
                self._icx_queue.remove_head()
                del self._icx_queue_order_id[counterparty_address]
            else:
                counterparty_order.set_value1(
                    counterparty_order.get_value1() - matched_icx)

            remaining_sicx -= matched_sicx
            if not remaining_sicx:
                filled = True

        current_icx_total = self._icx_queue_total.get() - removed_icx
        self._icx_queue_total.set(current_icx_total)

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

    def _update_account_snapshot(self, _account: Address, _id: int) -> None:
        """
        Updates a user's balance snapshot
        :param _account: Address to update
        :param _id: pool id to update
        """
        current_id = self._current_day.get()
        current_value = self.balanceOf(_account, _id)
        length = self._account_balance_snapshot[_id][_account]['length'][0]
        if length == 0:
            self._account_balance_snapshot[_id][_account]['values'][length] = current_value
            self._account_balance_snapshot[_id][_account]['length'][0] += 1
            return
        else:
            last_snapshot_id = self._account_balance_snapshot[_id][_account]['ids'][length - 1]

        if last_snapshot_id < current_id:
            self._account_balance_snapshot[_id][_account]['ids'][length] = current_id
            self._account_balance_snapshot[_id][_account]['values'][length] = current_value
            self._account_balance_snapshot[_id][_account]['length'][0] += 1
        else:
            self._account_balance_snapshot[_id][_account]['values'][length -
                                                                    1] = current_value

    def _update_total_supply_snapshot(self, _id: int) -> None:
        """
        Updates a an asset's total supply snapshot
        :param _id: pool id to update
        """
        current_id = self._current_day.get()
        current_value = self.totalSupply(_id)
        length = self._total_supply_snapshot[_id]['length'][0]
        if length == 0:
            self._total_supply_snapshot[_id]['values'][length] = current_value
            self._total_supply_snapshot[_id]['length'][0] += 1
            return
        else:
            last_snapshot_id = self._total_supply_snapshot[_id]['ids'][length - 1]

        if last_snapshot_id < current_id:
            self._total_supply_snapshot[_id]['ids'][length] = current_id
            self._total_supply_snapshot[_id]['values'][length] = current_value
            self._total_supply_snapshot[_id]['length'][0] += 1
        else:
            self._total_supply_snapshot[_id]['values'][length -
                                                       1] = current_value

    @external(readonly=True)
    def balanceOfAt(self, _account: Address, _id: int, _snapshot_id: int) -> int:
        if _snapshot_id < 0:
            revert(f'Snapshot id is equal to or greater then Zero')
        low = 0
        high = self._account_balance_snapshot[_id][_account]['length'][0]

        while (low < high):
            mid = (low + high) // 2
            if self._account_balance_snapshot[_id][_account]['ids'][mid] > _snapshot_id:
                high = mid
            else:
                low = mid + 1
        if self._account_balance_snapshot[_id][_account]['ids'][0] == _snapshot_id:
            return self._account_balance_snapshot[_id][_account]['values'][0]
        elif low == 0:
            return 0
        else:
            return self._account_balance_snapshot[_id][_account]['values'][low - 1]

    @external(readonly=True)
    def totalSupplyAt(self, _id: int, _snapshot_id: int) -> int:
        if _snapshot_id < 0:
            revert(f'Snapshot id is equal to or greater then Zero')
        low = 0
        high = self._total_supply_snapshot[_id]['length'][0]

        while (low < high):
            mid = (low + high) // 2
            if self._total_supply_snapshot[_id]['ids'][mid] > _snapshot_id:
                high = mid
            else:
                low = mid + 1

        if self._total_supply_snapshot[_id]['ids'][0] == _snapshot_id:
            return self._total_supply_snapshot[_id]['values'][0]
        elif low == 0:
            return 0
        else:
            return self._total_supply_snapshot[_id]['values'][low - 1]

    @external(readonly=True)
    def getTotalValue(self, _name: str, _snapshot_id: int) -> int:
        return self.totalSupplyAt(self._named_markets[_name], _snapshot_id)

    @external(readonly=True)
    def loadBalancesAtSnapshot(self, _pid: int, _snapshot_id: int, _limit: int,  _offset: int = 0) -> dict:
        if _snapshot_id < 0:
            revert(f'Snapshot id is equal to or greater then Zero')
        if _pid < 0:
            revert(f'Pool id must be equal to or greater than Zero')
        if _offset < 0:
            revert(f'Offset must be equal to or greater than Zero')
        rv = {}
        for addr in self._funded_addresses.select(_offset):
            snapshot_balance = self.balanceOfAt(addr, _pid, _snapshot_id)
            if snapshot_balance:
                rv[str(addr)] = snapshot_balance
        return rv

    @external(readonly=True)
    def getDataBatch(self, _name: str, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        total = self.totalDexAddresses()
        clamped_offset = min(_offset, total)
        clamped_limit = min(_limit, total - clamped_offset)
        pid = self._named_markets[_name]
        rv = self.loadBalancesAtSnapshot(
            pid, _snapshot_id, clamped_limit, clamped_offset)
        Logger.info(len(rv), self._TAG)
        return rv

    ####################################
    # Owner permission for new pools

    @external
    @only_governance
    def permit(self, _pid: int, _permission: bool):
        """
        :param _pid: Pool ID to manage trading enabled/disabled on
        :param _permission: True = trading enabled, False = disabled

        This function is used to enable or disable trading on a particular pair.
        It should be used by the governance score. If a situation arises such
        as an actively fraudulent market being listed, the community could
        choose to cancel it here.
        """
        self.active[_pid] = _permission

    @external
    def withdraw(self, _token: Address, _value: int):
        """
        :param _token: Address of the token the user wishes to withdraw
        :param _value: Amount of token the users wishes to withdraw

        This function is used to withdraw funds deposited to the DEX, but
        not currently committed to a pool.
        """
        if _value > self._deposit[_token][self.msg.sender]:
            revert("Insufficient balance")
        self._deposit[_token][self.msg.sender] -= _value
        token_score = self.create_interface_score(_token, TokenInterface)
        token_score.transfer(self.msg.sender, _value)
        self.Withdraw(_token, self.msg.sender, _value)

    @external
    def remove(self, _pid: int, _value: int, _withdraw: bool = False):
        """
        :param _pid: The pool ID the user wishes to stop contributing to
        :param _value: Amount of LP tokens the user wishes to withdraw
        :param _withdraw: Switch for withdrawing directly to wallet or contract

        This method can withdraw up to a user's holdings in a pool, but it cannot
        be called if the user has not passed their withdrawal lock time period.
        """
        balance = self._balance[_pid][self.msg.sender]
        if not self.active[_pid]:
            revert("Pool is not active")
        if _value > balance:
            revert("Invalid input")
        if self._withdraw_lock[self.msg.sender][_pid] + WITHDRAW_LOCK_TIMEOUT < self.now():
            revert("Funds not yet unlocked")
        token1 = self._pool_base[_pid]
        token2 = self._pool_quote[_pid]
        self._pool_total[_pid][token1] -= int(self._pool_total[_pid]
                                              [token1] * (_value / self._total[_pid]))
        self._pool_total[_pid][token2] -= int(self._pool_total[_pid]
                                              [token2] * (_value / self._total[_pid]))
        token1_amount = int(
            self._pool_total[_pid][token1] * (_value / self._total[_pid]))
        token2_amount = int(
            self._pool_total[_pid][token2] * (_value / self._total[_pid]))
        self._balance[_pid][self.msg.sender] -= _value
        self._total[_pid] -= _value
        self.Remove(_pid, self.msg.sender, _value)
        self.TransferSingle(self.msg.sender, self.msg.sender, Address.from_string(
            ZERO_SCORE_ADDRESS), _pid, _value)
        if not _withdraw:
            self._deposit[token1][self.msg.sender] += token1_amount
            self._deposit[token2][self.msg.sender] += token2_amount
        else:
            self.withdraw(token1, token1_amount)
            self.withdraw(token2, token2_amount)
        self._update_account_snapshot(self.msg.sender, _pid)
        self._update_total_supply_snapshot(_pid)

    @external
    def add(self, _baseToken: Address, _quoteToken: Address, _maxBaseValue: int, _quoteValue: int):
        """
        Adds liquidity to a pool for trading, or creates a new pool. Rules:
        - The quote coin of the pool must be one of the allowed quote currencies.
        - Tokens must be deposited in the pool's ratio.
        - If ratio is incorrect, it is advisable to call `swap` first.
        """
        _owner = self.msg.sender
        _pid = self._pool_id[_baseToken][_quoteToken]
        if _baseToken == _quoteToken:
            revert("Pool must contain two token contracts")
        if not _maxBaseValue:
            revert("Please send initial value for first currency")
        if not _quoteValue:
            revert("Please send initial value for second currency")
        if self._deposit[_baseToken][self.msg.sender] < _maxBaseValue:
            revert("Insufficient base asset funds deposited")
        if self._deposit[_quoteToken][self.msg.sender] < _quoteValue:
            revert("insufficient quote asset funds deposited")

        # By default on new pools, use the maximum sent _maxBaseValue for supplied liquidity
        base_to_commit = _maxBaseValue

        if _pid == 0:
            if not (_quoteToken == self._bnUSD.get()) and not (_quoteToken == self._sicx.get()):
                revert("Second currency must be bnUSD or sICX")
            self._pool_id[_baseToken][_quoteToken] = self._nonce.get()
            self._pool_id[_quoteToken][_baseToken] = self._nonce.get()
            _pid = self._nonce.get()
            liquidity = DEFAULT_INITAL_LP
            self._nonce.set(self._nonce.get() + 1)
            self.active[_pid] = True
            self._pool_base[_pid] = _baseToken
            self._pool_quote[_pid] = _quoteToken
            self.MarketAdded(_pid, _baseToken, _quoteToken,
                             _maxBaseValue, _quoteValue)

        else:
            base_to_commit = (_quoteValue * self._pool_total[_pid][self._pool_base[_pid]]) // (self._pool_total[_pid][self._pool_quote[_pid]])
            if base_to_commit > _maxBaseValue:
                revert('Proportionate base amount is {}, but sent {}'.format(base_to_commit, _maxBaseValue))
            liquidity = (self._total[_pid] * base_to_commit) // self._pool_total[_pid][_baseToken]
        self._pool_total[_pid][_baseToken] += base_to_commit
        self._pool_total[_pid][_quoteToken] += _quoteValue
        self._deposit[_baseToken][self.msg.sender] -= base_to_commit
        self._deposit[_quoteToken][self.msg.sender] -= _quoteValue
        self._balance[_pid][_owner] += liquidity
        self._total[_pid] += liquidity
        self.Add(_pid, _owner, liquidity)
        self.TransferSingle(_owner, Address.from_string(
            ZERO_SCORE_ADDRESS), _owner, _pid, liquidity)
        self._withdraw_lock[self.msg.sender][_pid] = self.now()
        if self.msg.sender not in self._funded_addresses:
            self._funded_addresses.add(self.msg.sender)
        self._update_account_snapshot(_owner, _pid)
        self._update_total_supply_snapshot(_pid)
