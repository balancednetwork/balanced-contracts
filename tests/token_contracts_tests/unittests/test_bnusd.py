from iconservice import Address
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from token_contracts.bnUSD.bnUSD import BalancedDollar
from token_contracts.bnUSD.utils.checks import SenderNotScoreOwnerError, SenderNotAuthorized, SenderNotGovernance
from token_contracts.bnUSD.tokens.IRC2 import NegativeValueError
from unittest import mock


class TestBNXLM(ScoreTestCase):
    def setUp(self):
        super().setUp()

        # initialize test accounts
        self.owner_address = Address.from_string(f"hx{'1578' * 10}")
        self.admin_address = Address.from_string(f"hx{'12345' * 8}")
        self.oracle_address = Address.from_string(f"hx{'1234' * 10}")
        self.test_account4 = Address.from_string(f"hx{'8457' * 10}")
        self.governance_address = Address.from_string(f"hx{'1434' * 10}")

        account_info = {
            self.owner_address: 10 * 21,
            self.governance_address: 10 ** 21,
            self.owner_address: 10 ** 21,
            self.admin_address: 10 ** 21,
            self.oracle_address: 10 ** 21,
            self.test_account4: 10 ** 21,
        }
        self.initialize_accounts(account_info)

        # create test score
        self.mock_score_address = Address.from_string(f"cx{'1234' * 10}")

        self.score = self.get_score_instance(BalancedDollar, self.owner_address,
                                             score_address=self.mock_score_address,
                                             on_install_params={'_governance': self.governance_address})

    def test_get_peg(self):
        self.assertEqual(self.score._peg.get(), self.score.getPeg())

    def test_set_governance_not_owner(self):
        self.set_msg(self.test_account2)
        try:
            self.score.setGovernance(self.governance_address)
        except SenderNotScoreOwnerError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def _set_governace(self):
        self.set_msg(self.owner_address)
        self.score.setGovernance(self.governance_address)

    def test_set_governance(self):
        self._set_governace()
        self.assertEqual(self.governance_address, self.score._governance.get())

    def test_get_governance(self):
        self._set_governace()
        self.assertEqual(self.score._governance.get(), self.score.getGovernance())

    def test_set_admin_not_governance(self):
        try:
            self.set_msg(self.test_account4)
            self.score.setAdmin(self.admin_address)
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def _set_admin(self):
        self.set_msg(self.governance_address)
        self.score.setAdmin(self.admin_address)

    def test_set_admin(self):
        self._set_admin()
        self.assertEqual(self.admin_address, self.score._admin.get())

    def test_set_oracle_not_governance(self):
        try:
            self.set_msg(self.test_account4)
            self.score.setOracle(self.admin_address)
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def _set_oracle(self):
        self.set_msg(self.governance_address)
        self.score.setOracle(self.oracle_address)

    def test_set_oracle(self):
        self._set_oracle()
        self.assertEqual(self.oracle_address, self.score._oracle_address.get())

    def test_get_oracle(self):
        self._set_oracle()
        self.assertEqual(self.score.getOracle(), self.score._oracle_address.get())

    def test_set_oracle_name_not_governance(self):
        try:
            self.set_msg(self.test_account4)
            self.score.setOracleName(self.admin_address)
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_set_oracle_name(self):
        # TODO: DOES ORACLE NEED TO BE A CONTRACT?
        oracle_name = "oracle__name"
        self.set_msg(self.governance_address)
        self.score.setOracleName(oracle_name)
        self.assertTrue(oracle_name, self.score._oracle_name.get())

    def test_get_oracle_name(self):
        oracle_name = "oracle__name"
        self.set_msg(self.governance_address)
        self.score.setOracleName(oracle_name)
        self.assertTrue(self.score.getOracleName(), self.score._oracle_name.get())

    def test_set_min_interval_not_governance(self):
        try:
            self.set_msg(self.test_account4)
            self.score.setMinInterval(12)
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_set_min_interval(self):
        self.set_msg(self.governance_address)
        self.score.setMinInterval(12)
        self.assertEqual(12, self.score._min_interval.get())

    def test_get_min_interval(self):
        self.set_msg(self.governance_address)
        self.score.setMinInterval(12)
        self.assertEqual(self.score.getMinInterval(), self.score._min_interval.get())

    def test_get_price_update_time(self):
        self.assertEqual(self.score._price_update_time.get(), self.score.getPriceUpdateTime())

    def test_priceInLoop(self):

        mock_obj = MockOracle()
        self.set_block(12, 123123123)
        with mock.patch.object(self.score, "create_interface_score", return_value=mock_obj):
            self.score.priceInLoop()

        price_data = mock_obj.get_reference_data(self.score._peg.get(), "ICX")
        rate = price_data['rate']

        self.assertEqual(rate, self.score._last_price.get())
        self.assertEqual(123123123, self.score._price_update_time.get())

    def test_last_price_in_loop(self):
        mock_obj = MockOracle()
        with mock.patch.object(self.score, "create_interface_score", return_value=mock_obj):
            return_data = self.score.lastPriceInLoop()
        self.assertEqual(597955725813433531, return_data)

    def test_update_asset_value(self):
        mock_obj = MockOracle()

        self.set_block(12, 123123123)
        with mock.patch.object(self.score, "create_interface_score", return_value=mock_obj):
            self.score.update_asset_value()
        price_data = mock_obj.get_reference_data(self.score._peg.get(), "ICX")
        rate = price_data['rate']

        self.assertEqual(rate, self.score._last_price.get())
        self.assertEqual(123123123, self.score._price_update_time.get())

    def test_mint_non_owner(self):
        try:
            self.set_msg(self.test_account2)
            self.score.mint(1)
        except SenderNotAuthorized as err:
            self.assertEqual(str(self.test_account2), str(err))

    def test_mint_negative(self):
        self._set_admin()

        self.set_msg(self.admin_address)
        try:
            self.score.mint(-1)
        except NegativeValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_mint(self):
        self._set_admin()

        pre_mint_balance = self.score.balanceOf(self.admin_address)
        pre_mint_total_supply = self.score.totalSupply()

        self.set_msg(self.admin_address)
        self.score.mint(1)

        post_mint_balance = self.score.balanceOf(self.admin_address)
        post_mint_total_supply = self.score.totalSupply()

        self.assertEqual(pre_mint_balance + 1, post_mint_balance)
        self.assertEqual(pre_mint_total_supply + 1, post_mint_total_supply)

    def test_mint_to_non_owner(self):
        self._set_admin()

        try:
            self.set_msg(self.test_account2)
            self.score.mintTo(self.test_account2, 1)
        except SenderNotAuthorized as err:
            self.assertEqual(str(self.test_account2), str(err))

    def test_mint_to_negative(self):
        self._set_admin()

        self.set_msg(self.admin_address)
        try:
            self.score.mintTo(self.test_account2, -1)
        except NegativeValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_mint_to(self):
        self._set_admin()

        pre_mint_balance = self.score.balanceOf(self.test_account2)
        pre_mint_total_supply = self.score.totalSupply()

        self.set_msg(self.admin_address)
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
        self._set_admin()

        try:
            self.set_msg(self.admin_address)
            self.score.burn(-1)
        except NegativeValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_burn(self):
        self._set_admin()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.admin_address, 10)

        pre_burn_balance = self.score.balanceOf(self.admin_address)
        pre_burn_total_supply = self.score.totalSupply()

        self.set_msg(self.admin_address)
        self.score.burn(1)

        post_burn_balance = self.score.balanceOf(self.admin_address)
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
        self._set_admin()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.admin_address, 10)

        self.set_msg(self.admin_address)
        try:
            self.score.burnFrom(self.test_account2, -1)
        except NegativeValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_burn_from(self):
        self._set_admin()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, 10)

        pre_burn_balance = self.score.balanceOf(self.test_account2)
        pre_burn_total_supply = self.score.totalSupply()

        self.set_msg(self.admin_address)
        self.score.burnFrom(self.test_account2, 1)

        post_burn_balance = self.score.balanceOf(self.test_account2)
        post_burn_total_supply = self.score.totalSupply()

        self.assertEqual(pre_burn_balance - 1, post_burn_balance)
        self.assertEqual(pre_burn_total_supply - 1, post_burn_total_supply)


class MockOracle:

    def get_reference_data(self, _base, _quote):
        if _base == "USD" and _quote == "ICX":
            return {"rate": 597955725813433531, "last_update_base": 1602202275702605,
                    "last_update_quote": 1602202190000000}
        if _base == "DOGE" and _quote == "USD":
            return {"rate": 50784000000000000, "last_update_base": 1616643098000000,
                    "last_update_quote": 1616643311790241}
        if _base == "XLM" and _quote == "USD":
            return {"rate": 360358450000000000, "last_update_base": 1616650080000000,
                    "last_update_quote": 1616650390762201}
