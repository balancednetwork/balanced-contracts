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
            'updateDistPercent': self._gov.updateBalTokenDistPercentage
        }

    def __getitem__(self, key: str):
        return self._actions[key]

    def __setitem__(self, key, value):
        revert('illegal access')


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
    def create_proposal(cls, name: str, description: str, proposer: Address, quorum: int, majority: int, snapshot: int,
                        start: int,
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
    FAILED_EXECUTION = 7
    STATUS = ["Pending", "Active", "Cancelled", "Defeated", "Succeeded", "No Quorum", "Executed", "Failed Execution"]
