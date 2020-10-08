from iconservice import *
from .utils.checks import *
from .scorelib import *

TAG = 'BalancedLoans'

UNITS_PER_TOKEN = 1000000000000000000
DEFAULT_MINING_RATIO = 500
DEFAULT_LOCKING_RATIO = 400
DEFAULT_LIQUIDATION_RATIO = 125
MIN_UPDATE_TIME = 300000000  # 5 minutes
#  Old Oracle address cx8b679486b721b70e332f59cfb9c46dadc23ff0c5
BAND_PRICE_ORACLE_ADDRESS = "cx61a36e5d10412e03c907a507d1e8c6c3856d9964"


# An interface to the Band Price Oracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass

# An interface of token to distribute daily rewards
class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes=None):
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def symbol(self) -> str:
        pass

    @interface
    def get_peg(self) -> str:
        pass

    @interface
    def mintTo(self, _account: Address, _amount: int, _data: bytes = None) -> None:
        pass

    @interface
    def burn(self, _amount: int) -> None:
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
    _POSITIONS = 'positions'
    _SYSTEM_DEBT = 'system_debt'
    _RESERVE = 'reserve'
    _ASSET_LIST = 'asset_list'
    _ASSET_PEGS = 'asset_peg'
    _ASSET_ADDRESS_LIST = 'asset_address_list'
    _ASSET_ADDRESSES = 'asset_addresses'
    _ASSETS = 'assets'
    _EVENT_LOG = 'event_log'
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
        self._day_index = VarDB(self._DAY_INDEX, db, value_type=int)
        self._positions = DictDB(self._POSITIONS, db, value_type=int, depth=3)
        self._system_debt = DictDB(self._SYSTEM_DEBT, db, value_type=int)
        self._reserve = DictDB(self._RESERVE, db, value_type=int)
        self._asset_list = ArrayDB(self._ASSET_LIST, db, value_type=str)  # List of asset symbols.
        self._asset_pegs = DictDB(self._ASSET_PEGS, db, value_type=str)
        self._asset_address_list = ArrayDB(self._ASSET_ADDRESS_LIST, db, value_type=Address)  # List of asset addresses.
        self._asset_addresses = DictDB(self._ASSET_ADDRESSES, db, value_type=Address)
        # _assets[<symbol>]['address', ]
        self._assets = DictDB(self._ASSETS, db, value_type=int, depth=2)
        self._event_log = ArrayDB(self._EVENT_LOG, db, value_type=int)
        self._sICX_address = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        self._staking_contract = VarDB(self._STAKING_CONTRACT, db, value_type=Address)
        self._oracle_address = VarDB(self._ORACLE_ADDRESS, db, value_type=Address)
        self._mining_ratio = VarDB(self._MINING_RATIO, db, value_type=int)
        self._locking_ratio = VarDB(self._LOCKING_RATIO, db, value_type=int)
        self._liquidation_ratio = VarDB(self._LIQUIDATION_RATIO, db, value_type=int)

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
    def OraclePriceUpdate(self, symbol: str, rate: int, note: str):
        pass

    def on_install(self) -> None:
        super().on_install()
        self._loans_on.set(False)
        self._admin.set(self.owner)
        self._day_index.set(0)
        self._oracle_address.set(Address.from_string(BAND_PRICE_ORACLE_ADDRESS))
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
    def set_sicx_address(self, _address: Address) -> None:
        self._sICX_address.set(_address)

    @external
    @only_owner
    def toggle_loans_on(self) -> None:
        self._loans_on.set(not self._loans_on.get())

    @external(readonly=True)
    def get_sicx_address(self) -> Address:
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
    def get_account_positions(self, _owner: Address) -> dict:
        """
        Get account positions.
        """
        if self.msg.sender != _owner and self.msg.sender != self.owner:
            revert("Only the account owner and Balanced management wallet "
                   "are allowed to call this method.")
        pass

    @external(readonly=True)
    def get_available_assets(self) -> list:
        """
        Returns a list of token contract addresses and symbols.
        """
        assets = []
        for asset in self._asset_list:
            assets.append((asset, str(self._asset_addresses[asset]), self._asset_pegs[asset]))
        return assets

    @external
    @only_admin
    def add_asset(self, _token_address: Address) -> None:
        """
        Adds a token to the assets dictionary and its symbol to the _asset_list.
        """
        token = self.create_interface_score(_token_address, TokenInterface)
        symbol = token.symbol()
        if symbol not in self._asset_list:
            self._asset_list.put(symbol)
            self._asset_address_list.put(_token_address)
            self._asset_addresses[symbol] = _token_address
            self._asset_pegs[symbol] = token.get_peg()
            self._assets[symbol]['added'] = self.now()
            self._assets[symbol]['active'] = 1

    @external
    def read_position_data_batch(self) -> dict:
        """
        Read position data batch.
        """
        pass

    @external
    def get_price_in_icx(self, _symbol: str) -> int:
        """
        Returns the price of the asset in loop. Makes a call to the oracle if
        the last recorded price is not recent enough.
        """
        if self.now() - self._assets[_symbol]['price_update_time'] > MIN_UPDATE_TIME:
            self.update_asset_value(_symbol)

        return self._assets[_symbol]['price']

    def update_asset_value(self, _symbol: str) -> None:
        """
        Calls the oracle method for the asset and updates the asset
        value in the _assets_ DictDB.
        """
        oracle = self.create_interface_score(self._oracle_address.get(), OracleInterface)
        priceData = oracle.get_reference_data(self._asset_pegs[_symbol], 'ICX')
        self._assets[_symbol]['price'] = priceData['rate']
        self._assets[_symbol]['price_update_time'] = self.now()

    def event_replay(self, _address: Address) -> None:
        """
        Event replay.
        """
        pass

    def _asset_mint(self, _address: Address, _amount: int, _symbol: str, _data: bytes = None) -> None:
        """
        Mint asset.
        """
        if _data is None:
            _data = b'None'
        token_address = self._asset_addresses[_symbol]
        token = self.create_interface_score(token_address, TokenInterface)
        token.mintTo(_address, _amount, _data)

    def _asset_burn(self, _amount: int, _symbol: str) -> None:
        """
        Burn asset.
        """
        token_address = self._asset_addresses[_symbol]
        token = self.create_interface_score(token_address, TokenInterface)
        token.burn(_amount)

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
        if (self.msg.sender not in self._asset_address_list
            and self.msg.sender != self._sICX_address.get()):
            revert(f'This contract does not accept that token type.')
        Logger.debug(f'({_value}) tokens received from {_from}.', TAG)
        try:
            Logger.debug(f'Decoding the _data sent with the tokens.', TAG)
            d = json_loads(_data.decode("utf-8"))
        except BaseException as e:
            Logger.debug(f'Invalid data with token transfer. Exception: {e}', TAG)
            revert(f'Invalid data: {_data}, returning tokens. Exception: {e}')
        if set(d.keys()) != set(["method", "params"]):
            revert('Invalid parameters.')
        if d["method"] == "_deposit_and_borrow":
            # try:
            #     Address._from_string(d['params']['_for'])
            # except BaseException as e:
            #     revert(f'Collateral recipient address invalid: {d["params"]["_for"]}')
            self._deposit_and_borrow(_value, **d['params'])
        elif d["method"] == "_repay_loan":
            self._repay_loan(_from, _value)
        elif d["method"] == "_retire_asset":
            self._retire_asset(_from, _value, **d['params'])
        else:
            revert(f'No valid method called, data: {_data}')

    def _deposit_and_borrow(self, _value: int, _for: str,
                            _asset: str = '', _amount: int = 0) -> None:
        """
        If the received token type is sICX it will be added to the account of
        the token sender.
        If the optional parameters of _asset and _amount are present a loan of
        _amount of _asset will be returned to the originating address if
        there is sufficient collateral present.

        :param _value: Number of tokens sent.
        :type _value: int
        :param _for: Controlling address for the collateral recipient position.
        :type _for: str
        :param _asset: Pegged asset to borrow.
        :type _asset: str
        :param _amount: Size of loan requested.
        :type _amount: int
        """
        if self.msg.sender != self._sICX_address.get():
            revert(f'sICX is the only type of collateral accepted.')
        self._positions[self._day_index.get()][_for]['sICX'] += _value
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
        if self.msg.sender == self._sICX_address.get():
            revert(f'This method does not accept sICX tokens')
        token = self.create_interface_score(self.msg.sender, TokenInterface)
        symbol = token.symbol()
        if self._positions[self._day_index.get()][str(_from)][symbol] - _value >= 0:
            self._positions[self._day_index.get()][str(_from)][symbol] -= _value
            repaid = _value
        else:
            repaid = self._positions[self._day_index.get()][str(_from)][symbol]
            refund = _value - repaid
            self._positions[self._day_index.get()][str(_from)][symbol] = 0
            self._send_token(symbol, _from, refund, "Excess refunded.")
        self._asset_burn(symbol, repaid)
        LoanRepaid(_from, symbol, repaid,
            f'Loan of {repaid // UNITS_PER_TOKEN} {symbol} repaid to Balanced.')

    def _retire_asset(self, _from: Address, _value: int, _for: str = '') -> None:
        """
        An asset holder who does not hold a position in the asset may retire
        it in exchange for collateral that comes proportionately from all
        collateral positions in the system.

        :param _from: Address of the token sender.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        """
        revert(f'It is not yet possible to retire assets on Balanced.')
        _to = _from
        if _for != '':
            try:
                _to = Address._from_string(_for)
            except BaseException as e:
                revert(f'Collateral recipient address invalid: {_for}')
        token = self.create_interface_score(self.msg.sender, TokenInterface)
        symbol = token.symbol()
        sicx_rate = self.get_sicx_value(UNITS_PER_TOKEN)
        price = self.get_icx_price(symbol)
        redeemed = _value * price // sicx_rate
        self._event_log.put(f'{self.now()},{symbol},{_value},{token.totalSupply()},{sicx_rate}')
        self._asset_burn(_value, symbol)
        self._send_token("sICX", _to, redeemed, "Collateral redeemed.")
        AssetRedeemed(_to, symbol, redeemed,
            f'{redeemed // UNITS_PER_TOKEN} {symbol} redeemed on Balanced.')

    @external
    def originate_loan(self, _asset: str, _amount: int) -> None:
        """
        Originate a loan of an asset if there is sufficient collateral.

        :param _asset: Symbol of the asset.
        :type _asset: str
        :param _value: Number of tokens sent.
        :type _value: int
        """
        address = str(self.tx.origin)
        collateral = self.get_sicx_value(self._positions[self._day_index.get()][address]['sICX'])
        max_loan_value = 100 * collateral // self._locking_ratio.get()
        new_loan_value = self.get_price_in_icx(_asset) * amount // UNITS_PER_TOKEN
        if self.get_total_position_value() + new_loan_value > max_loan_value:
            revert(f'Insufficient collateral to originate loan.')
        self._positions[self._day_index.get()][address][_asset] += _amount
        self._asset_mint(self.tx.origin, _amount, _asset)
        OriginateLoan(self.tx.origin, _asset, _amount,
            f'Loan of {_amount // UNITS_PER_TOKEN} {_asset} from Balanced.')

    @external
    def withdraw_collateral(self, _value: int) -> None:
        """
        Withdrawn sICX collateral up to the collateral locking ratio.

        :param _value: Amount of sICX to withdraw.
        :type _value: int
        """
        asset_value = self.get_total_position_value()
        remaining_sicx = self._positions[self._day_index.get()][self.tx.origin]['sICX'] - _value
        locking_value = self._locking_ratio.get() * asset_value // 100
        if self.get_sicx_value(remaining_sicx) < locking_value:
            revert(f'Requested withdrawal is more than available collateral.')
        self._positions[self._day_index.get()][self.tx.origin]['sICX'] -= _value
        self._send_token('sICX', self.tx.origin, _value, "Collateral withdrawn.")

    @external
    def get_total_position_value(self) -> int:
        """
        Returns the total value of all outstanding debt in loop.

        :return: Value of all outstanding debt in loop.
        :rtype: int
        """
        asset_value = 0
        for asset in self._asset_list:
            amount = self._positions[self._day_index.get()][self.tx.origin][asset]
            if amount > 0:
                asset_value += self.get_price_in_icx(asset) * amount // UNITS_PER_TOKEN
        return asset_value

    @external
    def get_sicx_value(self, _amount: int) -> int:
        """
        Returns the value of an amount of sICX in loop.

        :param _amount: Amount of sICX to convert to loop.
        :type _amount: int

        :return: Value of the sICX in loop.
        :rtype: int
        """
        staking = self.create_interface_score(self._staking_contract.get(), StakingInterface)
        value = _amount * staking.get_rate() // UNITS_PER_TOKEN
        return value

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

    def _send_token(self, _token: str, _to: Address, amount: int, msg: str) -> None:
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
        try:
            address = self._asset_addresses[_token]
            token_score = self.create_interface_score(address, TokenInterface)
            token_score.transfer(_to, amount)
            symbol = token_score.symbol()
            self.TokenTransfer(_to, amount, msg + f' {amount} {symbol} sent to {_to}.')
        except BaseException as e:
            revert(f'{amount} {symbol} not sent to {_to}. '
                   f'Exception: {e}')

    def _send_ICX(self, _to: Address, amount: int, msg: str) -> None:
        """
        Sends ICX to an address.
        :param _to: ICX destination address.
        :type _to: :class:`iconservice.base.address.Address`
        :param _amount: Number of ICX sent.
        :type _amount: int
        :param msg: Message for the event log.
        :type msg: str
        """
        try:
            self.icx.transfer(_to, amount)
            self.FundTransfer(_to, amount, msg + f' {amount} ICX sent to {_to}.')
        except BaseException as e:
            revert(f'{amount} ICX not sent to {_to}. '
                   f'Exception: {e}')

    def fallback(self):
        pass
