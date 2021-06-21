import json
from json import JSONDecodeError

from iconservice import Address, IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from core_contracts.governance.governance import Governance


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

        self.governance = self.update_score(self.governance.address, Governance)
        self.baln = Address.from_string(f"cx{'12345'*8}")
        self.governance.addresses._baln.set(self.baln)

    def test_create_vote(self):
        self.set_msg(self.test_account1)
        day = self.governance.getDay()
        print(day)
        self.governance.defineVote(name="Just a demo", quorum=40, vote_start=day + 2, duration=2, snapshot=30,
                                   actions="{\"enable_dividends\": {}}")
        self.patch_internal_method(self.baln, "totalStakedBalanceOfAt", lambda x: 500)
        expected = {'id': 1, 'name': 'Just a demo', 'majority': 666666666666666667, 'vote snapshot': 30,
                    'start day': day + 2, 'end day': day + 4, 'actions': "{\"enable_dividends\": {}}",
                    'quorum': 400000000000000000, 'for': 0, 'against': 0, 'status': 'Pending'}
        self.assertEqual(expected, self.governance.checkVote(_vote_index=1))

    def test_execute_vote_actions(self):

        dividends = Address.from_string(f"cx{'12345'*8}")
        self.governance.addresses._dividends.set(dividends)
        self.patch_internal_method(dividends, "setDistributionActivationStatus", lambda x: x)

        incorrect_actions = json.dumps({"enable_dividends": {"status": True}})
        correct_actions = json.dumps({"enable_dividends": {}})
        incorrect_json = "method: enable_dividends, params: {'status': True}"

        self.assertRaises(TypeError, self.governance._execute_vote_actions, incorrect_actions)
        try:
            self.governance._execute_vote_actions(correct_actions)
        except TypeError:
            self.fail("Raised type error unexpectedly")

        self.assertRaises(JSONDecodeError, self.governance._execute_vote_actions, incorrect_json)

    def test_conditions_to_define_vote(self):
        self.set_msg(self.test_account1)
        day = self.governance.getDay()
        print(day)

        with self.assertRaises(IconScoreException) as quorum:
            self.governance.defineVote(name="Enable the dividends", quorum=0, vote_start=day + 2, duration=2,
                                       snapshot=30, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Quorum must be greater than 0 and less than 100.", quorum.exception.message)

        with self.assertRaises(IconScoreException) as quorum2:
            self.governance.defineVote(name="Enable the dividends", quorum=100, vote_start=day + 2, duration=2,
                                       snapshot=30, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Quorum must be greater than 0 and less than 100.", quorum2.exception.message)

        with self.assertRaises(IconScoreException) as start_day:
            self.governance.defineVote(name="Enable the dividends", quorum=40, vote_start=day, duration=2,
                                       snapshot=30, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Vote cannot start before the current time.", start_day.exception.message)

        with self.assertRaises(IconScoreException) as start_day2:
            self.governance.defineVote(name="Enable the dividends", quorum=40, vote_start=day - 1, duration=2,
                                       snapshot=30, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Vote cannot start before the current time.", start_day2.exception.message)

        with self.assertRaises(IconScoreException) as snapshot:
            self.governance.defineVote(name="Enable the dividends", quorum=40, vote_start=day + 1, duration=2,
                                       snapshot=0, actions="{\"enable_dividends\": {}}")
        self.assertEqual("The reference snapshot index must be greater than zero.", snapshot.exception.message)

        with self.assertRaises(IconScoreException) as duration:
            self.governance.defineVote(name="Enable the dividends", quorum=40, vote_start=day + 1, duration=0,
                                       snapshot=15, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Votes must have a minimum duration of 1 days.", duration.exception.message)

        with self.assertRaises(IconScoreException) as duplicate:
            self.governance.defineVote(name="Enable the dividends", quorum=40, vote_start=day + 1, duration=2,
                                       snapshot=15, actions="{\"enable_dividends\": {}}")
            self.governance.defineVote(name="Enable the dividends", quorum=40, vote_start=day + 1, duration=2,
                                       snapshot=15, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Poll name Enable the dividends has already been used.", duplicate.exception.message)

        with self.assertRaises(IconScoreException) as max_actions:
            self.governance.defineVote(name="Enable the dividends max action", quorum=40, vote_start=day + 1, duration=2,
                                       snapshot=15,
                                       actions="{\"enable_dividends\": {}, \"enable_dividends1\": {}, "
                                               "\"enable_dividends2\": {}, \"enable_dividends3\": {}, "
                                               "\"enable_dividends4\": {}, \"enable_dividends5\": {}}")
        self.assertEqual("Balanced Governance: Only 5 actions are allowed", max_actions.exception.message)

    def test_vote_cycle_complete(self):
        self.set_msg(self.test_account1)
        day = self.governance.getDay()
        self.patch_internal_method(self.baln, "stakedBalanceOfAt", lambda x, y: 1000 * 10 ** 18)
        self.patch_internal_method(self.baln, "totalStakedBalanceOfAt", lambda x: 10 * 1000 * 10 ** 18)

        self.governance.defineVote(name="Enable the dividends", quorum=40, vote_start=day + 1, duration=2,
                                   snapshot=15, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Pending", self.governance.checkVote(1).get("status"))

        with self.assertRaises(IconScoreException) as inactive_poll:
            self.governance.castVote("Enable the dividends", True)
        self.assertEqual("That is not an active poll.", inactive_poll.exception.message)

        try:
            self.governance.activateVote("Enable the dividends")
        except IconScoreException:
            self.fail("Failed to execute activate poll method")
        self.assertEqual("Active", self.governance.checkVote(1).get("status"))

        self.governance.defineVote(name="Enable the dividends cancel this", quorum=40, vote_start=day + 1, duration=2,
                                   snapshot=15, actions="{\"enable_dividends\": {}}")
        try:
            self.governance.cancelVote("Enable the dividends cancel this")
        except IconScoreException:
            self.fail("Fail to cancel the vote")
        self.assertEqual("Cancelled", self.governance.checkVote(2).get("status"))

    def test_proposal_count(self):
        self.set_msg(self.test_account1)
        day = self.governance.getDay()
        self.governance.defineVote(name="Enable the dividends", quorum=40, vote_start=day + 1, duration=2,
                                   snapshot=15, actions="{\"enable_dividends\": {}}")
        self.governance.defineVote(name="Enable the dividends2", quorum=40, vote_start=day + 1, duration=2,
                                   snapshot=15, actions="{\"enable_dividends\": {}}")
        self.governance.defineVote(name="Enable the dividends3", quorum=40, vote_start=day + 1, duration=2,
                                   snapshot=15, actions="{\"enable_dividends\": {}}")

        self.assertEqual(3, self.governance.getProposalCount(), "Failed to create three proposals")
