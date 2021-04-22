from iconservice import *
from .scorelib.set import *


class LPMetadataDB:

    def __init__(self, db: IconScoreDatabase):
        self._metadata = {}
        self._db = db

    def __getitem__(self, _id: int) -> SetDB:
        if _id not in self._metadata:
            self._metadata[_id] = SetDB(f"lp{_id}", self._db, value_type=Address, order=True)

        return self._metadata[_id]