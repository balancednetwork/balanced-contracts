from iconservice import *

TAG = 'LoansSnapshots'

SNAP_DB_PREFIX = b'snaps'


class Snapshot(object):

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self._loans = loans
        # Total Debt elegible for mining rewards for each asset
        self.total_mining_debt = DictDB('total_mining_debt', db, int)
        # Oracle Price for each asset at snapshot time.
        self.prices = DictDB('prices', db, int)
        # Latest Replay Index at the time of each snapshot
        self.replay_index = VarDB('replay_index', db, int)
        # index to track progress through the single precompute pass for each snap.
        self._precompute_index = VarDB('precompute_index', db, int)
        # List of position ids in the mining state at snapshot time.
        self.mining = ArrayDB('mining', db, int)
        # List of position ids that move to non-zero collateral.
        self.add_to_nonzero = ArrayDB('nonzero', db, int)
        # List of position ids that move to a zero collateral status.
        self.remove_from_nonzero = ArrayDB('zero', db, int)

    def to_dict(self) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """
        total_debt = {}
        for symbol in self._loans.asset_db.slist:
            debt = self.total_mining_debt[symbol]
            if debt > 0:
                total_debt[symbol] = debt

        snap = {
            'total_mining_debt': total_debt,
            'prices': self._loans.asset_db.get_asset_prices(),
            'replay_index': self.replay_index.get(),
            'mining_count': len(self.mining)
        }

        if len(self._precompute_index) > 0:
            snap['precompute_index'] = self._precompute_index.get()
            snap['add_to_nonzero_count'] = len(self.add_to_nonzero)
            snap['remove_from_nonzero_count'] = len(self.remove_from_nonzero)

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
        if index in range(self._indexes[0], self._loans.getDay() + 1):
            if _day not in self._items:
                sub_db = self._db.get_sub_db(b'|'.join([SNAP_DB_PREFIX, str(index).encode()]))
                self._items[_day] = Snapshot(sub_db, self._loans)
        else:
            revert(f'No snapshot exists for {_day}.')
        return self._items[_day]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self) -> int:
        return self._indexes[-1] - self._indexes[0]

    def get_snapshot_id(self, _day: int) -> int:
        """
        Binary serch to return the snapshot id to use for the given day.
        Returns -1 if there was not yet a snapshot on the requested day.

        :param _day: Day number of the desired snapshot ID.
        :type _day: int

        :return: Index to the snapshot database.
        :rtype: int
        """
        if _day == -1:
            return self._indexes[-1]
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
        elif low == len(self._indexes):
            return self._indexes[-2]
        else:
            return self._indexes[low - 1]

    def new_snapshot(self, _day: int) -> Snapshot:
        self._indexes.put(_day)
        return self.__getitem__(_day)
