from iconservice import *
from .utils.checks import *
from .scorelib import *

TAG = 'BalancedLoans'

ICX = 1000000000000000000

# An interface of token to distribute daily rewards
class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes=None):
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def symbol(self, _owner: Address) -> str:
        pass


# An interface to the Staking Management contract
class StakingInterface(InterfaceScore):
    @interface
    def getRate(self) -> int:
        """Gets the exchange rate for sICXICX in loop / sICX."""
        pass


class Loans(IconScoreBase):

    _POSITIONS = 'positions'
    _RESERVE = 'reserve'
    _ASSETS = 'assets'
    _EVENT_LOG = 'event_log'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._positions = DictDB(self._POSITIONS, db, value_type=int, depth=3)
        self._reserve = DictDB(self._RESERVE, db, value_type=int)
        self._assets = DictDB(self._ASSETS, db, value_type=int, depth=2)
        self._event_log = ArrayDB(self._EVENT_LOG, db, value_type=int)

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, destination: Address, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def TokenTransfer(self, recipient: Address, amount: int, note: str):
        pass

    def on_install(self) -> None:
        super().on_install()
        self._loans_on.set(False)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "BalancedLoans"

    @external(readonly=True)
    def get_account_positions(self, _owner: Address) -> dict:
        """

        """
        if self.msg.sender != _owner and self.msg.sender != self.owner:
            revert('Only the account owner and Balanced management wallet '
                   'are allowed to call this method.')
        pass

    @external(readonly=True)
    def get_available_assets(self) -> list:
        """
        Returns a list of token contract addresses.
        """
        pass

    @external
    def add_asset(self, _token_address: Address) -> None:
        """

        """
        pass

    @external
    def read_position_data_batch(self) -> dict:
        """

        """
        pass

    def update_asset_value(self) -> None:
        """

        """
        pass

    def event_replay(self, _address: Address) -> None:
        """

        """
        pass

    def asset_mint(self, _amount: int) -> None:
        """

        """
        pass

    def asset_burn(self, _amount: int) -> None:
        """

        """
        pass

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Directs incoming tokens to either create or fill an order.
        :param _from: Token orgination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Method and parameters to call once tokens are received.
        :type _data: bytes
        """
        if self.msg.sender != self._token_score.get():
            revert(f'This contract can only accept sICX tokens.')
        Logger.debug(f'({_value}) tokens received from {_from}.', TAG)
        try:
            Logger.debug(f'Decoding the _data sent with the tokens.', TAG)
            d = json_loads(_data.decode("utf-8"))
        except BaseException as e:
            Logger.debug(f'Invalid data with token transfer. Exception: {e}', TAG)
            revert(f'Invalid data: {_data}, returning tokens. Exception: {e}')
        if set(d.keys()) != set(["method", "params"]):
            revert('Invalid parameters.')
        if d["method"] == "_deposit_collateral":
            self._deposit_collateral(self.tx.origin,
                               _value)
        elif d["method"] == "_repay_loan":
            self._repay_loan(self.tx.origin,
                               _value,
                               d["params"].get("price", -1))
        elif d["method"] == "_retire_asset":
            self._retire_asset(self.tx.origin,
                               _value,
                               d["params"].get("price", -1))
        else:
            revert(f'No valid method called, data: {_data}')

    def _deposit_collateral(self, _from: Address, _value: int) -> None:
        """

        """
        pass

    def _repay_loan(self, _from: Address, _value: int) -> None:
        """

        """
        pass

    def _retire_asset(self, _from: Address, _value: int) -> None:
        """

        """
        pass

    @external
    def originate_loan(self, _from: Address, _value: int) -> None:
        """

        """
        pass

    @external
    def withdraw_collateral(self, _from: Address, _value: int) -> None:
        """

        """
        pass

    @external
    def threshold_check(self, _from: Address, _value: int) -> None:
        """

        """
        pass

    @external
    def liquidate(self, _from: Address, _value: int) -> None:
        """

        """
        pass

    def _send_token(self, _to: Address, amount: int, msg: str) -> None:
        """
        Sends IRC2 token to an address.
        :param _to: Token destination address.
        :type _to: :class:`iconservice.base.address.Address`
        :param _amount: Number of tokens sent.
        :type _amount: int
        :param msg: Message for the event log.
        :type msg: str
        """
        try:
            token_score = self.create_interface_score(self._token_score.get(),
                                                      TokenInterface)
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
