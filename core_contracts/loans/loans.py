from iconservice import *
from .utils.checks import *
from .utils.consts import *
from .utils.events import *
from .scorelib import *
from .positions import *
from .assets import *
from .replay_log import *

TAG = 'BalancedLoans'

#  Old Oracle address cx8b679486b721b70e332f59cfb9c46dadc23ff0c5
BAND_PRICE_ORACLE_ADDRESS = "cx61a36e5d10412e03c907a507d1e8c6c3856d9964"


# An interface to the Band Price Oracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


# An interface to the Staking Management contract
class StakingInterface(InterfaceScore):
    @interface
    def get_rate(self) -> int:
        """Gets the exchange rate for sICXICX in loop / sICX."""
        pass


class Loans(IconScoreBase):

    _LOANS_ON = 'loans_on'
    _ADMIN = 'admin'
    _DAY_INDEX = 'day_index'
    _COLLATERAL_MIN = 'collateral_min'
    _POSITIONS = 'positions'
    _SYSTEM_DEBT = 'system_debt'
    _RESERVE = 'reserve'
    _ASSET_LIST = 'asset_list'
    _ASSET_ADDRESS_LIST = 'asset_address_list'
    _ASSETS = 'assets'
    _SICX_ADDRESS = 'sicx_address'
    _STAKING_CONTRACT = 'staking_contract'
    _ORACLE_ADDRESS = 'oracle_address'
    _MINING_RATIO = 'mining_ratio'
    _LOCKING_RATIO = 'locking_ratio'
    _LIQUIDATION_RATIO = 'liquidation_ratio'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._loans_on = VarDB(self._LOANS_ON, db, value_type=bool)

        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._sICX_address = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._staking_contract = VarDB(self._STAKING_CONTRACT, db, value_type=Address)
        self._oracle_address = VarDB(self._ORACLE_ADDRESS, db, value_type=Address)

        self._day_index = VarDB(self._DAY_INDEX, db, value_type=int)
        self._collateral_min = VarDB(self._COLLATERAL_MIN, db, value_type=int)
        self._positions = PositionsDB(db)
        self._event_log = ReplayLogDB(db)
        self._system_debt = DictDB(self._SYSTEM_DEBT, db, value_type=int)
        self._reserve = DictDB(self._RESERVE, db, value_type=int)

        self._asset_list = ArrayDB(self._ASSET_LIST, db, value_type=str)  # List of asset symbols.
        self._asset_address_list = ArrayDB(self._ASSET_ADDRESS_LIST, db, value_type=Address)  # List of asset addresses.
        self._assets = AssetsDB(db)

        self._mining_ratio = VarDB(self._MINING_RATIO, db, value_type=int)
        self._locking_ratio = VarDB(self._LOCKING_RATIO, db, value_type=int)
        self._liquidation_ratio = VarDB(self._LIQUIDATION_RATIO, db, value_type=int)
        self._origination_fee = VarDB(self._ORIGINATION_FEE, db, value_type=int)
        self._redemption_fee = VarDB(self._REDEMPTION_FEE, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._loans_on.set(False)
        self._admin.set(self.owner)
        self._day_index.set(0) # will be (self.now() // U_SECONDS_DAY) % 2
        self._oracle_address.set(Address.from_string(BAND_PRICE_ORACLE_ADDRESS)) # Will be moved to individual assets.
        self._mining_ratio.set(DEFAULT_MINING_RATIO)
        self._locking_ratio.set(DEFAULT_LOCKING_RATIO)
        self._liquidation_ratio.set(DEFAULT_LIQUIDATION_RATIO)

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
    def set_sicx_address(self, _address: Address) -> None: # Will be just another asset.
        self._sICX_address.set(_address)

    @external
    @only_owner
    def toggle_loans_on(self) -> None:
        self._loans_on.set(not self._loans_on.get())

    @external(readonly=True)
    def get_sicx_address(self) -> Address: # Will be just another asset.
        return self._sICX_address.get()

    @external
    @only_owner
    def set_staking_contract(self, _address: Address) -> None:
        self._staking_contract.set(_address)

    @external(readonly=True)
    def get_staking_contract(self) -> Address:
        return self._staking_contract.get()

    @external
    @only_owner
    def set_oracle_address(self, _address: Address) -> None:
        self._oracle_address.set(_address)

    @external(readonly=True)
    def get_oracle_address(self) -> Address:
        return self._oracle_address.get()

    @external(readonly=True)
    def get_total_collateral(self) -> int:
        return self.assets['sICX'].balanceOf(self.address)

    @external(readonly=True)
    def get_account_positions(self, _owner: Address) -> dict:
        """
        Get account positions.
        """
        if self.msg.sender != _owner and self.msg.sender != self.owner:
            revert("Only the account owner and Balanced management wallet "
                   "are allowed to call this method.")
        index = self._positions.addressID[_owner]
        position = self._positions[index]
        return position.to_json()

    @external(readonly=True)
    def get_available_assets(self) -> list:
        """
        Returns a list of assets.
        """
        return self._assets.list_assets()

    @external
    @only_admin
    def add_asset(self, _token_address: Address) -> Asset:
        """
        Adds a token to the assets dictionary and returns the asset object.
        """
        return self._assets.add_asset(_token_address)

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
        if self.msg.sender not in self._assets.address_list:
            revert(f'The Balanced Loans contract does not accept that token type.')
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
        if self.msg.sender != self._assets['sICX'].address.get():
            revert(f'sICX is the only type of collateral accepted.')
        index = self._positions.addressID[self.tx.origin]
        if index == 0:
            pos = self._positions.new_pos()
        else:
            pos = self._positions[id]
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
        if self.msg.sender == self._assets['sICX'].address.get():
            revert(f'This method does not accept sICX tokens')
        symbol = self._assets.addressdict[self.msg.sender]
        index = self._positions.addressID[self.tx.origin]
        pos = self._positions[index]
        if pos[symbol] - _value >= 0:
            pos[symbol] -= _value
            repaid = _value
        else:
            repaid = pos[symbol]
            refund = _value - repaid
            pos[symbol] = 0
            self._send_token(symbol, self.tx.origin, refund, "Excess refunded.")
        self.assets[symbol].burn(repaid)
        self.LoanRepaid(self.tx.origin, symbol, repaid,
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
        symbol = self._assets.addressdict[self.msg.sender]
        sicx_rate = self._assets['sICX'].price_in_icx()
        price = self._assets[symbol].price_in_icx()
        redeemed = _value * price // sicx_rate

        event = self._event_log.new_event()
        event.symbol.set(symbol)
        event.value.set(_value)
        event.sicx_rate.set(sicx_rate)
        event.asset_supply.set(self._assets[symbol].totalSupply())

        self._assets[symbol].burn(_value)
        self._send_token("sICX", _to, redeemed, "Collateral redeemed.")
        AssetRedeemed(_to, symbol, redeemed,
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
        id = self._positions.addressID[self.tx.origin]
        if id == 0:
            revert(f'No account exists for the originating address.')
        else:
            pos = self._positions[id]
        collateral = pos.assets['sICX'].price_in_icx()
        max_loan_value = 100 * collateral // self._locking_ratio.get()
        new_loan_value = self._assets[_asset].price_in_icx() * _amount // EXA
        if pos.total_debt() + new_loan_value > max_loan_value:
            revert(f'{collateral / EXA} collateral is insufficient'
                   f' to originate a loan of {_amount / EXA} {_asset}'
                   f' when max_loan_value = {max_loan_value / EXA} and'
                   f' new_loan_value = {new_loan_value / EXA}.')
        pos.assets[_asset] += _amount
        self._assets[_asset].mint(self.tx.origin, _amount)
        self.OriginateLoan(self.tx.origin, _asset, _amount,
            f'Loan of {_amount / EXA} {_asset} from Balanced.')

    @external
    def withdraw_collateral(self, _value: int) -> None:
        """
        Withdraw sICX collateral up to the collateral locking ratio.

        :param _value: Amount of sICX to withdraw.
        :type _value: int
        """
        id = self._positions.addressID[self.tx.origin]
        if id == 0:
            revert(f'No account exists for the originating address.')
        else:
            pos = self._positions[id]
        asset_value = pos.total_debt() # Value in ICX
        address = str(self.tx.origin)
        remaining_sicx = pos['sICX'] - _value
        remaining_coll = remaining_sicx * self._assets['sICX'].price_in_icx() // EXA
        locking_value = self._locking_ratio.get() * asset_value // 100
        if remaining_coll < locking_value:
            revert(f'Requested withdrawal is more than available collateral. '
                   f'total debt value: {asset_value} ICX '
                   f'remaining collateral value: {remaining_coll} ICX '
                   f'locking value (max debt): {locking_value} ICX')
        pos['sICX'] -= _value
        self._send_token('sICX', self.tx.origin, _value, "Collateral withdrawn.")

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
        pass

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
        if _token == 'sICX':
            address = self._sICX_address.get()
        else:
            address = self._asset_addresses[_token]

        try:
            token_score = self.create_interface_score(address, TokenInterface)
            token_score.transfer(_to, _amount)
            self.TokenTransfer(_to, _amount, msg + f' {_amount} {_token} sent to {_to}.')
        except BaseException as e:
            revert(f'{_amount} {_token} not sent to {_to}. '
                   f'Exception: {e}')

    def fallback(self):
        pass
