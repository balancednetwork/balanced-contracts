from iconservice import *
from .utils.checks import *
from .scorelib import *

TAG = 'Staking'

DENOMINATOR = 1000000000000000000

# An interface of token to distribute daily rewards
class sICXTokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes=None):
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def symbol(self, _owner: Address) -> str:
        pass

    @interface
    def totalSupply(self) -> int:
        pass

    @interface
    def mintTo(self, _account: Address, _amount: int, _data: bytes = None) -> None:
        pass

    @interface
    def mint(self, _amount: int, _data: bytes = None) -> None:
        pass

    @interface
    def burn(self, _amount: int) -> None:
        pass


class Staking(IconScoreBase):

    _SICX_SUPPLY = 'sICX_supply'
    _SICX_ADDRESS = 'sICX_address'

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, destination: Address, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def TokenTransfer(self, recipient: Address, amount: int, note: str):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._sICX_supply = VarDB(self._SICX_SUPPLY, db, value_type=int)
        self._sICX_address = VarDB(self._SICX_ADDRESS, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Staking"

    @external(readonly=True)
    def get_rate(self) -> int:
        sICX_score = self.create_interface_score(self._sICX_address.get(),
                                                 sICXTokenInterface)
        if self.icx.get_balance(self.address) == 0:
            rate = DENOMINATOR
        else:
            rate = self.icx.get_balance(self.address) * DENOMINATOR // sICX_score.totalSupply()
        return rate

    @external
    def set_sICX_supply(self) -> None:
        """Only necessary for the dummy contract."""
        sICX_score = self.create_interface_score(self._sICX_address.get(),
                                                 sICXTokenInterface)
        self._sICX_supply.set(sICX_score.totalSupply())

    @external(readonly=True)
    def get_sICX_address(self) -> Address:
        return self._sICX_address.get()

    @external
    def set_sICX_address(self, _address: Address) -> None:
        self._sICX_address.set(_address)

    @payable
    @external
    def add_collateral(self, _to: Address, _data: bytes = None) -> None:
        if _data is None:
            _data = b'None'
        sicx = self._sICX_address.get()
        sICX_score = self.create_interface_score(sicx, sICXTokenInterface)

        supply = self._sICX_supply.get()
        balance = self.icx.get_balance(self.address)
        if balance == self.msg.value:
            amount = self.msg.value
        else:
            amount = supply * self.msg.value // (balance - self.msg.value)
        # revert(f'Yes, got to here! Minting {amount / DENOMINATOR} {sICX_score.symbol()} to {_to}.')
        sICX_score.mintTo(_to, amount, _data)

        self._sICX_supply.set(self._sICX_supply.get() + amount)
        self.TokenTransfer(_to, amount, f'{amount / DENOMINATOR} sICX minted to {_to}')

    @payable
    @external
    def test_mint(self, _to: Address, _data: bytes = None) -> None:
        if _data is None:
            _data = b'None'
        sicx = self._sICX_address.get()
        sICX_score = self.create_interface_score(sicx, sICXTokenInterface)

        supply = self._sICX_supply.get()
        balance = self.icx.get_balance(self.address)
        if balance == self.msg.value:
            amount = self.msg.value
        else:
            amount = supply * self.msg.value // (balance - self.msg.value)
        # revert(f'Yes, got to here! Minting {amount / DENOMINATOR} {sICX_score.symbol()} to {_to}.')
        sICX_score.mint(amount, _data)
        sICX_score.transfer(_to, amount, _data)

        self._sICX_supply.set(self._sICX_supply.get() + amount)
        self.TokenTransfer(_to, amount, f'{amount / DENOMINATOR} sICX minted to {_to}')

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used only to receive sICX for unstaking.
        :param _from: Token orgination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        if self.msg.sender != self._sICX_address.get():
            revert(f'The Staking contract only accepts sICX tokens.')
        Logger.debug(f'({_value}) tokens received from {_from}.', TAG)
        self._unstake(_from, _value)

    def _unstake(self, _from: Address, _value: int) -> None:
        sICX_score = self.create_interface_score(self._sICX_address.get(),
                                                 sICXTokenInterface)
        unstaked = self.icx.get_balance(self.address) * _value // sICX_score.totalSupply()
        sICX_score.burn(_value)
        self._send_ICX(_from, unstaked, f'Unstaked sICX from {self.msg.sender}')

        self._sICX_supply.set(self._sICX_supply.get() - unstaked)

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

    @payable
    def fallback(self):
        """Only for the dummy contract, to simulate claiming Iscore."""
        pass
