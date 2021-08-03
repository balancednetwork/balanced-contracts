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
        self.vote_execute = VoteActions(db, self)
        self._launch_day = VarDB('launch_day', db, int)
        self._launch_time = VarDB('launch_time', db, int)
        self._launched = VarDB('launched', db, bool)
        self._rebalancing = VarDB('rebalancing', db, Address)
        self._time_offset = VarDB('time_offset', db, value_type=int)
        self._minimum_vote_duration = VarDB('min_duration', db, int)

    def on_install(self) -> None:
        super().on_install()
        self._launched.set(False)

    def on_update(self) -> None:
        super().on_update()
        self._time_offset.set(DAY_START + U_SECONDS_DAY * (DAY_ZERO + self._launch_day.get() - 1))
        self._minimum_vote_duration.set(1)

    @external(readonly=True)
    def name(self) -> str:
        return "Balanced Governance"

    @external(readonly=True)
    def getDay(self) -> int:
        return (self.now() - self._time_offset.get()) // U_SECONDS_DAY

    @external(readonly=True)
    def getVotersCount(self, name: str) -> dict:
        vote_index = ProposalDB.proposal_id(name, self.db)
        proposal = ProposalDB(var_key=vote_index, db=self.db)
        return {'for_voters': proposal.for_voters_count.get(), 'against_voters': proposal.against_voters_count.get()}

    @external
    @only_owner
    def activateVote(self, name: str) -> None:
        """
        After defining a vote it will have to be activated.
        """
        vote_index = ProposalDB.proposal_id(name, self.db)
        if vote_index == 0:
            revert(f'That is not a valid vote name.')
        proposal = ProposalDB(vote_index, self.db)
        if proposal.status.get() != ProposalStatus.STATUS[ProposalStatus.PENDING]:
            revert("Balanced Governance: A vote can be activated only from Pending status")
        proposal.active.set(True)
        proposal.status.set(ProposalStatus.STATUS[ProposalStatus.ACTIVE])

    @external
    @only_owner
    def cancelVote(self, name: str) -> None:
        """
        Cancels a vote, in case a mistake was made in its definition.
        """
        vote_index = ProposalDB.proposal_id(name, self.db)
        if vote_index == 0:
            revert(f'That is not a valid vote name.')
        proposal = ProposalDB(vote_index, self.db)
        if proposal.status.get() != ProposalStatus.STATUS[ProposalStatus.PENDING]:
            revert("Balanced Governance: Proposal can be cancelled only from pending status")
        proposal.active.set(False)
        proposal.status.set(ProposalStatus.STATUS[ProposalStatus.CANCELLED])

    @external
    @only_owner
    def defineVote(self, name: str, description: str, quorum: int, vote_start: int, duration: int, snapshot: int, actions: str,
                   majority: int = MAJORITY) -> None:
        """
        Names a new vote, defines quorum, and actions.
        """
        if len(description) > 500:
            revert(f'Description must be less than or equal to 500 characters.')
        if not 0 < quorum < 100:
            revert(f'Quorum must be greater than 0 and less than 100.')
        if vote_start <= self.getDay():
            revert(f'Vote cannot start before the current time.')
        if snapshot >= vote_start:
            revert(f'Snapshot reference index must be less than vote start.')
        min_duration = self._minimum_vote_duration.get()
        if duration < min_duration:
            revert(f'Votes must have a minimum duration of {min_duration} days.')
        vote_index = ProposalDB.proposal_id(name, self.db)
        if vote_index > 0:
            revert(f'Poll name {name} has already been used.')

        actions_dict = json_loads(actions)
        if len(actions_dict) > self.maxActions():
            revert(f"Balanced Governance: Only {self.maxActions()} actions are allowed")

        ProposalDB.create_proposal(name=name, description=description, proposer=self.msg.sender, quorum=quorum*EXA//100, majority=majority,
                                   snapshot=snapshot, start=vote_start, end=vote_start + duration, actions=actions,
                                   db=self.db)

    @external(readonly=True)
    def maxActions(self) -> int:
        return 5

    @external(readonly=True)
    def getProposalCount(self) -> int:
        return ProposalDB.proposal_count(self.db)

    @external(readonly=True)
    def getProposals(self, batch_size: int = 20, offset: int = 1) -> list:
        proposal_list = []
        start = max(1, offset)
        end = min(start + batch_size, self.getProposalCount())
        for proposal_id in range(start, end + 1):
            proposal = self.checkVote(proposal_id)
            proposal_list.append(proposal)
        return proposal_list

    @external
    def castVote(self, name: str, vote: bool) -> None:
        """
        Casts a vote in the named poll.
        """
        vote_index = ProposalDB.proposal_id(name, self.db)
        proposal = ProposalDB(var_key=vote_index, db=self.db)
        start_snap = proposal.start_snapshot.get()
        end_snap = proposal.end_snapshot.get()
        if vote_index <= 0 or not start_snap <= self.getDay() < end_snap or proposal.active.get() is False:
            revert(f'That is not an active poll.')
        sender = self.msg.sender
        snapshot = proposal.vote_snapshot.get()
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        stake = baln.stakedBalanceOfAt(sender, snapshot)
        dex_pool = self._get_pool_baln(sender, snapshot)
        total_vote = stake + dex_pool
        if total_vote == 0:
            revert(f'Balanced tokens need to be staked or BALN liquidity provided to a DEX pool to cast the vote.')
        prior_vote = (proposal.for_votes_of_user[sender], proposal.against_votes_of_user[sender])
        total_for_votes = proposal.total_for_votes.get()
        total_against_votes = proposal.total_against_votes.get()
        total_for_voters_count = proposal.for_voters_count.get()
        total_against_voters_count = proposal.against_voters_count.get()
        if vote:
            proposal.for_votes_of_user[sender] = total_vote
            proposal.against_votes_of_user[sender] = 0
            total_for = total_for_votes + total_vote - prior_vote[0]
            total_against = total_against_votes - prior_vote[1]
            if prior_vote[0] == 0 and prior_vote[1] == 0:
                proposal.for_voters_count.set(total_for_voters_count + 1)
            else:
                if prior_vote[1]:
                    proposal.against_voters_count.set(total_against_voters_count - 1)
                    proposal.for_voters_count.set(total_for_voters_count + 1)
        else:
            proposal.for_votes_of_user[sender] = 0
            proposal.against_votes_of_user[sender] = total_vote
            total_for = total_for_votes - prior_vote[0]

            total_against = total_against_votes + total_vote - prior_vote[1]
            if prior_vote[0] == 0 and prior_vote[1] == 0:
                proposal.against_voters_count.set(total_against_voters_count + 1)
            else:
                if prior_vote[0]:
                    proposal.against_voters_count.set(total_against_voters_count + 1)
                    proposal.for_voters_count.set(total_for_voters_count - 1)

        proposal.total_for_votes.set(total_for)
        proposal.total_against_votes.set(total_against)
        self.VoteCast(name, vote, sender, total_vote, total_for, total_against)

    def _get_pool_baln(self, _account: Address, _day: int) -> int:

        dex_score = self.create_interface_score(self.addresses['dex'], DexInterface)

        my_baln_from_pools = 0
        for pool_id in (BALNBNUSD_ID, BALNSICX_ID):
            my_lp = dex_score.balanceOfAt(_account, pool_id, _day)
            total_lp = dex_score.totalSupplyAt(pool_id, _day)
            total_baln = dex_score.totalBalnAt(pool_id, _day)

            equivalent_baln = 0
            if my_lp > 0 and total_lp > 0 and total_baln > 0:
                equivalent_baln = (my_lp * total_baln) // total_lp

            my_baln_from_pools += equivalent_baln

        my_total_baln_token = my_baln_from_pools
        return my_total_baln_token

    @external(readonly=True)
    def totalBaln(self, _day: int) -> int:
        baln = self.create_interface_score(self.addresses['baln'], BalancedInterface)
        total_stake = baln.totalStakedBalanceOfAt(_day)
        dex_score = self.create_interface_score(self.addresses['dex'], DexInterface)

        total_baln_from_pools = 0
        for pool_id in (BALNBNUSD_ID, BALNSICX_ID):
            total_baln = dex_score.totalBalnAt(pool_id, _day)

            total_baln_from_pools += total_baln

        total_baln_token = total_baln_from_pools + total_stake
        return total_baln_token

    @external
    def executeVoteAction(self, vote_index: int) -> None:
        """
        Executes the vote action if the vote has completed and passed.
        """
        result = self.checkVote(vote_index)
        if result == {}:
            revert(f'Provided vote index, {vote_index}, out of range.')
        proposal = ProposalDB(vote_index, self.db)
        end_snap = proposal.end_snapshot.get()

        if self.getDay() < end_snap:
            revert("Balanced Governance: Voting period has not ended")

        if result['for'] + result['against'] >= result['quorum']:
            majority = proposal.majority.get()
            if (EXA - majority) * result['for'] > majority * result['against']:
                try:
                    self._execute_vote_actions(proposal.actions.get())
                except BaseException as e:
                    revert(f"Failed Execution of action. Reason: {e}")
                proposal.status.set(ProposalStatus.STATUS[ProposalStatus.EXECUTED])
            else:
                proposal.status.set(ProposalStatus.STATUS[ProposalStatus.DEFEATED])
        else:
            proposal.status.set(ProposalStatus.STATUS[ProposalStatus.NO_QUORUM])
        proposal.active.set(False)

    def _execute_vote_actions(self, _vote_actions: str) -> None:
        actions = json_loads(_vote_actions)
        for action in actions:
            self.vote_execute[action](**actions[action])

    @external(readonly=True)
    def getVoteIndex(self, _name: str) -> int:
        return ProposalDB.proposal_id(_name, self.db)

    @external(readonly=True)
    def checkVote(self, _vote_index: int) -> dict:
        if _vote_index < 1 or _vote_index > ProposalDB.proposal_count(self.db):
            return {}
        vote_data = ProposalDB(_vote_index, self.db)
        try:
            total_baln = self.totalBaln(vote_data.vote_snapshot.get())
        except BaseException:
            total_baln = 0
        if total_baln == 0:
            _for = 0
            _against = 0
        else:
            total_voted = (vote_data.total_for_votes.get(), vote_data.total_against_votes.get())
            _for = EXA * total_voted[0] // total_baln
            _against = EXA * total_voted[1] // total_baln

        vote_status = {'id': _vote_index,
                       'name': vote_data.name.get(),
                       'proposer': vote_data.proposer.get(),
                       'description': vote_data.description.get(),
                       'majority': vote_data.majority.get(),
                       'vote snapshot': vote_data.vote_snapshot.get(),
                       'start day': vote_data.start_snapshot.get(),
                       'end day': vote_data.end_snapshot.get(),
                       'actions': vote_data.actions.get(),
                       'quorum': vote_data.quorum.get(),
                       'for': _for,
                       'against': _against,
                       'for_voter_count': vote_data.for_voters_count.get(),
                       'against_voter_count': vote_data.against_voters_count.get(),
                       }
        status = vote_data.status.get()
        majority = vote_status['majority']
        if status == ProposalStatus.STATUS[ProposalStatus.ACTIVE] and self.getDay() >= vote_status["end day"]:
            if vote_status['for'] + vote_status['against'] < vote_status['quorum']:
                vote_status['status'] = ProposalStatus.STATUS[ProposalStatus.NO_QUORUM]
            elif (EXA - majority) * vote_status['for'] > majority * vote_status['against']:
                vote_status['status'] = ProposalStatus.STATUS[ProposalStatus.SUCCEEDED]
            else:
                vote_status['status'] = ProposalStatus.STATUS[ProposalStatus.DEFEATED]
        else:
            vote_status['status'] = status

        return vote_status

    @external(readonly=True)
    def getVotesOfUser(self, vote_index: int, user: Address) -> dict:
        vote_data = ProposalDB(vote_index, self.db)
        return {"for": vote_data.for_votes_of_user[user], "against": vote_data.against_votes_of_user[user]}

    @external
    @only_owner
    def configureBalanced(self) -> None:
        """
        Set parameters after deployment and before launch.
        Add Assets to Loans.
        """
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
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
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        dex = self.create_interface_score(self.addresses['dex'], DexInterface)
        rewards = self.create_interface_score(self.addresses['rewards'], RewardsInterface)
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
        amount = EXA * value // (price * 7)
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
    def rebalancingSetBnusd(self,_address: Address) -> None:
        rebalancing = self.create_interface_score(self._rebalancing.get(), RebalancingInterface)
        rebalancing.setBnusd(_address)

    @external
    @only_owner
    def rebalancingSetSicx(self, _address: Address) -> None:
        rebalancing = self.create_interface_score(self._rebalancing.get(), RebalancingInterface)
        rebalancing.setSicx(_address)

    @external
    @only_owner
    def rebalancingSetDex(self, _address: Address) -> None:
        rebalancing = self.create_interface_score(self._rebalancing.get(), RebalancingInterface)
        rebalancing.setDex(_address)

    @external
    @only_owner
    def rebalancingSetLoans(self, _address: Address) -> None:
        rebalancing = self.create_interface_score(self._rebalancing.get(), RebalancingInterface)
        rebalancing.setLoans(_address)

    @external
    @only_owner
    def setLoansRebalance(self, _address: Address) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.setRebalance(_address)

    @external
    @only_owner
    def setLoansDex(self, _address: Address) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.setDex(_address)

    @external
    @only_owner
    def setRebalancing(self, _address: Address) -> None:
        self._rebalancing.set(_address)

    @external
    @only_owner
    def setRebalancingSicx(self, _value: int) -> None:
        rebalancing = self.create_interface_score(self._rebalancing.get(), RebalancingInterface)
        rebalancing.setSicxReceivable(_value)

    @external
    @only_owner
    def setRebalancingThreshold(self, _value: int) -> None:
        rebalancing = self.create_interface_score(self._rebalancing.get(), RebalancingInterface)
        rebalancing.setPriceDiffThreshold(_value)

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

    def enableDividends(self) -> None:
        dividends = self.create_interface_score(self.addresses['dividends'], DividendsInterface)
        dividends.setDistributionActivationStatus(True)

    def setMiningRatio(self, _value: int):
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.setMiningRatio(_value)

    def setLockingRatio(self, _value: int):
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.setLockingRatio(_value)

    def setOriginationFee(self, _fee: int):
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.setOriginationFee(_fee)

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
    def bonusDist(self, _addresses: List[Address], _amounts: List[int]) -> None:
        """
        Method to enable distribution of bonus BALN.

        :param _addresses: List of recipient addresses.
        :type _addresses: List[:class:`iconservice.base.address.Address`]
        :param _amounts: List of BALN amounts to send.
        :type _amounts: List[int]
        """
        rewards = self.create_interface_score(self.addresses['rewards'], RewardsInterface)
        rewards.bonusDist(_addresses, _amounts)

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
    def daoDisburse(self, _recipient: Address, _amounts: List[Disbursement]) -> None:
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
    @only_owner
    def setRedemptionFee(self, _fee: int) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.setRedemptionFee(_fee)

    @external
    @only_owner
    def setMaxRetirePercent(self, _value: int) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.setMaxRetirePercent(_value)

    @external
    @only_owner
    def setRedeemBatchSize(self, _value: int) -> None:
        loans = self.create_interface_score(self.addresses['loans'], LoansInterface)
        loans.setRedeemBatchSize(_value)

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

    @eventlog(indexed=2)
    def VoteCast(self, vote_name: str, vote: bool, voter: Address, stake: int, total_for: int, total_against: int):
        pass
