from iconservice import *

TAG = 'LoansSnapshots'

SNAP_DB_PREFIX = b'snaps'


class Snapshot(object):

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self._loans = loans
        self.snap_day = VarDB('snap_day', db, int)
        # Time of snapshot
        self.snap_time = VarDB('snap_time', db, int)
        # Total Debt elegible for mining rewards for each asset. Will be calculated
        # after the snap is complete, in the precompute method.
        self.total_mining_debt = VarDB('total_mining_debt', db, int)
        # Oracle Price for each asset at snapshot time.
        self.prices = DictDB('prices', db, int)
        # Latest Replay Index at the time of each snapshot
        self.replay_index = VarDB('replay_index', db, int)
        # index to track progress through the single precompute pass for each snap.
        # Starts at zero and counts up to the last index in the mining ArrayDB.
        self.precompute_index = VarDB('precompute_index', db, int)
        # List of position ids in the mining state at snapshot time. This list
        # will be compiled in the precompute method as each position in the
        # nonzero ArrayDB is brought up to date.
        self.mining = ArrayDB('mining', db, int)
        # List of position ids that changed to non-zero collateral status since the last snap.
        # used to update the nonzero ArrayDB during calls to the precompute method.
        self.add_to_nonzero = ArrayDB('nonzero', db, int)
        # List of position ids that changed to a zero collateral status since the last snap.
        # used to update the nonzero ArrayDB during calls to the precompute method.
        self.remove_from_nonzero = ArrayDB('zero', db, int)

    def to_dict(self) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """
        snap = {
            'snap_day': self.snap_day.get(),
            'snap_time': self.snap_time.get(),
            'total_mining_debt': self.total_mining_debt.get(),
            'prices': self._loans._assets.get_asset_prices(),
            'replay_index': len(self._loans._event_log),
            'mining_count': len(self.mining),
            'precompute_index': self.precompute_index.get(),
            'add_to_nonzero_count': len(self.add_to_nonzero),
            'remove_from_nonzero_count': len(self.remove_from_nonzero)
        }
        return snap

class SnapshotDB:

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase):
        self._db = db
        self._loans = loans
        self._indexes = ArrayDB('indexes', db, int)
        self._items = {}

    def __getitem__(self, _day: int) -> Snapshot:
        index = self.get_snapshot_id(_day)
        if _day < 0:
            _day = index
        # revert(f'current_day: {self._loans._current_day.get()}, index: {index}, _day: {_day}, [{self._indexes[0], self._indexes[-1] + 1}]')
        if index in range(self._indexes[0], self._indexes[-1] + 1):
            if _day not in self._items:
                return self._get_snapshot(_day, index)
        else:
            revert(f'No snapshot exists for {_day}.')
        return self._items[_day]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self) -> int:
        return self._indexes[-1] - self._indexes[0]

    def _get_snapshot(self, _day: int, _index: int) -> Snapshot:
        sub_db = self._db.get_sub_db(b'|'.join([SNAP_DB_PREFIX, str(_index).encode()]))
        self._items[_day] = Snapshot(sub_db, self._loans)
        return self._items[_day]

    def get_snapshot_id(self, _day: int) -> int:
        """
        Binary serch to return the snapshot id to use for the given day.
        Returns -1 if there was not yet a snapshot on the requested day.

        :param _day: Day number of the desired snapshot ID.
        :type _day: int

        :return: Index to the snapshot database.
        :rtype: int
        """
        if _day < 0:
            index = _day + len(self._indexes)
            if index < 0:
                revert(f'Snapshot index {_day} out of range.')
            return self._indexes[index]
        low = 0
        high = len(self._indexes)

        while low < high:
            mid = (low + high) // 2
            if self._indexes[mid] > _day:
                high = mid
            else:
                low = mid + 1

        if self._indexes[0] == _day:
            return _day
        elif low == 0:
            return -1
        elif low == len(self._indexes) and low > 1:
            return self._indexes[-2] # The last element in _indexes does not give a
        else: # completed snapshot and must be referred to explicitly with _day = -1.
            return self._indexes[low - 1]

    def start_new_snapshot(self) -> None:
        _day: int = self._loans._current_day.get()
        if len(self._indexes) == 0 or _day > self._indexes[-1]: # Ensures that the
            self._indexes.put(_day) # sequence in _indexes is monotonically increasing.
            snapshot = self._get_snapshot(_day, _day)
            snapshot.snap_day.set(_day)
        else:
            revert(f'New snapshot called for a day less than the previous snapshot.')
