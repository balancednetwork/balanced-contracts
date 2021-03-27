from iconservice import *
from ..scorelib.id_factory import IdFactory
from .snapshots import SnapshotDB, Snapshot

TAG = 'BalancedReplayLog'

REPLAY_DB_PREFIX = b'replay'

class ReplayEvent(object):

    @property
    def db(self) -> 'IconScoreDatabase':
        return self.__db

    def __init__(self, db: IconScoreDatabase) -> None:
        self.__db = db
        self.index = VarDB('index', db, int)
        self.created = VarDB('created', db, int)
        self.snapshot = VarDB('snapshot', db, int)
        self.symbol = VarDB('symbol', db, str)
        self.value = VarDB('value', db, int)
        self.remaining_value = VarDB('remaining_value', db, int)
        self.sicx_rate = VarDB('sicx_rate', db, int)
        self.asset_price = VarDB('asset_price', db, int)
        self.sicx_returned = VarDB('sicx_returned', db, int)
        self.returned_sicx_remaining = VarDB('returned_sicx_remaining', db, int)
        self.asset_supply = VarDB('asset_supply', db, int)
        self.remaining_supply = VarDB('remaining_supply', db, int)

    def to_dict(self) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """

        event = {
            'index': self.index.get(),
            'created': self.created.get(),
            'snapshot': self.snapshot.get(),
            'symbol': self.symbol.get(),
            'value': self.value.get(),
            'remaining_value': self.remaining_value.get(),
            'sicx_rate': self.sicx_rate.get(),
            'asset_price': self.asset_price.get(),
            'sicx_returned': self.sicx_returned.get(),
            'returned_sicx_remaining': self.returned_sicx_remaining.get(),
            'asset_supply': self.asset_supply.get(),
            'remaining_supply':self.remaining_supply.get()
        }

        return event


class ReplayLogDB:

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase):
        self._db = db
        self._loans = loans
        self._items = {}
        self._snapshot_db = SnapshotDB(db, loans)
        self._id_factory = IdFactory('id_factory', db)
        self._events = ArrayDB('events', db, value_type=int)

    def __getitem__(self, id: int) -> ReplayEvent:
        if id < 0:
            id = self._id_factory.get_last_uid() + id + 1
        if id < 0:
            revert(f'That is not a valid key.')
        if id not in self._items:
            if id > self._id_factory.get_last_uid():
                revert(f'That key does not exist yet. Add new items with the new_event method.')
            sub_db = self._db.get_sub_db(b'|'.join([REPLAY_DB_PREFIX, str(id).encode()]))
            self._items[id] = ReplayEvent(sub_db)
        return self._items[id]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self):
        return len(self._events) # length is the last id since ids start with number 1.

    def new_event(self, **kwargs) -> ReplayEvent:
        id = self._id_factory.get_uid()
        self._events.put(id)
        self._snapshot_db[-1].replay_index.set(id)
        _new_event = self.__getitem__(id)
        _new_event.index.set(id)
        _new_event.created.set(self._loans.now())
        _new_event.snapshot.set(kwargs.get('snapshot'))
        _new_event.symbol.set(kwargs.get('symbol'))
        _new_event.value.set(kwargs.get('value'))
        _new_event.remaining_value.set(kwargs.get('value'))
        _new_event.sicx_rate.set(kwargs.get('sicx_rate'))
        _new_event.asset_price.set(kwargs.get('asset_price'))
        _new_event.sicx_returned.set(kwargs.get('sicx_returned'))
        _new_event.returned_sicx_remaining.set(kwargs.get('sicx_returned'))
        _new_event.asset_supply.set(kwargs.get('asset_supply'))
        _new_event.remaining_supply.set(kwargs.get('asset_supply'))
        return _new_event
