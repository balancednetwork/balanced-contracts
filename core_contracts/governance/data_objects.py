from .utils.consts import *
from .interfaces import *


# TypedDict for disbursement specs
class Disbursement(TypedDict):
    address: Address
    amount: int
    symbol: str


class BalancedAddresses(TypedDict):
    loans: Address
    dex: Address
    staking: Address
    rewards: Address
    reserve: Address
    dividends: Address
    daofund: Address
    oracle: Address
    sicx: Address
    bnUSD: Address
    baln: Address
    bwt: Address


class VoteActions(object):

    def __init__(self, db: IconScoreDatabase, gov: IconScoreBase) -> None:
        self._db = db
        self._gov = gov
        self._actions = {
            'enable_dividends': self._gov.enableDividends,
            'addNewDataSource': self._gov.addNewDataSource,
            'updateDistPercent': self._gov.updateBalTokenDistPercentage,
            'update_mining_ratio': self._gov.setMiningRatio,
            'update_locking_ratio': self._gov.setLockingRatio,
            'update_origination_fee': self._gov.setOriginationFee,
            'update_liquidation_ratio': self._gov.setLiquidationRatio,
            'update_retirement_bonus': self._gov.setRetirementBonus,
            'update_liquidation_rewards': self._gov.setLiquidationReward,
            'update_max_retire_percent': self._gov.setMaxRetirePercent,
            'update_rebalancing_sicx': self._gov.setRebalancingSicx,
            'update_rebalancing_threshold': self._gov.setRebalancingThreshold,
            'update_vote_duration': self._gov.setVoteDuration,
            'update_quorum': self._gov.setQuorum,
            'update_vote_definition_fee': self.setVoteDefinitionFee,
            'update_baln_vote_definition_criterion': self.setBalnVoteDefinitionCriterion,
            'update_dividends_category_percent': self._gov.setDividendsCategoryPercentage,
            'update_dao_disburse': self._gov.daoDisburse
        }

    def __getitem__(self, key: str):
        return self._actions[key]

    def __setitem__(self, key, value):
        revert('illegal access')


class Addresses(object):

    def __init__(self, db: IconScoreDatabase, gov: IconScoreBase) -> None:
        self._db = db
        self._gov = gov
        self._loans = VarDB('loans', db, Address)
        self._dex = VarDB('dex', db, Address)
        self._staking = VarDB('staking', db, Address)
        self._rewards = VarDB('rewards', db, Address)
        self._reserve = VarDB('reserve', db, Address)
        self._dividends = VarDB('dividends', db, Address)
        self._daofund = VarDB('daofund', db, Address)
        self._oracle = VarDB('oracle', db, Address)
        self._sicx = VarDB('sicx', db, Address)
        self._bnUSD = VarDB('bnUSD', db, Address)
        self._baln = VarDB('baln', db, Address)
        self._bwt = VarDB('bwt', db, Address)

    def __getitem__(self, key: str) -> Address:
        if key == 'governance':
            return self._gov.address
        return VarDB(key, self._db, Address).get()

    def __setitem__(self, key, value):
        revert('illegal access')

    def setAddresses(self, addresses: BalancedAddresses) -> None:
        """
        Takes a TypedDict with 11 addresses and sets them.
        """
        set_func: dict = {'loans': self._loans.set,
                          'dex': self._dex.set,
                          'staking': self._staking.set,
                          'rewards': self._rewards.set,
                          'reserve': self._reserve.set,
                          'dividends': self._dividends.set,
                          'daofund': self._daofund.set,
                          'oracle': self._oracle.set,
                          'sicx': self._sicx.set,
                          'bnUSD': self._bnUSD.set,
                          'baln': self._baln.set,
                          'bwt': self._bwt.set}
        for key, value in addresses.items():
            set_func[key](value)

    def getAddresses(self) -> dict:
        return {
                'loans': self._loans.get(),
                'dex': self._dex.get(),
                'staking': self._staking.get(),
                'rewards': self._rewards.get(),
                'reserve': self._reserve.get(),
                'dividends': self._dividends.get(),
                'daofund': self._daofund.get(),
                'oracle': self._oracle.get(),
                'sicx': self._sicx.get(),
                'bnUSD': self._bnUSD.get(),
                'baln': self._baln.get(),
                'bwt': self._bwt.get()
               }

    def setContractAddresses(self) -> None:
        """
        Set the addresses in each SCORE for the other SCOREs. Which addresses
        are set in which SCOREs is specified in the consts.py file.
        """
        for contract in ADDRESSES:
            score = self._gov.create_interface_score(self[contract], SetAddressesInterface)
            set_methods = {'admin': score.setAdmin, 'loans': score.setLoans,
                           'staking': score.setStaking, 'rewards': score.setRewards,
                           'reserve': score.setReserve, 'dividends': score.setDividends,
                           'daofund': score.setDaofund, 'oracle': score.setOracle,
                           'sicx': score.setSicx, 'bnUSD': score.setbnUSD,
                           'baln': score.setBaln, 'bwt': score.setBwt, 'dex': score.setDex}
            for method in ADDRESSES[contract]:
                try:
                    set_methods[method](self[method])
                except BaseException as e:
                    revert(f'Problem setting {method} on {contract}. '
                           f'Exception: {e}')

    def setAdmins(self) -> None:
        """
        Set the admin addresses for each SCORE.
        """
        for contract in ADMIN_ADDRESSES:
            score = self._gov.create_interface_score(self[contract], SetAddressesInterface)
            try:
                score.setAdmin(self[ADMIN_ADDRESSES[contract]])
            except BaseException as e:
                revert(f'Problem setting admin address to {ADMIN_ADDRESSES[contract]} '
                       f'on {contract}. Exception: {e}')


class ProposalDB:

    _PREFIX = "ProposalDB_"

    def __init__(self, var_key: int, db: IconScoreDatabase):
        self._key = self._PREFIX + str(var_key)
        self.id = DictDB(self._PREFIX + "_id", db, value_type=int)
        self.proposals_count = VarDB(self._PREFIX + "_proposals_count", db, value_type=int)
        self.proposer = VarDB(self._key + "_proposer", db, value_type=Address)
        self.quorum = VarDB(self._key + "_quorum", db, value_type=int)
        self.majority = VarDB(self._key + "_majority", db, value_type=int)
        self.vote_snapshot = VarDB(self._key + "_vote_snapshot", db, value_type=int)
        self.start_snapshot = VarDB(self._key + "_start_snapshot", db, value_type=int)
        self.end_snapshot = VarDB(self._key + "_end_snapshot", db, value_type=int)
        self.actions = VarDB(self._key + "_actions", db, value_type=str)
        self.name = VarDB(self._key + "_name", db, value_type=str)
        self.description = VarDB(self._key + "_description", db, value_type=str)
        self.active = VarDB(self._key + "_active", db, value_type=bool)
        self.for_votes_of_user = DictDB(self._key + "_for_votes_of_user", db, value_type=int)
        self.against_votes_of_user = DictDB(self._key + "_against_votes_of_user", db, value_type=int)
        self.total_for_votes = VarDB(self._key + "_total_for_votes", db, value_type=int)
        self.for_voters_count = VarDB(self._key + "_for_voters_count", db, value_type=int)
        self.against_voters_count = VarDB(self._key + "_against_voters_count", db, value_type=int)
        self.total_against_votes = VarDB(self._key + "_total_against_votes", db, value_type=int)
        self.status = VarDB(self._key + "_status", db, value_type=str)

    @classmethod
    def proposal_id(cls, _proposal_name: str, db: IconScoreDatabase) -> int:
        proposal = cls(0, db)
        return proposal.id[_proposal_name]

    @classmethod
    def proposal_count(cls, db: IconScoreDatabase) -> int:
        proposal = cls(0, db)
        return proposal.proposals_count.get()

    @classmethod
    def create_proposal(cls, name: str, description: str, proposer: Address, quorum: int, majority: int, snapshot: int, start: int,
                        end: int, actions: str, db: IconScoreDatabase) -> 'ProposalDB':

        vote_index = cls(0, db).proposals_count.get() + 1
        new_proposal = ProposalDB(vote_index, db)
        new_proposal.proposals_count.set(vote_index)

        new_proposal.id[name] = vote_index
        new_proposal.proposer.set(proposer)
        new_proposal.quorum.set(quorum)
        new_proposal.majority.set(majority)
        new_proposal.vote_snapshot.set(snapshot)
        new_proposal.start_snapshot.set(start)
        new_proposal.end_snapshot.set(end)
        new_proposal.actions.set(actions)
        new_proposal.name.set(name)
        new_proposal.description.set(description)
        new_proposal.status.set(ProposalStatus.STATUS[ProposalStatus.PENDING])
        return new_proposal


class ProposalStatus:
    PENDING = 0
    ACTIVE = 1
    CANCELLED = 2
    DEFEATED = 3
    SUCCEEDED = 4
    NO_QUORUM = 5
    EXECUTED = 6
    STATUS = ["Pending", "Active", "Cancelled", "Defeated", "Succeeded", "No Quorum", "Executed"]
