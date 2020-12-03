from iconservice import *

TAG = 'BalancedAssets'

ASSET_DB_PREFIX = b'asset'

# An interface of token to distribute daily rewards
class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes=None):
        pass

    @interface
    def symbol(self) -> str:
        pass

    @interface
    def totalSupply(self) -> int:
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
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

    @interface
    def price_in_icx(self) -> int:
        pass


class Asset(object):

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self._loans = loans
        self.added = VarDB('added', db, value_type=int)
        self.updated = VarDB('updated', db, value_type=int)
        self.asset_address = VarDB('address', db, value_type=Address)
        self.bad_debt = VarDB('bad_debt', db, value_type=int)
        self.active = VarDB('active', db, value_type=bool)
        self.dead_market = VarDB('dead_market', db, value_type=bool)

    def price_in_icx(self) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.price_in_icx()

    def mint(self, _to: Address, _amount: int, _data: bytes = None) -> None:
        """
        Mint asset.
        """
        if _data is None:
            _data = b'None'
        try:
            token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
            token.mintTo(_to, _amount, _data)
        except BaseException as e:
            revert(f'Trouble minting {self.symbol()} tokens to {_to}. Exception: {e}')

    def burn(self, _amount: int) -> None:
        """
        Burn asset.
        """
        try:
            token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
            token.burn(_amount)
        except BaseException as e:
            revert(f'Trouble burning {self.get()} tokens. Exception: {e}')

    def balanceOf(self, _address: Address) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.balanceOf(_address)

    def symbol(self) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.symbol()

    def get_peg(self) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.get_peg()

    def to_json(self) -> str:
        """
        Convert to json string
        :return: the json string
        """

        asset = {
            'symbol': self.symbol(),
            'address': str(self.asset_address.get()),
            'peg': self.get_peg(),
            'added': self.added.get(),
            'active': self.active.get()
        }

        if self.updated.get():
            asset['updated'] = self.updated.get()

        if self.dead_market.get():
            asset['dead_market'] = self.dead_market.get()

        if self.bad_debt.get():
            asset['bad_debt'] = self.bad_debt.get()

        return json_dumps(asset)


class AssetsDB:

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase):
        self._db = db
        self._loans = loans
        self.alist = ArrayDB('address_list', db, value_type=Address)
        self.slist = ArrayDB('symbol_list', db, value_type=str)
        self.symboldict = DictDB('symbol|address', db, value_type=str)
        self._items = {}

    def __getitem__(self, _symbol: str) -> Asset:
        if _symbol in self.slist:
            if _symbol not in self._items:
                self._items[_symbol] = self._get_asset(self.symboldict[_symbol])
        else:
            revert(f'{_symbol} is not a supported asset.')
        return self._items[_symbol]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self) -> int:
        return len(self.alist)

    def _get_asset(self, _address: str) -> Asset:
        sub_db = self._db.get_sub_db(b'|'.join([ASSET_DB_PREFIX, _address.encode()]))
        return Asset(sub_db, self._loans)

    def list_assets(self) -> list:
        assets = []
        for address in self.alist:
            asset = self._get_asset(str(address))
            if asset.active.get():
                assets.append(asset.to_json())
        return assets

    def add_asset(self, _address: Address) -> None:
        address = str(_address)
        if _address in self.alist:
            revert(f'{address} already exists in the database.')
        self.alist.put(_address)
        asset = self._get_asset(address)
        asset.asset_address.set(_address)
        asset.added.set(self._loans.now())
        symbol = asset.symbol()
        self.slist.put(symbol)
        self.symboldict[symbol] = address
        asset.active.set(True)
        self._items[symbol] = asset
