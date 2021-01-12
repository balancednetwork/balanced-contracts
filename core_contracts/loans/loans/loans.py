from iconservice import *
from ..utils.checks import *
from ..utils.consts import *
from ..scorelib import *
from .positions import PositionsDB
from .assets import AssetsDB, Asset
from .replay_log import ReplayLogDB

TAG = 'BalancedLoans'

# For testing only
TEST_ADDRESS = Address.from_string('hx3f01840a599da07b0f620eeae7aa9c574169a4be')

# An interface to the Emergency Reserve Fund
class ReserveFund(InterfaceScore):
    @interface
    def redeem(self, _to: Address, _amount: int, sicx_rate: int):
        pass


# An interface of token
class TokenInterface(InterfaceScore):
    @interface
    def symbol(self) -> str:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes=None):
        pass


class Loans(IconScoreBase):

    _LOANS_ON = 'loans_on'
    _DIVIDENDS = "dividends"
    _RESERVE = 'reserve'
    _ADMIN = 'admin'
    _REPLAY_BATCH_SIZE = 'replay_batch_size'

    _SYSTEM_DEBT = 'system_debt'

    _MINING_RATIO = 'mining_ratio'
    _LOCKING_RATIO = 'locking_ratio'
    _LIQUIDATION_RATIO = 'liquidation_ratio'
    _ORIGINATION_FEE = 'origination_fee'
    _REDEMPTION_FEE = 'redemption_fee'
    _RETIREMENT_BONUS = 'retirement_bonus'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._loans_on = VarDB(self._LOANS_ON, db, value_type=bool)
        self._dividends = VarDB(self._DIVIDENDS, db, value_type=Address)
        self._reserve = VarDB(self._RESERVE, db, value_type=Address)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._replay_batch_size = VarDB(self._REPLAY_BATCH_SIZE, db, value_type=int)

        self._assets = AssetsDB(db, self)
        self._positions = PositionsDB(db, self)
        self._event_log = ReplayLogDB(db)
        self._system_debt = DictDB(self._SYSTEM_DEBT, db, value_type=int)

        self._mining_ratio = VarDB(self._MINING_RATIO, db, value_type=int)
        self._locking_ratio = VarDB(self._LOCKING_RATIO, db, value_type=int)
        self._liquidation_ratio = VarDB(self._LIQUIDATION_RATIO, db, value_type=int)
        self._origination_fee = VarDB(self._ORIGINATION_FEE, db, value_type=int)
        self._redemption_fee = VarDB(self._REDEMPTION_FEE, db, value_type=int)
        self._retirement_bonus = VarDB(self._RETIREMENT_BONUS, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._loans_on.set(False)
        self._admin.set(self.owner)
        self._replay_batch_size.set(REPLAY_BATCH_SIZE)
        self._mining_ratio.set(DEFAULT_MINING_RATIO)
        self._locking_ratio.set(DEFAULT_LOCKING_RATIO)
        self._liquidation_ratio.set(DEFAULT_LIQUIDATION_RATIO)
        self._origination_fee.set(DEFAULT_ORIGINATION_FEE)
        self._redemption_fee.set(DEFAULT_REDEMPTION_FEE)
        self._retirement_bonus.set(BAD_DEBT_RETIREMENT_BONUS)
        self._positions.frozen.set(False)

    def on_update(self) -> None:
        super().on_update()
        # # Create bad position for testing liquidation. Take out a loan that is too large.
        # pos = self._positions.get_pos(TEST_ADDRESS)
        # # Independently, 782769 * 10**15 =~$299 worth of collateral will be
        # # deposited for this position.
        # icd: int = 2 * 10**20 # $200 ICD debt
        # self._assets['ICD'].mint(TEST_ADDRESS, icd)
        # pos['ICD'] += icd

    @external(readonly=True)
    def name(self) -> str:
        return "BalancedLoans"

    @external
    @only_owner
    def setAdmin(self, _admin: Address) -> None:
        self._admin.set(_admin)

    @external
    @only_owner
    def toggle_loans_on(self) -> None:
        self._loans_on.set(not self._loans_on.get())

    @external
    @only_owner
    def set_dividends(self, _address: Address) -> None:
        self._dividends.set(_address)

    @external(readonly=True)
    def get_dividends(self) -> Address:
        self._dividends.get()

    @external
    @only_owner
    def set_reserve(self, _address: Address) -> None:
        self._reserve.set(_address)

    @external(readonly=True)
    def get_reserve(self) -> Address:
        self._reserve.get()

    @external
    @only_owner
    def set_origination_fee(self, _fee: int) -> None:
        self._origination_fee.set(_fee)

    @external(readonly=True)
    def get_origination_fee(self) -> int:
        self._origination_fee.get()

    @external
    @only_owner
    def set_replay_batch_size(self, _size: int) -> None:
        self._replay_batch_size.set(_size)

    @external(readonly=True)
    def get_replay_batch_size(self) -> int:
        self._replay_batch_size.get()

    @external(readonly=True)
    def get_collateral_tokens(self) -> dict:
        """
        Returns a dictionary of assets from the assetsDB that are marked as
        collateral, with token symbol as the key and address as a string value.
        """
        assets = self._assets.get_assets()
        collateral = {}
        for symbol in assets:
            if assets[symbol]['is_collateral']:
                collateral[symbol] = assets[symbol]['address']
        return collateral

    @external(readonly=True)
    def get_total_collateral(self) -> int:

        try:
            return self._assets['sICX'].balanceOf(self.address)
        except:
            return 0

    @external(readonly=True)
    def get_account_positions(self, _owner: Address) -> str:
        """
        Get account positions.
        """
        if self.msg.sender != _owner and self.msg.sender != self.owner:
            revert("Only the account owner and Balanced management wallet "
                   "are allowed to call this method.")
        position = self._positions.list_pos(_owner)
        return position

    @external(readonly=True)
    def get_available_assets(self) -> dict:
        """
        Returns a dict of assets.
        """
        return self._assets.get_assets()

    @external(readonly=True)
    def asset_count(self) -> int:
        """
        Returns the number of assets in the AssetsDB.
        """
        return len(self._assets)

    @external
    @only_admin
    def add_asset(self, _token_address: Address, is_active: bool = True, is_collateral: bool = False) -> None:
        """
        Adds a token to the assets dictionary.
        """
        self._assets.add_asset(_token_address, is_active, is_collateral)
        token_score = self.create_interface_score(_token_address, TokenInterface)
        self.AssetAdded(_token_address, token_score.symbol(), is_collateral)

    @external
    @only_owner
    def toggle_asset_active(self, _symbol) -> None:
        self._assets[_symbol].active.set(not self._assets[_symbol].active.get())

    @external
    def read_position_data_batch(self) -> dict:
        """
        Read position data batch.
        """
        pass

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
        if _value <= 0:
            revert(f'Amount sent must be greater than zero.')
        if self.msg.sender not in self._assets.alist:
            revert(f'The Balanced Loans contract does not accept that token type.')
        if _from == self._reserve.get():
            return
        try:
            d = json_loads(_data.decode("utf-8"))
        except BaseException as e:
            revert(f'Invalid data: {_data}, returning tokens. Exception: {e}')
        if set(d.keys()) != set(["method", "params"]):
            revert('Invalid parameters.')
        if d["method"] == "_deposit_and_borrow":
            self._deposit_and_borrow(_value, **d['params'])
        elif d["method"] == "_repay_loan":
            self._repay_loan(_from, _value)
        elif d["method"] == "_retire_asset":
            self._retire_asset(_from, _value, **d['params'])
        else:
            revert(f'No valid method called, data: {_data}')

    def _deposit_and_borrow(self, _value: int, _asset: str = '',
                            _amount: int = 0) -> None:
        """
        If the received token type is sICX it will be added to the account of
        the token sender.
        If the optional parameters of _asset and _amount are present a loan of
        _amount of _asset will be returned to the originating address if
        there is sufficient collateral present.

        :param _value: Number of tokens sent.
        :type _value: int
        :param _asset: Symbol of asset to borrow.
        :type _asset: str
        :param _amount: Size of loan requested.
        :type _amount: int
        """
        if self.msg.sender != self._assets['sICX'].asset_address.get():
            revert(f'sICX is the only type of collateral accepted.')
        pos = self._positions.get_pos(self.tx.origin)
        if pos['sICX'] == 0:
            self._positions.add_nonzero(self.tx.origin)
        pos['sICX'] += _value
        if _asset == '' or _amount == 0:
            return
        self.originate_loan(_asset, _amount)

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
        asset = self._assets._get_asset(str(self.msg.sender))
        symbol = asset.symbol()
        origin = self.tx.origin
        pos = self._positions.get_pos(origin)
        if pos[symbol] - _value >= 0:
            pos[symbol] -= _value
            repaid = _value
        else:
            repaid = pos[symbol]
            refund = _value - repaid
            pos[symbol] = 0
            self._send_token(symbol, origin, refund, "Excess refunded.")
        self._assets[symbol].burn(repaid)
        self.LoanRepaid(origin, symbol, repaid,
            f'Loan of {repaid / EXA} {symbol} repaid to Balanced.')

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
        asset = self._assets._get_asset(str(self.msg.sender))
        symbol = asset.symbol()
        bad_debt = asset.bad_debt.get()
        sicx_rate = self._assets['sICX'].price_in_loop()
        price = asset.price_in_loop()
        self._assets[symbol].burn(_value)
        redeemed = _value
        sicx: int = 0
        if bad_debt > 0:
            bd_value = min(bad_debt, redeemed)
            redeemed -= bd_value
            sicx += self.bd_redeem(_from, asset, bd_value, sicx_rate, price)
        if redeemed > 0:
            sicx += redeemed * price // sicx_rate
            supply = self._assets[symbol].totalSupply()
            self._event_log.new_event(symbol=symbol,
                                      value=redeemed,
                                      sicx_rate=sicx_rate,
                                      sicx_returned=sicx,
                                      asset_supply=supply)

        self._send_token("sICX", _from, sicx, "Collateral redeemed.")
        self.AssetRedeemed(_from, symbol, _value,
            f'{_value // EXA} {symbol} redeemed on Balanced.')

    def bd_redeem(self, _from: Address, asset: Asset, bd_value: int, sicx_rate: int, price: int) -> int:
        """
        Returns the amount of the bad debt paid off in sICX coming from both
        the liquidation pool for the asset or the ReserveFund SCORE.

        :param _from: Address of the token sender.
        :type _from: :class:`iconservice.base.address.Address`
        :param bd_value: Amount of bad debt to redeem.
        :type bd_value: int
        :param sicx_rate: Price of sICX in loop.
        :type sicx_rate: int
        :param price: Price of the asset in loop.
        :type price: int

        :return: Amount of sICX supplied from reserve.
        :rtype: int
        """
        reserve_address = self._reserve.get()
        in_pool = asset.liquidation_pool.get()
        bd_sicx = (POINTS + self._retirement_bonus.get()) * bd_value * price // (POINTS * sicx_rate)
        if in_pool > bd_sicx:
            asset.liquidation_pool.set(in_pool - bd_sicx)
            bad_debt = asset.bad_debt.get() - bd_value
            asset.bad_debt.set(bad_debt)
            if bad_debt == 0:
                self._send_token('sICX', reserve_address, in_pool - bd_sicx, "Sweep to ReserveFund:")
                asset.liquidation_pool.set(0)
            return bd_sicx
        asset.liquidation_pool.set(0)
        reserve = self.create_interface_score(reserve_address, ReserveFund)
        return in_pool + reserve.redeem(_from, bd_sicx - in_pool)

    @external
    def originate_loan(self, _asset: str, _amount: int) -> None:
        """
        Originate a loan of an asset if there is sufficient collateral.

        :param _asset: Symbol of the asset.
        :type _asset: str
        :param _value: Number of tokens sent.
        :type _value: int
        """
        origin = self.tx.origin
        pos = self._positions.get_pos(origin)

        # Check for sufficient collateral
        collateral = pos['sICX']
        if collateral == 0:
            revert(f'Collateral must be deposited before originating a loan.')
        if self._assets[_asset].dead():
            revert(f'No new loans of {_asset} can be originated since '
                   f'it is in a dead market state.')
        max_debt_value = 100 * collateral // self._locking_ratio.get()
        fee = self._origination_fee.get() * _amount // POINTS
        new_debt_value = self._assets[_asset].price_in_loop() * (_amount + fee) // EXA
        if pos.total_debt() + new_debt_value > max_debt_value:
            revert(f'{collateral / EXA} collateral is insufficient'
                   f' to originate a loan of {_amount / EXA} {_asset}'
                   f' when max_debt_value = {max_debt_value / EXA} and'
                   f' new_debt_value = {new_debt_value / EXA},'
                   f' plus a fee of {fee / EXA} {_asset},'
                   f' and an existing loan value of {pos.total_debt() / EXA}.')

        # Originate loan
        pos[_asset] += _amount + fee
        self._assets[_asset].mint(origin, _amount)
        self.OriginateLoan(origin, _asset, _amount,
            f'Loan of {_amount / EXA} {_asset} from Balanced.')

        # Pay fee
        self._assets[_asset].mint(self._dividends.get(), fee)
        self.FeePaid(_asset, fee, "origination", "")

    @external
    def withdraw_collateral(self, _value: int) -> None:
        """
        Withdraw sICX collateral up to the collateral locking ratio.

        :param _value: Amount of sICX to withdraw.
        :type _value: int
        """
        origin = self.tx.origin
        pos = self._positions.get_pos(origin)
        if pos['sICX'] < _value:
            revert(f'Position holds less collateral than the requested withdrawal.')
        asset_value = pos.total_debt() # Value in ICX
        remaining_sicx = pos['sICX'] - _value
        remaining_coll = remaining_sicx * self._assets['sICX'].price_in_loop() // EXA
        locking_value = self._locking_ratio.get() * asset_value // 100
        if remaining_coll < locking_value:
            revert(f'Requested withdrawal is more than available collateral. '
                   f'total debt value: {asset_value} ICX '
                   f'remaining collateral value: {remaining_coll} ICX '
                   f'locking value (max debt): {locking_value} ICX')
        pos['sICX'] = remaining_sicx
        if remaining_sicx == 0:
            self._positions.remove_nonzero(origin)
        self._send_token('sICX', origin, _value, "Collateral withdrawn.")

    @external
    def threshold_check(self, _position: Address) -> int:
        """
        Check liquidation threshold. Replay retirement events that have not yet
        been applied to the position. Update the standing of the position given
        current asset prices.

        :param _value: Amount of sICX to withdraw.
        :type _value: int
        """
        pos = self._positions.get_pos(_position)
        if pos.replay_index.get() < len(self._event_log):
            results = self.replay_events(_position)
            if results[1] != 0:
                return Standing.UNDETERMINED
        else:
            pos.update_standing()
        return pos.get_standing()

    @external
    def liquidate(self, _position: Address) -> None:
        """
        Liquidate collateral if the position is below the liquidation threshold.
        """
        _standing = self.threshold_check(_position)
        pos = self._positions.get_pos(_position)
        if _standing == Standing.LIQUIDATE:
            collateral = pos['sICX']
            reward = collateral * LIQUIDATION_REWARD // POINTS
            for_pool = collateral - reward
            total_debt = pos.total_debt()
            for symbol in self._assets.slist:
                if not self._assets[symbol].is_collateral.get() and pos[symbol] > 0:
                    bad_debt = self._assets[symbol].bad_debt.get()
                    self._assets[symbol].bad_debt.set(bad_debt + pos[symbol])
                    symbol_debt = pos[symbol] * self._assets[symbol].price_in_loop()
                    share = for_pool * symbol_debt // total_debt
                    total_debt -= symbol_debt
                    for_pool -= share
                    pool = self._assets[symbol].liquidation_pool.get()
                    self._assets[symbol].liquidation_pool.set(pool + share)
                    pos[symbol] = 0
            self._send_token('sICX', self.tx.origin, reward, "Liquidation reward of")
            pos['sICX'] = 0
            self._positions.remove_nonzero(self.tx.origin)
            self.Liquidate(_position, collateral, f'{collateral} liquidated from {_position}')
        elif _standing != Standing.UNDETERMINED:
            self.PositionStanding(_position,
                                  Standing.STANDINGS[_standing],
                                  str(pos.collateral_value() / pos.total_debt()),
                                  "Position up to date.")
        else:
            self.PositionStanding(_position,
                                  Standing.STANDINGS[_standing],
                                  "Ratio not yet determined.",
                                  "Position not up to date.")

    def replay_events(self, _apply_to: Address) -> (int, int):
        """
        Replay up to replay_batch_size redemption events. Returns the number of
        events replayed and the number of events remaining to replay.

        :param _apply_to: Address to be updated.
        :type _apply_to: :class:`iconservice.base.address.Address`
        :type _apply_to: int

        :return: Tuple - (Number replayed, Number remaining).
        :rtype: (int, int)
        """
        pos = self._positions.get_pos(_apply_to)

        index = pos.replay_index.get()
        last_event = len(self._event_log)
        if index < last_event:
            # Iterate over _batch_size unplayed events or fewer.
            end = min([index + self.replay_batch_size.get(), last_event])
            for id in range(index, end + 1):
                pos.apply_event(self._event_log[id])
        return end - index, last_event - end

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

    # ------------------------------------------------------------------------------------------------------------------
    # EVENTS
    # ------------------------------------------------------------------------------------------------------------------

    @eventlog(indexed=3)
    def AssetAdded(self, account: Address, symbol: str, is_collateral: bool):
        pass

    @eventlog(indexed=2)
    def TokenTransfer(self, recipient: Address, amount: int, note: str):
        pass

    @eventlog(indexed=3)
    def OriginateLoan(self, recipient: Address, symbol: str, amount: int, note: str):
        pass

    @eventlog(indexed=3)
    def LoanRepaid(self, account: Address, symbol: str, amount: int, note: str):
        pass

    @eventlog(indexed=3)
    def AssetRedeemed(self, account: Address, symbol: str, amount: int, note: str):
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
    def PositionStanding(self, address: Address, standing: str, ratio: str, note: str):
        pass
