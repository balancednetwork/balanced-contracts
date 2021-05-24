from unittest import mock

from iconservice import *
from iconservice.base.exception import IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from token_contracts.bwt.worker_token import WorkerToken
from token_contracts.bwt.utils.checks import SenderNotScoreOwnerError, SenderNotAuthorized, SenderNotGovernance


class Mock:
    logs = {}

    def balanceOf(self, address):
        return 10 ** 24

    def transfer(self, address, amount):
        self.logs[address] = amount


class TestBWT(ScoreTestCase):
    def setUp(self):
        super().setUp()

        # initialize test accounts
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 * 10 ** 18,
            self.test_account4: 10 * 10 ** 18}
        self.initialize_accounts(account_info)
        # create test score
        self.governance_address = Address.from_string(f"cx{'2348' * 10}")

        self.admin_address = self.test_account3
        self.mock_score_address = Address.from_string(f"cx{'1234' * 10}")
        self.score = self.get_score_instance(WorkerToken, self.test_account1,
                                             score_address=self.mock_score_address,
                                             on_install_params={'_governance': self.governance_address})

    def test_set_governance_not_owner(self):
        try:
            self.score.setGovernance(self.governance_address)
        except SenderNotScoreOwnerError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_set_governance_not_contract(self):
        try:
            self.set_msg(self.test_account1)
            self.score.setGovernance(self.governance_address)
        except IconScoreException as err:
            self.assertIn("BALW: Address provided is an EOA address. A contract address is required.", str(err))

    def test_set_governance(self):
        self.set_msg(self.test_account1)
        self.score.setGovernance(self.governance_address)
        self.assertEqual(self.governance_address, self.score._governance.get())

    def test_get_governance(self):
        self.set_msg(self.test_account1)
        self.score.setGovernance(self.governance_address)
        self.assertEqual(self.governance_address, self.score.getGovernance())

    def test_set_admin_sender_not_governance(self):
        try:
            self.score.setAdmin(self.admin_address)
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_set_admin(self):

        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

        self.assertEqual(self.admin_address, self.score._admin.get())

    def test_set_baln_not_authorized(self):

        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

        # self.set_msg(self.test_account2)
        baln_address = Address.from_string(f"cx{'1234' * 10}")
        try:
            self.score.setBaln(baln_address)
        except SenderNotAuthorized:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_set_baln(self):
        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

        self.set_msg(self.admin_address)
        baln_address = Address.from_string(f"cx{'1234' * 10}")
        self.score.setBaln(baln_address)

        self.assertEqual(baln_address, self.score._baln_token.get())

    def test_get_baln(self):

        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

        self.set_msg(self.admin_address)
        baln_address = Address.from_string(f"cx{'1234' * 10}")
        self.score.setBaln(baln_address)

        self.assertEqual(self.score._baln_token.get(), self.score.getBaln())

    def test_admin_transfer_non_owner(self):

        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

        self.set_msg(self.test_account4)
        try:
            self.score.adminTransfer(_from=self.test_account1, _to=self.test_account4, _value=10)
        except SenderNotAuthorized:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_admin_transfer(self):

        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

        pre_balance_from = self.score.balanceOf(self.test_account1)
        pre_balance_to = self.score.balanceOf(self.test_account4)

        self.set_msg(self.admin_address)
        self.score.adminTransfer(_from=self.test_account1, _to=self.test_account4, _value=10)

        post_balance_from = self.score.balanceOf(self.test_account1)
        post_balance_to = self.score.balanceOf(self.test_account4)

        self.assertEqual(pre_balance_from - 10, post_balance_from)
        self.assertEqual(pre_balance_to + 10, post_balance_to)

    def test_distribute(self):

        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

        transfer_amount = int(self.score.balanceOf(self.test_account1) * 0.25)

        self.set_msg(self.admin_address)
        self.score.adminTransfer(_from=self.test_account1, _to=self.test_account4,
                                 _value=transfer_amount)

        mock_object = Mock()
        with mock.patch.object(self.score, "create_interface_score",
                               wraps=self.score.create_interface_score,
                               return_value=mock_object):
            self.score.distribute()
        self.assertEqual(750000000000000000000000, mock_object.logs[self.test_account1])
        self.assertEqual(250000000000000000000000, mock_object.logs[self.test_account4])

    def test_token_fallback_non_baln(self):

        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

        self.set_msg(self.admin_address)
        baln_address = Address.from_string(f"cx{'1234' * 10}")
        self.score.setBaln(baln_address)

        self.set_msg(self.test_account1)
        try:
            self.score.tokenFallback(None, 1, None)
        except IconScoreException as err:
            self.assertIn("The Worker Token contract can only accept BALN tokens.", str(err))
        else:
            self.assertTrue(False)

    def test_token_fallback(self):

        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

        self.set_msg(self.admin_address)
        baln_address = Address.from_string(f"cx{'1234' * 10}")
        self.score.setBaln(baln_address)

        self.set_msg(baln_address)
        pre_value = self.score._baln.get()
        self.score.tokenFallback(None, 1, None)
        self.assertEqual(pre_value + 1, self.score._baln.get())
