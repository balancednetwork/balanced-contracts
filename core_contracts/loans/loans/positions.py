from iconservice import *
from ..scorelib.id_factory import IdFactory
from ..utils.consts import *
from .assets import AssetsDB
from .replay_log import ReplayLogDB

TAG = 'BalancedPositions'

class Position(object):

    FROZEN = 'frozen'

    def __init__(self, db: IconScoreDatabase, main_db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self.asset_db = AssetsDB(main_db, loans)
        self._loans = loans
        self.id = VarDB('id', db, int)
        self.created = VarDB('created', db, int)
        self.updated = VarDB('updated', db, int)
        self.address = VarDB('address', db, Address)
        self.assets = DictDB('assets', db, int, depth=2)
        self.replay_index = VarDB('active', db, int)
        self.frozen = VarDB(self.FROZEN, main_db, bool)

    def __getitem__(self, _symbol: str) -> int:
        if _symbol in self.asset_db.slist:
            return self.assets[_symbol][get_day_index(self._loans)]
        else:
            revert(f'{_symbol} is not a supported asset on Balanced.')

    def __setitem__(self, key: str, value: int):
        self.assets[key][get_day_index(self._loans)] = value
        if not self.frozen.get():
            self.assets[key][(get_day_index(self._loans) + 1) % 2] = value

    def total_debt(self) -> int:
        """
        Returns the total value of all outstanding debt in loop.

        :return: Value of all outstanding debt in loop.
        :rtype: int
        """
        asset_value = 0
        for symbol in self.asset_db.slist:
            if symbol != 'sICX' and symbol in self.assets:
                amount = self.assets[symbol][get_day_index(self._loans)]
                if amount > 0:
                    asset_value += self.asset_db[symbol].price_in_icx() * amount // EXA
        return asset_value

    def to_json(self) -> str:
        """
        Convert to json string
        :return: the json string
        """
        assets = {}
        for asset in self.asset_db.slist:
            if asset in self.assets:
                amount = self.assets[asset][get_day_index(self._loans)]
                assets[asset] = amount

        position = {
            'created': self.created.get(),
            'address': str(self.address.get()),
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
    FROZEN = 'frozen'

    def __init__(self, db: IconScoreDatabase, loans: IconScoreBase):
        self._db = db
        self._loans = loans
        self._items = {}
        self._event_log = ReplayLogDB(db)
        self._id_factory = IdFactory(self.POSITIONS + self.IDFACTORY, db)
        self.addressID = DictDB(self.POSITIONS + self.ADDRESSID, db, value_type=int)
        self.mining = ArrayDB(self.MINING + self.POSITIONS, db, value_type=bool)
        self.nonzero = ArrayDB(self.NONZERO + self.POSITIONS, db, value_type=bool)
        self.frozen = VarDB(self.FROZEN, db, bool)

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

    def list_pos(self, _owner: Address) -> str:
        index = self.addressID[_owner]
        if index == 0:
            return "That address has no outstanding loans or deposited collateral."
        return self.__getitem__(index).to_json()

    def get_pos(self, _owner: Address) -> Position:
        index = self.addressID[_owner]
        if index == 0:
            return self.new_pos(_owner)
        return self.__getitem__(index)

    def new_pos(self, _address: Address) -> Position:
        if self.addressID[_address] != 0:
            revert(f'A position already exists for that address.')
        id = self._id_factory.get_uid()
        self.addressID[_address] = id
        _new_pos = self.__getitem__(id)
        _new_pos.created.set(self._loans.now())
        _new_pos.address.set(_address)
        _new_pos.replay_index.set(len(self._event_log))
        _new_pos.id.set(id)
        return _new_pos
