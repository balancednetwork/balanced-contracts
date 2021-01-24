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
    _ICD_ADDRESS = 'icd_address'
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

    ####################################
    # Events
    @eventlog(indexed=2)
    def Swap(self, _fromToken: Address, _toToken: Address, _sender: Address,
             _receiver: Address, _fromValue: int, _toValue: int): pass

    @eventlog(indexed=2)
    def Add(self, _pid: int, _owner: Address, _value: int): pass

    @eventlog(indexed=2)
    def Remove(self, _pid: int, _owner: Address, _value: int): pass

    @eventlog(indexed=2)
    def Deposit(self, _token: Address, _owner: Address, _value: int): pass

    @eventlog(indexed=2)
    def Withdraw(self, _token: Address, _owner: Address, _value: int): pass

    @eventlog(indexed=2)
    def Dividends(self, _token: Address, _value: int): pass

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
        self._sICX_address = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._staking_address = VarDB(
            self._STAKING_ADDRESS, db, value_type=Address)
        self._dividends = VarDB(
            self._DIVIDENDS_ADDRESS, db, value_type=Address)
        self._governance = VarDB(
            self._GOVERNANCE_ADDRESS, db, value_type=Address)
        self._rewards = VarDB(
            self._REWARDS_ADDRESS, db, value_type=Address)

        # DEX Activation (can be set by governance only)
        self._dex_on = VarDB(self._DEX_ON, db, value_type=bool)

        # deposited irc not locked in pool
        # deposit[TokenAddress][UserAddress] = intValue
        self.deposit = DictDB('deposit', db, value_type=int, depth=2)

        # PoolId
        # poolId[token1Address][token2Address] = nonce 1 to n
        self.poolId = DictDB('poolId', db, value_type=int, depth=2)

        # Top Nonce count == n = (1,n) pools
        self.nonce = VarDB('nonce', db, value_type=int)

        # Total amount of tokens in pool
        # poolTotal[nonce][tokenAddress] = intAmount
        self.poolTotal = DictDB('poolTotal', db, value_type=int, depth=2)

        # Total number of pool LP tokens
        # total[nonce] = intValue
        self.total = DictDB('poolLPTotal', db, value_type=int)

        # Balance of LP Tokens of nonce
        # balance[nonce][userAddress]
        self.balance = DictDB('balances', db, value_type=int, depth=2)

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
        self.funded_addresses = SetDB(
            self._FUNDED_ADDRESSES, db, value_type=Address, order=True)

        # Fees in basis points (divide by 1000)
        self.fees = VarDB('fees', db, value_type=int)

        # pid to tokens
        # poolTn[nonce] = tokenAddress
        self.poolBase = DictDB('baseToken', db, value_type=Address)
        self.poolQuote = DictDB('quoteToken', db, value_type=Address)
        # pid permissions
        # active[pool] = bool
        self.active = DictDB('activePool', db, value_type=bool)

        # poolTotal[nonce][tokenAddress] = intAmount
        self.poolTotal = DictDB('poolTotal', db, value_type=int, depth=2)

        self.withdrawLock = DictDB('withdrawLock', db, value_type=int, depth=2)

        # Swap queue for sicxicx
        self.icxQueue = LinkedListDB(
            'icxQueue', db, value1_type=int, value2_type=Address)
        self.icxQueueOrderId = DictDB('icxQueueOrderId', db, value_type=int)

        # Total ICX Balance available for conversion
        self.icxQueueTotal = VarDB(self._ICX_QUEUE_TOTAL, db, value_type=int)

        # Withdraw lock for sicxicx
        self.icxWithdrawLock = DictDB('icxWithdrawLock', db, value_type=int)

        # Approvals for token transfers (map[grantor][grantee] = T/F)
        self.approvals = DictDB('approvals', db, value_type=bool, depth=2)

        self.named_markets = IterableDictDB(
            self._NAMED_MARKETS, db, value_type=int, key_type=str, order=True)

    def on_install(self) -> None:
        super().on_install()
        self.fees.set(3)
        # avoid 0 as default null pid
        self.nonce.set(1)
        self._current_day.set(0)
        self.named_markets[self._SICXICX_MARKET_NAME] = 0

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def getAdmin(self) -> Address:
        return self._admin.get()

    @only_owner
    @external
    def setAdmin(self, _admin: Address) -> None:
        self._admin.set(_admin)

    @external(readonly=True)
    def getSicxAddress(self) -> Address:
        return self._sICX_address.get()

    @only_owner
    @external
    def set_sICX_address(self, _address: Address) -> None:
        self._sICX_address.set(_address)

    @only_owner
    @external
    def set_dividends_address(self, _address: Address) -> None:
        self._dividends.set(_address)

    @external(readonly=True)
    def getDividendsAddress(self) -> Address:
        return self._dividends.get()

    @only_owner
    @external
    def set_staking_address(self, _address: Address) -> None:
        self._staking_address.set(_address)

    @external(readonly=True)
    def getStakingAddress(self) -> Address:
        return self._staking_address.get()

    @external(readonly=True)
    def getStakingAddress(self) -> Address:
        return self._staking_address.get()

    @only_owner
    @external
    def setGovernance(self, _address: Address) -> None:
        self._governance.set(_address)

    @external
    def getGovernance(self) -> Address:
        return self._governance.get()

    @only_owner
    @external
    def setRewards(self, _address: Address) -> None:
        self._rewards.set(_address)

    @external
    def getRewards(self) -> Address:
        return self._rewards.get()

    @only_owner
    @external
    def setMarketName(self, _pid: int, _name: str) -> None:
        self.named_markets[_name] = _pid

    @only_governance
    @external
    def turnDexOn(self) -> None:
        self._dex_on.set(True)

    @external(readonly=True)
    def getDexOn(self) -> bool:
        return self._dex_on.get()

    @external
    def getDay(self) -> int:
        return (self.now() - self._time_offset.get()) // U_SECONDS_DAY

    @only_governance
    @external
    def setTimeOffset(self, _delta_time: int) -> None:
        if self.msg.sender != self._governance.get():
            revert("The time_offset can only be set by the Governance SCORE.")
        self._time_offset.set(_delta_time)

    @external(readonly=True)
    def getTimeOffset(self) -> int:
        self._time_offset.get()

    @payable
    def fallback(self):
        """
        If someone sends ICX directly to the SCORE, it goes to the SICXICX swap queue.
        Repeat orders bump back your spot in line.
        """
        order_id = self.icxQueueOrderId[self.msg.sender]
        if order_id:
            # First, modify our order
            node = self.icxQueue._get_node(order_id)
            node.set_value1(node.get_value1() + self.msg.value)
            # Next, bump the user to the end of the line if it is not the tail
            if self.icxQueue._length.get() > 1:
                self.icxQueue.move_node_tail(order_id)
        else:
            order_id = self.icxQueue.append(self.msg.value, self.msg.sender)
            self.icxQueueOrderId[self.msg.sender] = order_id

        current_icx_total = self.icxQueueTotal.get() + self.msg.value
        self.icxQueueTotal.set(current_icx_total)

        self.icxWithdrawLock[self.msg.sender] = self.now()
        if self.msg.sender not in self.funded_addresses:
            self.funded_addresses.add(self.msg.sender)
        self._updateAccountSnapshot(self.msg.sender, 0)
        self._updateTotalSupplySnapshot(0)

    @external
    def cancelSicxicxOrder(self):
        """
        Cancels user's order in the SICXICX queue.
        Cannot be called within 1 day of the withdraw lock time.
        """
        if not self.icxQueueOrderId[self.msg.sender]:
            revert("No open order in SICXICX queue")

        if self.icxWithdrawLock[self.msg.sender] + WITHDRAW_LOCK_TIMEOUT > self.now():
            revert("Withdraw lock not expired")

        order_id = self.icxQueueOrderId[self.msg.sender]
        order = self.icxQueue._get_node(order_id)
        withdraw_amount = order.get_value1()

        current_icx_total = self.icxQueueTotal.get() - withdraw_amount
        self.icxQueueTotal.set(current_icx_total)

        self.icxQueue.remove(order_id)
        self.icx.transfer(self.msg.sender, withdraw_amount)
        del self.icxQueueOrderId[self.msg.sender]

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        # if user sends some irc token to score
        Logger.info("called token fallback", self._TAG)

        # Update snapshots if necessary and notify the rewards score
        self._take_new_day_snapshot()
        self._check_distributions()

        unpacked_data = json_loads(_data.decode('utf-8'))
        _fromToken = self.msg.sender
        if unpacked_data["method"] == "_deposit":
            self.deposit[_fromToken][_from] += _value
            self.Deposit(_fromToken, _from, _value)
        elif unpacked_data["method"] == "_swap_icx":
            if _fromToken == self._sICX_address.get():
                self.sicx_convert(_from, _value)
        elif unpacked_data["method"] == "_swap":
            self.exchange(_fromToken, Address.from_string(unpacked_data["params"]["toToken"]), _from, _from, _value)
        elif unpacked_data["method"] == "_transfer":
            self.exchange(_fromToken, unpacked_data["params"]["toToken"], _from, Address.from_string(
                unpacked_data["params"]["to"]), _value)
        else:
            revert("Fallback directly not allowed")

    @external
    def precompute(self, snap: int, batch_size: int) -> bool:
        """
        Required by the rewards score data source API, but unneeded.
        Returns true to match the required workflow.
        """
        return True

    @external
    def transfer(self, _to: Address, _value: int, _id: int, _data: bytes = None):
        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)

    def _transfer(self, _from: Address, _to: Address, _value: int, _id: int, _data: bytes):
        if _value < 0:
            revert("Transferring value cannot be less than 0")
        if self.balance[_id][_from] < _value:
            revert("Out of balance")

        if _to not in self.funded_addresses:
            self.funded_addresses.add(_to)

        self.balance[_id][_from] = self.balance[_from] - _value
        self.balance[_id][_to] = self.balance[_to] + _value

        self.TransferSingle(self.msg.sender, _from, _to, _id, _value)

        self._updateAccountSnapshot(self.msg.sender, _id)

        # TODO: Implement token fallback for multitoken score

    ####################################
    # Read
    @external(readonly=True)
    def getDeposit(self, _tokenAddress: Address, _user: Address) -> int:
        return self.deposit[_tokenAddress][_user]

    @external(readonly=True)
    def getPoolId(self, _token1Address: Address, _token2Address: Address) -> int:
        return self.poolId[_token1Address][_token2Address]

    @external(readonly=True)
    def getNonce(self) -> int:
        return self.nonce.get()

    @external(readonly=True)
    def getNamedPools(self) -> list:
        rv = []
        for pool in self.named_markets.keys():
            rv.append(pool)
        return rv

    @external(readonly=True)
    def lookupPid(self, _name: str) -> int:
        return self.named_markets[_name]

    @external(readonly=True)
    def getPoolTotal(self, _pid: int, _token: Address) -> int:
        return self.poolTotal[_pid][_token]

    @external(readonly=True)
    def totalSupply(self, _pid: int) -> int:
        if _pid == 0:
            return self.icxQueueTotal.get()
        return self.total[_pid]

    @external(readonly=True)
    def balanceOf(self, _owner: Address, _id: int) -> int:
        """
        Returns the balance of the owner's tokens.
        NOTE: ID 0 will return SICXICX balance
        :param _owner: the address of the token holder
        :param _id: ID of the token/pool
        :return: the _owner's balance of the token type requested
        """
        if _id == 0:
            order_id = self.icxQueueOrderId[self.msg.sender]
            if not order_id:
                return 0
            return self.icxQueue._get_node(order_id).get_value1()
        else:
            return self.balance[_id][_owner]

    @external(readonly=True)
    def getFees(self) -> int:
        return self.fees.get()

    @external(readonly=True)
    def getPoolBase(self, _pid: int) -> Address:
        return self.poolBase[_pid]

    @external(readonly=True)
    def getPoolQuote(self, _pid: int) -> Address:
        return self.poolQuote[_pid]

    @external(readonly=True)
    def getPrice(self, _pid: int) -> int:
        return int(self.poolTotal[_pid][self.poolBase[_pid]] / self.poolTotal[_pid][self.poolQuote[_pid]] * 10**10)

    @external(readonly=True)
    def getInversePrice(self, _pid: int) -> int:
        return int(self.poolTotal[_pid][self.poolQuote[_pid]] / self.poolTotal[_pid][self.poolBase[_pid]] * 10**10)

    @external(readonly=True)
    def getICXBalance(self, _address: Address) -> int:
        order_id = self.icxQueueOrderId[_address]
        if not order_id:
            return 0
        return self.icxQueue._get_node(order_id).get_value1()

    @external(readonly=True)
    def getICXWithdrawLock(self) -> int:
        return self.icxWithdrawLock[self.msg.sender]

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
        self.approvals[self.msg.sender][_operator] = _approved
        self.ApprovalForAll(self.msg.sender, _operator, _approved)

    @external(readonly=True)
    def isApprovedForAll(self, _owner: Address, _operator: Address) -> bool:
        """
        Returns the approval status of an operator for a given owner.

        :param _owner: the owner of the tokens
        :param _operator: the address of authorized operator
        :return: true if the operator is approved, false otherwise
        """
        if self.approvals[_owner][_operator]:
            return self.approvals[_owner][_operator]
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
        if self.balance[_id][_from] < _value:
            revert("Out of balance")

        self.balance[_id][_from] = self.balance[_from] - _value
        self.balance[_id][_to] = self.balance[_to] + _value
        self.TransferSingle(self.msg.sender, _from, _to, _id, _value)

        if _to not in self.funded_addresses:
            self.funded_addresses.add(_to)

        self._updateAccountSnapshot(_from, _id)

        # TODO: Implement onIRC31Received function

    @external(readonly=True)
    def hasUsedDex(self, _user: Address) -> bool:
        """
        Returns whether an address has previously used the dex.

        :param _user: Address to check
        """
        return _user in self.funded_addresses

    @external(readonly=True)
    def totalDexAddresses(self) -> int:
        """
        Returns total number of users that have used the dex.

        :param _user: Address to check
        """
        return self.funded_addresses.__len__()

    def _get_exchange_rate(self) -> int:
        """
        Internal function for use in SICXICX pools.
        Gets the current exchange rate (expressed in units 1 = 1e18).
        Requires that the _staking_address property is set via the contract admin.
        """
        staking_score = self.create_interface_score(
            self._staking_address.get(), stakingInterface)
        return staking_score.getTodayRate()

    ####################################
    # Internal exchange function

    def exchange(self, _fromToken: Address, _toToken: Address, _sender: Address, _receiver: Address, _value: int):
        fees = int(_value * (self.fees.get() / 1000))
        original_value = _value
        _value -= fees
        Logger.info('From Token: ' + str(_fromToken), self._TAG)
        Logger.info('To Token: ' + str(_toToken), self._TAG)
        _pid = self.poolId[_fromToken][_toToken]
        Logger.info('Pool ID: ' + str(self.getPoolId(_fromToken, _toToken)), self._TAG)
        Logger.info('Inv Pool ID: ' + str(self.getPoolId(_toToken, _fromToken)), self._TAG)
        pool1base = self.getPoolBase(1)
        pool1quote = self.getPoolQuote(1)
        Logger.info('Pool 1 base: ' + str(pool1base) + ' pool 1 quote: ' + str(pool1quote), self._TAG)
        Logger.info('Matches quote: ' + str(pool1quote == _fromToken) + ' matches base: ' + str(pool1base == _fromToken), self._TAG)
        Logger.info('Matches quote: ' + str(pool1quote == _toToken) + ' matches base: ' + str(pool1base == _toToken), self._TAG)
        if _pid == 0:
            revert("Pool does not exist")
        Logger.info("PID: " + str(_pid), self._TAG)
        old_price = self.getPrice(_pid)
        if not self.active[_pid]:
            revert("Pool is not active")
        new_token1 = self.poolTotal[_pid][_fromToken] + _value
        new_token2 = int(
            self.poolTotal[_pid][_fromToken] * self.poolTotal[_pid][_toToken] / new_token1)
        send_amt = self.poolTotal[_pid][_toToken] - new_token2

        if original_value / send_amt < (old_price * 975) / 1000:
            revert("Maximum Slippage exceeded")

        else:
            token_score = self.create_interface_score(_toToken, TokenInterface)
            token_score.transfer(self.msg.sender, send_amt)
        self.poolTotal[_pid][_fromToken] = new_token1 + fees
        self.poolTotal[_pid][_toToken] = new_token2
        self.Swap(_fromToken, _toToken, _sender, _receiver, _value, send_amt)

    def _get_sicx_rate(self) -> int:
        staking_score = self.create_interface_score(
            self._staking_address.get(), stakingInterface)
        return staking_score.getTodayRate()

    @external
    def sicx_convert(self, _sender: Address, _value: int):
        """
        Perform an instant conversion from SICX to ICX.
        Gets orders from SICXICX queue by price time precedence.
        """
        remaining_sicx = _value
        conversion_factor = self._get_sicx_rate()

        sicx_score = self.create_interface_score(
            self._sICX_address.get(), TokenInterface)
        filled = False
        filled_icx = 0
        removed_icx = 0
        while not filled:

            if self.icxQueue._length.get() == 0:
                Logger.info("Transferring remaining SICX", 'DEX')
                sicx_score.transfer(_sender, remaining_sicx)
                break

            counterparty_order = self.icxQueue._get_head_node()
            counterparty_address = counterparty_order.get_value2()
            order_sicx_value = (int)(counterparty_order.get_value1() * EXA /
                                     conversion_factor)
            # Perform match. Matched amount is up to order size
            matched_sicx = min(order_sicx_value, remaining_sicx)
            matched_icx = (int)(matched_sicx * conversion_factor / EXA)
            filled_icx += (int)((matched_icx * 99) / 100)
            removed_icx += matched_icx

            dividends_contribution = (int)((matched_icx * 3) / 1000)
            self.icx.transfer(self._dividends.get(),
                              dividends_contribution)

            sicx_score.transfer(counterparty_address, matched_sicx)
            self.icx.transfer(counterparty_address, (int)
                              ((matched_icx * 7) / 1000))

            if matched_icx == counterparty_order.get_value1():
                self.icxQueue.remove_head()
                del self.icxQueueOrderId[counterparty_address]
            else:
                counterparty_order.set_value1(
                    counterparty_order.get_value1() - matched_icx)

            remaining_sicx -= matched_sicx
            if not remaining_sicx:
                filled = True

        current_icx_total = self.icxQueueTotal.get() - removed_icx
        self.icxQueueTotal.set(current_icx_total)

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
            dividends = self.create_interface_score(self._dividends.get(), Dividends)
            self._dividends_done.set(dividends.distribute())

    def _updateAccountSnapshot(self, _account: Address, _id: int) -> None:
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

    def _updateTotalSupplySnapshot(self, _id: int) -> None:
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
    def loadBalancesAtSnapshot(self, _pid: int, _snapshot_id: int, _limit: int,  _offset: int = 0) -> dict:
        if _snapshot_id < 0:
            revert(f'Snapshot id is equal to or greater then Zero')
        if _pid < 0:
            revert(f'Pool id must be equal to or greater than Zero')
        if _offset < 0:
            revert(f'Offset must be equal to or greater than Zero')
        rv = {}
        for addr in self.funded_addresses.select(_offset):
            snapshot_balance = self.balanceOfAt(addr, _pid, _snapshot_id)
            if snapshot_balance:
                rv[str(addr)] = snapshot_balance
        return rv

    @external(readonly=True)
    def getDataBatch(self, _name: str, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        pid = self.named_markets[_name]
        rv = self.loadBalancesAtSnapshot(pid, _snapshot_id, _limit, _offset)
        Logger.info(len(rv), self._TAG)
        return rv

    ####################################
    # Owner permission for new pools

    @external
    def permit(self, _pid: int, _permission: bool):
        if self.msg.sender != self.owner:
            revert("only owner can set admins")
        self.active[_pid] = _permission

    @external
    def withdraw(self, _token: Address, _value: int):
        if _value > self.deposit[_token][self.msg.sender]:
            revert("Insufficient balance")
        self.deposit[_token][self.msg.sender] -= _value
        token_score = self.create_interface_score(_token, TokenInterface)
        token_score.transfer(self.msg.sender, _value)
        self.Withdraw(_token, self.msg.sender, _value)

    @external
    def remove(self, _pid: int, _value: int):
        balance = self.balance[_pid][self.msg.sender]
        if not self.active[_pid]:
            revert("Pool is not active")
        if _value > balance:
            revert("Invalid input")
        if self.withdrawLock[self.msg.sender][_pid] + WITHDRAW_LOCK_TIMEOUT < self.now():
            revert("Funds not yet unlocked")
        token1 = self.poolBase[_pid]
        token2 = self.poolQuote[_pid]
        self.poolTotal[_pid][token1] -= int(self.poolTotal[_pid]
                                            [token1] * (_value / self.total[_pid]))
        self.poolTotal[_pid][token2] -= int(self.poolTotal[_pid]
                                            [token2] * (_value / self.total[_pid]))
        self.deposit[token1][self.msg.sender] += int(
            self.poolTotal[_pid][token1] * (_value / self.total[_pid]))
        self.deposit[token2][self.msg.sender] += int(
            self.poolTotal[_pid][token2] * (_value / self.total[_pid]))
        self.balance[_pid][self.msg.sender] -= _value
        self.total[_pid] -= _value
        self.Remove(_pid, self.msg.sender, _value)
        self._updateAccountSnapshot(self.msg.sender, _pid)
        self._updateTotalSupplySnapshot(_pid)

    @external
    def add(self, _baseToken: Address, _quoteToken: Address, _baseValue: int, _quoteValue: int):
        """
        Adds liquidity to a pool for trading, or creates a new pool. Rules:
        - The quote coin of the pool must be one of the allowed quote currencies.
        - Tokens must be deposited in the pool's ratio.
        - If ratio is incorrect, it is advisable to call `swap` first.
        """
        _owner = self.msg.sender
        _pid = self.poolId[_baseToken][_quoteToken]
        if _baseToken == _quoteToken:
            revert("Pool must contain two token contracts")
        if not _baseValue:
            revert("Please send initial value for first currency")
        if not _quoteValue:
            revert("Please send initial value for second currency")
        if _pid == 0:
            self.poolId[_baseToken][_quoteToken] = self.nonce.get()
            self.poolId[_quoteToken][_baseToken] = self.nonce.get()
            _pid = self.nonce.get()
            liquidity = DEFAULT_INITAL_LP
            self.nonce.set(self.nonce.get() + 1)
            self.active[_pid] = True
            self.poolBase[_pid] = _baseToken
            self.poolQuote[_pid] = _quoteToken
        else:
            token1price = self.getPrice(_pid)
            if not int(_baseValue * (token1price / 10**10)) == _quoteValue:
                revert('disproportionate amount')
            liquidity = int(self.total[_pid] * (self.poolTotal[_pid]
                                                [_baseToken] + _baseValue) / self.poolTotal[_pid][_baseToken])
        self.poolTotal[_pid][_baseToken] += _baseValue
        self.poolTotal[_pid][_quoteToken] += _quoteValue
        self.deposit[_baseToken][self.msg.sender] -= _baseValue
        self.deposit[_quoteToken][self.msg.sender] -= _quoteValue
        self.balance[_pid][_owner] += liquidity
        self.total[_pid] += liquidity
        self.Add(_pid, _owner, liquidity)
        self.withdrawLock[self.msg.sender][_pid] = self.now()
        if self.msg.sender not in self.funded_addresses:
            self.funded_addresses.add(self.msg.sender)
        self._updateAccountSnapshot(_owner, _pid)
        self._updateTotalSupplySnapshot(_pid)
