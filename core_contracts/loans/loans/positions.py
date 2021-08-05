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

    def __getitem__(self, _symbol: str) -> int:
        if _symbol in self.asset_db.slist:
            return self.assets[self.snaps[-1]][_symbol]
        else:
            revert(f'{TAG}: {_symbol} is not a supported asset on Balanced.')

    def __setitem__(self, key: str, value: int):
        day = self.check_snap()
        self.assets[day][key] = value
        if key in self.asset_db.aalist:
            borrowers = self.asset_db[key].get_borrowers()
            # if id does not exist in borrowers a new node is created.
            borrowers[self.id.get()] = value

    def __delitem__(self, _symbol: str):
        self.assets[self.snaps[-1]].remove(_symbol)
        if _symbol in self.asset_db.aalist:
            self.asset_db[_symbol].remove_borrower(self.id.get())

    def check_snap(self) -> int:
        """
        If the current day is ahead of the last day in the snaps ArrayDB it is
        added to the snaps array and a new snapshot is initialized.

        :return: index for the current day.
        :rtype: int
        """
        day = self._loans.getDay()
        if day > self.snaps[-1]:
            self.snaps.put(day)
            previous = self.snaps[-2]
            for symbol in self.asset_db.slist:
                if symbol in self.assets[previous]:
                    self.assets[day][symbol] = self.assets[previous][symbol]
        return day

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

    def has_debt(self, _day: int = -1) -> bool:
        """
        Returns True if the snapshot from _day for the position holds any debt.

        :return: Existence of a debt position.
        :rtype: bool
        """
        _id = self.get_snapshot_id(_day)
        if _id == -1:
            return False
        for symbol in self.asset_db.aalist:
            if self.assets[_id][symbol] != 0:
                return True
        return False

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
            if _day == -1 or _day == self._loans.getDay():
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
                if _day == -1 or _day == self._loans.getDay():
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

        if ratio > self._loans._mining_ratio.get() * EXA // POINTS:
            if _day == -1 or _day == self._loans.getDay():
                if _readonly:
                    price = self.asset_db["bnUSD"].lastPriceInLoop()
                else:
                    price = self.asset_db["bnUSD"].priceInLoop()
            else:
                price = self.snaps_db[_day].prices["bnUSD"]

            bnUSD_debt: int = debt * EXA // price
            if bnUSD_debt < self._loans._min_mining_debt.get():
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

    def update_standing(self, _day: int = -1) -> int:
        """
        This method updates the standing for a snapshot. It will calculate the
        total debt and collateralization ratio and record them in the position
        snapshot along with the standing.

        :return: Enum of standing from class Standing.
        :rtype: int
        """
        state = self.snaps_db[_day].pos_state[self.id.get()]

        status = self.get_standing(_day)
        state['total_debt'] = status['debt']
        state['ratio'] = status['ratio']
        state['standing'] = status['standing']

        return status['standing']

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
        # The mining list is updated each day for the most recent snapshot.
        self._snapshot_db = SnapshotDB(db, loans)

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

    def get_nonzero(self) -> LinkedListDB:
        return LinkedListDB(self.NONZERO, self._db, value_type=int)

    def add_nonzero(self, _owner_id: int) -> None:
        current_snapshot = self._snapshot_db[-1]
        add_to_nonzero = current_snapshot.get_add_nonzero()
        remove_from_nonzero = current_snapshot.get_remove_nonzero()
        if _owner_id in remove_from_nonzero:
            remove_from_nonzero.remove(_owner_id)
        else:
            add_to_nonzero.append(0, _owner_id)

    def remove_nonzero(self, _owner_id: int) -> None:
        current_snapshot = self._snapshot_db[-1]
        add_to_nonzero = current_snapshot.get_add_nonzero()
        remove_from_nonzero = current_snapshot.get_remove_nonzero()
        if _owner_id in add_to_nonzero:
            add_to_nonzero.remove(_owner_id)
        else:
            remove_from_nonzero.append(0, _owner_id)

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
        _new_pos.snaps.put(snap_id)
        _new_pos.assets[snap_id]['sICX'] = 0
        self._items[_id] = _new_pos
        return _new_pos

    def _take_snapshot(self) -> None:
        """
        Captures necessary data for the current snapshot in the SnapshotDB,
        issues a Snapshot eventlog, and starts a new snapshot.
        """
        snapshot = self._snapshot_db[-1]
        assets = self._loans._assets
        for symbol in assets.slist:
            if assets[symbol].is_active():
                snapshot.prices[symbol] = assets[symbol].priceInLoop()
        snapshot.snap_time.set(self._loans.now())
        self._loans.Snapshot(self._loans.getDay())
        self._snapshot_db.start_new_snapshot()

    def _calculate_snapshot(self, _day: int, batch_size: int) -> bool:
        """
        Iterates once over all positions to calculate their ratios at the end
        of the snapshot period.

        :param _day: Operating day of the snapshot as passed from rewards via
                     the precompute() method.
        :type _day: int
        :param batch_size: Number of positions to bring up to date.
        :type batch_size: int

        :return: True if complete.
        :rtype: bool
        """
        snapshot = self._snapshot_db[_day]
        _id = snapshot.snap_day.get()
        if _id < _day:
            return Complete.DONE

        add_to_nonzero = snapshot.get_add_nonzero()
        remove_from_nonzero = snapshot.get_remove_nonzero()
        add = len(add_to_nonzero)
        remove = len(remove_from_nonzero)
        nonzero_deltas = add + remove
        nonzero = self.get_nonzero()
        if nonzero_deltas > 0:  # Bring the list of all nonzero positions up to date.
            _iter = self._loans._snap_batch_size.get()  # Starting default is 50.
            loops = min(_iter, remove)
            if remove > 0:
                next_node = remove_from_nonzero.get_head_id()
            for _ in range(loops):
                nonzero.remove(next_node)
                remove_from_nonzero.remove(next_node)
                next_node = remove_from_nonzero.get_head_id()
                _iter -= 1
            if _iter > 0:
                loops = min(_iter, add)
                if add > 0:
                    next_node = add_to_nonzero.get_head_id()
                for _ in range(loops):
                    nonzero.append(0, next_node)
                    add_to_nonzero.remove(next_node)
                    next_node = add_to_nonzero.get_head_id()
            nonzero.serialize()
            return Complete.NOT_DONE

        index = snapshot.precompute_index.get()  # Tracks where the precompute is over multiple calls.
        total_nonzero = len(nonzero)
        next_node = self.next_node.get()
        if next_node == 0:
            next_node = nonzero.get_head_id()
        remaining = total_nonzero - index
        batch_mining_debt = 0
        for _ in range(min(remaining, batch_size)):  # Update standing for all nonzero positions.
            account_id = next_node
            pos = self.__getitem__(account_id)
            # Only positions created before the day of this snapshot are used.
            if _id >= pos.snaps[0]:
                standing = pos.update_standing(_id)  # Calculates total_debt, ratio, and standing.
                if standing == Standing.MINING:
                    snapshot.mining.put(account_id)
                    batch_mining_debt += snapshot.pos_state[account_id]['total_debt']
            index += 1
            if next_node == nonzero.get_tail_id():
                next_node = 0
            else:
                next_node = nonzero.next(next_node)
        snapshot.total_mining_debt.set(snapshot.total_mining_debt.get() + batch_mining_debt)
        snapshot.precompute_index.set(index)
        self.next_node.set(next_node)
        if total_nonzero == index:
            return Complete.DONE
        return Complete.NOT_DONE
