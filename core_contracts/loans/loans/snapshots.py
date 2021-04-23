from iconservice import *
from ..scorelib.linked_list import *

TAG = 'BalancedLoansSnapshots'
SNAP_DB_PREFIX = b'snaps'


class Snapshot(object):

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self._db = db
        self._loans = loans
        self.snap_day = VarDB('snap_day', db, int)
        # Time of snapshot
        self.snap_time = VarDB('snap_time', db, int)
        # Total Debt elegible for mining rewards for each asset. Will be calculated
        # after the snap is complete, in the precompute method.
        self.total_mining_debt = VarDB('total_mining_debt', db, int)
        # Oracle Price for each asset at snapshot time.
        self.prices = DictDB('prices', db, int)
        # index to track progress through the single precompute pass for each snap.
        # Starts at zero and counts up to the last index in the mining ArrayDB.
        self.precompute_index = VarDB('precompute_index', db, int)
        # State will contain the most recent calculated state for each position
        # id with fields for total_debt, ratio, and standing.
        self.pos_state = DictDB('pos_state', db, int, depth=2)
        # List of position ids in the mining state at snapshot time. This list
        # will be compiled in the precompute method as each position in the
        # nonzero ArrayDB is brought up to date.
        self.mining = ArrayDB('mining', db, int)

    def get_add_nonzero(self) -> LinkedListDB:
        return LinkedListDB('add_to_nonzero', self._db, value_type=int)

    def get_remove_nonzero(self) -> LinkedListDB:
        return LinkedListDB('remove_from_nonzero', self._db, value_type=int)

    def to_dict(self) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """
        prices = {}
        assets = self._loans._assets
        for symbol in assets.slist:
            if assets[symbol].added.get() < self.snap_time.get() and assets[symbol].is_active():
                prices[symbol] = self.prices[symbol]
        snap = {
            'snap_day': self.snap_day.get(),
            'snap_time': self.snap_time.get(),
            'total_mining_debt': self.total_mining_debt.get(),
            'prices': prices,
            'mining_count': len(self.mining),
            'precompute_index': self.precompute_index.get(),
            'add_to_nonzero_count': len(self.get_add_nonzero()),
            'remove_from_nonzero_count': len(self.get_remove_nonzero())
        }
        return snap

class SnapshotDB:

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase):
        self._db = db
        self._loans = loans
        self._indexes = ArrayDB('indexes', db, int)
        self._items = {}

    def __getitem__(self, _day: int) -> Snapshot:
        input_day = _day
        index = self.get_snapshot_id(_day)
        if _day < 0:
            _day = index
        if index in range(self._indexes[0], self._indexes[-1] + 1):
            if _day not in self._items:
                return self._get_snapshot(_day, index)
            return self._items[_day]
        else:
            revert(f'{TAG}: No snapshot exists for {_day}, input_day: {input_day}.')

    def __setitem__(self, key, value):
        revert(f'{TAG}: Illegal access.')

    def __len__(self) -> int:
        return self._indexes[-1] - self._indexes[0]

    def _get_snapshot(self, _day: int, _index: int) -> Snapshot:
        sub_db = self._db.get_sub_db(b'|'.join([SNAP_DB_PREFIX, str(_index).encode()]))
        self._items[_day] = Snapshot(sub_db, self._loans)
        return self._items[_day]

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
            index = _day + len(self._indexes)
            if index < 0:
                revert(f'{TAG}: Snapshot index {_day} out of range.')
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
        else:
            return self._indexes[low - 1]

    def start_new_snapshot(self) -> None:
        _day: int = self._loans.getDay()
        if len(self._indexes) == 0 or _day > self._indexes[-1]:  # Ensures that the sequence in
            self._indexes.put(_day)                              # _indexes is monotonically increasing.
            snapshot = self._get_snapshot(_day, _day)
            snapshot.snap_day.set(_day)
        else:
            revert(f'{TAG}: New snapshot called for a day less than the previous snapshot.')
