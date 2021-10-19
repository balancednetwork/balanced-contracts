import json
from unittest import mock
from json import JSONDecodeError

from iconservice import Address, IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from core_contracts.governance.utils.checks import SenderNotScoreOwnerError
from iconservice.base.exception import InvalidParamsException
from core_contracts.governance.governance import Governance, ProposalDB
from core_contracts.governance.utils.consts import DAY_ZERO, DAY_START, U_SECONDS_DAY, EXA


class MockClass:
    def __init__(self, balanceOfAt=None, totalSupplyAt=None, totalBalnAt=None, totalStakedBalanceOfAt=None,
                 stakedBalanceOfAt=None, totalSupply=None, stakedBalanceOf=None):
        self._balanceOfAt, self._totalSupplyAt, self._totalBalnAt, self._totalStakedBalanceOfAt = \
            balanceOfAt, totalSupplyAt, totalBalnAt, totalStakedBalanceOfAt
        self._stakedBalanceOfAt = stakedBalanceOfAt
        self._totalSupply = totalSupply
        self._stakedBalanceOf = stakedBalanceOf
        self.callStack = []

    def totalSupply(self):
        return self._totalSupply

    def stakedBalanceOf(self, address):
        return self._stakedBalanceOf

    def transfer(self, to, amount):
        pass

    def setMiningRatio(self, _value: int):
        self.callStack.append(f"setMiningRatio({_value})")

    def setLockingRatio(self, _value: int):
        self.callStack.append(f"setLockingRatio({_value})")

    def setOriginationFee(self, _fee: int):
        self.callStack.append(f"setOriginationFee({_fee})")

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

    def govTransfer(self, _from, _to, _value, _data=None):
        pass

    def addNewDataSource(self, a, b):
        self.callStack.append(f"addNewDataSource({a},{b})")

    def updateBalTokenDistPercentage(self, a):
        self.callStack.append(f"updateBalTokenDistPercentage({a})")

    def disburse(self, recipients, amount):
        pass

    def addAcceptedTokens(self, _token):
        pass


class TestGovernanceUnit(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.mock_score = Address.from_string(f"cx{'1234' * 10}")
        self.governance = self.get_score_instance(Governance, self.test_account1)
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)

        self.governance._time_offset.set(DAY_START + U_SECONDS_DAY * (DAY_ZERO + self.governance._launch_day.get() - 1))

        self.baln = Address.from_string(f"cx{'12345' * 8}")
        self.dex = Address.from_string(f"cx{'15785' * 8}")
        self.bnusd = Address.from_string(f"cx{'13343' * 8}")
        self.rebalancing = Address.from_string(f"cx{'99999' * 8}")
        self.governance.addresses._baln.set(self.baln)
        self.governance.addresses._dex.set(self.dex)
        self.governance.addresses._bnUSD.set(self.bnusd)
        self.governance.addresses._rebalancing.set(self.rebalancing)

    def test_set_vote_duration(self):
        self.set_msg(self.test_account1)

        self.assertFalse(self.governance._vote_duration.get())
        self.governance.setVoteDuration(5)
        self.assertEqual(self.governance.getVoteDuration(), 5)

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

    def test_set_vote_definition_criterion(self):
        self.set_msg(self.test_account1)

        self.assertFalse(self.governance._baln_vote_definition_criterion.get())
        self.governance.setBalnVoteDefinitionCriterion(15)
        self.assertEqual(self.governance.getBalnVoteDefinitionCriterion(), 15)

        # Set value below range.
        with self.assertRaises(IconScoreException) as e:
            self.governance.setBalnVoteDefinitionCriterion(-1)
        self.assertEqual("Basis point must be between 0 and 10000.", e.exception.message)

        # Set value above range.
        with self.assertRaises(IconScoreException) as e:
            self.governance.setBalnVoteDefinitionCriterion(10001)
        self.assertEqual("Basis point must be between 0 and 10000.", e.exception.message)

    def test_create_vote(self):
        self.set_msg(self.test_account1)
        self._set_governance_params()
        day = self.governance.getDay()
        duration = self.governance.getVoteDuration()
        vote_start = day + 1

        # Test define vote method.
        mock_class = MockClass(totalSupply=10000, stakedBalanceOf=100)
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            self.governance.defineVote(name="Just a demo", description='Testing description field',
                                       vote_start=vote_start, snapshot=day,
                                       actions="[{\"enable_dividends\": {}}]")

            expected = {'id': 1, 'name': 'Just a demo', 'proposer': self.governance.msg.sender,
                        'description': 'Testing description field',
                        'majority': 666666666666666667, 'vote snapshot': day,
                        'start day': vote_start, 'end day': vote_start + duration, 'fee_refund_status': False,
                        'actions': "[{\"enable_dividends\": {}}]",
                        'quorum': 400000000000000000, 'for': 0, 'against': 0, 'for_voter_count': 0,
                        'against_voter_count': 0, 'status': 'Active'}

            self.assertEqual(expected, self.governance.checkVote(_vote_index=1))

    def test_execute_vote_actions(self):

        dividends = Address.from_string(f"cx{'12345' * 8}")
        self.governance.addresses._dividends.set(dividends)
        self.patch_internal_method(dividends, "setDistributionActivationStatus", lambda x: x)

        incorrect_actions = json.dumps([{"enableDividends": {"status": True}}])
        correct_actions = json.dumps([{"enableDividends": {}}])
        incorrect_json = "method: enableDividends, params: {'status': True}"

        self.assertRaises(TypeError, self.governance._execute_vote_actions, incorrect_actions)
        try:
            self.governance._execute_vote_actions(correct_actions)
        except TypeError:
            self.fail("Raised type error unexpectedly")

        self.assertRaises(JSONDecodeError, self.governance._execute_vote_actions, incorrect_json)

    def test_conditions_to_define_vote(self):
        self.set_msg(self.test_account1)
        self._set_governance_params()
        day = self.governance.getDay()
        mock_class = MockClass(totalSupply=10000, stakedBalanceOf=100)
        duration = self.governance.getVoteDuration()
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            # Start at or before current day.
            with self.assertRaises(IconScoreException) as start_day_before:
                self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                           vote_start=day, snapshot=day, actions="[{\"enable_dividends\": {}}]")
            self.assertEqual("Vote cannot start at or before the current day.", start_day_before.exception.message)

            # Snapshot less then current day.
            with self.assertRaises(IconScoreException) as snapshot_1:
                self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                           vote_start=day + 1, snapshot=day - 1, actions="[{\"enable_dividends\": {}}]")
            self.assertEqual(f'The reference snapshot must be in the range: [current_day ({day}), '
                             f'start_day - 1 ({day})].', snapshot_1.exception.message)

            # Snapshot larger than or equal to the day of vote start.
            with self.assertRaises(IconScoreException) as snapshot_2:
                self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                           vote_start=day + 1, snapshot=day + 1, actions="[{\"enable_dividends\": {}}]")
            self.assertEqual(f'The reference snapshot must be in the range: [current_day ({day}), '
                             f'start_day - 1 ({day})].', snapshot_2.exception.message)

            with self.assertRaises(IconScoreException) as start_day:
                self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                           vote_start=day,
                                           snapshot=day, actions="[{\"enable_dividends\": {}}]")
            self.assertEqual("Vote cannot start at or before the current day.", start_day.exception.message)

            with self.assertRaises(IconScoreException) as start_day2:
                self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                           vote_start=day - 1,
                                           snapshot=day, actions="[{\"enable_dividends\": {}}]")
            self.assertEqual("Vote cannot start at or before the current day.", start_day2.exception.message)

            with self.assertRaises(IconScoreException) as snapshot:
                self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                           vote_start=day + 1,
                                           snapshot=day + 1, actions="[{\"enable_dividends\": {}}]")
            self.assertEqual(
                f"The reference snapshot must be in the range: [current_day ({day}), start_day - 1 ({day})].",
                snapshot.exception.message)

            # Duplicate use of poll name.
            with self.assertRaises(IconScoreException) as duplicate:
                self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                           vote_start=day + 1,
                                           snapshot=day, actions="[{\"enable_dividends\": {}}]")
                self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                           vote_start=day + 1,
                                           snapshot=day, actions="[{\"enable_dividends\": {}}]")
            self.assertEqual("Poll name Enable the dividends has already been used.", duplicate.exception.message)

            # More actions then allowed.
            with self.assertRaises(IconScoreException) as max_actions:
                self.governance.defineVote(name="Enable the dividends max action",
                                           description='Testing description field',
                                           vote_start=day + 1,
                                           snapshot=day,
                                           actions="[{\"enable_dividends\": {}}, {\"enable_dividends1\": {}}, "
                                                   "{\"enable_dividends2\": {}}, {\"enable_dividends3\": {}}, "
                                                   "{\"enable_dividends4\": {}}, {\"enable_dividends5\": {}}]")
            self.assertEqual("Balanced Governance: Only 5 actions are allowed", max_actions.exception.message)

        # New mock class that does not fulfill baln staking criterion for voteDefinition.
        mock_class = MockClass(totalSupply=2001, stakedBalanceOf=1)
        baln_criterion = self.governance.getBalnVoteDefinitionCriterion()
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            # Not enough baln staked.
            with self.assertRaises(IconScoreException) as balnstaked:
                self.governance.defineVote(name="Enable the dividends 2", description='Testing description field',
                                           vote_start=day + 1, snapshot=day, actions="[{\"enable_dividends\": {}}]")
            self.assertEqual(
                f'User needs at least {baln_criterion / 100}% of total baln supply staked to define a vote.',
                balnstaked.exception.message)

    def test_vote_cycle_complete(self):
        self.set_msg(self.test_account1, 0)
        self._set_governance_params()
        self.set_block(0, 0)
        day = self.governance.getDay()
        mock_class = MockClass(balanceOfAt=1, totalSupplyAt=2, totalBalnAt=3, totalStakedBalanceOfAt=4,
                               stakedBalanceOfAt=5, totalSupply=1000, stakedBalanceOf=100)
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            self.governance.defineVote(name="Enable the dividends", description="Count pool BALN",
                                       vote_start=day + 1, snapshot=day, actions="[{\"enable_dividends\": {}}]")
            self.assertEqual("Active", self.governance.checkVote(1).get("status"))

            with self.assertRaises(IconScoreException) as inactive_poll:
                self.governance.castVote(1, True)
            self.assertEqual("That is not an active poll.", inactive_poll.exception.message)

            launch_time = self.governance._launch_time.get()
            new_day = launch_time + (DAY_ZERO + day + 2) * 10 ** 6 * 60 * 60 * 24
            self.set_block(55, new_day)
            self.governance.castVote(1, True)

            self.set_block(55, 0)
            self.governance.defineVote(name="Enable the dividends cancel this", description="Count pool BALN",
                                       vote_start=day + 1, snapshot=day, actions="[{\"enable_dividends\": {}}]")
            vote_index = self.governance.getVoteIndex("Enable the dividends cancel this")
            try:
                self.governance.cancelVote(vote_index)
            except IconScoreException:
                self.fail("Fail to cancel the vote")
            self.assertEqual("Cancelled", self.governance.checkVote(2).get("status"))

    def test_proposal_count(self):
        self.set_msg(self.test_account1)
        self._set_governance_params()

        day = self.governance.getDay()
        mock_class = MockClass(totalSupply=10000, stakedBalanceOf=100)

        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                       vote_start=day + 1, snapshot=day, actions="[{\"enable_dividends\": {}}]")
            self.governance.defineVote(name="Enable the dividends2", description='Testing description field',
                                       vote_start=day + 1, snapshot=day, actions="[{\"enable_dividends\": {}}]")
            self.governance.defineVote(name="Enable the dividends3", description='Testing description field',
                                       vote_start=day + 1, snapshot=day, actions="[{\"enable_dividends\": {}}]")

            self.assertEqual(3, self.governance.getProposalCount(), "Failed to create three proposals")

    def test_get_pool_baln(self):

        dex_score = Address.from_string(f"cx{'2578' * 10}")

        self.governance.addresses._dex.set(dex_score)
        mock_class = MockClass(balanceOfAt=10, totalSupplyAt=20, totalBalnAt=30)
        with mock.patch.object(self.governance, "create_interface_score", wraps=mock_class.patch_internal):
            result = self.governance._get_pool_baln(_account=self.test_account3, _day=1)
        self.assertEqual(2 * (10 * 30 / 20), result)

        mock_class = MockClass(balanceOfAt=0, totalSupplyAt=0, totalBalnAt=0)
        with mock.patch.object(self.governance, "create_interface_score", wraps=mock_class.patch_internal):
            result = self.governance._get_pool_baln(_account=self.test_account3, _day=1)
        self.assertEqual(0, result)

    def test_totalBaln(self):
        mock_class = MockClass(balanceOfAt=10, totalSupplyAt=20, totalBalnAt=30, totalStakedBalanceOfAt=12)
        with mock.patch.object(self.governance, "create_interface_score", wraps=mock_class.patch_internal):
            result = self.governance.totalBaln(1)
        self.assertEqual(2 * 30 + 12, result)

    def test_vote_actions(self):
        self.set_msg(self.test_account1, 0)
        self.set_block(0, 0)
        self._set_governance_params()

        duration = self.governance._vote_duration.get()
        day = self.governance.getDay()
        mock_class = MockClass(totalSupply=1000, stakedBalanceOf=10, balanceOfAt=1, totalSupplyAt=2, totalBalnAt=3,
                               totalStakedBalanceOfAt=4,
                               stakedBalanceOfAt=5)
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            actions = [{"addNewDataSource": {"_data_source_name": "test1", "_contract_address": f"cx{'37845' * 8}"}},
                       {"updateBalTokenDistPercentage": {
                           "_recipient_list": [{"recipient_name": "", "dist_percent": 12}]}},
                       {"setMiningRatio": {"_value": 20}},
                       {"setLockingRatio": {"_value": 10}},
                       {"setOriginationFee": {"_fee": 1}
                        }]
            self.governance.defineVote(name="Test add data source", description="Count pool BALN",
                                       vote_start=day + 1,
                                       snapshot=day, actions=json.dumps(actions))

            # self.governance.activateVote("Test add data source")

            launch_time = self.governance._launch_time.get()
            new_day = launch_time + (day + DAY_ZERO + 1) * 10 ** 6 * 60 * 60 * 24
            self.set_block(55, new_day)
            self.governance.castVote(1, True)

            launch_time = self.governance._launch_time.get()
            new_day = launch_time + (DAY_ZERO + day + duration + 2) * 10 ** 6 * 60 * 60 * 24
            self.set_block(55, new_day)
            self.governance.evaluateVote(1)
            expected = ['addNewDataSource(test1,cx3784537845378453784537845378453784537845)',
                        "updateBalTokenDistPercentage([{'recipient_name': '', 'dist_percent': 12}])",
                        'setMiningRatio(20)', 'setLockingRatio(10)', 'setOriginationFee(1)']
            self.assertListEqual(expected, mock_class.callStack)

    def test_refund_vote_definition_fee(self):
        self.set_msg(self.test_account1)
        self._set_governance_params()

        day = self.governance.getDay()
        mock_class = MockClass(totalSupply=10000, stakedBalanceOf=100)

        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            self.governance.defineVote(name="Enable the dividends", description='Testing description field',
                                       vote_start=day + 1, snapshot=day, actions="[{\"enable_dividends\": {}}]")
            proposal = ProposalDB(1, self.governance.db)
            self.assertEqual(proposal.fee_refunded.get(), False)
            self.governance._refund_vote_definition_fee(proposal)
            self.assertEqual(proposal.fee_refunded.get(), True)

    def test_scoreUpdate_13(self):
        self.governance.scoreUpdate_13()
        self.assertEqual(self.governance.getQuorum(), 20)
        self.assertEqual(self.governance.getVoteDefinitionFee(), 100 * EXA)
        self.assertEqual(self.governance.getVoteDuration(), 5)
        self.assertEqual(self.governance.getBalnVoteDefinitionCriterion(), 10)

    def _set_governance_params(self, quorum=40, min_vote_dur=5, vote_def_fee=100 * EXA, baln_vote_def_criterion=5):
        self.governance.setQuorum(quorum)
        self.governance.setVoteDuration(min_vote_dur)
        self.governance.setVoteDefinitionFee(vote_def_fee)
        self.governance.setBalnVoteDefinitionCriterion(baln_vote_def_criterion)

    def test_score_update_11(self):
        self.set_msg(self.test_account1)
        self._set_governance_params()
        day = self.governance.getDay()
        mock_class = MockClass(balanceOfAt=1, totalSupplyAt=1, totalBalnAt=1, totalStakedBalanceOfAt=1, totalSupply=1,
                               stakedBalanceOf=1)
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            self.governance.defineVote(name="Just a demo", description='Testing description field',
                                       vote_start=day + 2, snapshot=day, actions="[{\"enableDividends\": {}}]")
            self.governance.scoreUpdate_11()
            name = self.governance.checkVote(1).get("name")
            self.assertEqual(name, "BIP1: Activate network fee distribution")

    def test_my_voting_weight(self):
        mock_class = MockClass(balanceOfAt=1, totalSupplyAt=2, totalBalnAt=3, totalStakedBalanceOfAt=4,
                               stakedBalanceOfAt=5)
        with mock.patch.object(self.governance, "create_interface_score", wraps=mock_class.patch_internal):
            vote = self.governance.myVotingWeight(self.test_account1, 1)
            self.assertEqual((2 * (1 * 3 // 2) + 5), vote)

    def test_addDataSource(self):
        mock_class = MockClass(balanceOfAt=1, totalSupplyAt=2, totalBalnAt=3, totalStakedBalanceOfAt=4,
                               stakedBalanceOfAt=5)
        with self.assertRaises(SenderNotScoreOwnerError) as err:
            self.governance.addNewDataSource("source", "cx122233")
        self.assertEqual(str(self.test_account1), str(err.exception))

        self.set_msg(self.test_account1)
        with mock.patch.object(self.governance, "create_interface_score", wraps=mock_class.patch_internal):
            with self.assertRaises(InvalidParamsException) as err:
                self.governance.addNewDataSource("source", "cx12223")
        self.assertEqual("Invalid address", str(err.exception.message))

        # testing address parameter given as string in addNewDataSource

        with mock.patch.object(self.governance, "create_interface_score", wraps=mock_class.patch_internal):
            self.governance.addNewDataSource("source", f"cx{'37845' * 8}")

        self.assertListEqual(['addNewDataSource(source,cx3784537845378453784537845378453784537845)'],
                             mock_class.callStack)

        # testing address parameter given as address in addNewDataSource
        with mock.patch.object(self.governance, "create_interface_score", wraps=mock_class.patch_internal):
            with self.assertRaises(InvalidParamsException) as err:
                self.governance.addNewDataSource("source", Address.from_string(f"cx{'37845' * 8}"))
        self.assertEqual("Invalid address", str(err.exception.message))

    def test_score_update_14(self):
        self.set_msg(self.test_account1)
        self._set_governance_params()
        day = self.governance.getDay()
        mock_class = MockClass(balanceOfAt=1, totalSupplyAt=1, totalBalnAt=1, totalStakedBalanceOfAt=1, totalSupply=1,
                               stakedBalanceOf=1, stakedBalanceOfAt=1)
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            for i in range(5):
                self.governance.defineVote(name=f"{i}Just a demo", description='Testing description field',
                                           vote_start=day + 1, snapshot=day, actions="[{\"enableDividends\": {}}]")

            previous_value = "[{\"enableDividends\": {}}]"
            previous_action = self.governance.checkVote(5).get("actions")
            self.assertEqual(previous_value, previous_action)

            self.governance.scoreUpdate_14()

            launch_time = self.governance._launch_time.get()
            new_day = launch_time + (day + DAY_ZERO + 2) * 10 ** 6 * 60 * 60 * 24
            self.set_block(55, new_day)

            self.governance.castVote(5, True)

            new_day = launch_time + (day + DAY_ZERO + 10) * 10 ** 6 * 60 * 60 * 24
            self.set_block(55, new_day)
            self.governance.evaluateVote(5)
            action = self.governance.checkVote(5).get("actions")
            expected = json.dumps({"addNewDataSource": {"_data_source_name": "IUSDC/bnUSD",
                                                        "_contract_address": "cxa0af3165c08318e988cb30993b3048335b94af6c"},
                                   "updateBalTokenDistPercentage": {
                                       "_recipient_list": [
                                           {"recipient_name": "Loans", "dist_percent": 100000000000000000},
                                           {"recipient_name": "sICX/ICX", "dist_percent": 70000000000000000},
                                           {"recipient_name": "sICX/bnUSD", "dist_percent": 175000000000000000},
                                           {"recipient_name": "BALN/bnUSD", "dist_percent": 175000000000000000},
                                           {"recipient_name": "BALN/sICX", "dist_percent": 50000000000000000},
                                           {"recipient_name": "IUSDC/bnUSD", "dist_percent": 5000000000000000},
                                           {"recipient_name": "Worker Tokens", "dist_percent": 200000000000000000},
                                           {"recipient_name": "Reserve Fund", "dist_percent": 25000000000000000},
                                           {"recipient_name": "DAOfund", "dist_percent": 200000000000000000}]}})
            self.assertEqual(expected, action)

    def test_dao_disburse(self):
        _recepient = 'cx3784537845378453784537845378453784537845'
        _amount = [{'address': 'cx3784537845378453784537845378453784537845', 'amount': 10 * 10 ** 18},
                   {'address': 'cx3784537845378453784537845378453784537845', 'amount': 10 * 10 ** 18},
                   {'address': 'cx3784537845378453784537845378453784537845', 'amount': 10 * 10 ** 18},
                   {'address': 'cx3784537845378453784537845378453784537845', 'amount': 10 * 10 ** 18}]
        with self.assertRaises(IconScoreException) as err:
            self.governance.daoDisburse(_recepient, _amount)
        self.assertEqual('Cannot disburse more than 3 assets at a time.', err.exception.message)

        mock_class = MockClass(balanceOfAt=1, totalSupplyAt=1, totalBalnAt=1, totalStakedBalanceOfAt=1, totalSupply=1,
                               stakedBalanceOf=1, stakedBalanceOfAt=1)
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            _recepient = 'cx3784537845378453784537845378453784537845'
            _amount = [{'address': 'cx3784537845378453784537845378453784537845', 'amount': 10 * 10 ** 18},
                       {'address': 'cx3784537845378453784537845378453784537845', 'amount': 10 * 10 ** 18},
                       {'address': 'cx3784537845378453784537845378453784537845', 'amount': 10 * 10 ** 18}]
            self.governance.daoDisburse(_recepient, _amount)

    def test_addAcceptedTokens(self):
        self.set_msg(self.test_account1)
        mock_class = MockClass(balanceOfAt=1, totalSupplyAt=1, totalBalnAt=1, totalStakedBalanceOfAt=1, totalSupply=1,
                               stakedBalanceOf=1, stakedBalanceOfAt=1)
        with mock.patch.object(self.governance, "create_interface_score", mock_class.patch_internal):
            _token = 'cx3784537845378453784537845378453784537845'
            self.governance.addAcceptedTokens(_token)

    def test_getAddresses(self):
        addresses = self.governance.getAddresses()
        self.assertEqual('cx9999999999999999999999999999999999999999', str(addresses['rebalancing']))
