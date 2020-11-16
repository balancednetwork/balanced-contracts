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


class Asset(object):

    @property
    def db(self) -> 'IconScoreDatabase':
        return self.__db

    def __init__(self, db: IconScoreDatabase) -> None:
        self.__db = db
        self.symbol = VarDB('symbol', db, value_type=str)
        self.added = VarDB('added', db, value_type=int)
        self.updated = VarDB('updated', db, value_type=int)
        self.address = VarDB('address', db, value_type=Address)
        self.bad_debt = VarDB('bad_debt', db, value_type=int)
        self.active = VarDB('active', db, value_type=bool)
        self.dead_market = VarDB('dead_market', db, value_type=bool)

    def price_in_icx(self) -> int:
        token = self.create_interface_score(self.address.get(), TokenInterface)
        return token.price_in_icx()

    def mint(self, _to: Address, _amount: int, _data: bytes = None) -> None:
        """
        Mint asset.
        """
        if _data is None:
            _data = b'None'
        try:
            token = self.create_interface_score(self.address.get(), TokenInterface)
            token.mintTo(_to, _amount, _data)
        except BaseException as e:
            revert(f'Trouble minting {self.symbol.get()} tokens to {_to}. Exception: {e}')

    def burn(self, _amount: int) -> None:
        """
        Burn asset.
        """
        try:
            token = self.create_interface_score(self.address.get(), TokenInterface)
            token.burn(_amount)
        except BaseException as e:
            revert(f'Trouble burning {self.symbol.get()} tokens. Exception: {e}')

    def balanceOf(self, _address: Address) -> int:
        token = self.create_interface_score(self.address.get(), TokenInterface)
        return token.balanceOf(_address)

    def symbol(self, _address: Address) -> int:
        token = self.create_interface_score(self.address.get(), TokenInterface)
        return token.symbol(_address)

    def get_peg(self, _address: Address) -> int:
        token = self.create_interface_score(self.address.get(), TokenInterface)
        return token.get_peg(_address)

    def to_json(self) -> str:
        """
        Convert to json string
        :return: the json string
        """

        asset = {
            'symbol': self.symbol(),
            'address': self.address.get(),
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

    def __init__(self, db: IconScoreDatabase):
        self._db = db
        self.alist = ArrayDB('symbol_list', db, value_type=str)
        self.addressdict = DictDB('address|symbol', db, value_type=str)
        self._items = {}

    def __getitem__(self, _symbol: str) -> Asset:
        if _symbol in self.alist:
            if _symbol not in self._items:
                self._items[_symbol] = self._get_asset(_symbol)
        else:
            revert(f'{_symbol} is not a supported asset.')
        return self._items[_symbol]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self) -> int:
        return len(self.alist)

    def _get_asset(self, _symbol: str) -> Asset:
        sub_db = self._db.get_sub_db(b'|'.join([ASSET_DB_PREFIX, _symbol.encode()]))
        return Asset(sub_db)

    def list_assets(self) -> list:
        assets = []
        for symbol in self.alist:
            asset = self._get_asset(symbol)
            if asset.active.get():
                assets.append(asset.to_json())
        return assets

    def add_asset(self, _address: Address) -> Asset:
        token = self.create_interface_score(_address, TokenInterface)
        symbol = token.symbol()
        if symbol in self.alist:
            revert(f'{symbol} already exists in the database.')
        self.alist.put(symbol)
        self.addressdict[_address] = symbol
        self._items[symbol] = self._get_asset(symbol)
        self._items[symbol].added.set(self.now())
        self._items[symbol].address.set(_address)

        return self._items[symbol]
