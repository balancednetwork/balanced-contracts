from iconservice import *
from ..utils.checks import *
from ..utils.consts import *
from .positions import PositionsDB
from .assets import AssetsDB, Asset

TAG = 'BalancedLoans'

# For testing only
TEST_ADDRESS = Address.from_string('hx3f01840a599da07b0f620eeae7aa9c574169a4be')


# An interface to the Emergency Reserve Fund
class ReserveFund(InterfaceScore):
    @interface
    def redeem(self, _to: Address, _amount: int, _sicx_rate: int) -> int:
        pass


# An interface to the Staking Management SCORE
class Staking(InterfaceScore):
    @interface
    def stakeICX(self, _to: Address = None, _data: bytes = None) -> int:
        pass


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


# An interface of token
class TokenInterface(InterfaceScore):
    @interface
    def symbol(self) -> str:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


class Loans(IconScoreBase):
    _TEST_MODE = "test_mode"
    _LOANS_ON = 'loans_on'
    _GOVERNANCE = 'governance'
    _DIVIDENDS = 'dividends'
    _RESERVE = 'reserve'
    _REWARDS = 'rewards'
    _STAKING = 'staking'
    _ADMIN = 'admin'
    _SNAP_BATCH_SIZE = 'snap_batch_size'
    _GLOBAL_INDEX = 'global_index'
    _GLOBAL_BATCH_INDEX = 'global_batch_index'

    _REWARDS_DONE = 'rewards_done'
    _DIVIDENDS_DONE = 'dividends_done'
    _CURRENT_DAY = 'current_day'
    _TIME_OFFSET = 'time_offset'

    _MINING_RATIO = 'mining_ratio'
    _LOCKING_RATIO = 'locking_ratio'
    _LIQUIDATION_RATIO = 'liquidation_ratio'
    _ORIGINATION_FEE = 'origination_fee'
    _REDEMPTION_FEE = 'redemption_fee'
    _RETIREMENT_BONUS = 'retirement_bonus'
    _LIQUIDATION_REWARD = 'liquidation_reward'
    _REDEEM_MINIMUM = 'redeem_minimum'
    _NEW_LOAN_MINIMUM = 'new_loan_minimum'
    _MIN_MINING_DEBT = 'min_mining_debt'
    _MAX_DEBTS_LIST_LENGTH = 'max_debts_list_length'

    _REDEEM_BATCH_SIZE = 'redeem_batch_size'
    _MAX_RETIRE_PERCENT = 'max_retire_percent'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._test_mode = VarDB(self._TEST_MODE, db, value_type=bool)
        self._loans_on = VarDB(self._LOANS_ON, db, value_type=bool)
        self._governance = VarDB(self._GOVERNANCE, db, value_type=Address)
        self._dividends = VarDB(self._DIVIDENDS, db, value_type=Address)
        self._reserve = VarDB(self._RESERVE, db, value_type=Address)
        self._rewards = VarDB(self._REWARDS, db, value_type=Address)
        self._staking = VarDB(self._STAKING, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._snap_batch_size = VarDB(self._SNAP_BATCH_SIZE, db, value_type=int)
        self._global_index = VarDB(self._GLOBAL_INDEX, db, value_type=int)
        self._global_batch_index = VarDB(self._GLOBAL_BATCH_INDEX, db, value_type=int)

        self._assets = AssetsDB(db, self)
        self._positions = PositionsDB(db, self)
        self._rewards_done = VarDB(self._REWARDS_DONE, db, value_type=bool)
        self._dividends_done = VarDB(self._DIVIDENDS_DONE, db, value_type=bool)
        self._current_day = VarDB(self._CURRENT_DAY, db, value_type=int)
        self._time_offset = VarDB(self._TIME_OFFSET, db, value_type=int)

        self._mining_ratio = VarDB(self._MINING_RATIO, db, value_type=int)
        self._locking_ratio = VarDB(self._LOCKING_RATIO, db, value_type=int)
        self._liquidation_ratio = VarDB(self._LIQUIDATION_RATIO, db, value_type=int)
        self._origination_fee = VarDB(self._ORIGINATION_FEE, db, value_type=int)
        self._redemption_fee = VarDB(self._REDEMPTION_FEE, db, value_type=int)
        self._retirement_bonus = VarDB(self._RETIREMENT_BONUS, db, value_type=int)
        self._liquidation_reward = VarDB(self._LIQUIDATION_REWARD, db, value_type=int)
        self._redeem_minimum = VarDB(self._REDEEM_MINIMUM, db, value_type=int)
        self._new_loan_minimum = VarDB(self._NEW_LOAN_MINIMUM, db, value_type=int)
        self._min_mining_debt = VarDB(self._MIN_MINING_DEBT, db, value_type=int)
        self._max_debts_list_length = VarDB(self._MAX_DEBTS_LIST_LENGTH, db, value_type=int)

        # batch size for redeem-retire
        self._redeem_batch = VarDB(self._REDEEM_BATCH_SIZE, db, value_type=int)
        # max percentage of the batch total debt that can be accepted in one redemption.
        self._max_retire_percent = VarDB(self._MAX_RETIRE_PERCENT, db, value_type=int)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._test_mode.set(False)
        self._governance.set(_governance)
        self._loans_on.set(False)
        self._admin.set(self.owner)
        self._snap_batch_size.set(SNAP_BATCH_SIZE)
        self._rewards_done.set(True)
        self._dividends_done.set(True)
        self._mining_ratio.set(DEFAULT_MINING_RATIO)
        self._locking_ratio.set(DEFAULT_LOCKING_RATIO)
        self._liquidation_ratio.set(DEFAULT_LIQUIDATION_RATIO)
        self._origination_fee.set(DEFAULT_ORIGINATION_FEE)
        self._redemption_fee.set(DEFAULT_REDEMPTION_FEE)
        self._liquidation_reward.set(LIQUIDATION_REWARD)
        self._retirement_bonus.set(BAD_DEBT_RETIREMENT_BONUS)
        self._redeem_minimum.set(REDEEM_MINIMUM)
        self._new_loan_minimum.set(NEW_LOAN_MINIMUM)
        self._min_mining_debt.set(DEFAULT_MIN_MINING_DEBT)
        self._redeem_batch.set(DEFAULT_REDEEM_BATCH_SIZE)
        self._max_retire_percent.set(DEFAULT_MAX_RETIRE_PERCENT)
        self._max_debts_list_length.set(MAX_DEBTS_LIST_LENGTH)

    def on_update(self) -> None:
        super().on_update()
        self._redeem_minimum.set(REDEEM_MINIMUM)

    @payable
    @external
    def create_test_position(self, _address: Address, _asset: str, _amount: int) -> None:
        # Create bad position for testing liquidation. Take out a loan that is too large.
        # Add ICX collateral via staking contract.
        if not self._test_mode.get():
            revert(f'This method may only be called in test mode.')
        params = {"_sender": str(_address), "_asset": "", "_amount": 0}
        data = json_dumps({"method": "_deposit_and_borrow", "params": params}).encode("utf-8")
        staking = self.create_interface_score(self._staking.get(), Staking)
        staking.icx(self.msg.value).stakeICX(self.address, data)
        pos = self._positions.get_pos(_address)
        # Mint asset for this position.
        if _amount > 0:
            self._assets[_asset].mint(_address, _amount)
            pos[_asset] += _amount
        pos.update_standing()

    @external
    @only_owner
    def toggleTestMode(self) -> None:
        self._test_mode.set(not self._test_mode.get())

    @external(readonly=True)
    def getTestMode(self) -> bool:
        return self._test_mode.get()

    @external
    @only_owner
    def setRedeemBatchSize(self, _value: int):
        self._redeem_batch.set(_value)

    @external(readonly=True)
    def getRedeemBatchSize(self) -> int:
        return self._redeem_batch.get()

    @external(readonly=True)
    def name(self) -> str:
        return "Balanced Loans"

    @external(readonly=True)
    def snapIndexes(self) -> List[int]:
        """
        Diagnostic only. Will be removed for production.
        """
        indexes = []
        for i in self._positions._snapshot_db._indexes:
            indexes.append(i)
        return indexes

    @external
    @only_governance
    def turnLoansOn(self) -> None:
        self._loans_on.set(True)
        self.ContractActive("Loans", "Active")
        self._current_day.set(self.getDay())
        self._positions._snapshot_db.start_new_snapshot()

    @external
    @only_governance
    def toggleLoansOn(self) -> None:
        self._loans_on.set(not self._loans_on.get())
        self.ContractActive("Loans", "Active" if self._loans_on.get() else "Inactive")

    @external(readonly=True)
    def getLoansOn(self) -> bool:
        return self._loans_on.get()

    @external(readonly=True)
    def getDay(self) -> int:
        return (self.now() - self._time_offset.get()) // U_SECONDS_DAY

    @external(readonly=True)
    def getDebts(self, _address_list: List[str], _day: int) -> dict:
        """
        Returns the debt held by each address in the list.
        """
        max_length = self._max_debts_list_length.get()
        if len(_address_list) > max_length:
            revert(f'Address list is longer than the maximum allowable length ({max_length}).')
        debts = {}
        for address in _address_list:
            pos_id = self._positions.get_id_for(Address.from_string(address))
            snapshot = self._positions._snapshot_db[_day]
            debts[address] = snapshot.pos_state[pos_id]['total_debt']
        return debts

    @external(readonly=True)
    def getMaxRetireAmount(self, _symbol: str) -> int:
        batch_size = self._redeem_batch.get()
        borrowers = self._assets[_symbol].borrowers
        node_id = borrowers._head_id.get()
        tail_id = borrowers._tail_id.get()
        total_batch_debt: int = 0

        for i in range(min(batch_size, len(borrowers))):
            user_position = self._positions[borrowers.node_value(node_id)]
            user_debt = user_position[_symbol]
            total_batch_debt += user_debt
            if tail_id != node_id:
                node_id = borrowers.next(node_id)

        bad_debt = self._assets[_symbol].bad_debt.get()
        return bad_debt + self._max_retire_percent.get() * total_batch_debt // POINTS

    @external(readonly=True)
    def checkDeadMarkets(self) -> list:
        """
        Returns the symbols for all assets with dead_market status.
        """
        dead_markets = []
        for symbol in self._assets.slist:
            if self._assets[symbol].dead_market.get():
                dead_markets.append(symbol)
        return dead_markets

    @external(readonly=True)
    def getNonzeroPositionCount(self) -> int:
        """
        Returns the total number of nonzero positions.
        """
        pos = self._positions
        snap = pos._snapshot_db[-1]
        nonzero = len(pos.nonzero) + len(snap.add_to_nonzero) - len(snap.remove_from_nonzero)
        if snap.snap_day.get() > 1:
            last_snap = pos._snapshot_db[-2]
            nonzero += len(last_snap.add_to_nonzero) - len(last_snap.remove_from_nonzero)
        return nonzero

    @external(readonly=True)
    def getPositionStanding(self, _address: Address, _snapshot: int = -1) -> dict:
        """
        Returns the current standing for a position.
        """
        pos = self._positions.get_pos(_address)
        status = pos.get_standing(_snapshot, True)
        status['standing'] = Standing.STANDINGS[status['standing']]
        return status

    @external(readonly=True)
    def getPositionAddress(self, _index: int) -> Address:
        """
        returns the address of a position given its index. Enables iteration over
        all positions in Balanced.
        """
        return self._positions[_index].address.get()

    @external(readonly=True)
    def getAssetTokens(self) -> dict:
        """
        Returns a dictionary of assets from the assetsDB with token symbol as
        the key and address as a string value.
        """
        assets = {}
        for symbol in self._assets.slist:
            assets[symbol] = self._assets.symboldict[symbol]
        return assets

    @external(readonly=True)
    def getCollateralTokens(self) -> dict:
        """
        Returns a dictionary of assets from the assetsDB that are marked as
        collateral, with token symbol as the key and address as a string value.
        """
        collateral = {}
        for symbol in self._assets.slist:
            if self._assets[symbol].is_collateral.get():
                collateral[symbol] = self._assets.symboldict[symbol]
        return collateral

    @external(readonly=True)
    def getTotalCollateral(self) -> int:
        """
        Sum of all active collateral held on the loans SCORE in loop.
        Read-only; does not check for a more recent price update.
        """
        total_collateral = 0
        for symbol in self._assets.slist:
            asset = self._assets[symbol]
            if asset.is_collateral.get() and asset.active.get():
                held = asset.balanceOf(self.address)
                price = asset.lastPriceInLoop()
                total_collateral += held * price
        return total_collateral // EXA

    @external(readonly=True)
    def getAccountPositions(self, _owner: Address) -> dict:
        """
        Get account positions.
        """
        return self._positions.list_pos(_owner)

    @external(readonly=True)
    def getPositionByIndex(self, _index: int, _day: int) -> dict:
        """
        Get account positions.
        """
        return self._positions[_index].to_dict(_day)

    @external(readonly=True)
    def getAvailableAssets(self) -> dict:
        """
        Returns a dict of assets.
        """
        return self._assets.get_assets()

    @external(readonly=True)
    def assetCount(self) -> int:
        """
        Returns the number of assets in the AssetsDB.
        """
        return len(self._assets)

    @external(readonly=True)
    def borrowerCount(self) -> int:
        """
        Returns the number of borrowers on Balanced.
        """
        return len(self._positions)

    @external(readonly=True)
    def hasDebt(self, _owner: Address) -> bool:
        """
        Returns whether the address holds a debt position.
        """
        pos = self._positions.get_pos(_owner)
        return pos.has_debt()

    @external(readonly=True)
    def getSnapshot(self, _snap_id: int = -1) -> dict:
        """
        Returns a summary of the snapshot for the system. Returns an empty dict
        for snapshot indexes that are out of range.
        """
        if (_snap_id > self._positions._snapshot_db._indexes[-1] or
                _snap_id + len(self._positions._snapshot_db._indexes) < 0):
            return {}
        return self._positions._snapshot_db[_snap_id].to_dict()

    @external
    @only_admin
    def addAsset(self, _token_address: Address,
                 _active: bool = True,
                 _collateral: bool = False) -> None:
        """
        Adds a token to the assets dictionary.
        """
        self._assets.add_asset(_token_address, _active, _collateral)
        token_score = self.create_interface_score(_token_address, TokenInterface)
        self.AssetAdded(_token_address, token_score.symbol(), _collateral)

    @external
    @only_admin
    def toggleAssetActive(self, _symbol) -> None:
        asset = self._assets[_symbol]
        asset.active.set(not asset.active.get())
        self.AssetActive(_symbol, "Active" if asset.active.get() else "Inactive")

    @external
    def precompute(self, _snapshot_id: int, batch_size: int) -> bool:
        """
        prepares the position data snapshot to send to the rewards SCORE.
        """
        if self.msg.sender != self._rewards.get():
            revert(f'The precompute method may only be invoked by the rewards SCORE.')
        self.checkForNewDay()  # Only does something if it is internal on a DEX tx.
        # Iterate through all positions in the snapshot to bring them up to date.
        if self._positions._calculate_snapshot(_snapshot_id, batch_size):
            return Complete.DONE
        return Complete.NOT_DONE

    @external(readonly=True)
    def getTotalValue(self, _name: str, _snapshot_id: int) -> int:
        """
        Gets total outstanding debt for mining rewards calculation.
        """
        return self._positions._snapshot_db[_snapshot_id].total_mining_debt.get()

    @external(readonly=True)
    def getDataCount(self, _snapshot_id: int) -> int:
        """
        Returns the number of records in the snapshot.
        """
        return len(self._positions._snapshot_db[_snapshot_id].mining)

    @external(readonly=True)
    def getDataBatch(self, _name: str, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        """
        Read position data batch.
        """
        batch = {}
        snapshot = self._positions._snapshot_db[_snapshot_id]
        total_mining = len(snapshot.mining)
        start = max(0, min(_offset, total_mining))
        end = min(_offset + _limit, total_mining)
        for i in range(start, end):
            pos_id = snapshot.mining[i]
            pos = self._positions[pos_id]
            batch[str(pos.address.get())] = snapshot.pos_state[pos_id]['total_debt']
        return batch

    @external
    def checkForNewDay(self) -> (int, bool):
        day = self.getDay()
        new_day: bool = False
        if day > self._current_day.get():
            new_day = True
            self._current_day.set(day)
            self._positions._take_snapshot()
            self.check_dead_markets()
        return day, new_day

    @external
    def checkDistributions(self, _day: int, _new_day: bool) -> None:
        if _new_day and self._rewards_done.get() and self._dividends_done.get():
            self._rewards_done.set(False)
            if _day % 7 == 0:
                self._dividends_done.set(False)
        elif not self._dividends_done.get():
            dividends = self.create_interface_score(self._dividends.get(), Dividends)
            self._dividends_done.set(dividends.distribute())
        elif not self._rewards_done.get():
            rewards = self.create_interface_score(self._rewards.get(), Rewards)
            self._rewards_done.set(rewards.distribute())

    @payable
    @external
    def addCollateral(self, _asset: str = '', _amount: int = 0) -> None:
        """
        Sends ICX to the addCollateral method on the staking SCORE and specifies
        an amount and type of asset to borrow.

        :param _asset: Symbol for the pegged asset to borrow.
        :type _asset: str
        :param _amount: Amount of asset to borrow.
        :type _amount: int
        """
        params = {"_sender": str(self.msg.sender), "_asset": _asset, "_amount": _amount}
        data = json_dumps({"method": "_deposit_and_borrow", "params": params}).encode("utf-8")
        staking = self.create_interface_score(self._staking.get(), Staking)
        staking.icx(self.msg.value).stakeICX(self.address, data)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Directs incoming tokens to either deposit collateral or return an asset.

        :param _from: Address of the token sender.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Method and parameters to call once tokens are received.
        :type _data: bytes
        """
        if not self._loans_on.get():
            revert('Balanced is currently not accepting transactions.')
        if _value <= 0:
            revert(f'Amount sent must be greater than zero.')
        if self.msg.sender not in self._assets.alist:
            revert(f'The Balanced Loans contract does not accept that token type.')
        day, new_day = self.checkForNewDay()
        self.checkDistributions(day, new_day)
        if _from == self._reserve.get():
            return
        try:
            d = json_loads(_data.decode("utf-8"))
            if set(d.keys()) != {"method", "params"}:
                revert('Invalid parameters.')
            if d["method"] == "_deposit_and_borrow":
                self._deposit_and_borrow(_value, **d['params'])
            elif d["method"] == "_repay_loan":
                self._repay_loan(_from, _value)
            elif d["method"] == "_retire_asset":
                # TODO unexpected last param
                # self._retire_asset(_from, _value, **d['params'])
                self._retire_asset(_from, _value)
            else:
                revert(f'No valid method called, data: {_data}')
        except BaseException as e:
            revert(f'Invalid data: {_data}, returning tokens. Exception: {e}')

    def _deposit_and_borrow(self, _value: int, _sender: str, _asset: str = '',
                            _amount: int = 0) -> None:
        """
        If the received token type is sICX it will be added to the account of
        the token sender.
        If the optional parameters of _asset and _amount are present a loan of
        _amount of _asset will be returned to the originating address if
        there is sufficient collateral present.

        :param _sender: Address of the token sender.
        :type _sender: str
        :param _value: Number of tokens sent.
        :type _value: int
        :param _asset: Symbol of asset to borrow.
        :type _asset: str
        :param _amount: Size of loan requested.
        :type _amount: int
        """
        if self.msg.sender != self._assets['sICX'].asset_address.get():
            revert(f'sICX is the only type of collateral accepted.')
        _from = Address.from_string(_sender)
        pos = self._positions.get_pos(_from)
        pos['sICX'] += _value
        self.CollateralReceived(_from, 'sICX')
        if _asset == '' or _amount == 0:
            pos.update_standing()
            return
        self.originateLoan(_asset, _amount, _from=_from)

    def _repay_loan(self, _from: Address, _value: int) -> None:
        """
        If the received token type is in the asset list the loan position for
        the account of the token sender will be reduced by _value. If there is
        any excess it will be returned.

        :param _from: Address of the token sender.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        """
        if self.msg.sender == self._assets['sICX'].asset_address.get():
            revert(f'This method does not accept sICX tokens')
        if not self._positions._exists(_from):
            revert(f'This address does not have a position on Balanced.')
        if not _value > 0:
            revert(f'Repayment requires a positive value.')
        pos = self._positions.get_pos(_from)

        asset = self._assets._get_asset(str(self.msg.sender))
        symbol = asset.symbol()
        borrowed = pos[symbol]
        if borrowed == 0:
            revert(f'No debt exists to be repaid.')
        if borrowed - _value > 0:
            pos[symbol] -= _value
            repaid = _value
        else:
            repaid = borrowed
            refund = _value - repaid
            pos[symbol] = 0
            del pos[symbol]
            pos_id = pos.id.get()
            asset.remove_borrower(pos_id)
            if not pos.has_debt():
                self._positions.remove_nonzero(pos_id)
            if refund > 0:
                self._send_token(symbol, _from, refund, "Excess refunded.")
        if repaid != 0:
            asset.burn(repaid)
        self.LoanRepaid(_from, symbol, repaid,
            f'Loan of {repaid} {symbol} repaid to Balanced.')
        self.check_dead_markets()
        pos.update_standing()

    def _retire_asset(self, _from: Address, _value: int) -> None:
        """
        An asset holder who does not hold a position in the asset may retire
        it in exchange for collateral that comes proportionately from all
        collateral positions in the system.

        :param _from: Address of the token sender.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        """
        if _value <= 0:
            revert(f'Amount retired must be greater than zero.')
        asset = self._assets._get_asset(str(self.msg.sender))
        symbol = asset.symbol()
        if self._positions._exists(_from):
            pos = self._positions.get_pos(_from)
            repay = min(pos[symbol], _value)
            if repay > 0:
                self._repay_loan(_from, repay)
            if repay == _value:
                return
            else:
                _value -= repay
        price = asset.priceInLoop()
        redeem_min = self._redeem_minimum.get()
        min_value = redeem_min * self._assets['bnUSD'].priceInLoop() // price
        min_asset_value = min(min_value, 75 * self.getMaxRetireAmount(symbol) // 100)
        if _value < min_asset_value:
            revert(f'Minimum redeemed asset value is ${min_asset_value // EXA}')
        sicx_rate = self._assets['sICX'].priceInLoop()
        fee = _value * self._redemption_fee.get() // POINTS
        redeemed = _value - fee
        bad_debt = asset.bad_debt.get()
        supply = asset.totalSupply() - bad_debt
        asset.burn(redeemed)
        sicx: int = 0
        total_batch_debt = 0
        batch_dict = {}
        if bad_debt > 0:
            bd_value = min(bad_debt, redeemed)
            redeemed -= bd_value
            sicx += self.bd_redeem(_from, asset, bd_value, sicx_rate, price)
        if redeemed > 0:
            sicx_from_lenders = redeemed * price // sicx_rate
            sicx += sicx_from_lenders
            batch_dict = self._retire_redeem(symbol, redeemed, sicx_from_lenders)
            total_batch_debt = batch_dict[0]
            del batch_dict[0]
        self._send_token("sICX", _from, sicx, "Collateral redeemed.")
        self._send_token(symbol, self._dividends.get(), fee, "Redemption fee.")
        self.check_dead_markets()
        self.AssetRetired(symbol, redeemed, price, f'total_batch_debt: {total_batch_debt}, batch_dict: {batch_dict}, _from: {_from}')

    def _retire_redeem(self, _symbol: str, _redeemed: int, _sicx_from_lenders: int) -> dict:
        batch_size = self._redeem_batch.get()
        borrowers = self._assets[_symbol].borrowers
        pos_id = borrowers.head_value()
        total_batch_debt: int = 0
        positions_dict = {}

        for _ in range(min(batch_size, len(borrowers))):
            user_position = self._positions[pos_id]
            user_debt = user_position[_symbol]
            positions_dict[pos_id] = user_debt
            total_batch_debt += user_debt
            borrowers.move_head_to_tail()
            pos_id = borrowers.head_value()

        if POINTS * _redeemed > self._max_retire_percent.get() * total_batch_debt:
            revert(f'Retired amount is greater than the current maximum allowed.')
        remaining_value = _redeemed
        remaining_supply = total_batch_debt
        returned_sicx_remaining = _sicx_from_lenders

        for pos_id, user_debt in positions_dict.items():
            redeemed_from_this_pos = remaining_value * user_debt // remaining_supply
            remaining_value -= redeemed_from_this_pos
            self._positions[pos_id][_symbol] = user_debt - redeemed_from_this_pos

            sicx_share = returned_sicx_remaining * user_debt // remaining_supply
            returned_sicx_remaining -= sicx_share
            self._positions[pos_id]['sICX'] -= sicx_share

            remaining_supply -= user_debt

        positions_dict[0] = total_batch_debt
        return positions_dict

    def bd_redeem(self, _from: Address,
                  _asset: Asset,
                  _bd_value: int,
                  _sicx_rate: int,
                  _price: int) -> int:
        """
        Returns the amount of the bad debt paid off in sICX coming from both
        the liquidation pool for the asset or the ReserveFund SCORE.

        :param _from: Address of the token sender.
        :type _from: :class:`iconservice.base.address.Address`
        :param _asset: Balanced Asset that is being redeemed.
        :type _asset: :class:`loans.assets.Asset`
        :param _bd_value: Amount of bad debt to redeem.
        :type _bd_value: int
        :param _sicx_rate: Price of sICX in loop.
        :type _sicx_rate: int
        :param _price: Price of the asset in loop.
        :type _price: int

        :return: Amount of sICX supplied from reserve.
        :rtype: int
        """
        reserve_address = self._reserve.get()
        in_pool = _asset.liquidation_pool.get()
        bd_sicx = (POINTS + self._retirement_bonus.get()) * _bd_value * _price // (POINTS * _sicx_rate)
        if in_pool > bd_sicx:
            _asset.liquidation_pool.set(in_pool - bd_sicx)
            bad_debt = _asset.bad_debt.get() - _bd_value
            _asset.bad_debt.set(bad_debt)
            if bad_debt == 0:
                self._send_token('sICX', reserve_address, in_pool - bd_sicx, "Sweep to ReserveFund:")
                _asset.liquidation_pool.set(0)
            return bd_sicx
        _asset.liquidation_pool.set(0)
        reserve = self.create_interface_score(reserve_address, ReserveFund)
        return in_pool + reserve.redeem(_from, bd_sicx - in_pool, _sicx_rate)

    @external
    def originateLoan(self, _asset: str, _amount: int, _from: Address = None) -> None:
        """
        Originate a loan of an asset if there is sufficient collateral.

        :param _asset: Symbol of the asset.
        :type _asset: str
        :param _amount: Number of tokens sent.
        :type _amount: int
        :param _from
        :type _from: Address
        """
        if _from is None:
            _from = self.msg.sender
        if not self._positions._exists(_from):
            revert(f'This address does not have a position on Balanced. '
                   f'Collateral must be deposited before originating a loan.')
        if self._assets[_asset].dead():
            revert(f'No new loans of {_asset} can be originated since '
                   f'it is in a dead market state.')
        if self._assets[_asset].is_collateral.get():
            revert(f'Loans of collateral assets are not allowed.')
        if not self._assets[_asset].active.get():
            revert(f'Loans of inactive assets are not allowed.')
        if self.msg.sender != self._assets['sICX'].asset_address.get():  # to avoid doubling this call.
            day, new_day = self.checkForNewDay()
            self.checkDistributions(day, new_day)
        pos = self._positions.get_pos(_from)

        # Check for sufficient collateral
        collateral = pos._collateral_value()
        max_debt_value = POINTS * collateral // self._locking_ratio.get()
        fee = self._origination_fee.get() * _amount // POINTS
        new_debt_value = self._assets[_asset].priceInLoop() * (_amount + fee) // EXA
        # Check for loan minimum
        if pos[_asset] == 0:
            loan_minimum = self._new_loan_minimum.get()
            dollar_value = new_debt_value * EXA // self._assets['bnUSD'].priceInLoop()
            if dollar_value < loan_minimum:
                revert(f'The initial loan of any asset must have a minimum value '
                       f'of {loan_minimum / EXA} dollars.')
            pos_id = pos.id.get()
            self._assets[_asset].add_borrower(pos_id)
            if not pos.has_debt():
                self._positions.add_nonzero(pos_id)
        if pos._total_debt() + new_debt_value > max_debt_value:
            revert(f'{collateral / EXA} collateral is insufficient'
                   f' to originate a loan of {_amount / EXA} {_asset}'
                   f' when max_debt_value = {max_debt_value / EXA} and'
                   f' new_debt_value = {new_debt_value / EXA},'
                   f' plus a fee of {fee / EXA} {_asset},'
                   f' and an existing loan value of {pos._total_debt() / EXA}.')

        # Originate loan
        pos[_asset] += _amount + fee
        self.OriginateLoan(_from, _asset, _amount,
            f'Loan of {_amount} {_asset} from Balanced.')
        self._assets[_asset].mint(_from, _amount)

        # Pay fee
        self._assets[_asset].mint(self._dividends.get(), fee)
        self.FeePaid(_asset, fee, "origination", "")
        pos.update_standing()

    @external
    def withdrawCollateral(self, _value: int) -> None:
        """
        Withdraw sICX collateral up to the collateral locking ratio.

        :param _value: Amount of sICX to withdraw.
        :type _value: int
        """
        if _value <= 0:
            revert(f'Withdraw amount must be more than zero.')
        _from = self.msg.sender
        if not self._positions._exists(_from):
            revert(f'This address does not have a position on Balanced.')
        day, new_day = self.checkForNewDay()
        self.checkDistributions(day, new_day)
        pos = self._positions.get_pos(_from)

        if pos['sICX'] < _value:
            revert(f'Position holds less collateral than the requested withdrawal.')
        asset_value = pos._total_debt()  # Value in ICX
        remaining_sicx = pos['sICX'] - _value
        remaining_coll = remaining_sicx * self._assets['sICX'].priceInLoop() // EXA
        locking_value = self._locking_ratio.get() * asset_value // POINTS
        if remaining_coll < locking_value:
            revert(f'Requested withdrawal is more than available collateral. '
                   f'total debt value: {asset_value} ICX '
                   f'remaining collateral value: {remaining_coll} ICX '
                   f'locking value (max debt): {locking_value} ICX')
        pos['sICX'] = remaining_sicx
        self._send_token('sICX', _from, _value, "Collateral withdrawn.")
        pos.update_standing()

    @external
    def updateStanding(self, _owner: Address) -> int:
        """
        Update the standing of the position given current asset prices.

        :param _owner: Address of position to update.
        :type _owner: :class:`iconservice.base.address.Address`
        """
        if not self._positions._exists(_owner):
            revert(f'This address does not have a position on Balanced.')
        day, new_day = self.checkForNewDay()
        self.checkDistributions(day, new_day)
        pos = self._positions.get_pos(_owner)
        standing = pos.update_standing()
        total_debt = pos._total_debt()
        self.PositionStanding(_owner,
                              Standing.STANDINGS[standing],
                              0 if total_debt == 0 else pos._collateral_value() * EXA // total_debt,
                              "Position up to date.")
        return standing

    @external
    def liquidate(self, _owner: Address) -> None:
        """
        Liquidate collateral if the position is below the liquidation threshold.

        :param _owner: Address of position to update.
        :type _owner: :class:`iconservice.base.address.Address`
        """
        if not self._positions._exists(_owner):
            revert(f'This address does not have a position on Balanced.')
        _standing = self.updateStanding(_owner)
        if _standing == Standing.LIQUIDATE:
            pos = self._positions.get_pos(_owner)
            pos_id = pos.id.get()
            collateral = pos['sICX']
            reward = collateral * self._liquidation_reward.get() // POINTS
            for_pool = collateral - reward
            total_debt = pos._total_debt()
            for symbol in self._assets.slist:
                asset = self._assets[symbol]
                is_collateral = asset.is_collateral.get()
                active = asset.active.get()
                if not is_collateral and active and pos[symbol] > 0:
                    bad_debt = asset.bad_debt.get()
                    asset.bad_debt.set(bad_debt + pos[symbol])
                    symbol_debt = pos[symbol] * asset.priceInLoop() // EXA
                    share = for_pool * symbol_debt // total_debt
                    total_debt -= symbol_debt
                    for_pool -= share  # The share of the collateral for that asset.
                    pool = asset.liquidation_pool.get()
                    asset.liquidation_pool.set(pool + share)
                    asset.remove_borrower(pos_id)
                    pos[symbol] = 0
                    del pos[symbol]
            pos['sICX'] = 0
            self._send_token('sICX', self.msg.sender, reward, "Liquidation reward of")
            pos.update_standing()
            self.check_dead_markets()
            self._positions.remove_nonzero(pos_id)
            self.Liquidate(_owner, collateral, f'{collateral} liquidated from {_owner}')

    def check_dead_markets(self) -> None:
        """
        Checks if any of the assets have changed Dead Market status and updates
        them accordingly.
        """
        for symbol in self._assets.slist:
            self._assets[symbol].dead()

    def _send_token(self, _token: str, _to: Address, _amount: int, msg: str) -> None:
        """
        Sends IRC2 token to an address.
        :param _token: Token symbol.
        :type _token: str
        :param _to: Token destination address.
        :type _to: :class:`iconservice.base.address.Address`
        :param _amount: Number of tokens sent.
        :type _amount: int
        :param msg: Message for the event log.
        :type msg: str
        """
        address = self._assets[_token].asset_address.get()
        try:
            token_score = self.create_interface_score(address, TokenInterface)
            token_score.transfer(_to, _amount)
            self.TokenTransfer(_to, _amount, msg + f' {_amount} {_token} sent to {_to}.')
        except BaseException as e:
            revert(f'{_amount} {_token} not sent to {_to}. '
                   f'Exception: {e}')

    def fallback(self):
        pass

    # -------------------------------------------------------------------------------
    #   SETTERS AND GETTERS
    # -------------------------------------------------------------------------------

    @external
    @only_owner
    def setGovernance(self, _address: Address) -> None:
        self._governance.set(_address)

    @external
    @only_governance
    def setAdmin(self, _admin: Address) -> None:
        self._admin.set(_admin)

    @external
    @only_admin
    def setDividends(self, _address: Address) -> None:
        self._dividends.set(_address)

    @external
    @only_admin
    def setReserve(self, _address: Address) -> None:
        self._reserve.set(_address)

    @external
    @only_admin
    def setRewards(self, _address: Address) -> None:
        self._rewards.set(_address)

    @external
    @only_admin
    def setStaking(self, _address: Address) -> None:
        self._staking.set(_address)

    @external
    @only_admin
    def setMiningRatio(self, _ratio: int) -> None:
        self._mining_ratio.set(_ratio)

    @external
    @only_admin
    def setLockingRatio(self, _ratio: int) -> None:
        self._locking_ratio.set(_ratio)

    @external
    @only_admin
    def setLiquidationRatio(self, _ratio: int) -> None:
        self._liquidation_ratio.set(_ratio)

    @external
    @only_admin
    def setOriginationFee(self, _fee: int) -> None:
        self._origination_fee.set(_fee)

    @external
    @only_admin
    def setRedemptionFee(self, _fee: int) -> None:
        self._redemption_fee.set(_fee)

    @external
    @only_admin
    def setLiquidationReward(self, _points: int) -> None:
        self._liquidation_reward.set(_points)

    @external
    @only_admin
    def setRedeemMinimum(self, _minimum: int) -> None:
        self._redeem_minimum.set(_minimum)

    @external
    @only_admin
    def setNewLoanMinimum(self, _minimum: int) -> None:
        self._new_loan_minimum.set(_minimum)

    @external
    @only_admin
    def setMinMiningDebt(self, _minimum: int) -> None:
        self._min_mining_debt.set(_minimum)

    @external
    @only_governance
    def setTimeOffset(self, _delta_time: int) -> None:
        self._time_offset.set(_delta_time)

    @external(readonly=True)
    def getParameters(self) -> dict:
        return {
            "admin": self._admin.get(),
            "governance": self._governance.get(),
            "dividends": self._dividends.get(),
            "reserve_fund": self._reserve.get(),
            "rewards": self._rewards.get(),
            "staking": self._staking.get(),
            "mining ratio": self._mining_ratio.get(),
            "locking ratio": self._locking_ratio.get(),
            "liquidation ratio": self._liquidation_ratio.get(),
            "origination fee": self._origination_fee.get(),
            "redemption fee": self._redemption_fee.get(),
            "liquidation reward": self._liquidation_reward.get(),
            "redeem minimum": self._redeem_minimum.get(),
            "new loan minimum": self._new_loan_minimum.get(),
            "min mining debt": self._min_mining_debt.get(),
            "max div debt length": self._max_debts_list_length.get(),
            "time offset": self._time_offset.get()
        }

    # -------------------------------------------------------------------------------
    #   EVENT LOGS
    # -------------------------------------------------------------------------------

    @eventlog(indexed=1)
    def ContractActive(self, _contract: str, _state: str):
        pass

    @eventlog(indexed=1)
    def AssetActive(self, _asset: str, _state: str):
        pass

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, destination: Address, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def TokenTransfer(self, recipient: Address, amount: int, note: str):
        pass

    @eventlog(indexed=3)
    def AssetAdded(self, account: Address, symbol: str, is_collateral: bool):
        pass

    @eventlog(indexed=2)
    def CollateralReceived(self, account: Address, symbol: str):
        pass

    @eventlog(indexed=3)
    def OriginateLoan(self, recipient: Address, symbol: str, amount: int, note: str):
        pass

    @eventlog(indexed=3)
    def LoanRepaid(self, account: Address, symbol: str, amount: int, note: str):
        pass

    @eventlog(indexed=3)
    def AssetRetired(self, symbol: str, amount: int, price: int, note: str):
        pass

    @eventlog(indexed=2)
    def Liquidate(self, account: Address, amount: int, note: str):
        pass

    @eventlog(indexed=3)
    def BadDebt(self, account: Address, symbol: str, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def TotalDebt(self, symbol: str, amount: int, note: str):
        pass

    @eventlog(indexed=3)
    def FeePaid(self, symbol: str, amount: int, type: str, note: str):
        pass

    @eventlog(indexed=2)
    def OraclePriceUpdate(self, symbol: str, rate: int, note: str):
        pass

    @eventlog(indexed=2)
    def PositionStanding(self, address: Address, standing: str, ratio: int, note: str):
        pass

    @eventlog(indexed=1)
    def Diagnostic(self, symbol: str, amount: int, note: str):
        pass

    @eventlog(indexed=1)
    def Snapshot(self, _id: int):
        """
        Emitted as a new snapshot is generated.
        :param _id: ID of the snapshot.
        """
        pass
