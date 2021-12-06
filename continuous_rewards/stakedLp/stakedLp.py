from .utils.checks import *
from .interfaces import *
from iconservice import *

MICROSECONDS = 10 ** 6
SICX_BNUSD_ID = 2


class StakedLp(IconScoreBase):
    _GOVERNANCE_ADDRESS = 'governance_address'
    _REWARDS_ADDRESS = 'rewards_address'
    _ADMIN_ADDRESS = 'admin_address'
    _DEX_ADDRESS = 'dex_address'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        # Business Logic
        self._supportedPools = DictDB('supportedPools', db, bool)
        self._poolStakeDetails = DictDB('poolStakeDetails', db, value_type=int, depth=3)
        self._totalStaked = DictDB('totalStaked', db, value_type=int)
        self._addressMap = DictDB('addressMap', db, value_type=Address)

        # Linked Contracts
        self._governance = VarDB(self._GOVERNANCE_ADDRESS, db, value_type=Address)
        self._dex = VarDB(self._DEX_ADDRESS, db, value_type=Address)
        self._rewards = VarDB(self._REWARDS_ADDRESS, db, value_type=Address)
        self._admin = VarDB(self._ADMIN_ADDRESS, db, value_type=Address)

    def on_install(self, _governance: Address) -> None:
        super().on_install()
        self._governance.set(_governance)

    def on_update(self) -> None:
        super().on_update()

    @staticmethod
    def _require(_condition: bool, _message: str):
        if not _condition:
            revert(f'{TAG}: {_message}')

    @external(readonly=True)
    def name(self) -> str:
        return f'Balanced {TAG}'
    
    # Contract getters and setters

    @external(readonly=True)
    def getDex(self) -> Address:
        """
        Gets the address of the DEX SCORE.
        """
        return self._dex.get()

    @only_governance
    @external
    def setDex(self, _dex: Address) -> None:
        """
        :param _dex: the new DEX address to set.
        """
        self._dex.set(_dex)

    @external(readonly=True)
    def getGovernance(self) -> Address:
        """
        Gets the address of the Governance SCORE.
        """
        return self._governance.get()

    @only_admin
    @external
    def setGovernance(self, _governance: Address) -> None:
        """
        :param _dex: the new DEX address to set.
        """
        self._governance.set(_dex)


    @external(readonly=True)
    def getAdmin(self) -> Address:
        """
        Gets the current admin address. This user can call using the
        `@only_admin` decorator.
        """
        return self._governance.get()

    @only_governance
    @external
    def setAdmin(self, _admin: Address) -> None:
        """
        :param _admin: The new admin address to set.
        Can make calls with the `@only_admin` decorator.
        Should be called before DEX use.
        """
        self._admin.set(_admin)

    @only_admin
    @external
    def setRewards(self, _address: Address) -> None:
        """
        :param _address: New contract address to set.
        Sets new Rewards contract address. Should be called before dex use.
        """
        if not _address.is_contract:
            revert(f"{TAG}: Address provided is an EOA address. A contract address is required.")
        self._rewards.set(_address)

    @external(readonly=True)
    def getRewards(self) -> Address:
        """
        Gets the address of the Rewards contract.
        """
        return self._rewards.get()

    @external(readonly=True)
    def balanceOf(self, _owner: Address, _id: int) -> int:
        return self._poolStakeDetails[_owner][_id][Status.STAKED]

    @external(readonly=True)
    def totalSupply(self, _id: int) -> int:
        return self._totalStaked[_id]

    @only_governance
    @external
    def addPool(self, _id: int) -> None:
        if not self._supportedPools[_id]:
            self._supportedPools[_id] = True

    @only_governance
    @external
    def removePool(self, _id: int) -> None:
        if self._supportedPools[_id]:
            self._supportedPools[_id] = False

    def _stake(self, _user: Address, _id: int, _value: int) -> None:
        # Validate inputs
        pool_id = self._supportedPools[_id]
        StakedLp._require(pool_id, f'pool with id:{_id} is not supported')
        StakedLp._require(_value > 0, f'Cannot stake less than zero ,value to stake {_value}')

        # Compute and store changes
        previous_balance = self._poolStakeDetails[_user][_id][Status.STAKED]
        previous_total = self._totalStaked[_id]
        balance = previous_balance + _value
        total = previous_total + _value
        self._poolStakeDetails[_user][_id][Status.STAKED] = balance
        self._totalStaked[_id] = total

        # Define Interfaces
        dex = self.create_interface_score(self._dex.get(), LiquidityPoolInterface)

        # Get Source Name
        name = dex.getPoolName(_id)

        rewards = self.create_interface_score(self._rewards.get(), RewardInterface)
        rewards.updateRewardsData(name, previous_total, _user, previous_balance)

    @external
    def unstake(self, _id: int, _value: int) -> None:
        StakedLp._require(_id in self._supportedPools, f'pool with id:{_id} is not supported')
        _user = self.msg.sender
        StakedLp._require(_value > 0, f'Cannot unstake less than zero'
                                      f'value to stake {_value}')

        previous_balance = self._poolStakeDetails[_user][_id][Status.STAKED]
        previous_total = self._totalStaked[_id]

        StakedLp._require(previous_balance >= _value, f'Cannot unstake,user dont have enough staked balance '
                                                        f'amount to unstake {_value} '
                                                        f'staked balance of user: {_user} is  {previous_balance}')
        balance = previous_balance - _value
        total = previous_total - _value
        self._poolStakeDetails[_user][_id][Status.STAKED] = balance
        self._totalStaked[_id] = total

        # Define Interfaces
        rewards = self.create_interface_score(self._rewards.get(), RewardInterface)
        dex = self.create_interface_score(self._dex.get(), LiquidityPoolInterface)

        # Get Source Name
        name = dex.getPoolName(_id)
        rewards.updateRewardsData(name, previous_total, _user, previous_balance)

        lpToken = self.create_interface_score(self._dex.get(), LiquidityPoolInterface)
        lpToken.transfer(_user, _value, _id)

    @only_dex
    @external
    def onIRC31Received(self, _operator: Address, _from: Address, _id: int, _value: int, _data: bytes):
        d = None
        try:
            d = json_loads(_data.decode("utf-8"))
        except Exception:
            revert(f'{TAG}: Invalid data: {_data}.')
        if set(d.keys()) != {"method"}:
            revert(f'{TAG}: Invalid parameters.')
        if d["method"] == "_stake":
            self._stake(_from, _id, _value)
        else:
            revert(f'{TAG}: No valid method called, data: {_data}')