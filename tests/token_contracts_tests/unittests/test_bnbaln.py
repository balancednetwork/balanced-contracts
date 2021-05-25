from iconservice import Address
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from token_contracts.baln.utils.consts import Status
from iconservice.base.exception import IconScoreException
from token_contracts.baln.balance import BalancedToken, EXA
from token_contracts.baln.utils.checks import SenderNotScoreOwnerError, SenderNotAuthorized, SenderNotGovernance
from token_contracts.baln.tokens.IRC2 import ZeroValueError
from unittest import mock


class TestBNXLM(ScoreTestCase):
    def setUp(self):
        super().setUp()

        # initialize test accounts
        self.owner_address = Address.from_string(f"hx{'5842' * 10}")
        self.governance_address = Address.from_string(f"hx{'5862' * 10}")
        self.admin_address = Address.from_string(f"hx{'12345' * 8}")
        self.oracle_address = Address.from_string(f"hx{'1234' * 10}")
        self.bnusd_address = Address.from_string(f"hx{'1434' * 10}")
        self.dex_address = Address.from_string(f"hx{'7586' * 10}")
        self.dividends_address = Address.from_string(f"hx{'5219' * 10}")

        account_info = {
            self.dividends_address: 10 ** 21,
            self.owner_address: 10 ** 21,
            self.governance_address: 10 ** 21,
            self.admin_address: 10 ** 21,
            self.oracle_address: 10 ** 21,
            self.bnusd_address: 10 ** 21,
            self.dex_address: 10 ** 21
        }
        self.initialize_accounts(account_info)

        # create test score
        self.mock_score_address = Address.from_string(f"cx{'1234' * 10}")

        self.score = self.get_score_instance(BalancedToken, self.owner_address,
                                             score_address=self.mock_score_address,
                                             on_install_params={'_governance': self.governance_address})

    def test_get_peg(self):
        self.assertEqual("BALN", self.score.getPeg())

    def test_set_governance_not_owner(self):
        self.set_msg(self.test_account2)
        try:
            self.score.setGovernance(self.governance_address)
        except SenderNotScoreOwnerError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def _set_governance(self):
        self.set_msg(self.owner_address)
        self.score.setGovernance(self.governance_address)

    def test_set_governance(self):
        self._set_governance()
        self.assertEqual(self.governance_address, self.score._governance.get())

    def test_get_governance(self):
        self._set_governance()
        self.assertEqual(self.score._governance.get(), self.score.getGovernance())

    def test_set_bn_usd_not_governance(self):
        try:
            self.score.setbnUSD(self.bnusd_address)
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def _set_bn_usd(self):
        self.set_msg(self.governance_address)
        self.score.setbnUSD(self.bnusd_address)

    def test_set_bn_usd(self):
        self._set_governance()
        self._set_bn_usd()

        self.assertEqual(self.bnusd_address, self.score._bnusd_score.get())

    def test_get_bn_usd(self):
        self._set_governance()
        self._set_bn_usd()

        self.assertEqual(self.score._bnusd_score.get(), self.score.getbnUSD())

    def test_set_admin_not_governance(self):
        try:
            self.set_msg(self.test_account2)
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
            self.set_msg(self.test_account2)
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
        self.assertEqual(self.oracle_address, self.score._oracle.get())

    def test_get_oracle(self):
        self._set_oracle()
        self.assertEqual(self.score.getOracle(), self.score._oracle.get())

    def test_set_oracle_name_not_governance(self):
        try:
            self.set_msg(self.test_account2)
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
            self.set_msg(self.test_account2)
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

    def test_set_dex_not_governance(self):
        try:
            self.score.setDex(self.dex_address)
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def _set_dex(self):
        self.set_msg(self.governance_address)
        self.score.setDex(self.dex_address)

    def test_set_dex(self):
        self._set_dex()
        self.assertTrue(self.dex_address, self.score._dex_score.get())

    def test_get_dex(self):
        self._set_dex()
        self.assertTrue(self.score._dex_score.get(), self.score.getDex())

    def test_priceInLoop(self):
        self._set_dex()
        self._set_oracle()

        mock_object = CreateMockObject(self.dex_address, self.oracle_address)
        self.set_block(12, 123123123)

        with mock.patch.object(self.score, "create_interface_score", wraps=mock_object.create):
            self.score.priceInLoop()

        dex_price = mock_object.create(self.dex_address, None).getBalnPrice()
        price_data = mock_object.create(self.oracle_address, None).get_reference_data('USD', 'ICX')

        last_price = price_data['rate'] * dex_price // EXA

        self.assertEqual(last_price, self.score._last_price.get())
        self.assertEqual(123123123, self.score._price_update_time.get())

    def test_last_price_in_loop(self):
        self._set_dex()
        self._set_oracle()

        mock_object = CreateMockObject(self.dex_address, self.oracle_address)
        self.set_block(12, 123123123)

        with mock.patch.object(self.score, "create_interface_score", wraps=mock_object.create):
            return_data = self.score.lastPriceInLoop()
        self.assertEqual(59, return_data)

    def test_update_asset_value(self):
        self._set_dex()
        self._set_oracle()

        mock_object = CreateMockObject(self.dex_address, self.oracle_address)
        self.set_block(12, 123123123)

        with mock.patch.object(self.score, "create_interface_score", wraps=mock_object.create):
            self.score.update_asset_value()

        dex_price = mock_object.create(self.dex_address, None).getBalnPrice()
        price_data = mock_object.create(self.oracle_address, None).get_reference_data('USD', 'ICX')

        last_price = price_data['rate'] * dex_price // EXA

        self.assertEqual(last_price, self.score._last_price.get())
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
        except ZeroValueError:
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
        except ZeroValueError:
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

        self.score.mintTo(self.test_account2, 1)
        try:
            self.set_msg(self.test_account2)
            self.score.burn(1)
        except SenderNotAuthorized as err:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_burn_negative(self):
        self._set_admin()

        try:
            self.set_msg(self.admin_address)
            self.score.burn(-1)
        except ZeroValueError:
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
        self.score.mintTo(self.test_account2, 2)

        try:
            self.set_msg(self.test_account2)
            self.score.burnFrom(self.test_account2, 1)
        except SenderNotAuthorized:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_burn_from_negative(self):
        self._set_admin()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.admin_address, 10)

        self.set_msg(self.admin_address)
        try:
            self.score.burnFrom(self.test_account2, -1)
        except ZeroValueError:
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

    def test_set_unstaking_period_not_governance(self):
        try:
            self.score.setUnstakingPeriod()
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_set_unstaking_period_negative(self):
        self._set_governance()
        self.set_msg(self.governance_address)
        try:
            self.score.setUnstakingPeriod(-1)
        except IconScoreException as err:
            self.assertIn("BALN: Time cannot be negative.", str(err))

    def test_set_unstaking_period(self):
        self._set_governance()
        self.set_msg(self.governance_address)
        self.score.setUnstakingPeriod(1)
        self.assertEqual(1 * 864 * 10 ** 8, self.score._unstaking_period.get())

    def test_get_unstaking_period(self):
        result = self.score.getUnstakingPeriod()
        self.assertEqual(self.score._unstaking_period.get() / (864 * 10 ** 8),
                         result)

    def test_set_minimum_stake_not_governance(self):
        try:
            self.score.setMinimumStake()
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_set_minimum_stake_negative(self):
        self.set_msg(self.governance_address)
        try:
            self.score.setMinimumStake(-1)
        except IconScoreException as err:
            self.assertIn("BALN: Amount cannot be less than zero.", str(err))

    def test_set_minimum_stake(self):
        self.set_msg(self.governance_address)
        self.score.setMinimumStake(1)
        self.assertEqual(1 * 10 ** self.score._decimals.get(), self.score._minimum_stake.get())

    def test_get_minimum_stake(self):
        self.set_msg(self.governance_address)
        self.score.setMinimumStake(1)
        self.assertEqual(self.score._minimum_stake.get(), self.score.getMinimumStake())

    def test_toggle_staking_enabled_not_governance(self):
        try:
            self.score.toggleStakingEnabled()
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_toggle_staking_enabled(self):
        staking_flag = self.score.getStakingEnabled()
        self._toggle_staking_enabled()
        self.assertEqual(not staking_flag, self.score._staking_enabled.get())

    def test_set_stake_update_db_not_dividents(self):
        self._toggle_staking_enabled()
        try:
            self.score.switchStakeUpdateDB()
        except IconScoreException as err:
            self.assertIn("BALN: This method can only be called by the dividends distribution contract.",
                          str(err))

    def test_set_stake_update_db_not_staking(self):
        self._set_dividends()
        try:
            self.set_msg(self.dividends_address)
            self.score.switchStakeUpdateDB()
        except IconScoreException as err:
            self.assertIn("BALN: Staking must first be enabled.",
                          str(err))

    def test_get_staking_enabled(self):
        result = self.score.getStakingEnabled()
        self.assertEqual(self.score._staking_enabled.get(), result)

    def test_set_dividends_not_governance(self):
        try:
            self.score.setDividends()
        except SenderNotGovernance:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def _set_dividends(self):
        self.set_msg(self.governance_address)
        self.score.setDividends(self.dividends_address)

    def test_set_dividends_not_governance(self):
        self._set_dividends()
        self.assertEqual(self.dividends_address, self.score._dividends_score.get())

    def test_get_dividends(self):
        self.score.getDividends()

    def test_details_balance_of_single_stake(self):
        self._toggle_staking_enabled()
        self._set_admin()

        _balance = 120 * 10 ** 18

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, _balance)

        self.set_msg(self.test_account2)

        stake_amount = 12 * 10 ** 18
        self._stake(self.test_account2, stake_amount, 1)

        result = self.score.detailsBalanceOf(self.test_account2)

        self.assertEqual(_balance, result["Total balance"])
        self.assertEqual(_balance - stake_amount, result["Available balance"])
        self.assertEqual(stake_amount, result["Staked balance"])
        self.assertEqual(0, result["Unstaking balance"])
        self.assertEqual(0, result["Unstaking time (in microseconds)"])

        self.assertEqual(0, self.score.unstakedBalanceOf(self.test_account2))
        self.assertEqual(stake_amount, self.score.stakedBalanceOf(self.test_account2))
        self.assertEqual(_balance - stake_amount, self.score.availableBalanceOf(self.test_account2))

    def test_details_balance_of_incremental_stake(self):
        self._toggle_staking_enabled()
        self._set_admin()

        _balance = 120 * 10 ** 18

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, _balance)

        self.set_msg(self.test_account2)

        stake_amount_1 = 12 * 10 ** 18
        self._stake(self.test_account2, stake_amount_1, 1)
        stake_amount_2 = 20 * 10 ** 18
        self._stake(self.test_account2, stake_amount_2, 2)

        result = self.score.detailsBalanceOf(self.test_account2)

        self.assertEqual(_balance, result["Total balance"])
        self.assertEqual(_balance - stake_amount_2, result["Available balance"])
        self.assertEqual(stake_amount_2, result["Staked balance"])
        self.assertEqual(0, result["Unstaking balance"])
        self.assertEqual(0, result["Unstaking time (in microseconds)"])

        self.assertEqual(0, self.score.unstakedBalanceOf(self.test_account2))
        self.assertEqual(stake_amount_2, self.score.stakedBalanceOf(self.test_account2))
        self.assertEqual(_balance - stake_amount_2, self.score.availableBalanceOf(self.test_account2))

    def test_details_balance_of_decremental_stake(self):
        self._toggle_staking_enabled()
        self._set_admin()

        _balance = 120 * 10 ** 18

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, _balance)

        self.set_msg(self.test_account2)

        stake_amount_1 = 20 * 10 ** 18
        self._stake(self.test_account2, stake_amount_1, 1)
        stake_amount_2 = 12 * 10 ** 18
        self._stake(self.test_account2, stake_amount_2, 2)

        result = self.score.detailsBalanceOf(self.test_account2)

        self.assertEqual(_balance, result["Total balance"])
        self.assertEqual(_balance - stake_amount_1, result["Available balance"])
        self.assertEqual(stake_amount_2, result["Staked balance"])
        self.assertEqual(stake_amount_1 - stake_amount_2, result["Unstaking balance"])
        self.assertEqual(self.score._staked_balances[self.test_account2][Status.UNSTAKING_PERIOD],
                         result["Unstaking time (in microseconds)"])

        self.assertEqual(stake_amount_1 - stake_amount_2, self.score.unstakedBalanceOf(self.test_account2))
        self.assertEqual(stake_amount_2, self.score.stakedBalanceOf(self.test_account2))
        self.assertEqual(_balance - stake_amount_1, self.score.availableBalanceOf(self.test_account2))

    def test_stake_staking_disabled(self):
        try:
            self.score.stake(1)
        except IconScoreException as err:
            self.assertIn("BALN: Staking must first be enabled.", str(err))
        else:
            self.assertTrue(False)

    def test_stake_insufficient_balance(self):
        self._toggle_staking_enabled()
        self._set_admin()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, 1)

        self.set_msg(self.test_account2)
        try:
            self.score.stake(12)
        except IconScoreException as err:
            self.assertIn("BALN: Out of BALN balance.", str(err))
        else:
            self.assertTrue(False)

    def test_stake_low_stake(self):
        self._toggle_staking_enabled()
        self._set_admin()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, 12)

        self.set_msg(self.test_account2)
        try:
            self.score.stake(1)
        except IconScoreException as err:
            self.assertIn("BALN: Staked BALN must be greater than the minimum stake amount and non zero.", str(err))
        else:
            self.assertTrue(False)

    def test_stake_zero_stake(self):
        self._toggle_staking_enabled()
        self._set_admin()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, 12)

        self.set_msg(self.test_account2)
        try:
            self.score.stake(0)
        except IconScoreException as err:
            self.assertIn("BALN: Staked BALN must be greater than the minimum stake amount and non zero.", str(err))
        else:
            self.assertTrue(False)

    def test_stake_negative_stake(self):
        self._toggle_staking_enabled()
        self._set_admin()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, 12)

        self.set_msg(self.test_account2)
        try:
            self.score.stake(-1)
        except IconScoreException as err:
            self.assertIn("BALN: Staked BALN value can't be less than zero.", str(err))
        else:
            self.assertTrue(False)

    def _stake(self, _from, stake_amount, ts):
        self.set_block(1, ts)
        self.set_msg(_from)
        self.score.stake(stake_amount)

    def test_stake_single(self):
        self._toggle_staking_enabled()
        self._set_admin()

        _balance = 120 * 10 ** 18
        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, _balance)

        _stake_amount = 60 * 10 ** 18
        _from = self.test_account2
        self._stake(_from, _stake_amount, 1)

        self.assertEqual(_stake_amount, self.score._staked_balances[_from][Status.STAKED])
        self.assertEqual(0, self.score._staked_balances[_from][Status.UNSTAKING])
        self.assertEqual(1 + self.score._unstaking_period.get(),
                         self.score._staked_balances[_from][Status.UNSTAKING_PERIOD])
        self.assertEqual(_stake_amount, self.score._total_staked_balance.get())
        self.assertEqual(_balance - _stake_amount, self.score._staked_balances[_from][Status.AVAILABLE])

    def test_stake_incremental(self):
        self._toggle_staking_enabled()
        self._set_admin()

        _balance = 120 * 10 ** 18
        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, _balance)

        _stake_amount_1 = 30 * 10 ** 18
        _from = self.test_account2
        self._stake(_from, _stake_amount_1, 1)

        _stake_amount_2 = 60 * 10 ** 18
        _from = self.test_account2
        self._stake(_from, _stake_amount_2, 2)

        self.assertEqual(_stake_amount_2, self.score._staked_balances[_from][Status.STAKED])
        self.assertEqual(0, self.score._staked_balances[_from][Status.UNSTAKING])
        self.assertEqual(2 + self.score._unstaking_period.get(),
                         self.score._staked_balances[_from][Status.UNSTAKING_PERIOD])
        self.assertEqual(_stake_amount_2, self.score._total_staked_balance.get())
        self.assertEqual(_balance - _stake_amount_2,
                         self.score._staked_balances[_from][Status.AVAILABLE])

    def test_stake_decrement(self):
        self._toggle_staking_enabled()
        self._set_admin()

        _balance = 120 * 10 ** 18
        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, _balance)

        _stake_amount_1 = 60 * 10 ** 18
        _from = self.test_account2
        self._stake(_from, _stake_amount_1, 1)

        _stake_amount_2 = 30 * 10 ** 18
        _from = self.test_account2
        self._stake(_from, _stake_amount_2, 2)

        self.assertEqual(_stake_amount_2, self.score._staked_balances[_from][Status.STAKED])
        self.assertEqual(_stake_amount_1 - _stake_amount_2, self.score._staked_balances[_from][Status.UNSTAKING])
        self.assertEqual(2 + self.score._unstaking_period.get(),
                         self.score._staked_balances[_from][Status.UNSTAKING_PERIOD])
        self.assertEqual(_stake_amount_2, self.score._total_staked_balance.get())
        self.assertEqual(_balance - _stake_amount_1,
                         self.score._staked_balances[_from][Status.AVAILABLE])

    def test_get_total_stake_balance(self):
        self._set_admin()
        self._toggle_staking_enabled()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account2, 10 * 10 ** 18)
        self.score.mintTo(self.test_account1, 10 * 10 ** 18)

        result = self.score.totalStakedBalance()
        self.assertEqual(0, result)

        self._stake(self.test_account2, 5 * 10 ** 18, 1)
        result = self.score.totalStakedBalance()
        self.assertEqual(5 * 10 ** 18, result)

        self._stake(self.test_account1, 5 * 10 ** 18, 1)
        result = self.score.totalStakedBalance()
        self.assertEqual(10 * 10 ** 18, result)

        self._stake(self.test_account2, 4 * 10 ** 18, 1)
        result = self.score.totalStakedBalance()
        self.assertEqual(9 * 10 ** 18, result)

        self._stake(self.test_account1, 6 * 10 ** 18, 1)
        result = self.score.totalStakedBalance()
        self.assertEqual(10 * 10 ** 18, result)

    def test_to_test(self):
        raise

        self.score.clearYesterdaysStakeChanges()
        self.score.getStakeUpdates()

    def test_transfer_insufficient_balance(self):
        self._set_admin()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account1, 20)

        try:
            self.set_msg(self.test_account1)
            self.score.transfer(self.test_account2, 30)
        except IconScoreException as err:
            self.assertIn("BALN: Out of available balance. Please check staked and total balance.", str(err))
        else:
            self.assertTrue(False)

    def test_transfer_all_balance_staked(self):
        self._set_admin()
        self._toggle_staking_enabled()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account1, 20 * 10 ** 18)
        self._stake(self.test_account1, 20 * 10 ** 18, 1)

        try:
            self.set_msg(self.test_account1)
            self.score.transfer(self.test_account2, 20 * 10 ** 18)
        except IconScoreException as err:
            self.assertIn("BALN: Out of available balance. Please check staked and total balance.", str(err))
        else:
            self.assertTrue(False)

    def test_transfer(self):
        self._set_admin()
        self._toggle_staking_enabled()

        self.set_msg(self.admin_address)
        self.score.mintTo(self.test_account1, 20 * 10 ** 18)

        self.set_msg(self.test_account1)
        self.score.transfer(self.test_account2, 10 * 10 ** 18)
        self.assertEqual(10 * 10 ** 18, self.score.balanceOf(self.test_account1))
        self.assertEqual(10 * 10 ** 18, self.score.balanceOf(self.test_account2))

    def _toggle_staking_enabled(self):
        self.set_msg(self.governance_address)
        self.score.toggleStakingEnabled()

    def test_set_stake_update_db(self):
        self._set_dividends()
        self._toggle_staking_enabled()

        self.set_msg(self.dividends_address)
        self.score.switchStakeUpdateDB()

        new_day = (self.score._stake_address_update_db.get() + 1) % 2
        print(new_day)
        # self.score._stake_address_update_db.set(new_day)
        stake_changes = self.score._stake_changes[new_day]
        print([i for i in stake_changes])
        # self._index_stake_address_changes.set(len(stake_changes))
        raise


class CreateMockObject():

    def __init__(self, dex_address, oracle_address):
        self.dex_address = dex_address
        self.oracle_address = oracle_address

    def create(self, address, interface):
        class OracleMock:
            def get_reference_data(self, a, b):
                return {"rate": 597955725813433531, "last_update_base": 1602202275702605,
                        "last_update_quote": 1602202190000000}

        class DexMock:
            def getBalnPrice(self):
                return 100

        if address == self.dex_address:
            return DexMock()
        elif address == self.oracle_address:
            return OracleMock()
