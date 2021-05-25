from iconservice import Address
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from token_contracts.sicx.sicx import StakedICX
from token_contracts.sicx.utils.checks import SenderNotScoreOwnerError, SenderNotAuthorized
from token_contracts.sicx.tokens.IRC2 import ZeroValueError


class TestSICX(ScoreTestCase):
    def setUp(self):
        super().setUp()

        # initialize test accounts
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        self.owner_address = Address.from_string(f"hx{'1589' * 10}")
        account_info = {
            self.owner_address: 10 ** 21,
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)

        # create test score
        self.mock_score_address = Address.from_string(f"cx{'1234' * 10}")
        self.score = self.get_score_instance(StakedICX, self.owner_address,
                                             score_address=self.mock_score_address,
                                             on_install_params={'_admin': self.test_account3})

    def test_get_peg(self):
        peg = self.score.getPeg()
        self.assertEqual(self.score._peg.get(), peg)

    def test_set_staking_address_non_owner(self):
        try:
            self.set_tx(self.test_account2)
            self.score.setStakingAddress(Address.from_string(f"cx{'9876' * 10}"))
        except SenderNotScoreOwnerError as err:
            self.assertNotEqual(self.test_account2, err)

    def _set_staking_address(self):
        self.set_msg(self.owner_address)
        self.score.setStakingAddress(self.test_account2)

    def test_set_staking_address(self):
        self._set_staking_address()
        self.assertEqual(self.score._staking_address.get(), self.test_account2)

    def test_get_staking_address(self):
        self._set_staking_address()
        self.assertEqual(self.score.getStakingAddress(), self.test_account2)

    def test_mint_non_owner(self):
        try:
            self.set_msg(self.test_account2)
            self.score.mint(1)
        except SenderNotAuthorized as err:
            self.assertEqual(str(self.test_account2), str(err))

    def test_mint_negative(self):
        self.set_msg(self.test_account3)
        try:
            self.score.mint(-1)
        except ZeroValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_mint(self):
        pre_mint_balance = self.score.balanceOf(self.test_account3)
        pre_mint_total_supply = self.score.totalSupply()

        self.set_msg(self.test_account3)
        self.score.mint(1)

        post_mint_balance = self.score.balanceOf(self.test_account3)
        post_mint_total_supply = self.score.totalSupply()

        self.assertEqual(pre_mint_balance + 1, post_mint_balance)
        self.assertEqual(pre_mint_total_supply + 1, post_mint_total_supply)

    def test_mint_to_non_owner(self):
        try:
            self.set_msg(self.test_account2)
            self.score.mintTo(self.test_account2, 1)
        except SenderNotAuthorized as err:
            self.assertEqual(str(self.test_account2), str(err))

    def test_mint_to_negative(self):
        self.set_msg(self.test_account3)
        try:
            self.score.mintTo(self.test_account2, -1)
        except ZeroValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_mint_to(self):
        pre_mint_balance = self.score.balanceOf(self.test_account2)
        pre_mint_total_supply = self.score.totalSupply()

        self.set_msg(self.test_account3)
        self.score.mintTo(self.test_account2, 1)

        post_mint_balance = self.score.balanceOf(self.test_account2)
        post_mint_total_supply = self.score.totalSupply()

        self.assertEqual(pre_mint_balance + 1, post_mint_balance)
        self.assertEqual(pre_mint_total_supply + 1, post_mint_total_supply)

    def test_burn_non_owner(self):
        try:
            self.set_msg(self.test_account2)
            self.score.burn(1)
        except SenderNotAuthorized as err:
            self.assertEqual(str(self.test_account2), str(err))

    def test_burn_negative(self):
        try:
            self.set_msg(self.test_account3)
            self.score.burn(-1)
        except ZeroValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_burn(self):
        pre_burn_balance = self.score.balanceOf(self.test_account3)
        pre_burn_total_supply = self.score.totalSupply()

        self.set_msg(self.test_account3)
        self.score.burn(1)

        post_burn_balance = self.score.balanceOf(self.test_account3)
        post_burn_total_supply = self.score.totalSupply()

        self.assertEqual(pre_burn_balance - 1, post_burn_balance)
        self.assertEqual(pre_burn_total_supply - 1, post_burn_total_supply)

    def test_burn_from_non_owner(self):
        try:
            self.set_msg(self.test_account2)
            self.score.burnFrom(self.test_account2, 1)
        except SenderNotAuthorized as err:
            self.assertEqual(str(self.test_account2), str(err))

    def test_burn_from_negative(self):
        self.set_msg(self.test_account3)
        try:
            self.score.burnFrom(self.test_account2, -1)
        except ZeroValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_burn_from(self):
        pre_burn_balance = self.score.balanceOf(self.test_account2)
        pre_burn_total_supply = self.score.totalSupply()

        self.set_msg(self.test_account3)
        self.score.burnFrom(self.test_account2, 1)

        post_burn_balance = self.score.balanceOf(self.test_account2)
        post_burn_total_supply = self.score.totalSupply()

        self.assertEqual(pre_burn_balance - 1, post_burn_balance)
        self.assertEqual(pre_burn_total_supply - 1, post_burn_total_supply)
