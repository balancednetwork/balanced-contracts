from iconservice import *
from .scorelib.id_factory import IdFactory
from .utils.consts import *
from .assets import *
from .events import *

TAG = 'BalancedPositions'

class Position(object):

    @property
    def db(self) -> 'IconScoreDatabase':
        return self.__db

    def __init__(self, db: IconScoreDatabase, main_db: IconScoreDatabase) -> None:
        self.__db = db
        self._main_db = main_db
        self.asset_db = Assets(main_db)
        self.id = VarDB('id', db, int)
        self.created = VarDB('created', db, int)
        self.updated = VarDB('updated', db, int)
        self.address = VarDB('address', db, Address)
        self.assets = DictDB('assets', db, int, depth=2)
        self.replay_index = VarDB('active', db, int)
        self._frozen = VarDB('frozen', db, bool)
        self._frozen.set(False)

    def __getitem__(self, symbol: str) -> int:
        if symbol in self.asset_db.alist:
            return self.assets[symbol][self._get_day_index()]
        else:
            revert(f'{symbol} is not a supported asset on Balanced.')

    def __setitem__(self, key, value):
        self.assets[key][self._get_day_index()] = value
        if not self._frozen.get():
            self.assets[key][(self._get_day_index() + 1) % 2] = value

    def total_debt(self) -> int:
        """
        Returns the total value of all outstanding debt in loop.

        :return: Value of all outstanding debt in loop.
        :rtype: int
        """
        asset_value = 0
        for symbol in self._assets:
            if symbol != 'sICX':
                amount = self._assets[symbol][self._get_day_index()]
                if amount > 0:
                    asset_value += self.asset_db[symbol].price_in_icx() * amount // EXA
        return asset_value

    def to_json(self) -> str:
        """
        Convert to json string
        :return: the json string
        """
        assets = {}
        for asset in self._assets:
            amount = self._assets[asset][self._get_day_index()]
            assets[asset] = amount

        position = {
            'created': self.created.get(),
            'address': self.address.get(),
            'assets': assets
        }

        if self.updated.get():
            position['updated'] = self.updated.get()

        return json_dumps(position)


class PositionsDB:

    POSITIONS = 'positions'
    IDFACTORY = '_idfactory'
    ADDRESSID = '_addressid'
    MINING = 'mining_'
    NONZERO = 'nonzero_'

    def __init__(self, db: IconScoreDatabase):
        self._db = db
        self._items = {}
        self._event_log = ReplayLogDB(db)
        self._id_factory = IdFactory(POSITIONS + IDFACTORY, db)
        self.addressID = DictDB(POSITIONS + ADDRESSID, db, value_type=int)
        self.mining = ArrayDB(MINING + POSITIONS, db, value_type=bool)
        self.nonzero = ArrayDB(NONZERO + POSITIONS, db, value_type=bool)

    def __getitem__(self, id: int) -> Position:
        if id not in self._items:
            if id > self._id_factory.get_last_uid():
                revert(f'That key does not exist yet.')
            sub_db = self._db.get_sub_db(b'|'.join([POSITION_DB_PREFIX, id.encode()]))
            self._items[id] = Position(sub_db)

        return self._items[id]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self):
        return self._id_factory.get_last_uid()

    def new_pos(self) -> Position:
        if self.addressID[self.tx.origin] != 0:
            revert(f'A position already exists for that address.')
        id = self._id_factory.get_uid()
        self.addressID[self.tx.origin] = id
        _new_pos = self.__getitem__(id)
        _new_pos.created.set(self.now())
        _new_pos.address.set(address)
        _new_pos.replay_index.set(len(self._event_log))
        _new_pos.id.set(id)
        return _new_pos
