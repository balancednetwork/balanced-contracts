from ..scorelib.linked_list import *

TAG = 'BalancedAssets'

ASSET_DB_PREFIX = b'asset'

# An interface of token to distribute daily rewards
class TokenInterface(InterfaceScore):
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
    def getPeg(self) -> str:
        pass

    @interface
    def mintTo(self, _account: Address, _amount: int, _data: bytes = None) -> None:
        pass

    @interface
    def burn(self, _amount: int) -> None:
        pass

    @interface
    def burnFrom(self, _account: Address, _amount: int) -> None:
        pass

    @interface
    def priceInLoop(self) -> int:
        pass

    @interface
    def lastPriceInLoop(self) -> int:
        pass


class Asset(object):

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self._loans = loans
        self.added = VarDB('added', db, value_type=int)
        self.asset_address = VarDB('address', db, value_type=Address)
        self.bad_debt = VarDB('bad_debt', db, value_type=int)
        self.liquidation_pool = VarDB('liquidation_pool', db, value_type=int)
        self._burned = VarDB('burned', db, value_type=int)
        self._is_collateral = VarDB('is_collateral', db, value_type=bool)
        self._active = VarDB('active', db, value_type=bool)
        self.dead_market = VarDB('dead_market', db, value_type=bool)
        self.borrowers = LinkedListDB('borrowers', db, value_type=int)

    def symbol(self) -> str:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.symbol()

    def totalSupply(self) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.totalSupply()

    def balanceOf(self, _address: Address) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.balanceOf(_address)

    def getPeg(self) -> str:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.getPeg()

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
            self._burned.set(self._burned.get() + _amount)
        except BaseException as e:
            revert(f'Trouble burning {self.symbol()} tokens. Exception: {e}')

    def burnFrom(self, _account: Address, _amount: int) -> None:
        """
        Burn asset.
        """
        try:
            token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
            token.burnFrom(_account, _amount)
            self._burned.set(self._burned.get() + _amount)
        except BaseException as e:
            revert(f'Trouble burning {self.symbol()} tokens. Exception: {e}')

    def priceInLoop(self) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.priceInLoop()

    def lastPriceInLoop(self) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        return token.lastPriceInLoop()

    def get_address(self) -> Address:
        return self.asset_address.get()

    def is_collateral(self) -> bool:
        return self._is_collateral.get()

    def is_active(self) -> bool:
        return self._active.get()

    def is_dead(self) -> bool:
        """
        Calculates whether the market is dead and sets the dead market flag. A
        dead market is defined as being below the point at which total debt
        equals the minimum value of collateral that could be backing it.

        :return: Dead status
        :rtype: bool
        """
        if self._is_collateral.get() or not self._active.get():
            return False
        bad_debt = self.bad_debt.get()
        outstanding = self.totalSupply() - bad_debt
        pool_value = self.liquidation_pool.get() * self.priceInLoop() // self._loans._assets['sICX'].priceInLoop()
        net_bad_debt = bad_debt - pool_value
        dead = net_bad_debt > outstanding / 2
        if dead != self.dead_market.get():
            self.dead_market.set(dead)
        return dead

    def remove_borrower(self, _pos_id: int) -> None:
        """
        Removes a borrower from the asset nonzero list.
        """
        self.borrowers.remove(_pos_id)
        self.borrowers.serialize()

    def add_borrower(self, _new_debt: int, _pos_id: int) -> None:
        """
        Adds a borrower to the asset nonzero list.
        """
        self.borrowers.append(_new_debt, _pos_id)
        self.borrowers.serialize()

    def to_dict(self) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """

        asset = {
            'symbol': self.symbol(),
            'address': str(self.asset_address.get()),
            'peg': self.getPeg(),
            'added': self.added.get(),
            'is_collateral': self._is_collateral.get(),
            'active': self._active.get(),
            'borrowers': len(self.borrowers),
            'total_supply': self.totalSupply(),
            'total_burned': self._burned.get(),
            'bad_debt': self.bad_debt.get(),
            'liquidation_pool': self.liquidation_pool.get(),
            'dead_market': self.dead_market.get()
        }
        return asset


class AssetsDB:

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase):
        self._db = db
        self._loans = loans
        self.alist = ArrayDB('address_list', db, value_type=Address)
        self.slist = ArrayDB('symbol_list', db, value_type=str)
        self.aalist = ArrayDB('active_assets_list', db, value_type=str)  # Does not include collateral.
        self.aclist = ArrayDB('active_collateral_list', db, value_type=str)
        self.collateral = ArrayDB('collateral', db, value_type=str)
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

    def __iter__(self):
        for symbol in self.slist:
            yield self.__getitem__(symbol)

    def _get_asset(self, _address: str) -> Asset:
        sub_db = self._db.get_sub_db(b'|'.join([ASSET_DB_PREFIX, _address.encode()]))
        return Asset(sub_db, self._loans)

    def get_assets(self) -> dict:
        assets = {}
        for symbol in self.aalist:
            asset = self.__getitem__(symbol)
            asset_dict = asset.to_dict()
            assets[symbol] = asset_dict
        return assets

    def get_asset_prices(self) -> dict:
        assets = {}
        for symbol in self.aalist:
            asset = self.__getitem__(symbol)
            assets[symbol] = asset.lastPriceInLoop()
        return assets

    def add_asset(self, _address: Address, is_active: bool = True, is_collateral: bool = False) -> None:
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
        if is_active and not is_collateral:
            asset._active.set(is_active)
            self.aalist.put(symbol)
        if is_collateral:
            asset._is_collateral.set(is_collateral)
            self.collateral.put(symbol)
            if is_active:
                self.aclist.put(symbol)
        self._items[symbol] = asset
