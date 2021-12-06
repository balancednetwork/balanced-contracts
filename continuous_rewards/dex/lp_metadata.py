from iconservice import *
from .scorelib.enumerable_set import EnumerableSetDB


class LPMetadataDB:

    def __init__(self, db: IconScoreDatabase):
        self._metadata = {}
        self._db = db

    def __getitem__(self, _id: int) -> EnumerableSetDB:
        if _id not in self._metadata:
            self._metadata[_id] = EnumerableSetDB(f"lp{_id}", self._db, value_type=Address)

        return self._metadata[_id]
