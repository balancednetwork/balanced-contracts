from iconservice import *
from ..utils.checks import *
from ..utils.consts import *
from ..scorelib import *
from .positions import PositionsDB
from .assets import AssetsDB
from .replay_log import ReplayLogDB

TAG = 'BalancedLoans'

POINTS = 10000

# An interface of token
class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes=None):
        pass


class Loans(IconScoreBase):

    _LOANS_ON = 'loans_on'
    _DIVIDENDS = "dividends"
    _ADMIN = 'admin'
    _COLLATERAL_MIN = 'collateral_min'
    _SYSTEM_DEBT = 'system_debt'
    _MINING_RATIO = 'mining_ratio'
    _LOCKING_RATIO = 'locking_ratio'
    _LIQUIDATION_RATIO = 'liquidation_ratio'
    _ORIGINATION_FEE = 'origination_fee'
    _REDEMPTION_FEE = 'redemption_fee'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._loans_on = VarDB(self._LOANS_ON, db, value_type=bool)
        self._dividends = VarDB(self._DIVIDENDS, db, value_type=Address)

        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._collateral_min = VarDB(self._COLLATERAL_MIN, db, value_type=int)

        self._assets = AssetsDB(db, self)
        self._positions = PositionsDB(db, self)
        self._event_log = ReplayLogDB(db)
        self._system_debt = DictDB(self._SYSTEM_DEBT, db, value_type=int)
        self._reserve = DictDB(self._RESERVE, db, value_type=int)

        self._mining_ratio = VarDB(self._MINING_RATIO, db, value_type=int)
        self._locking_ratio = VarDB(self._LOCKING_RATIO, db, value_type=int)
        self._liquidation_ratio = VarDB(self._LIQUIDATION_RATIO, db, value_type=int)
        self._origination_fee = VarDB(self._ORIGINATION_FEE, db, value_type=int)
        self._redemption_fee = VarDB(self._REDEMPTION_FEE, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._loans_on.set(False)
        self._admin.set(self.owner)
        self._mining_ratio.set(DEFAULT_MINING_RATIO)
        self._locking_ratio.set(DEFAULT_LOCKING_RATIO)
        self._liquidation_ratio.set(DEFAULT_LIQUIDATION_RATIO)
        self._positions.frozen.set(False)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "BalancedLoans"

    @external
    @only_owner
    def set_admin(self, _address: Address) -> None:
        self._admin.set(_address)

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
    def set_origination_fee(self, _fee: int) -> None:
        self._origination_fee.set(_address)

    @external(readonly=True)
    def get_origination_fee(self) -> int:
        self._origination_fee.get()

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
    def get_available_assets(self) -> list:
        """
        Returns a list of assets.
        """
        return self._assets.list_assets()

    @external(readonly=True)
    def asset_count(self) -> int:
        """
        Returns the number of assets in the AssetsDB.
        """
        return len(self._assets)

    @external
    @only_admin
    def add_asset(self, _token_address: Address) -> None:
        """
        Adds a token to the assets dictionary and returns the asset object.
        """
        self._assets.add_asset(_token_address)

    @external
    def read_position_data_batch(self) -> dict:
        """
        Read position data batch.
        """
        pass

    def event_replay(self, _address: Address) -> None:
        """
        Event replay.
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
        # revert(f'{_value} sICX received. About to load data.')
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
        sicx_rate = self._assets['sICX'].price_in_icx()
        price = asset.price_in_icx()
        redeemed = _value * price // sicx_rate

        event = self._event_log.new_event()
        event.symbol.set(symbol)
        event.value.set(_value)
        event.sicx_rate.set(sicx_rate)
        event.asset_supply.set(self._assets[symbol].totalSupply())

        self._assets[symbol].burn(_value)
        self._send_token("sICX", _to, redeemed, "Collateral redeemed.")
        self.AssetRedeemed(_to, symbol, redeemed,
            f'{redeemed // EXA} {symbol} redeemed on Balanced.')

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
        collateral = pos['sICX']
        if collateral == 0:
            revert(f'Collateral must be deposited before originating a loan.')
        max_loan_value = 100 * collateral // self._locking_ratio.get()
        new_loan_value = self._assets[_asset].price_in_icx() * _amount // EXA
        fee = self._origination_fee.get() * new_loan_value // POINTS
        if pos.total_debt() + new_loan_value + fee > max_loan_value:
            revert(f'{collateral / EXA} collateral is insufficient'
                   f' to originate a loan of {_amount / EXA} {_asset}'
                   f' when max_loan_value = {max_loan_value / EXA} and'
                   f' new_loan_value = {new_loan_value / EXA}'
                   f' plus a fee of {fee / EXA}.')
        pos[_asset] += _amount
        self._assets[_asset].mint(origin, _amount)
        self.OriginateLoan(origin, _asset, _amount,
            f'Loan of {_amount / EXA} {_asset} from Balanced.')
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
        asset_value = pos.total_debt() # Value in ICX
        remaining_sicx = pos['sICX'] - _value
        remaining_coll = remaining_sicx * self._assets['sICX'].price_in_icx() // EXA
        locking_value = self._locking_ratio.get() * asset_value // 100
        if remaining_coll < locking_value:
            revert(f'Requested withdrawal is more than available collateral. '
                   f'total debt value: {asset_value} ICX '
                   f'remaining collateral value: {remaining_coll} ICX '
                   f'locking value (max debt): {locking_value} ICX')
        pos['sICX'] -= _value
        self._send_token('sICX', origin, _value, "Collateral withdrawn.")

    @external
    def threshold_check(self, _from: Address, _value: int) -> None:
        """
        Check liquidation threshold.
        """
        pass

    @external
    def liquidate(self, _from: Address, _value: int) -> None:
        """
        Liquidate collateral.
        """
        self.Liquidate(_from, _value, f'{_value} liquidated from {_from}')

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
