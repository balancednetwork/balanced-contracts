# Copyright 2021 Balanced DAO
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .data_objects import *
from .utils.checks import *

TAG = 'Governance'


class Governance(IconScoreBase):
    """
    The Governance SCORE will have control of all parameters in BalancedDAO.
    All other SCOREs and external queries will be able to get SCORE addresses
    and parameter values here.
    """

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self.addresses = Addresses(db, self)
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
        return "Balanced Governance"

    @external
    @only_owner
    def configureBalanced(self) -> None:
        """
        Set parameters after deployment and before launch.
        Add Assets to Loans.
        """
        loans = self.create_interface_score(self.addresses._loans.get(), LoansInterface)
        rewards = self.create_interface_score(self.addresses._rewards.get(), RewardsInterface)
        self.addresses.setAdmins()
        self.addresses.setContractAddresses()
        addresses: dict = self.addresses.getAddresses()
        for asset in ASSETS:
            loans.addAsset(addresses[asset['address']],
                           asset['active'],
                           asset['collateral'])

    @external
    @only_owner
    def launchBalanced(self) -> None:
        if self._launched.get():
            return
        self._launched.set(True)
        loans = self.create_interface_score(self.addresses._loans.get(), LoansInterface)
        dex = self.create_interface_score(self.addresses._dex.get(), DexInterface)
        rewards = self.create_interface_score(self.addresses._rewards.get(), RewardsInterface)
        offset = DAY_ZERO + self._launch_day.get()
        day = (self.now() - DAY_START) // U_SECONDS_DAY - offset
        self._set_launch_day(day)
        self._set_launch_time(self.now())
        # Minimum day value is 1 since 0 is the default value for uninitialized storage.
        time_delta = DAY_START + U_SECONDS_DAY * (DAY_ZERO + self._launch_day.get() - 1)
        loans.setTimeOffset(time_delta)
        dex.setTimeOffset(time_delta)
        rewards.setTimeOffset(time_delta)
        addresses: dict = self.addresses.getAddresses()
        for source in DATA_SOURCES:
            rewards.addNewDataSource(source['name'], addresses[source['address']])
        rewards.updateBalTokenDistPercentage(RECIPIENTS)
        self.balanceToggleStakingEnabled()
        loans.turnLoansOn()
        dex.turnDexOn()

    @external
    @only_owner
    @payable
    def createBnusdMarket(self) -> None:
        value = self.msg.value
        if value == 0:
            revert(f'ICX sent must be greater than zero.')
        dex_address = self.addresses['dex']
        sICX_address = self.addresses['sicx']
        bnUSD_address = self.addresses['bnUSD']
        staking = self.create_interface_score(self.addresses['staking'], StakingInterface)
        rewards = self.create_interface_score(self.addresses['rewards'], RewardsInterface)
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        bnUSD = self.create_interface_score(bnUSD_address, AssetInterface)
        sICX = self.create_interface_score(sICX_address, AssetInterface)
        dex = self.create_interface_score(dex_address, DexInterface)
        price = bnUSD.priceInLoop()
        amount = UNITS_PER_TOKEN * value // (price * 7)
        staking.icx(value // 7).stakeICX()
        loans.icx(self.icx.get_balance(self.address)).depositAndBorrow('bnUSD', amount)
        bnUSD_value = bnUSD.balanceOf(self.address)
        sICX_value = sICX.balanceOf(self.address)
        bnUSD.transfer(dex_address, bnUSD_value, json_dumps({"method": "_deposit"}).encode())
        sICX.transfer(dex_address, sICX_value, json_dumps({"method": "_deposit"}).encode())
        dex.add(sICX_address, bnUSD_address, sICX_value, bnUSD_value)
        name = 'sICX/bnUSD'
        pid = dex.getPoolId(sICX_address, bnUSD_address)
        dex.setMarketName(pid, name)
        rewards.addNewDataSource(name, dex_address)
        recipients = [{'recipient_name': 'Loans', 'dist_percent': 25 * 10 ** 16},
                      {'recipient_name': 'sICX/ICX', 'dist_percent': 10 * 10 ** 16},
                      {'recipient_name': 'Worker Tokens', 'dist_percent': 20 * 10 ** 16},
                      {'recipient_name': 'Reserve Fund', 'dist_percent': 5 * 10 ** 16},
                      {'recipient_name': 'DAOfund', 'dist_percent': 225 * 10 ** 15},
                      {'recipient_name': 'sICX/bnUSD', 'dist_percent': 175 * 10 ** 15}]
        rewards.updateBalTokenDistPercentage(recipients)

    @external
    @only_owner
    def createBalnMarket(self, _bnUSD_amount: int, _baln_amount: int) -> None:
        dex_address = self.addresses['dex']
        bnUSD_address = self.addresses['bnUSD']
        baln_address = self.addresses['baln']
        rewards = self.create_interface_score(self.addresses['rewards'], RewardsInterface)
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        baln = self.create_interface_score(baln_address, BalancedInterface)
        bnUSD = self.create_interface_score(bnUSD_address, AssetInterface)
        dex = self.create_interface_score(dex_address, DexInterface)
        rewards.claimRewards()
        loans.depositAndBorrow('bnUSD', _bnUSD_amount)
        bnUSD.transfer(dex_address, _bnUSD_amount, json_dumps({"method": "_deposit"}).encode())
        baln.transfer(dex_address, _baln_amount, json_dumps({"method": "_deposit"}).encode())
        dex.add(baln_address, bnUSD_address, _baln_amount, _bnUSD_amount)
        name = 'BALN/bnUSD'
        pid = dex.getPoolId(baln_address, bnUSD_address)
        dex.setMarketName(pid, name)
        rewards.addNewDataSource(name, dex_address)
        recipients = [{'recipient_name': 'Loans', 'dist_percent': 25 * 10 ** 16},
                      {'recipient_name': 'sICX/ICX', 'dist_percent': 10 * 10 ** 16},
                      {'recipient_name': 'Worker Tokens', 'dist_percent': 20 * 10 ** 16},
                      {'recipient_name': 'Reserve Fund', 'dist_percent': 5 * 10 ** 16},
                      {'recipient_name': 'DAOfund', 'dist_percent': 5 * 10 ** 16},
                      {'recipient_name': 'sICX/bnUSD', 'dist_percent': 175 * 10 ** 15},
                      {'recipient_name': 'BALN/bnUSD', 'dist_percent': 175 * 10 ** 15}]
        rewards.updateBalTokenDistPercentage(recipients)

    @external
    @only_owner
    def setAddresses(self, _addresses: BalancedAddresses) -> None:
        self.addresses.setAddresses(_addresses)

    @external(readonly=True)
    def getAddresses(self) -> dict:
        return self.addresses.getAddresses()

    @external
    @only_owner
    def setAdmins(self) -> None:
        self.addresses.setAdmins()

    @external
    @only_owner
    def setContractAddresses(self) -> None:
        self.addresses.setContractAddresses()

    @external
    @only_owner
    def toggleBalancedOn(self) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
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

    @external
    @only_owner
    def addAsset(self, _token_address: Address,
                 _active: bool = True,
                 _collateral: bool = False) -> None:
        """
        Adds a token to the assets dictionary on the Loans contract.
        """
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.addAsset(_token_address, _active, _collateral)
        asset = self.create_interface_score(_token_address, AssetInterface)
        asset.setAdmin(self.addresses['loans'])

    @external
    @only_owner
    def toggleAssetActive(self, _symbol: str) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.toggleAssetActive(_symbol)

    @external
    @only_owner
    def addNewDataSource(self, _data_source_name: str, _contract_address: Address) -> None:
        """
        Add a new data source to receive BALN tokens. Starts with a default of
        zero percentage of the distribution.
        """
        rewards = self.create_interface_score(self.addresses['rewards'], RewardsInterface)
        rewards.addNewDataSource(_data_source_name, _contract_address)

    @external
    @only_owner
    def updateBalTokenDistPercentage(self, _recipient_list: List[DistPercentDict]) -> None:
        """
        Assign percentages for distribution to the data sources. Must sum to 100%.
        """
        rewards = self.create_interface_score(self.addresses['rewards'], RewardsInterface)
        rewards.updateBalTokenDistPercentage(_recipient_list)

    @external
    @only_owner
    def setDay(self, _day: int) -> None:
        rewards = self.create_interface_score(self.addresses['rewards'], RewardsInterface)
        rewards.setDay(_day)

    @external
    @only_owner
    def dexPermit(self, _id: int, _permission: bool):
        dex = self.create_interface_score(self.addresses['dex'], DexInterface)
        dex.permit(_id, _permission)

    @external
    @only_owner
    def dexAddQuoteCoin(self, _address: Address) -> None:
        dex = self.create_interface_score(self.addresses['dex'], DexInterface)
        dex.addQuoteCoin(_address)

    @external
    @only_owner
    def setMarketName(self, _id: int, _name: str) -> None:
        """
        :param _id: Pool ID to map to the name
        :param _name: Name to associate

        Links a pool ID to a name, so users can look up platform-defined
        markets more easily.
        """
        dex_address = self.addresses['dex']
        dex = self.create_interface_score(dex_address, DexInterface)
        dex.setMarketName(_id, _name)
        rewards = self.create_interface_score(self.addresses['rewards'], RewardsInterface)
        rewards.addNewDataSource(_name, dex_address)

    @external
    @only_owner
    def delegate(self, _delegations: List[PrepDelegations]):
        """
        Sets the delegation preference for the sICX held on the Loans contract.

        :param _delegations: List of dictionaries with two keys, Address and percent.
        :type _delegations: List[PrepDelegations]
        """
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.delegate(_delegations)

    @external
    @only_owner
    def balwAdminTransfer(self, _from: Address, _to: Address, _value: int, _data: bytes = None):
        if _data is None:
            _data = b'None'
        balw = self.create_interface_score(self.addresses['bwt'], BalancedWorkerTokenInterface)
        balw.adminTransfer(_from, _to, _value, _data)

    @external
    @only_owner
    def setbnUSD(self, _address: Address) -> None:
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        baln.setbnUSD(_address)

    @external
    @only_owner
    def setDividends(self, _score: Address) -> None:
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        baln.setDividends(_score)

    @external
    @only_owner
    def balanceSetDex(self, _address: Address) -> None:
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        baln.setDex(_address)

    @external
    @only_owner
    def balanceSetOracleName(self, _name: str) -> None:
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        baln.setOracleName(_name)

    @external
    @only_owner
    def balanceSetMinInterval(self, _interval: int) -> None:
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        baln.setMinInterval(_interval)

    @external
    @only_owner
    def balanceToggleStakingEnabled(self) -> None:
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        baln.toggleStakingEnabled()

    @external
    @only_owner
    def balanceSetMinimumStake(self, _amount: int) -> None:
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        baln.setMinimumStake(_amount)

    @external
    @only_owner
    def balanceSetUnstakingPeriod(self, _time: int) -> None:
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        baln.setUnstakingPeriod(_time)

    @external
    @only_owner
    def daoDisburse(self, _recipient: Address, _amounts: List[Disbursement]) -> bool:
        dao = self.create_interface_score(self.addresses['daofund'], DAOfundInterface)
        dao.disburse(_recipient, _amounts)

    @external
    @only_owner
    def setAssetOracle(self, _symbol: str, _address: Address) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        asset_addresses = loans.getAssetTokens()
        if _symbol not in asset_addresses:
            revert(f'{_symbol} is not a supported asset in Balanced.')
        token = asset_addresses[_symbol]
        asset = self.create_interface_score(Address.from_string(token), AssetInterface)
        asset.setOracle(_address)

    @external
    @only_owner
    def setAssetOracleName(self, _symbol: str, _name: str) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        asset_addresses = loans.getAssetTokens()
        if _symbol not in asset_addresses:
            revert(f'{_symbol} is not a supported asset in Balanced.')
        token = asset_addresses[_symbol]
        asset = self.create_interface_score(Address.from_string(token), AssetInterface)
        asset.setOracleName(_name)

    @external
    @only_owner
    def setAssetMinInterval(self, _symbol: str, _interval: int) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        asset_addresses = loans.getAssetTokens()
        if _symbol not in asset_addresses:
            revert(f'{_symbol} is not a supported asset in Balanced.')
        token = asset_addresses[_symbol]
        asset = self.create_interface_score(Address.from_string(token), AssetInterface)
        asset.setMinInterval(_interval)

    @external
    @only_owner
    def bnUSDSetOracle(self, _address: Address) -> None:
        bnUSD = self.create_interface_score(self.addresses['bnUSD'], AssetInterface)
        bnUSD.setOracle(_address)

    @external
    @only_owner
    def bnUSDSetOracleName(self, _name: str) -> None:
        bnUSD = self.create_interface_score(self.addresses['bnUSD'], AssetInterface)
        bnUSD.setOracleName(_name)

    @external
    @only_owner
    def bnUSDSetMinInterval(self, _interval: int) -> None:
        bnUSD = self.create_interface_score(self.addresses['bnUSD'], AssetInterface)
        bnUSD.setMinInterval(_interval)

    @external
    @only_owner
    def addUsersToActiveAddresses(self, _poolId: int, _addressList: List[Address]):
        dex = self.create_interface_score(self.addresses['dex'], DexInterface)
        dex.addLpAddresses(_poolId, _addressList)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used only to receive sICX for unstaking.
        :param _from: Token origination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        pass

    @payable
    def fallback(self):
        pass
