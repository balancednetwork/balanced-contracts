import time

from iconservice import Address
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

    def test_create_proposal(self):
        self.set_msg(self.test_account1)
        day = self.governance.getDay()
        print(day)
        self.governance.defineVote(name="Just a demo", quorum=40, vote_start=day + 2, duration=2, snapshot=30,
                                   actions="hello")
        baln = Address.from_string(f"cx{'12345'*8}")
        self.governance.addresses._baln.set(baln)
        self.patch_internal_method(baln, "totalStakedBalanceOfAt", lambda x: 500)
        expected = {'id': 1, 'name': 'Just a demo', 'majority': 66666666666666667, 'vote snapshot': 30,
                    'start day': 150, 'end day': 152, 'actions': 'hello', 'quorum': 400000000000000000, 'for': 0,
                    'against': 0, 'result': 'Pending'}
        self.assertEqual(expected, self.governance.checkVote(_vote_index=1))
