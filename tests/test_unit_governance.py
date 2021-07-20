import json
from unittest import mock
from json import JSONDecodeError

from iconservice import Address, IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from core_contracts.governance.governance import Governance
from core_contracts.governance.utils.consts import DAY_ZERO


class MockClass:
    def __init__(self, balanceOfAt, totalSupplyAt, totalBalnAt, totalStakedBalanceOfAt=12, stakedBalanceOfAt=None):
        self._balanceOfAt, self._totalSupplyAt, self._totalBalnAt, self._totalStakedBalanceOfAt = \
            balanceOfAt, totalSupplyAt, totalBalnAt, totalStakedBalanceOfAt
        self._stakedBalanceOfAt = stakedBalanceOfAt

    def balanceOfAt(self, _account, pool_id, _day):
        return self._balanceOfAt

    def totalSupplyAt(self, pool_id, _day):
        return self._totalSupplyAt

    def totalBalnAt(self, pool_id, _day):
        return self._totalBalnAt

    def totalStakedBalanceOfAt(self, _day):
        return self._totalStakedBalanceOfAt

    def patch_internal(self, address, score):
        return self

    def stakedBalanceOfAt(self, address, day):
        return self._stakedBalanceOfAt

    def addNewDataSource(self, a, b):
        pass

    def updateBalTokenDistPercentage(self,a):
        pass

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
        self.baln = Address.from_string(f"cx{'12345' * 8}")
        self.dex = Address.from_string(f"cx{'15785' * 8}")
        self.governance.addresses._baln.set(self.baln)
        self.governance.addresses._dex.set(self.dex)

    def test_create_vote(self):
        self.set_msg(self.test_account1)
        day = self.governance.getDay()
        with mock.patch.object(self.governance, "create_interface_score", MockClass(1, 1, 1, 1).patch_internal):
            self.governance.defineVote(name="Just a demo", description='Testing description field', quorum=40,
                                       vote_start=day + 2, duration=2, snapshot=30,
                                       actions="{\"enable_dividends\": {}}")
            expected = {'id': 1, 'name': 'Just a demo', 'description': 'Testing description field',
                        'majority': 666666666666666667, 'vote snapshot': 30,
                        'start day': day + 2, 'end day': day + 4, 'actions': "{\"enable_dividends\": {}}",
                        'quorum': 400000000000000000, 'for': 0, 'against': 0, 'status': 'Pending'}
            self.assertEqual(expected, self.governance.checkVote(_vote_index=1))

    def test_execute_vote_actions(self):

        dividends = Address.from_string(f"cx{'12345' * 8}")
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

        with self.assertRaises(IconScoreException) as quorum:
            self.governance.defineVote(name="Enable the dividends", description='Testing description field', quorum=0,
                                       vote_start=day + 2, duration=2,
                                       snapshot=30, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Quorum must be greater than 0 and less than 100.", quorum.exception.message)

        with self.assertRaises(IconScoreException) as quorum2:
            self.governance.defineVote(name="Enable the dividends", description='Testing description field', quorum=100,
                                       vote_start=day + 2, duration=2,
                                       snapshot=30, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Quorum must be greater than 0 and less than 100.", quorum2.exception.message)

        with self.assertRaises(IconScoreException) as start_day:
            self.governance.defineVote(name="Enable the dividends", description='Testing description field', quorum=40,
                                       vote_start=day, duration=2,
                                       snapshot=30, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Vote cannot start before the current time.", start_day.exception.message)

        with self.assertRaises(IconScoreException) as start_day2:
            self.governance.defineVote(name="Enable the dividends", description='Testing description field', quorum=40,
                                       vote_start=day - 1, duration=2,
                                       snapshot=30, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Vote cannot start before the current time.", start_day2.exception.message)

        with self.assertRaises(IconScoreException) as snapshot:
            self.governance.defineVote(name="Enable the dividends", description='Testing description field', quorum=40,
                                       vote_start=day + 1, duration=2,
                                       snapshot=0, actions="{\"enable_dividends\": {}}")
        self.assertEqual("The reference snapshot index must be greater than zero.", snapshot.exception.message)

        with self.assertRaises(IconScoreException) as duration:
            self.governance.defineVote(name="Enable the dividends", description='Testing description field', quorum=40,
                                       vote_start=day + 1, duration=0,
                                       snapshot=15, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Votes must have a minimum duration of 1 days.", duration.exception.message)

        with self.assertRaises(IconScoreException) as duplicate:
            self.governance.defineVote(name="Enable the dividends", description='Testing description field', quorum=40,
                                       vote_start=day + 1, duration=2,
                                       snapshot=15, actions="{\"enable_dividends\": {}}")
            self.governance.defineVote(name="Enable the dividends", description='Testing description field', quorum=40,
                                       vote_start=day + 1, duration=2,
                                       snapshot=15, actions="{\"enable_dividends\": {}}")
        self.assertEqual("Poll name Enable the dividends has already been used.", duplicate.exception.message)

        with self.assertRaises(IconScoreException) as max_actions:
            self.governance.defineVote(name="Enable the dividends max action", description='Testing description field',
                                       quorum=40, vote_start=day + 1, duration=2,
                                       snapshot=15,
                                       actions="{\"enable_dividends\": {}, \"enable_dividends1\": {}, "
                                               "\"enable_dividends2\": {}, \"enable_dividends3\": {}, "
                                               "\"enable_dividends4\": {}, \"enable_dividends5\": {}}")
        self.assertEqual("Balanced Governance: Only 5 actions are allowed", max_actions.exception.message)

    def test_vote_cycle_complete(self):
        self.set_msg(self.test_account1, 0)

        self.set_block(0, 0)
        day = self.governance.getDay()
        with mock.patch.object(self.governance, "create_interface_score", MockClass(1, 2, 3, 4, 5).patch_internal):

            self.governance.defineVote(name="Enable the dividends", description="Count pool BALN", quorum=40,
                                       vote_start=day + 1, duration=2,
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
            launch_time = self.governance._launch_time.get()
            from core_contracts.governance.utils.consts import DAY_ZERO
            new_day = launch_time + (DAY_ZERO + day + 2) * 10 ** 6 * 60 * 60 * 24
            self.set_block(55, new_day)
            self.governance.castVote("Enable the dividends", True)

            self.set_block(55, 0)
            self.governance.defineVote(name="Enable the dividends cancel this", description="Count pool BALN",
                                       quorum=40,
                                       vote_start=day + 1, duration=2,
                                       snapshot=15, actions="{\"enable_dividends\": {}}")
            try:
                self.governance.cancelVote("Enable the dividends cancel this")
            except IconScoreException:
                self.fail("Fail to cancel the vote")
            self.assertEqual("Cancelled", self.governance.checkVote(2).get("status"))

    def test_proposal_count(self):
        self.set_msg(self.test_account1)
        day = self.governance.getDay()
        self.governance.defineVote(name="Enable the dividends", description='Testing description field', quorum=40,
                                   vote_start=day + 1, duration=2,
                                   snapshot=15, actions="{\"enable_dividends\": {}}")
        self.governance.defineVote(name="Enable the dividends2", description='Testing description field', quorum=40,
                                   vote_start=day + 1, duration=2,
                                   snapshot=15, actions="{\"enable_dividends\": {}}")
        self.governance.defineVote(name="Enable the dividends3", description='Testing description field', quorum=40,
                                   vote_start=day + 1, duration=2,
                                   snapshot=15, actions="{\"enable_dividends\": {}}")

        self.assertEqual(3, self.governance.getProposalCount(), "Failed to create three proposals")

    def test_get_pool_baln(self):

        dex_score = Address.from_string(f"cx{'2578' * 10}")

        self.governance.addresses._dex.set(dex_score)
        with mock.patch.object(self.governance, "create_interface_score", wraps=MockClass(10, 20, 30).patch_internal):
            result = self.governance._get_pool_baln(_account=self.test_account3, _day=1)
        self.assertEqual(2 * (10 * 30 / 20), result)

        with mock.patch.object(self.governance, "create_interface_score", wraps=MockClass(0, 0, 0).patch_internal):
            result = self.governance._get_pool_baln(_account=self.test_account3, _day=1)
        self.assertEqual(0, result)

    def test_totalBaln(self):
        with mock.patch.object(self.governance, "create_interface_score", wraps=MockClass(10, 20, 30).patch_internal):
            result = self.governance.totalBaln(1)
        self.assertEqual(2 * 30 + 12, result)

    def test_add_new_data_source(self):
        self.set_msg(self.test_account1, 0)
        self.set_block(0, 0)
        day = self.governance.getDay()
        with mock.patch.object(self.governance, "create_interface_score", MockClass(1, 2, 3, 4, 5).patch_internal):
            actions = {"addNewDataSource": {"_data_source_name": "", "_contract_address": ""},
                       "updateDistPercent": {"_recipient_list": [{"recipient_name": "", "dist_percent": 12}]}}
            self.governance.defineVote(name="Enable the dividends", description="Count pool BALN", quorum=1,
                                       vote_start=day + 1, duration=1,
                                       snapshot=15, actions=json.dumps(actions))

            self.governance.activateVote("Enable the dividends")

            launch_time = self.governance._launch_time.get()
            new_day = launch_time + (DAY_ZERO + day + 1) * 10 ** 6 * 60 * 60 * 24
            self.set_block(55, new_day)
            self.governance.castVote("Enable the dividends", True)

            launch_time = self.governance._launch_time.get()
            new_day = launch_time + (DAY_ZERO + day + 4) * 10 ** 6 * 60 * 60 * 24
            self.set_block(55, new_day)
            self.governance.executeVoteAction(1)

