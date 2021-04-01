from iconservice import *
from ..scorelib.id_factory import IdFactory
from ..scorelib.linked_list import *
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

    def __getitem__(self, _symbol: str) -> int:
        if _symbol in self.asset_db.slist:
            return self.assets[self.snaps[-1]][_symbol]
        else:
            revert(f'{_symbol} is not a supported asset on Balanced.')

    def __setitem__(self, key: str, value: int):
        day = self._loans._current_day.get()
        self.check_snap()
        self.assets[day][key] = value

    def __delitem__(self, _symbol: str):
        self.assets[self.snaps[-1]].remove(_symbol)

    def check_snap(self, _day: int = -1) -> None:
        """
        If the specified day is ahead of the last day in the snaps ArrayDB it is
        added to the snaps array and a new snapshot is initialized.

        :param _day: Day number of the snapshot to be added.
        :type _day: int
        """
        current_day = self._loans._current_day.get()
        if _day == -1:
            day = current_day
        else:
            day = _day
        if day > self.snaps[-1] and day <= current_day:
            self.snaps.put(day)
            previous = self.snaps[-2]
            for symbol in self.asset_db.slist:
                if symbol in self.assets[previous]:
                    self.assets[day][symbol] = self.assets[previous][symbol]
            self.replay_index[day] = self.replay_index[previous]

    def last_event_played(self, _day: int = -1) -> int:
        id = self.get_snapshot_id(_day)
        return self.replay_index[id]

    def get_standing(self, _day: int = -1) -> int:
        state = self.snaps_db[_day].pos_state[self.id.get()]
        return state['standing']

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
        id = self.get_snapshot_id(_day)
        if id == -1:
            return False
        for _symbol in self.asset_db.slist:
            if self.assets[id][_symbol] != 0:
                asset = self.asset_db[_symbol]
                if asset.active.get() and not asset.is_collateral.get():
                    return True
        return False

    def _collateral_value(self, _day: int = -1) -> int:
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
        if _day == -1:
            price = asset.priceInLoop()
        else:
            price = self.snaps_db[_day].prices['sICX']
        return amount * price // EXA

    def _total_debt(self, _day: int = -1, _readonly: bool = False) -> int:
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
                    if _day == -1:
                        if _readonly:
                            price = self.asset_db[symbol].lastPriceInLoop()
                        else:
                            price = self.asset_db[symbol].priceInLoop()
                    else:
                        price = self.snaps_db[_day].prices[symbol]
                    asset_value += (price * amount) // EXA
        return asset_value

    def apply_next_event(self) -> bool:
        """
        Updates the position with the next redemption event if there is one.

        :return: True if an event was applied.
        :rtype: bool
        """
        event_log = self._loans._event_log
        snap_index = self.snaps[-1]
        # Check if there are any remaining events to replay.
        total_events = len(event_log)
        if self.replay_index[snap_index] == total_events:
            return Outcome.NO_SUCCESS

        event_index = self.replay_index[snap_index]
        event_snap_index = event_log[event_index].snapshot.get()
        # Finds the next event that applies to the position.
        i = 1
        next_event = event_log[event_index + i]
        while (next_event.index.get() < total_events and
               next_event.symbol.get() not in self.assets[snap_index]):
            i += 1
            next_event = event_log[event_index + i]
        next_event_snap_index = next_event.snapshot.get()
        # If the snapshot of the next event is larger than that of the current
        # event add a new snapshot, if it is also larger than the current one.
        if next_event_snap_index > event_snap_index:
            self.check_snap(next_event_snap_index)

        assets = self.assets[next_event_snap_index]
        symbol = next_event.symbol.get()
        # Note use of dust-free distribution approach.
        pos_value = assets[symbol]
        if pos_value != 0:
            remaining_supply = next_event.remaining_supply.get()
            next_event.remaining_supply.set(remaining_supply - pos_value)

            remaining_value = next_event.remaining_value.get()
            redeemed_from_this_pos = remaining_value * pos_value // remaining_supply
            next_event.remaining_value.set(remaining_value - redeemed_from_this_pos)
            assets[symbol] = pos_value - redeemed_from_this_pos

            returned_sicx_remaining = next_event.returned_sicx_remaining.get()
            sicx_share = returned_sicx_remaining * pos_value // remaining_supply
            next_event.returned_sicx_remaining.set(returned_sicx_remaining - sicx_share)
            assets["sICX"] -= sicx_share

        self.replay_index[next_event_snap_index] = next_event.index.get()
        return Outcome.SUCCESS

    def update_standing(self, _day: int = -1) -> int:
        """
        This method updates the standing for a snapshot. If that snapshot is not
        up to date with the replay events for that day it will set the standing
        to Indeterminate and return. If the position is up to date with
        event replays for the snapshot it will calculate the total debt and
        collateralization ratio and record them in the positon snapshot along
        with the standing.

        :return: Enum of standing from class Standing.
        :rtype: int
        """
        state = self.snaps_db[_day].pos_state[self.id.get()]
        pos_rp_id = self.last_event_played(_day)
        rp_id = self.snaps_db[_day].replay_index.get()
        if pos_rp_id < rp_id:
            state['standing'] = Standing.INDETERMINATE
            return Standing.INDETERMINATE

        debt: int = self._total_debt(_day)
        bnUSD_debt: int = debt * EXA // self.asset_db["bnUSD"].priceInLoop()
        collateral: int = self._collateral_value(_day)
        state['total_debt'] = debt
        if debt == 0:
            state['ratio'] = 0
            if collateral == 0:
                state['standing'] = Standing.ZERO
                return state['standing']
            state['standing'] = Standing.NO_DEBT
            return state['standing']
        ratio: int = collateral * EXA // debt
        state['ratio'] = ratio
        if ratio > DEFAULT_MINING_RATIO * EXA // POINTS:
            if bnUSD_debt < self._loans._min_mining_debt.get():
                state['standing'] = Standing.NOT_MINING
            else:
                state['standing'] = Standing.MINING
        elif ratio > DEFAULT_LOCKING_RATIO * EXA // POINTS:
            state['standing'] = Standing.NOT_MINING
        elif ratio > DEFAULT_LIQUIDATION_RATIO * EXA // POINTS:
            state['standing'] = Standing.LOCKED
        else:
            state['standing'] = Standing.LIQUIDATE
        return state['standing']

    def to_dict(self, _day: int = -1) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """
        id = self.get_snapshot_id(_day)
        if id == -1 or _day > self._loans._current_day.get():
            return {}
        assets = {}
        for asset in self.asset_db.slist:
            if asset in self.assets[id]:
                amount = self.assets[id][asset]
                assets[asset] = amount

        pos_rp_id = self.replay_index[id]
        sys_rp_id = self.snaps_db[_day].replay_index.get()
        pos_id = self.id.get()
        state = self.snaps_db[_day].pos_state[pos_id]
        position = {
            'pos_id': pos_id,
            'created': self.created.get(),
            'address': str(self.address.get()),
            'snap_id': id,
            'snaps_length': len(self.snaps),
            'last_snap': self.snaps[-1],
            'first day': self.snaps[0],
            'assets': assets,
            'replay_index': pos_rp_id,
            'events_behind': sys_rp_id - pos_rp_id,
            'total_debt': self._total_debt(id, True),
            'ratio': state['ratio'],
            'standing': Standing.STANDINGS[state['standing']]
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

        # linked list of all the non zero users
        self.users = LinkedListDB('users', db)

        # The mining list is updated each day for the most recent snapshot.
        self._snapshot_db = SnapshotDB(db, loans)

    def __getitem__(self, id: int) -> Position:
        if id < 0:
            id = self._id_factory.get_last_uid() + id + 1
        if id < 1:
            revert(f'That is not a valid key.')
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
            return {"message": "That address has no outstanding loans or deposited collateral."}
        return self.__getitem__(id).to_dict()

    def get_id_for(self, _owner: Address) -> int:
        return self.addressID[_owner]

    def append_user(self, _owner: Address) -> None:
        # call get pos
        self.get_pos(_owner)
        id = self.addressID[_owner]
        self.users.append(_owner, id)

    def remove_user(self, _owner: Address) -> None:
        id = self.addressID[_owner]
        if id == 0 or id is None:
            revert(f'user does not exist. (remove_user)')
        self.users.remove(id)

    def add_nonzero(self, _owner: Address) -> None:
        id = self.addressID[_owner]
        if id > self._id_factory.get_last_uid() or id < 1:
            revert(f'That key does not exist yet. (add_nonzero)')
        if _owner in self._snapshot_db[-1].remove_from_nonzero:
            self._remove(id, self._snapshot_db[-1].remove_from_nonzero)
        else:
            self._snapshot_db[-1].add_to_nonzero.put(id)

    def remove_nonzero(self, _owner: Address) -> None:
        id = self.addressID[_owner]
        if id > self._id_factory.get_last_uid() or id < 1:
            revert(f'That key does not exist yet. (remove_nonzero)')
        if _owner in self._snapshot_db[-1].add_to_nonzero:
            self._remove(id, self._snapshot_db[-1].add_to_nonzero)
        else:
            self._snapshot_db[-1].remove_from_nonzero.put(id)

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
        now = self._loans.now()
        snap_id = self._loans._current_day.get()
        _new_pos = self.__getitem__(id)
        _new_pos.id.set(id)
        _new_pos.created.set(now)
        _new_pos.address.set(_address)
        _new_pos.snaps.put(snap_id)
        _new_pos.assets[snap_id]['sICX'] = 0
        _new_pos.replay_index[snap_id] = len(self._event_log)
        return _new_pos

    def _take_snapshot(self) -> None:
        """
        Captures necessary data for the current snapshot in the SnapshotDB,
        issues a Snapshot eventlog, and starts a new snapshot.
        """
        snapshot = self._snapshot_db[-1]
        assets = self._loans._assets
        rp_index = len(self._event_log)
        snapshot.replay_index.set(rp_index)
        for symbol in assets.slist:
            if assets[symbol].active.get():
                snapshot.prices[symbol] = assets[symbol].priceInLoop()
        snapshot.snap_time.set(self._loans.now())
        self._loans.Snapshot(self._loans._current_day.get())
        self._snapshot_db.start_new_snapshot()

    def _calculate_snapshot(self, _day: int, batch_size: int) -> bool:
        """
        Iterates once over all positions to play back all remaining retire
        events and calculate their ratios at the end of the snapshot period.

        :param _day: Operating day of the snapshot as passed from rewards via
                     the precompute() method.
        :type _day: int
        :param batch_size: Number of positions to bring up to date.
        :type batch_size: int

        :return: True if complete.
        :rtype: bool
        """
        snapshot = self._snapshot_db[_day]
        id = snapshot.snap_day.get()
        if id < _day:
            return Complete.DONE
        add = len(snapshot.add_to_nonzero)
        remove = len(snapshot.remove_from_nonzero)
        nonzero_deltas = add + remove
        if nonzero_deltas > 0:  # Bring the list of all nonzero positions up to date.
            iter = self._loans._snap_batch_size.get()  # Starting default is 400.
            loops = min(iter, remove)
            for _ in range(loops):
                self._remove(snapshot.remove_from_nonzero.pop(), self.nonzero)
                iter -= 1
            if iter > 0:
                loops = min(iter, add)
                for _ in range(loops):
                    self.nonzero.put(snapshot.add_to_nonzero.pop())
            return Complete.NOT_DONE

        index = snapshot.precompute_index.get()  # Tracks where the precompute is over multiple calls.
        total_nonzero = len(self.nonzero)
        remaining = total_nonzero - index
        batch_mining_debt = 0
        for _ in range(min(remaining, batch_size)):  # Update standing for all nonzero positions.
            account_id = self.nonzero[index]
            pos = self.__getitem__(account_id)
            # all retirement events that happened after the position creation,
            # but before the snapshot must be applied to the position before
            # calculating its value.
            if id >= pos.snaps[0]:
                pos_rp_id = pos.replay_index[id]  # last replay applied to the position for snapshot id
                snap_rp_id = snapshot.replay_index.get()  # last replay for that day from system snapshot.
                if pos_rp_id < snap_rp_id:
                    for _ in range(pos_rp_id, snap_rp_id):
                        pos.apply_next_event()
                standing = pos.update_standing(id)  # Calculates total_debt, ratio, and standing.
                if standing == Standing.MINING:
                    snapshot.mining.put(account_id)
                    batch_mining_debt += snapshot.pos_state[account_id]['total_debt']
            index += 1
        snapshot.total_mining_debt.set(snapshot.total_mining_debt.get() + batch_mining_debt)
        snapshot.precompute_index.set(index)
        if total_nonzero == index:
            return Complete.DONE
        return Complete.NOT_DONE
