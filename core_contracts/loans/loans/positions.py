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

from iconservice import *
from ..scorelib.id_factory import IdFactory
from ..scorelib.linked_list import *
from ..utils.consts import *
from .assets import AssetsDB

TAG = 'BalancedLoansPositions'
POSITION_DB_PREFIX = b'position'


class Position(object):

    def __init__(self, db: IconScoreDatabase, main_db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self.asset_db = AssetsDB(main_db, loans)
        self._loans = loans
        self.id = VarDB('id', db, int)
        self.created = VarDB('created', db, int)
        self.address = VarDB('address', db, Address)

        # TODO: sicx here | move to snapshot handling after new collateral migration
        self.assets = DictDB('assets', db, int, depth=2)

        # other collateral
        self.collateral_loans = DictDB('collateral_loans', db, int, depth=2)
        self.collateral_owned = DictDB('collateral_owned', db, int)

    def get_loans(self, collateral: str = '', symbol: str = '') -> int:
        if collateral == '':
            collaterals = [i for i in self.asset_db.active_collateral_list]
        else:
            collaterals = [collateral]
        if symbol == '':
            symbols = [i for i in self.asset_db.symbol_list]
        else:
            symbols = [symbol]
        sum = 0
        for collateral in collaterals:
            for symbol in symbols:
                sum += self.collateral_loans[collateral][symbol]
        return sum

    def set_loan_amt(self, collateral: str, _symbol: str, value: int) -> None:
        if collateral not in self.asset_db.active_collateral_list:
            revert(f"{collateral} is not an active collateral.")
        if _symbol not in self.asset_db.symbol_list:
            revert(f"{_symbol} is not supported.")

        self.collateral_loans[collateral][_symbol] = value

        if _symbol in self.asset_db.active_address_list:
            borrowers = self.asset_db[_symbol].get_borrowers(collateral)
            # if id does not exist in borrowers a new node is created.
            borrowers[self.id.get()] = value

    def set_collateral_amt(self, collateral: str, value: int) -> None:
        if collateral not in self.asset_db.active_collateral_list:
            revert(f"{collateral} is not an active collateral.")
        self.collateral_owned[collateral] = value

    def clear_loans(self, collateral: str, symbol: str):
        if collateral in self.asset_db.active_collateral_list:
            if symbol in self.asset_db.active_address_list:
                self.collateral_loans[collateral][symbol].remove_borrower(self.id.get())

    def has_debt(self, collateral: str = '', symbol: str = '') -> bool:
        """
        Returns True if the account has debt.

        :return: Existence of a debt position.
        :rtype: bool
        """
        collateral_list = [i for i in self.asset_db.active_collateral_list]
        if collateral != '':
            if collateral not in collateral_list:
                revert(f"{collateral} is not an active collateral.")
            collateral_list = [collateral]
        if symbol == '':
            symbol_list = [symbol for symbol in self.asset_db.active_address_list]
        else:
            symbol_list = [symbol]
        for collateral in collateral_list:
            for symbol in symbol_list:
                if self.get_loans(collateral, symbol) != 0:
                    return True
        return False

    def collateral_value(self, symbol: str = '') -> int:
        """
        Returns the value of the collateral in loop.

        :return: Value of position collateral in loop.
        :rtype: int
        """
        value = 0
        if symbol == '':
            symbol_list = [symbol for symbol in self.asset_db.active_collateral_list]
        else:
            symbol_list = [symbol]
        for symbol in symbol_list:
            asset = self.asset_db[symbol]
            amount = self.collateral_owned[symbol]
            price = asset.priceInLoop()
            value += amount * price // EXA
        return value

    def total_debt(self, collateral: str = '', symbol: str = '', _readonly: bool = False) -> int:
        """
        Returns the total value of all outstanding debt in loop. Only valid
        for updated positions.

        :return: Value of all outstanding debt in loop.
        :rtype: int
        """
        asset_value = 0

        collateral_list = [i for i in self.asset_db.active_collateral_list]
        if collateral != '':
            if collateral not in collateral_list:
                revert(f"{collateral} is not an active collateral.")
            collateral_list = [collateral]

        if symbol == '':
            symbol_list = [symbol for symbol in self.asset_db.active_address_list]
        else:
            symbol_list = [symbol]
        for collateral in collateral_list:
            for symbol in symbol_list:
                amount = self.get_loans(collateral, symbol)
                if amount > 0:
                    if _readonly:
                        price = self.asset_db[symbol].lastPriceInLoop()
                    else:
                        price = self.asset_db[symbol].priceInLoop()
                    asset_value += (price * amount) // EXA
        return asset_value

    def get_standing(self, collateral_symbol: str = '', _readonly: bool = False) -> dict:
        """
        Calculates the standing for a position. Uses the readonly method for
        asset prices if the _readonly flag is True.

        :return: Total debt, collateralization ration, enum of standing from class Standing.
        :rtype: dict
        """
        status = {}
        debt = self.total_debt(collateral=collateral_symbol, _readonly=_readonly)
        status['debt'] = debt
        collateral = self.collateral_value(collateral_symbol)
        status['collateral'] = collateral

        if debt == 0:
            status['ratio'] = 0
            if collateral == 0:
                status['standing'] = Standing.ZERO
                return status
            status['standing'] = Standing.NO_DEBT
            return status

        ratio = collateral * EXA // debt

        if ratio > self._loans._mining_ratio.get() * EXA // POINTS:
            price = self.total_debt(collateral_symbol, _readonly=_readonly)

            debt: int = debt * EXA // price
            if debt < self._loans._min_mining_debt.get():
                standing = Standing.NOT_MINING
            else:
                standing = Standing.MINING
        elif ratio > self._loans._locking_ratio.get() * EXA // POINTS:
            standing = Standing.NOT_MINING
        elif ratio > self._loans._liquidation_ratio.get() * EXA // POINTS:
            standing = Standing.LOCKED
        else:
            standing = Standing.LIQUIDATE

        status['ratio'] = ratio
        status['standing'] = standing
        return status

    def to_dict(self) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """
        assets = {}
        for collateral in self.asset_db.active_collateral_list:
            for asset in self.asset_db.symbol_list:
                if asset in self.collateral_loans[collateral]:
                    amount = self.assets[collateral][asset]
                    assets[asset] = amount

        pos_id = self.id.get()
        status = self.get_standing(_readonly=True)
        position = {
            'pos_id': pos_id,
            'created': self.created.get(),
            'address': str(self.address.get()),
            'assets': assets,
            'total_debt': status['debt'],
            'collateral': status['collateral'],
            'ratio': status['ratio'],
            'standing': Standing.STANDINGS[status['standing']]
        }
        return position


class PositionsDB:
    IDFACTORY = 'idfactory'
    ADDRESSID = 'addressid'
    NONZERO = 'nonzero'
    NEXT_NODE = 'next_node'

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase):
        self._db = db
        self._loans = loans
        self._items = {}
        self._id_factory = IdFactory(self.IDFACTORY, db)
        self.addressID = DictDB(self.ADDRESSID, db, value_type=int)

        self.next_node = VarDB(self.NEXT_NODE, db, value_type=int)

    def __getitem__(self, _id: int) -> Position:
        if _id < 0:
            _id = self._id_factory.get_last_uid() + _id + 1
        if _id < 1:
            revert(f'{TAG}: That is not a valid key.')
        if _id not in self._items:
            if _id > self._id_factory.get_last_uid():
                revert(f'{TAG}: That key does not exist yet.')
            sub_db = self._db.get_sub_db(b'|'.join([POSITION_DB_PREFIX, str(_id).encode()]))
            self._items[_id] = Position(sub_db, self._db, self._loans)

        return self._items[_id]

    def __setitem__(self, key, value):
        revert(f'{TAG}: Illegal access.')

    def __len__(self):
        return self._id_factory.get_last_uid()

    def _exists(self, _address: Address) -> bool:
        return self.addressID[_address] != 0

    def list_pos(self, _owner: Address) -> dict:
        _id = self.addressID[_owner]
        if _id == 0:
            return {"message": "That address has no outstanding loans or deposited collateral."}
        return self.__getitem__(_id).to_dict()

    def get_id_for(self, _owner: Address) -> int:
        return self.addressID[_owner]

    def get_pos(self, _owner: Address) -> Position:
        _id = self.addressID[_owner]
        if _id == 0:
            return self.new_pos(_owner)
        return self.__getitem__(_id)

    def new_pos(self, _address: Address) -> Position:
        if self.addressID[_address] != 0:
            revert(f'{TAG}: A position already exists for that address.')
        _id = self._id_factory.get_uid()
        self.addressID[_address] = _id
        now = self._loans.now()
        _new_pos = self.__getitem__(_id)
        _new_pos.id.set(_id)
        _new_pos.created.set(now)
        _new_pos.address.set(_address)
        # TODO: bigya default balance?
        # _new_pos.collateral_loans[snap_id]['sICX'] = 0
        self._items[_id] = _new_pos
        return _new_pos
