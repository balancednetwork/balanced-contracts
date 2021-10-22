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
from .snapshots import SnapshotDB

TAG = 'BalancedLoansPositions'
POSITION_DB_PREFIX = b'position'


class Position(object):

    def __init__(self, db: IconScoreDatabase, main_db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self.asset_db = AssetsDB(main_db, loans)
        self.snaps_db = SnapshotDB(main_db, loans)
        self._loans = loans
        self.id = VarDB('id', db, int)
        self.created = VarDB('created', db, int)
        self.address = VarDB('address', db, Address)

        self.snaps = ArrayDB('snaps', db, int)
        self.assets = DictDB('assets', db, int, depth=2)
        self._snapshot_db = SnapshotDB(db, loans)

    def __getitem__(self, _symbol: str) -> int:
        if _symbol in self.asset_db.slist:
            return self.assets[self.snaps[-1]][_symbol]
        else:
            revert(f'{TAG}: {_symbol} is not a supported asset on Balanced.')

    def __setitem__(self, key: str, value: int):
        self.assets[self.snaps[-1]][key] = value
        if key in self.asset_db.aalist:
            borrowers = self.asset_db[key].get_borrowers()
            # if id does not exist in borrowers a new node is created.
            borrowers[self.id.get()] = value

    def __delitem__(self, _symbol: str):
        self.assets[self.snaps[-1]].remove(_symbol)
        if _symbol in self.asset_db.aalist:
            self.asset_db[_symbol].remove_borrower(self.id.get())

    def get_snapshot_id(self, _day: int = -1) -> int:
        """
        Binary search to return the snapshot id to use for the given day.
        Returns -1 if there was not yet a snapshot on the requested day.

        :param _day: Day number of the desired snapshot ID.
        :type _day: int

        :return: Index to the snapshot database.
        :rtype: int
        """
        if _day < 0:
            if _day + len(self.snaps) < 0:
                return -1
            return self.snaps[_day]

        low = 0
        high = len(self.snaps)
        while low < high:
            mid = (low + high) // 2
            if self.snaps[mid] > _day:
                high = mid
            else:
                low = mid + 1

        if self.snaps[0] == _day:
            return _day
        elif low == 0:
            return -1
        else:
            return self.snaps[low - 1]

    def _collateral_value(self, _day: int = -1) -> int:
        """
        Returns the value of the collateral in loop.

        :return: Value of position collateral in loop.
        :rtype: int
        """
        _id = self.get_snapshot_id(_day)
        if _id == -1:
            return 0
        value = 0
        for symbol in self.asset_db.aclist:
            asset = self.asset_db[symbol]
            amount = self.assets[_id][symbol]
            if _day == -1 or _day == self.snaps[-1]:
                price = asset.priceInLoop()
            else:
                price = self.snaps_db[_day].prices[symbol]
            value += amount * price // EXA
        return value

    def total_debt(self, _day: int = -1, _readonly: bool = False) -> int:
        """
        Returns the total value of all outstanding debt in loop. Only valid
        for updated positions.

        :return: Value of all outstanding debt in loop.
        :rtype: int
        """
        _id = self.get_snapshot_id(_day)
        if _id == -1:
            return 0
        asset_value = 0
        for symbol in self.asset_db.aalist:
            amount = self.assets[_id][symbol]
            if amount > 0:
                if _day == -1 or _day == self.snaps[-1]:
                    if _readonly:
                        price = self.asset_db[symbol].lastPriceInLoop()
                    else:
                        price = self.asset_db[symbol].priceInLoop()
                else:
                    price = self.snaps_db[_day].prices[symbol]
                asset_value += (price * amount) // EXA
        return asset_value

    def get_standing(self, _day: int = -1, _readonly: bool = False) -> dict:
        """
        Calculates the standing for a position. Uses the readonly method for
        asset prices if the _readonly flag is True.

        :return: Total debt, collateralization ration, enum of standing from class Standing.
        :rtype: dict
        """
        status = {}
        debt = self.total_debt(_day, _readonly)
        status['debt'] = debt
        collateral = self._collateral_value(_day)
        status['collateral'] = collateral

        if debt == 0:
            status['ratio'] = 0
            if collateral == 0:
                status['standing'] = Standing.ZERO
                return status
            status['standing'] = Standing.NO_DEBT
            return status

        ratio = collateral * EXA // debt

        if ratio > self._loans._liquidation_ratio.get() * EXA // POINTS:
            standing = Standing.MINING
        else:
            standing = Standing.LIQUIDATE

        status['ratio'] = ratio
        status['standing'] = standing
        return status

    def to_dict(self, _day: int = -1) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """
        _id = self.get_snapshot_id(_day)
        if _id == -1 or _day > self._loans.getDay():
            return {}
        assets = {}
        if _id == self.snaps[-1]:
            _id = self._loans.getDay()
        for asset in self.asset_db.slist:
            if asset in self.assets[_id]:
                amount = self.assets[_id][asset]
                assets[asset] = amount

        pos_id = self.id.get()
        status = self.get_standing(_day, True)
        position = {
            'pos_id': pos_id,
            'created': self.created.get(),
            'address': str(self.address.get()),
            'snap_id': _id,
            'snaps_length': len(self.snaps),
            'last_snap': self.snaps[-1],
            'first day': self.snaps[0],
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
        snap_id = self._loans.getDay()
        _new_pos = self.__getitem__(_id)
        _new_pos.id.set(_id)
        _new_pos.created.set(now)
        _new_pos.address.set(_address)
        _new_pos.assets[snap_id]['sICX'] = 0
        self._items[_id] = _new_pos
        return _new_pos