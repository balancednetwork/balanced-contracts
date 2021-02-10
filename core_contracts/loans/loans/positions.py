from iconservice import *
from ..scorelib.id_factory import IdFactory
from ..utils.consts import *
from .assets import AssetsDB
from .replay_log import ReplayLogDB, ReplayEvent
from .snapshots import SnapshotDB, Snapshot

TAG = 'BalancedPositions'

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
        self.replay_index = DictDB('replay_index', db, int)
        self.total_debt = DictDB('total_debt', db, int)
        self.ratio = DictDB('ratio', db, int)
        self.standing = DictDB('standing', db, int)

    def __getitem__(self, _symbol: str) -> int:
        if _symbol in self.asset_db.slist:
            return self.assets[self.snaps[-1]][_symbol]
        else:
            revert(f'{_symbol} is not a supported asset on Balanced.')

    def __setitem__(self, key: str, value: int):
        day = self.snap()
        self.assets[day][key] = value

    def snap(self) -> int:
        day = self._loans.getDay()
        if self.snaps[-1] != day:
            self.snaps.put(day)
            today = self.snaps[-1]
            previous = self.snaps[-2]
            for symbol in self.asset_db.slist:
                asset = self.asset_db[symbol]
                self.assets[today][symbol] = self.assets[previous][symbol]
            self.replay_index[today] = self.replay_index[previous]
            self.total_debt[today] = self.total_debt[previous]
            self.ratio[today] = self.ratio[previous]
            self.standing[today] = self.standing[previous]
        return day

    def get_standing(self, _snapshot: int = -1) -> int:
        id = self.get_snapshot_id(_snapshot)
        snap_db_index = self.snaps_db[_snapshot].replay_index.get()
        pos_index = self.replay_index[id]
        # revert(f'id: {id}, pos_index: {pos_index}, snap_db_index: {snap_db_index}')
        if pos_index < snap_db_index:
            return Standing.INDETERMINATE
        return self.standing[id]

    def collateral_value(self, _day: int = -1) -> int:
        """
        Returns the value of the collateral in loop.

        :return: Value of position collateral in loop.
        :rtype: int
        """
        id = self.get_snapshot_id(_day)
        if id == -1:
            return 0
        asset = self.asset_db['sICX']
        amount = self.assets[id]['sICX']
        if id == self.snaps[-1]:
            price = asset.priceInLoop()
        else:
            price = self.snaps_db[id].prices['sICX']
        return amount * price // EXA

    def get_snapshot_id(self, _day: int = -1) -> int:
        """
        Binary serch to return the snapshot id to use for the given day.
        Returns -1 if there was not yet a snapshot on the requested day.

        :param _day: Day number of the desired snapshot ID.
        :type _day: int

        :return: Index to the snapshot database.
        :rtype: int
        """
        if _day < 0:
            if _day + len(self.snaps) < 0:
                revert(f'Snapshot index out of range.')
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
        elif low == len(self.snaps) and low > 1:
            return self.snaps[-2]
        else:
            return self.snaps[low - 1]

    def has_debt(self, _day: int = -1) -> bool:
        """
        Returns True if the snapshot from _day for the position holds any debt.

        :return: Existence of a debt position.
        :rtype: bool
        """
        id = self.get_snapshot_id(_day)
        if id == -1:
            return False
        for _symbol in self.asset_db.slist:
            asset = self.asset_db[_symbol]
            if (asset.active.get() and
                    not asset.is_collateral.get() and
                    self.assets[id][_symbol] != 0):
                return True
        return False

    def _total_debt(self, _day: int = -1) -> int:
        """
        Returns the total value of all outstanding debt in loop. Only valid
        for updated positions.

        :return: Value of all outstanding debt in loop.
        :rtype: int
        """
        id = self.get_snapshot_id(_day)
        if id == -1:
            return 0
        asset_value = 0
        for symbol in self.asset_db.slist:
            if not self.asset_db[symbol].is_collateral.get() and symbol in self.assets[id]:
                amount = self.assets[id][symbol]
                if amount > 0:
                    if id == self.snaps[-1]:
                        price = self.asset_db[symbol].priceInLoop()
                    else:
                        price = self.snaps_db[id].prices[symbol]
                    asset_value += (price * amount) // EXA
        return asset_value

    def apply_next_event(self) -> bool:
        """
        Updates the position with the next redemption event if there is one.
        """
        snap_index = self.snaps[-1]
        # Check if there are any remaining events to replay.
        if self.replay_index[snap_index] == len(self._loans._event_log):
            return Outcome.NO_SUCCESS

        event_index = self.replay_index[snap_index] + 1
        _event = self._loans._event_log[event_index]
        symbol = _event.symbol.get()
        remaining_supply = _event.remaining_supply.get()
        remaining_value = _event.remaining_value.get()
        returned_sicx_remaining = _event.returned_sicx_remaining.get()

        while event_index > self.snaps_db[snap_index].replay_index.get():
            snap_index += 1
        if snap_index != self.snaps[-1]:
            self.snaps.put(snap_index)
            for _symbol in self.asset_db.slist:
                self.assets[snap_index] = self.assets[self.snaps[-2]]

        assets = self.assets[snap_index]
        pos_value = assets[symbol]
        redeemed_from_this_pos = remaining_value * pos_value // remaining_supply
        sicx_share = returned_sicx_remaining * pos_value // remaining_supply
        _event.remaining_supply.set(remaining_supply - pos_value)
        _event.remaining_value.set(remaining_value - redeemed_from_this_pos)
        _event.returned_sicx_remaining.set(returned_sicx_remaining - sicx_share)
        assets["sICX"] -= sicx_share
        assets[symbol] = pos_value - redeemed_from_this_pos
        index = _event.index.get()
        self.replay_index[snap_index] = index
        return Outcome.SUCCESS

    def update_standing(self, _day: int = -1) -> int:
        id = self.get_snapshot_id(_day)
        if id == -1:
            revert(f'Invalid snapshot id.')
        if self.replay_index[id] != self.snaps_db[id].replay_index.get():
            self.standing[id] = Standing.INDETERMINATE
            return Standing.INDETERMINATE
        debt = self._total_debt(id)
        self.total_debt[id] = debt
        if debt == 0:
            if self.assets[id]['sICX'] == 0:
                self.standing[id] = Standing.ZERO
            self.standing[id] = Standing.NO_DEBT
            return self.standing[id]
        ratio: int = self.collateral_value(id) * EXA // debt
        self.ratio[id] = ratio
        if ratio > DEFAULT_MINING_RATIO * EXA // 100:
            self.standing[id] = Standing.MINING
        elif ratio > DEFAULT_LOCKING_RATIO * EXA // 100:
            self.standing[id] = Standing.NOT_MINING
        elif ratio > DEFAULT_LIQUIDATION_RATIO * EXA // 100:
            self.standing[id] = Standing.LOCKED
        else:
            self.standing[id] = Standing.LIQUIDATE
        return self.standing[id]

    def to_dict(self, _day: int = -1) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """
        id = self.get_snapshot_id(_day)
        if id == -1:
            revert(f'Invalid snapshot id.')
        assets = {}
        for asset in self.asset_db.slist:
            if asset in self.assets[id]:
                amount = self.assets[id][asset]
                assets[asset] = amount

        position = {
            'pos_id': self.id.get(),
            'created': self.created.get(),
            'address': str(self.address.get()),
            'assets': assets,
            'last_snap': self.snaps[-1],
            'this_snap': id,
            f'replay_index_{id}': self.replay_index[id],
            f'total_debt_{id}': self.total_debt[id],
            f'ratio_{id}': self.ratio[id],
            f'standing_{id}': Standing.STANDINGS[self.get_standing(id)]
        }
        return position


class PositionsDB:

    IDFACTORY = 'idfactory'
    ADDRESSID = 'addressid'
    NONZERO = 'nonzero'

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase):
        self._db = db
        self._loans = loans
        self._items = {}
        self._event_log = ReplayLogDB(db, loans)
        self._id_factory = IdFactory(self.IDFACTORY, db)
        self.addressID = DictDB(self.ADDRESSID, db, value_type=int)
        # list of nonzero positions will be brought up to date at the end of each day.
        self.nonzero = ArrayDB(self.NONZERO, db, value_type=int)
        # The mining list is updated each day for the most recent snapshot.
        self._snapshot_db = SnapshotDB(db, loans)

    def __getitem__(self, id: int) -> Position:
        if id not in self._items:
            if id > self._id_factory.get_last_uid():
                revert(f'That key does not exist yet.')
            sub_db = self._db.get_sub_db(b'|'.join([POSITION_DB_PREFIX, str(id).encode()]))
            self._items[id] = Position(sub_db, self._db, self._loans)

        return self._items[id]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self):
        return self._id_factory.get_last_uid()

    def _exists(self, _address: Address) -> bool:
        return self.addressID[_address] != 0

    def list_pos(self, _owner: Address) -> dict:
        id = self.addressID[_owner]
        if id == 0:
            return "That address has no outstanding loans or deposited collateral."
        return self.__getitem__(id).to_dict()

    def add_nonzero(self, _owner: Address) -> None:
        id = self.addressID[_owner]
        snap = self._loans.getDay()
        if id > self._id_factory.get_last_uid() or id < 1:
            revert(f'That key does not exist yet. (add_nonzero)')
        if _owner in self._snapshot_db[snap].remove_from_nonzero:
            self._remove(id, self._snapshot_db[snap].remove_from_nonzero)
        else:
            self._snapshot_db[snap].add_to_nonzero.put(id)

    def remove_nonzero(self, _owner: Address) -> None:
        id = self.addressID[_owner]
        snap = self._loans.getDay()
        if id > self._id_factory.get_last_uid() or id < 1:
            revert(f'That key does not exist yet. (remove_nonzero)')
        if _owner in self._snapshot_db[snap].add_to_nonzero:
            self._remove(id, self._snapshot_db[snap].add_to_nonzero)
        else:
            self._snapshot_db[snap].remove_from_nonzero.put(id)

    def _remove(self, item: int, array: ArrayDB) -> None:
        top = array.pop()
        if top != item:
            for i in range(len(array)):
                if array[i] == item:
                    array[i] = top
                    return

    def get_pos(self, _owner: Address) -> Position:
        id = self.addressID[_owner]
        if id == 0:
            return self.new_pos(_owner)
        return self.__getitem__(id)

    def new_pos(self, _address: Address) -> Position:
        if self.addressID[_address] != 0:
            revert(f'A position already exists for that address.')
        id = self._id_factory.get_uid()
        self.addressID[_address] = id
        snap_id = self._snapshot_db._indexes[-1]
        _new_pos = self.__getitem__(id)
        _new_pos.created.set(self._loans.now())
        _new_pos.address.set(_address)
        _new_pos.replay_index[snap_id] = len(self._event_log)
        _new_pos.assets[snap_id]['sICX'] = 0
        _new_pos.id.set(id)
        _new_pos.snaps.put(self._loans.getDay())
        return _new_pos

    def _take_snapshot(self) -> None:
        """
        Captures necessary data for the current snapshot in the SnapshotDB.
        """
        snapshot = self._snapshot_db[-1]
        assets = self._loans._assets
        for symbol in assets.slist:
            if assets[symbol].active.get():
                snapshot.prices[symbol] = assets[symbol].priceInLoop()
        snapshot.replay_index.set(len(self._event_log._events))
        snapshot.snap_time.set(self._loans.now())
        self._loans.Snapshot(self._snapshot_db._indexes[-1])
        self._snapshot_db.start_new_snapshot()

    def _calculate_snapshot(self, id: int, batch_size: int) -> bool:
        """
        Iterates once over all positions to play back all remaining retire
        events and calculate their ratios at the end of the snapshot period.
        """
        snapshot = self._snapshot_db[id]
        index = snapshot.precompute_index.get()
        add = len(snapshot.add_to_nonzero)
        remove = len(snapshot.remove_from_nonzero)
        nonzero_deltas = add + remove
        if nonzero_deltas > 0: # Bring the list of all nonzero positions up to date.
            iter = self._loans._snap_batch_size.get()
            for _ in range(min(iter, remove)):
                self._remove(snapshot.remove_from_nonzero.pop(), self.nonzero)
                iter -= 1
            if iter > 0:
                for _ in range(min(iter, add)):
                    self.nonzero.put(snapshot.add_to_nonzero.pop())
            return Complete.NOT_DONE
        remaining = len(self.nonzero) - index
        batch_mining_debt = 0
        for _ in range(min(remaining, batch_size)): # Update standing for all nonzero positions.
            account_id = self.nonzero[index]
            pos = self.__getitem__(account_id)
            # all retirement events that happened before the snapshot must be
            # applied to the position before calculating its value.
            pos_rp_id = pos.replay_index[id]
            snap_rp_id = snapshot.replay_index.get()
            if pos_rp_id < snap_rp_id:
                for rp_id in range(snap_rp_id, pos_rp_id + 1):
                    pos.apply_next_event()
                standing = pos.update_standing(id)
            else:
                standing = pos.update_standing(id)
            if standing == Standing.MINING:
                snapshot.mining.put(account_id)
                batch_mining_debt += pos.total_debt[id]
            index += 1
        snapshot.total_mining_debt.set(snapshot.total_mining_debt.get() + batch_mining_debt)
        if len(self.nonzero) == index:
            return Complete.DONE
        snapshot.precompute_index.set(index)
        return Complete.NOT_DONE
