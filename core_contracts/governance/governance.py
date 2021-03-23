from iconservice import *
from .utils.checks import *
from .utils.consts import *
from .interfaces import *
from .data_objects import *

TAG = 'Governance'


class DistPercentDict(TypedDict):
    recipient_name : str
    bal_token_dist_percent: int


class Governance(IconScoreBase):
    """
    The Governance SCORE will have control of all parameters in BalancedDAO.
    All other SCOREs and external queries will be able to get SCORE addresses
    and parameter values here.
    """

    _ADMIN = 'admin'
    _LAUNCH_DAY = 'launch_day'
    _LAUNCHED = 'launched'


    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self.addresses = Addresses(db, self)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._launch_day = VarDB('launch_day', db, int)
        self._launch_time = VarDB('launch_time', db, int)
        self._launched = VarDB('launched', db, bool)

    def on_install(self) -> None:
        super().on_install()
        self._launched.set(False)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Governance"

    @external
    @only_owner
    def launchBalanced(self) -> None:
        if not self._launched.get():
            self._launched.set(True)
            loans = self.create_interface_score(self.addresses._loans.get(), LoansInterface)
            dex = self.create_interface_score(self.addresses._dex.get(), DexInterface)
            rewards = self.create_interface_score(self.addresses._rewards.get(), RewardsInterface)
            self.addresses.setAdmins()
            self.addresses.setContractAddresses()
            self._set_launch_day(self.getDay())
            self._set_launch_time(self.now())
             # Minimum day value is 1 since 0 is the default value for uninitialized storage.
            time_delta = DAY_START + U_SECONDS_DAY * (DAY_ZERO + self._launch_day.get() - 1)
            loans.setTimeOffset(time_delta)
            dex.setTimeOffset(time_delta)
            rewards.setTimeOffset(time_delta)
            for asset in ASSETS:
                loans.addAsset(self.addresses.getAddresses()[asset['address']],
                               asset['active'], asset['collateral'])
            for source in DATA_SOURCES:
                rewards.addNewDataSource(source['name'],
                                         self.addresses.getAddresses()[source['address']])
            rewards.updateBalTokenDistPercentage(RECIPIENTS)
            loans.turnLoansOn()
            dex.turnDexOn()

    @external
    @only_owner
    def setAddresses(self, _addresses: BalancedAddresses) -> None:
        self.addresses.setAddresses(_addresses)

    @external(readonly=True)
    def getAddresses(self) -> dict:
        return self.addresses.getAddresses()

    @external
    @only_owner
    def setContractAddresses(self) -> None:
        self.addresses.setContractAddresses()

    @external
    @only_owner
    def toggleBalancedOn(self) -> None:
        loans = self.create_interface_score(self.addresses._loans.get(), LoansInterface)
        loans.toggleLoansOn()

    def _set_launch_day(self, _day: int) -> None:
        self._launch_day.set(_day)

    @external(readonly=True)
    def getLaunchDay(self) -> int:
        return self._launch_day.get()

    def _set_launch_time(self, _day: int) -> None:
        self._launch_time.set(_day)

    @external(readonly=True)
    def getLaunchTime(self) -> int:
        return self._launch_time.get()

    @external(readonly=True)
    def getDay(self) -> int:
        offset = DAY_ZERO + self._launch_day.get()
        return (self.now() - DAY_START) // U_SECONDS_DAY - offset

    @external
    @only_owner
    def addAsset(self, _token_address: Address,
                       _active: bool = True,
                       _collateral: bool = False) -> None:
        """
        Adds a token to the assets dictionary on the Loans contract.
        """
        loans = self.create_interface_score(self.addresses._loans.get(), LoansInterface)
        loans.addAsset(_token_address, _active, _collateral)

    @external
    @only_owner
    def toggleAssetActive(self, _symbol) -> None:
        loans = self.create_interface_score(self.addresses._loans.get(), LoansInterface)
        loans.toggleAssetActive(_symbol)

    @external
    @only_owner
    def addNewDataSource(self, _data_source_name: str, _contract_address: Address) -> None:
        """
        Add a new data source to receive BALN tokens. Starts with a default of
        zero percentage of the distribution.
        """
        rewards = self.create_interface_score(self.addresses._rewards.get(), RewardsInterface)
        rewards.addNewDataSource(_data_source_name, _contract_address)

    @external
    @only_owner
    def updateBalTokenDistPercentage(self, _recipient_list : List[DistPercentDict]) -> None:
        """
        Assign percentages for distribution to the data sources. Must sum to 100%.
        """
        rewards = self.create_interface_score(self.addresses._rewards.get(), RewardsInterface)
        rewards.updateBalTokenDistPercentage(_recipient_list)

    @external
    @only_owner
    def dexPermit(self, _pid: int, _permission: bool):
        dex = self.create_interface_score(self.addresses._dex.get(), DexInterface)
        dex.permit(_pid, _permission)

    @external
    @only_owner
    def setMarketName(self, _pid: int, _name: str) -> None:
        """
        :param _pid: Pool ID to map to the name
        :param _name: Name to associate
        Links a pool ID to a name, so users can look up platform-defined
        markets more easily.
        """
        dex_address = self.addresses._dex.get()
        dex = self.create_interface_score(dex_address, DexInterface)
        dex.setMarketName(_pid, _name)
        rewards = self.create_interface_score(self.addresses._rewards.get(), RewardsInterface)
        rewards.addNewDataSource(_name, dex_address)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used only to receive sICX for unstaking.
        :param _from: Token orgination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        revert("The Balanced Governance SCORE does not accept tokens.")

    @payable
    def fallback(self):
        pass

#-------------------------------------------------------------------------------
# EVENT LOGS
#-------------------------------------------------------------------------------
