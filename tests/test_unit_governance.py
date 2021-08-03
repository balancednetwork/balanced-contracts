import json
from json import JSONDecodeError
from unittest import mock

from iconservice import Address, IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from core_contracts.governance.governance import Governance

class MockClass:
    def __init__(self, totalSupply = None, stakedBalanceOf = None, transfer = None):

        self._totalSupply = totalSupply
        self._stakedBalanceOf = stakedBalanceOf
        self._transfer = transfer

    def totalSupply(self):
        return self._totalSupply

    def stakedBalanceOf(self, address):
        return self._stakedBalanceOf

    def transfer(self, to, amount):
        return self.transfer
    
    def patch_internal(self, address, score):
        return self

class TestGovernanceUnit(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score = Address.from_string(f"cx{'1234' * 10}")
        self.governance = self.get_score_instance(Governance, self.test_account1)
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)

        #self.governance = self.update_score(self.governance.address, Governance)

        # Mock addresses for other contracts.
        self.baln = Address.from_string(f"cx{'12345'*8}")
        self.daofund = Address.from_string(f"cx{'12343'*8}")
        self.bnusd = Address.from_string(f"cx{'13343'*8}")

        # Set addresses.
        self.governance.addresses._baln.set(self.baln)
        self.governance.addresses._daofund.set(self.daofund)
        self.governance.addresses._bnUSD.set(self.bnusd)

    def test_set_minimum_vote_duration(self):
        self.set_msg(self.test_account1)

        self.assertFalse(self.governance._minimum_vote_duration.get())
        self.governance.setMinimumVoteDuration(5)
        self.assertEqual(self.governance.getMinimumVoteDuration(), 5)

    def test_set_quorum(self):
        self.set_msg(self.test_account1)

        # Set correct value.
        self.assertFalse(self.governance._quorum.get())
        self.governance.setQuorum(40)
        self.assertEqual(self.governance.getQuorum(), 40)

        # Set value below range.
        with self.assertRaises(IconScoreException) as e:
            self.governance.setQuorum(0)
        self.assertEqual("Quorum must be between 0 and 100.", e.exception.message)

        # Set value above range.
        with self.assertRaises(IconScoreException) as e:
            self.governance.setQuorum(100)
        self.assertEqual("Quorum must be between 0 and 100.", e.exception.message)

    def test_set_vote_definition_fee(self):
        self.set_msg(self.test_account1)

        self.assertFalse(self.governance._bnusd_vote_definition_fee.get())
        self.governance.setVoteDefinitionFee(100)
        self.assertEqual(self.governance.getVoteDefinitionFee(), 100)

    def test_set_vote_definition_criteria(self):
        self.set_msg(self.test_account1)

        self.assertFalse(self.governance._baln_vote_definition_criteria.get())
        self.governance.setBalnVoteDefinitionCriteria("1.5")
        self.assertEqual(self.governance.getBalnVoteDefinitionCriteria(), "0.015")

        # Set value below range.
        with self.assertRaises(IconScoreException) as e:
            self.governance.setBalnVoteDefinitionCriteria("-1.5")
        self.assertEqual("Percentage must be in the 0-100 range.", e.exception.message)

        # Set value above range.
        with self.assertRaises(IconScoreException) as e:
            self.governance.setBalnVoteDefinitionCriteria("101")
        self.assertEqual("Percentage must be in the 0-100 range.", e.exception.message)

    def test_create_vote(self):
        self.set_msg(self.test_account1)
        day = self.governance.getDay()

        # Set governance parameters.
        self.governance.setQuorum(40)
        self.governance.setMinimumVoteDuration(5)
        self.governance.setVoteDefinitionFee(1000 * 10**18)
        self.governance.setBalnVoteDefinitionCriteria(1)

        # Test define vote method.
        mock_class = MockClass(totalSupply = 10000, stakedBalanceOf = 100)
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            self.governance.defineVote(name="Just a demo", vote_start=day + 2, duration=5, snapshot=day,
                                       actions="{\"enable_dividends\": {}}")

        self.patch_internal_method(self.baln, "totalStakedBalanceOfAt", lambda x: 500)

        expected = {'id': 1, 'name': 'Just a demo', 'majority': 666666666666666667, 'vote snapshot': day,
                    'start day': day + 2, 'end day': day + 7, 'actions': "{\"enable_dividends\": {}}",
                    'quorum': 400000000000000000, 'for': 0, 'against': 0, 'status': 'Pending'}
        self.assertEqual(expected, self.governance.checkVote(_vote_index=1))

    #def test_execute_vote_actions(self):

    #    dividends = Address.from_string(f"cx{'12345'*8}")
    #    self.governance.addresses._dividends.set(dividends)
    #    self.patch_internal_method(dividends, "setDistributionActivationStatus", lambda x: x)

    #    incorrect_actions = json.dumps({"enable_dividends": {"status": True}})
    #    correct_actions = json.dumps({"enable_dividends": {}})
    #    incorrect_json = "method: enable_dividends, params: {'status': True}"

    #    self.assertRaises(TypeError, self.governance._execute_vote_actions, incorrect_actions)
    #    try:
    #        self.governance._execute_vote_actions(correct_actions)
    #    except TypeError:
    #        self.fail("Raised type error unexpectedly")

    #    self.assertRaises(JSONDecodeError, self.governance._execute_vote_actions, incorrect_json)

    def test_conditions_to_define_vote(self):
        self.set_msg(self.test_account1)
        day = self.governance.getDay()

        # Set governance parameters.
        self.governance.setQuorum(40)
        self.governance.setMinimumVoteDuration(5)
        self.governance.setVoteDefinitionFee(1000 * 10**18)
        self.governance.setBalnVoteDefinitionCriteria(1)

        mock_class = MockClass(totalSupply = 10000, stakedBalanceOf = 100)
        min_duration = duration=self.governance.getMinimumVoteDuration()
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            
            # Start before current day.
            with self.assertRaises(IconScoreException) as start_day2:
                self.governance.defineVote(name="Enable the dividends", vote_start=day - 1, duration=min_duration,
                                           snapshot=day, actions="{\"enable_dividends\": {}}")
            self.assertEqual("Vote cannot start before the current time.", start_day2.exception.message)

            # Snapshot less then current day.
            with self.assertRaises(IconScoreException) as snapshot_1:
                self.governance.defineVote(name="Enable the dividends", vote_start=day, duration=min_duration,
                                           snapshot= day - 1, actions="{\"enable_dividends\": {}}")

            self.assertEqual(f'The reference snapshot must be in the range: [current_day ({day}), ' 
                             f'start_day ({day})].', snapshot_1.exception.message)

            # Snapshot larger than day of vote start.
            with self.assertRaises(IconScoreException) as snapshot_1:
                self.governance.defineVote(name="Enable the dividends", vote_start=day, duration=min_duration,
                                           snapshot= day + 1, actions="{\"enable_dividends\": {}}")
            self.assertEqual(f'The reference snapshot must be in the range: [current_day ({day}), '
                             f'start_day ({day})].', snapshot_1.exception.message)

            # Vote duration below minimum.
            with self.assertRaises(IconScoreException) as duration:
                self.governance.defineVote(name="Enable the dividends", vote_start=day, duration=min_duration - 1,
                                           snapshot=day, actions="{\"enable_dividends\": {}}")
            self.assertEqual(f'Votes must have a minimum duration of {min_duration} days.', duration.exception.message)

            # Dublicate use of poll name.
            with self.assertRaises(IconScoreException) as duplicate:
                self.governance.defineVote(name="Enable the dividendss", vote_start=day, duration=min_duration,
                                           snapshot=day, actions="{\"enable_dividends\": {}}")
                self.governance.defineVote(name="Enable the dividendss", vote_start=day, duration=min_duration,
                                           snapshot=day, actions="{\"enable_dividends\": {}}")
            self.assertEqual("Poll name Enable the dividendss has already been used.", duplicate.exception.message)

            # More actions then allowed.
            with self.assertRaises(IconScoreException) as max_actions:
                self.governance.defineVote(name="Enable the dividends max action", vote_start=day, duration=min_duration,
                                           snapshot=day,
                                           actions="{\"enable_dividends\": {}, \"enable_dividends1\": {}, "
                                                   "\"enable_dividends2\": {}, \"enable_dividends3\": {}, "
                                                   "\"enable_dividends4\": {}, \"enable_dividends5\": {}}")                                     
            self.assertEqual("Balanced Governance: Only 5 actions are allowed", max_actions.exception.message)

        # New mock class that does not fulfill baln staking criteria for voteDefinition.
        mock_class = MockClass(totalSupply = 100, stakedBalanceOf = 0.99)
        baln_criteria = float(self.governance.getBalnVoteDefinitionCriteria())
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            
            # Not enough baln staked.
            with self.assertRaises(IconScoreException) as balnstaked:
                self.governance.defineVote(name="Enable the dividends", vote_start=day, duration=min_duration,
                                           snapshot=day, actions="{\"enable_dividends\": {}}")
            self.assertEqual(f'User needs atleast {baln_criteria * 100}% of total baln supply staked to define a vote.', balnstaked.exception.message)


    #def test_vote_cycle_complete(self):
    #    self.set_msg(self.test_account1)
    #    day = self.governance.getDay()
#
    #    # Set governance parameters.
    #    self.governance.setQuorum(40)
    #    self.governance.setMinimumVoteDuration(5)
    #    self.governance.setVoteDefinitionFee(1000 * 10**18)
    #    self.governance.setBalnVoteDefinitionCriteria(1)
    #    min_duration = duration=self.governance.getMinimumVoteDuration()
#
    #    self.patch_internal_method(self.baln, "stakedBalanceOfAt", lambda x, y: 1000 * 10 ** 18)
    #    self.patch_internal_method(self.baln, "totalStakedBalanceOfAt", lambda x: 10 * 1000 * 10 ** 18)
    #    self.governance.defineVote(name="Enable the dividends",  vote_start=day + 1, duration=min_duration,
    #                               snapshot=day + 1, actions="{\"enable_dividends\": {}}")
    #    self.assertEqual("Pending", self.governance.checkVote(1).get("status"))
    #    with self.assertRaises(IconScoreException) as inactive_poll:
    #        self.governance.castVote("Enable the dividends", True)
    #    self.assertEqual("That is not an active poll.", inactive_poll.exception.message)
    #    try:
    #        self.governance.activateVote("Enable the dividends")
    #    except IconScoreException:
    #        self.fail("Failed to execute activate poll method")
    #    self.assertEqual("Active", self.governance.checkVote(1).get("status"))
    #    self.governance.defineVote(name="Enable the dividends cancel this", vote_start=day + 1, duration=min_duration,
    #                               snapshot=day + 1, actions="{\"enable_dividends\": {}}")
    #    try:
    #        self.governance.cancelVote("Enable the dividends cancel this")
    #    except IconScoreException:
    #        self.fail("Fail to cancel the vote")
    #    self.assertEqual("Cancelled", self.governance.checkVote(2).get("status"))

    #def test_proposal_count(self):
    #    self.set_msg(self.test_account1)
    #    day = self.governance.getDay()
    #    self.governance.defineVote(name="Enable the dividends", quorum=40, vote_start=day + 1, duration=2,
    #                               snapshot=15, actions="{\"enable_dividends\": {}}")
    #    self.governance.defineVote(name="Enable the dividends2", quorum=40, vote_start=day + 1, duration=2,
    #                               snapshot=15, actions="{\"enable_dividends\": {}}")
    #    self.governance.defineVote(name="Enable the dividends3", quorum=40, vote_start=day + 1, duration=2,
    #                               snapshot=15, actions="{\"enable_dividends\": {}}")

    #    self.assertEqual(3, self.governance.getProposalCount(), "Failed to create three proposals")
