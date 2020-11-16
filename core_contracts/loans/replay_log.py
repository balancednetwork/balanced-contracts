from iconservice import *
from .scorelib.id_factory import IdFactory

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
        self.symbol = VarDB('symbol', db, str)
        self.value = VarDB('value', db, int)
        self.sicx_rate = VarDB('sicx_rate', db, int)
        self.asset_supply = VarDB('asset_supply', db, int)

    def to_json(self) -> str:
        """
        Convert to json string
        :return: the json string
        """

        event = {
            'index': self.index.get(),
            'created': self.created.get(),
            'symbol': self.symbol.get(),
            'value': self.value.get(),
            'sicx_rate': self.sicx_rate.get(),
            'asset_supply': self.asset_supply.get()
        }

        return json_dumps(event)


class ReplayLogDB:

    REPLAY = 'replay'
    IDFACTORY = '_idfactory'
    EVENTS = '_events'

    def __init__(self, db: IconScoreDatabase):
        self._db = db
        self._items = {}
        self._id_factory = IdFactory(REPLAY + IDFACTORY, db)
        self._events = ArrayDB(REPLAY + EVENTS, db, value_type=int)

    def __getitem__(self, id: int) -> ReplayEvent:
        if id not in self._items:
            if id > self._id_factory.get_last_uid():
                revert(f'That key does not exist yet. Add new items with the new_event method.')
            sub_db = self._db.get_sub_db(b'|'.join([REPLAY_DB_PREFIX, id.encode()]))
            self._items[id] = ReplayEvent(sub_db)
        return self._items[id]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self):
        return len(self._events)

    def new_event(self) -> ReplayEvent:
        id = self._id_factory.get_uid()
        self._events.put(id)
        _new_event = __get_item__(id)
        _new_event.index.set(id)
        _new_event.created.set(self.now())
        return _new_event
