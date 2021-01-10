from iconservice import *
from ..scorelib.id_factory import IdFactory
from ..utils.consts import *
from .assets import AssetsDB
from .replay_log import ReplayLogDB, ReplayEvent

U_SECONDS_DAY = 86400000000  # Microseconds in a day.

TAG = 'BalancedPositions'

class Position(object):

    def __init__(self, db: IconScoreDatabase, main_db: IconScoreDatabase, loans: IconScoreBase) -> None:
        self.asset_db = AssetsDB(main_db, loans)
        self._loans = loans
        self.id = VarDB('id', db, int)
        self.created = VarDB('created', db, int)
        self.updated = VarDB('updated', db, int)
        self.address = VarDB('address', db, Address)
        self.assets = DictDB('assets', db, int, depth=2)
        self.replay_index = VarDB('replay_index', db, int)
        self.ratio = VarDB('ratio', db, int)
        self.standing = VarDB('standing', db, int)
        self.frozen = VarDB('frozen', main_db, bool)

    def __getitem__(self, _symbol: str) -> int:
        if _symbol in self.asset_db.slist:
            return self.assets[self.get_day_index()][_symbol]
        else:
            revert(f'{_symbol} is not a supported asset on Balanced.')

    def __setitem__(self, key: str, value: int):
        self.assets[self.get_day_index()][key] = value
        if not self.frozen.get():
            self.assets[(self.get_day_index() + 1) % 2][key] = value

    def get_day_index(self) -> int:
        return (self._loans.now() // U_SECONDS_DAY) % 2

    def get_standing(self) -> int:
        return self.standing.get()

    def collateral_value(self) -> int:
        """
        Returns the value of the collateral in loop.

        :return: Value of position collateral in loop.
        :rtype: int
        """
        return self['sICX'] * self.asset_db['sICX'].price_in_loop() // EXA

    def total_debt(self) -> int:
        """
        Returns the total value of all outstanding debt in loop.

        :return: Value of all outstanding debt in loop.
        :rtype: int
        """
        asset_value = 0
        for symbol in self.asset_db.slist:
            if not self.asset_db[symbol].is_collateral.get() and symbol in self.assets:
                amount = self.assets[self.get_day_index()][symbol]
                if amount > 0:
                    asset_value += self.asset_db[symbol].price_in_loop() * amount // EXA
        return asset_value

    def apply_event(self, _event: ReplayEvent) -> None:
        """
        Updates the position given one redemption event.

        :param _event: Token symbol.
        :type _event: :class:`loans.replay_log.ReplayEvent`
        """
        symbol = _event.symbol.get()
        remaining_supply = _event.remaining_supply.get()
        remaining_value = _event.remaining_value.get()
        returned_sicx_remaining = _event.returned_sicx_remaining.get()
        pos_value = self[symbol]
        redeemed_from_this_pos = remaining_value * pos_value // remaining_supply
        sicx_share = returned_sicx_remaining * pos_value // remaining_supply
        _event.remaining_supply.set(remaining_supply - pos_value)
        _event.remaining_value.set(remaining_value - redeemed_from_this_pos)
        _event.returned_sicx_remaining.set(returned_sicx_remaining - sicx_share)
        self["sICX"] -= sicx_share
        self[symbol] = pos_value - redeemed_from_this_pos
        index = _event.index.get()
        self.replay_index.set(index)
        if len(self._loans._event_log) != index:
            self.standing.set(Standing.UNDETERMINED)
            return
        self.update_standing()

    def update_standing(self) -> None:
        ratio: int = self.total_debt() * EXA // self.collateral_value()
        self.updated.set(self._loans.now())
        self.ratio.set(ratio)
        if ratio > DEFAULT_MINING_RATIO * EXA // 100:
            self.standing.set(Standing.MINING)
        elif ratio > DEFAULT_LOCKING_RATIO * EXA // 100:
            self.standing.set(Standing.NOT_MINING)
        elif ratio > DEFAULT_LIQUIDATION_RATIO * EXA // 100:
            self.standing.set(Standing.LOCKED)
        else:
            self.standing.set(Standing.LIQUIDATE)

    def to_dict(self) -> dict:
        """
        Return object data as a dict.

        :return: dict of the object data
        :rtype dict
        """
        assets = {}
        for asset in self.asset_db.slist:
            if asset in self.assets:
                amount = self.assets[self.get_day_index()][asset]
                assets[asset] = amount

        position = {
            'created': self.created.get(),
            'address': str(self.address.get()),
            'assets': assets
        }

        if self.updated.get():
            position['updated'] = self.updated.get()

        return position


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
        self.nonzero = ArrayDB(self.NONZERO + self.POSITIONS, db, value_type=int)
        self.frozen = VarDB(self.FROZEN, db, bool)

    def __getitem__(self, _owner: Union[Address, int]) -> Position:
        if type(_owner) == Address:
            id = self.addressID[_owner]
        else:
            id = _owner
        if id not in self._items:
            if id > self._id_factory.get_last_uid() or id < 1:
                revert(f'That key does not exist.')
            sub_db = self._db.get_sub_db(b'|'.join([POSITION_DB_PREFIX, str(id).encode()]))
            self._items[id] = Position(sub_db, self._db, self._loans)

        return self._items[id]

    def __setitem__(self, key, value):
        revert('illegal access')

    def __len__(self):
        return self._id_factory.get_last_uid()

    def list_pos(self, _owner: Union[Address, int]) -> dict:
        if type(_owner) == Address:
            id = self.addressID[_owner]
        if id == 0:
            return "That address has no outstanding loans or deposited collateral."
        return self.__getitem__(id).to_dict()

    def add_nonzero(self, _owner: Union[Address, int]) -> None:
        if type(_owner) == Address:
            id = self.addressID[_owner]
        if id > self._id_factory.get_last_uid() or id < 1:
            revert(f'That key does not exist yet. (add_nonzero)')
        self.nonzero.put(id)

    def remove_nonzero(self, _owner: Union[Address, int]) -> None:
        if type(_owner) == Address:
            id = self.addressID[_owner]
        if id > self._id_factory.get_last_uid() or id < 1:
            revert(f'That key does not exist yet. (remove_nonzero)')
        top = self.nonzero.pop()
        if top != id:
            for i in range(len(self.nonzero)):
                if self.nonzero[i] == _owner:
                    self.nonzero[i] = top
                    return

    def get_pos(self, _owner: Union[Address, int]) -> Position:
        if type(_owner) == Address:
            id = self.addressID[_owner]
        else:
            id = _owner
        if id == 0:
            return self.new_pos(_owner)
        return self.__getitem__(id)

    def new_pos(self, _address: Address) -> Position:
        if self.addressID[_address] != 0:
            revert(f'A position already exists for that address.')
        id = self._id_factory.get_uid()
        self.addressID[_address] = id
        _new_pos = self.__getitem__(id)
        _new_pos.created.set(self._loans.now())
        _new_pos.address.set(_address)
        _new_pos.replay_index.set(len(self._event_log))
        _new_pos.assets[0]['sICX'] = 0
        _new_pos.assets[1]['sICX'] = 0
        _new_pos.id.set(id)
        return _new_pos
