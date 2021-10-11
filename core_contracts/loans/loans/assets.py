# Copyright 2021 Balanced DAO
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ..scorelib.linked_list import *
from .loans import OracleInterface

TAG = 'BalancedLoansAssets'
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


class Asset(object):

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self._db = db
        self._loans = loans
        self.added = VarDB('added', db, value_type=int)
        self.asset_address = VarDB('address', db, value_type=Address)
        self.bad_debt = VarDB('bad_debt', db, value_type=int)
        self.liquidation_pool = VarDB('liquidation_pool', db, value_type=int)
        self._burned = VarDB('burned', db, value_type=int)
        self._is_collateral = VarDB('is_collateral', db, value_type=bool)
        self._active = VarDB('active', db, value_type=bool)
        self.dead_market = VarDB('dead_market', db, value_type=bool)

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
        except Exception:
            revert(f'{TAG}: Trouble minting {self.symbol()} tokens to {_to}.')

    def burn(self, _amount: int) -> None:
        """
        Burn asset.
        """
        try:
            token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
            token.burn(_amount)
            self._burned.set(self._burned.get() + _amount)
        except Exception:
            revert(f'{TAG}: Trouble burning {self.symbol()} tokens.')

    def burnFrom(self, _account: Address, _amount: int) -> None:
        """
        Burn asset.
        """
        try:
            token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
            token.burnFrom(_account, _amount)
            self._burned.set(self._burned.get() + _amount)
        except Exception:
            revert(f'{TAG}: Trouble burning {self.symbol()} tokens.')

    def priceInUSD(self) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        token_symbol = token.symbol()
        oracle = self._loans.create_interface_score(self._loans.getOracle(), OracleInterface)
        return oracle.priceInUSD(token_symbol)

    def lastPriceInUSD(self) -> int:
        token = self._loans.create_interface_score(self.asset_address.get(), TokenInterface)
        token_symbol = token.symbol()
        oracle = self._loans.create_interface_score(self._loans.getOracle(), OracleInterface)
        return oracle.lastPriceInUSD(token_symbol)

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
        pool_value = self.liquidation_pool.get() * self.priceInUSD() // self._loans._assets['sICX'].priceInUSD()
        net_bad_debt = bad_debt - pool_value
        dead = net_bad_debt > outstanding / 2
        if dead != self.dead_market.get():
            self.dead_market.set(dead)
        return dead

    def get_borrowers(self) -> LinkedListDB:
        return LinkedListDB('borrowers', self._db, value_type=int)

    def remove_borrower(self, _pos_id: int) -> None:
        """
        Removes a borrower from the asset nonzero list.
        """
        borrowers = self.get_borrowers()
        borrowers.remove(_pos_id)

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
            'borrowers': len(self.get_borrowers()),
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
            revert(f'{TAG}: {_symbol} is not a supported asset.')
        return self._items[_symbol]

    def __setitem__(self, key, value):
        revert(f'{TAG}: Illegal access.')

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
            assets[symbol] = asset.lastPriceInUSD()
        return assets

    def add_asset(self, _address: Address, is_active: bool = True, is_collateral: bool = False) -> None:
        address = str(_address)
        if _address in self.alist:
            revert(f'{TAG}: {address} already exists in the database.')
        self.alist.put(_address)
        asset = self._get_asset(address)
        asset.asset_address.set(_address)
        asset.added.set(self._loans.now())
        symbol = asset.symbol()
        self.slist.put(symbol)
        self.symboldict[symbol] = address
        if is_active:
            asset._active.set(is_active)
            if is_collateral:
                self.aclist.put(symbol)
            else:
                self.aalist.put(symbol)
        if is_collateral:
            asset._is_collateral.set(is_collateral)
            self.collateral.put(symbol)
        self._items[symbol] = asset
