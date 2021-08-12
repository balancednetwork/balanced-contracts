from unittest import mock

from iconservice import Address
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice.base.exception import IconScoreException

from core_contracts.dividends.dividends import Dividends
from core_contracts.dividends.utils.consts import DAOFUND, BALN_HOLDERS
from core_contracts.dividends.utils.checks import SenderNotScoreOwnerError, SenderNotGovernance, SenderNotAuthorized

MOCKED_ADDRESSES = {
    "GOV_ADDR": Address.from_string(f"cx{'1235' * 10}"),
    "LOAN_ADDR": Address.from_string(f"cx{'1236' * 10}"),
    "DAOFUND_ADDR": Address.from_string(f"cx{'1237' * 10}"),
    "BALN_ADDR": Address.from_string(f"cx{'1238' * 10}"),
    "DEX_ADDR": Address.from_string(f"cx{'1239' * 10}"),
    "TOKEN1": Address.from_string(f"cx{'1240' * 10}"),
    "TOKEN2": Address.from_string(f"cx{'1241' * 10}"),
}


class MockClass():

    def __init__(self, time_offset=12, user_baln_stacked=None, baln_total=None, dex_balance_of_at=None,
                 dex_total_supply=None, dex_baln_total=None):
        outer_cls = self
        self.time_offset = time_offset
        self.balance = {}
        self.user_baln_stacked = user_baln_stacked if user_baln_stacked else {}
        self.baln_total = baln_total if baln_total else {}
        self.dex_balance_of_at = dex_balance_of_at if dex_balance_of_at else {}
        self.dex_total_supply = dex_total_supply if dex_total_supply else {}
        self.dex_baln_total = dex_baln_total if dex_baln_total else {}

        class BalnMock:
            def stakedBalanceOfAt(self, _account, _day):
                balance = outer_cls.user_baln_stacked[_account]
                return balance[_day]

            def totalStakedBalanceOfAt(self, _day):
                return outer_cls.baln_total[_day]

        class DexMock:
            def getTimeOffset(self):
                return outer_cls.time_offset

            def balanceOfAt(self, _account, pool_id, _day):
                balance = outer_cls.dex_balance_of_at[_account]
                balance = balance[pool_id]
                return balance[_day]

            def totalBalnAt(self, pool_id, _day):
                balance = outer_cls.dex_baln_total[pool_id]
                return balance[_day]

            def totalSupplyAt(self, pool_id, _day):
                balance = outer_cls.dex_total_supply[pool_id]
                return balance[_day]

        class LoansMock:
            def getAssetTokens(self):
                return {"TOKEN1": str(MOCKED_ADDRESSES["TOKEN1"]),
                        "TOKEN2": str(MOCKED_ADDRESSES["TOKEN2"])}

        class TokenMock:
            def __init__(self, token_id):
                self.token_id = token_id

            def balanceOf(self, _address):
                if self.token_id not in outer_cls.balance:
                    outer_cls.balance[self.token_id] = {}
                return outer_cls.balance[self.token_id].get(_address, 0)

            def transfer(self, _to, _amount):
                if self.token_id not in outer_cls.balance:
                    outer_cls.balance[self.token_id] = {}
                outer_cls.balance[self.token_id][_to] = outer_cls.balance[self.token_id].get(_to, 0) + _amount

        self.dex = DexMock()
        self.loans = LoansMock()
        self.token1 = TokenMock("TOKEN1")
        self.token2 = TokenMock("TOKEN2")
        self.baln = BalnMock()

    def create_interface_score(self, _address, _score):
        address_mapping = {
            MOCKED_ADDRESSES["DEX_ADDR"]: self.dex,
            MOCKED_ADDRESSES["LOAN_ADDR"]: self.loans,
            MOCKED_ADDRESSES["TOKEN1"]: self.token1,
            MOCKED_ADDRESSES["TOKEN2"]: self.token2,
            MOCKED_ADDRESSES["BALN_ADDR"]: self.baln
        }
        return address_mapping[_address]


class TestDividends(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score_address = Address.from_string(f"cx{'1234' * 10}")

        self.admin = Address.from_string(f"hx{'12345' * 8}")
        self.owner = Address.from_string(f"hx{'1234' * 10}")
        self.test_account3 = Address.from_string(f"hx{'1574' * 10}")
        account_info = {
            self.admin: 10 ** 21,
            self.owner: 10 ** 21,
            self.test_account3: 10 ** 31}
        self.initialize_accounts(account_info)
        self.set_block(0, 0)
        self.score = self.get_score_instance(Dividends, self.owner,
                                             on_install_params={'_governance': self.admin})

    def _add_accepted_token(self):
        self.set_msg(MOCKED_ADDRESSES["GOV_ADDR"])
        self.score.addAcceptedTokens(MOCKED_ADDRESSES["TOKEN1"])
        self.set_msg(None)

    def _set_governance(self):
        self.set_msg(self.score.owner)
        gov_address = MOCKED_ADDRESSES["GOV_ADDR"]
        self.score.setGovernance(gov_address)
        self.set_msg(None)

    def _set_admin(self):
        self.set_msg(MOCKED_ADDRESSES["GOV_ADDR"])
        self.score.setAdmin(self.admin)
        self.set_msg(None)

    def _set_loans(self):
        self.set_msg(self.admin)
        self.score.setLoans(MOCKED_ADDRESSES["LOAN_ADDR"])
        self.set_msg(None)

    def _set_daofund(self):
        self.set_msg(self.admin)
        self.score.setDaofund(MOCKED_ADDRESSES["DAOFUND_ADDR"])
        self.set_msg(None)

    def _set_baln(self):
        self.set_msg(self.admin)
        self.score.setBaln(MOCKED_ADDRESSES["BALN_ADDR"])
        self.set_msg(None)

    def _set_dex(self):
        self.set_msg(self.admin)
        self.score.setDex(MOCKED_ADDRESSES["DEX_ADDR"])
        self.set_msg(None)

    def _add_dividends_category(self, item):
        self.set_msg(self.admin)
        self.score.addDividendsCategory(item)
        self.set_msg(None)

    def test_set_time_offset(self):
        self.score._dex_score.set(MOCKED_ADDRESSES["DEX_ADDR"])
        patched_fxn = MockClass().create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_fxn):
            self.score._set_time_offset()
        self.assertEqual(12, self.score._time_offset.get())

    def test_add_initial_categories(self):
        self.score._add_initial_categories()
        self.assertEqual(self.score._dividends_categories[0], DAOFUND)
        self.assertEqual(self.score._dividends_categories[1], BALN_HOLDERS)
        self.assertEqual(self.score._dividends_percentage[DAOFUND], 4 * 10 ** 17)
        self.assertEqual(self.score._dividends_percentage[BALN_HOLDERS], 6 * 10 ** 17)

    def test_name(self):
        result = self.score.name()
        self.assertEqual("Balanced Dividends", result)

    def test_getDistributionActivationStatus(self):
        result = self.score.getDistributionActivationStatus()
        self.assertEqual(result, False)

        self.set_msg(self.admin)
        self.score.setDistributionActivationStatus(True)
        result = self.score.getDistributionActivationStatus()
        self.assertEqual(result, True)

    def test_setGovernance(self):
        with self.assertRaises(SenderNotScoreOwnerError) as err:
            self.score.setGovernance()
        self.assertEqual(self.score.owner, err.exception.args[0])

        self._set_governance()
        self.assertEqual(MOCKED_ADDRESSES["GOV_ADDR"], self.score._governance.get())

    def test_getGovernance(self):
        self._set_governance()
        self.assertEqual(MOCKED_ADDRESSES["GOV_ADDR"], self.score.getGovernance())

    def test_setAdmin(self):
        self._set_governance()
        with self.assertRaises(SenderNotGovernance):
            self.score.setAdmin()
        self._set_admin()
        self.assertEqual(self.admin, self.score._admin.get())

    def test_getAdmin(self):
        self._set_governance()
        self._set_admin()
        self.assertEqual(self.admin, self.score.getAdmin())

    def test_setLoans(self):
        self._set_governance()
        self._set_admin()
        self.set_msg(None)
        with self.assertRaises(SenderNotAuthorized):
            self.score.setLoans(MOCKED_ADDRESSES["LOAN_ADDR"])
        self._set_loans()
        self.assertEqual(MOCKED_ADDRESSES["LOAN_ADDR"], self.score._loans_score.get())

    def test_getLoans(self):
        self._set_governance()
        self._set_admin()
        self._set_loans()
        result = self.score.getLoans()
        self.assertEqual(MOCKED_ADDRESSES["LOAN_ADDR"], result)

    def test_setDaofund(self):
        self._set_governance()
        self._set_admin()
        with self.assertRaises(SenderNotAuthorized):
            self.score.setDaofund(MOCKED_ADDRESSES["DAOFUND_ADDR"])
        self._set_daofund()
        self.assertEqual(MOCKED_ADDRESSES["DAOFUND_ADDR"], self.score._daofund.get())

    def getDaofund(self):
        self._set_governance()
        self._set_admin()
        self._set_daofund()
        self.assertEqual(MOCKED_ADDRESSES["DAOFUND_ADDR"], self.score.getDaofund())

    def test_setBaln(self):
        self._set_governance()
        self._set_admin()
        with self.assertRaises(SenderNotAuthorized):
            self.score.setBaln(MOCKED_ADDRESSES["BALN_ADDR"])
        self._set_baln()
        self.assertEqual(MOCKED_ADDRESSES["BALN_ADDR"], self.score._baln_score.get())

    def test_getBaln(self):
        self._set_governance()
        self._set_admin()
        self._set_baln()
        self.assertEqual(MOCKED_ADDRESSES["BALN_ADDR"], self.score.getBaln())

    def test_setDex(self):
        self._set_governance()
        self._set_admin()
        with self.assertRaises(SenderNotAuthorized):
            self.score.setDex(MOCKED_ADDRESSES["DEX_ADDR"])
        self._set_dex()
        self.assertEqual(MOCKED_ADDRESSES["DEX_ADDR"], self.score._dex_score.get())

    def test_getDex(self):
        self._set_governance()
        self._set_admin()
        self._set_dex()
        self.assertEqual(MOCKED_ADDRESSES["DEX_ADDR"], self.score.getDex())

    def test_getBalances(self):
        self._set_governance()
        self._set_admin()
        self._set_loans()
        patched_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            result1 = self.score.getBalances()
            self._add_accepted_token()
            result2 = self.score.getBalances()
        self.assertDictEqual({'ICX': 0}, result1)
        self.assertDictEqual({'ICX': 0}, result2)

    def test_getDailyFees(self):
        self._set_governance()
        result = self.score.getDailyFees(1)
        self.assertDictEqual({'cx0000000000000000000000000000000000000000': 0}, result)
        self._add_accepted_token()

        result = self.score.getDailyFees(1)
        self.assertDictEqual({'cx0000000000000000000000000000000000000000': 0,
                              str(MOCKED_ADDRESSES["TOKEN1"]): 0},
                             result)

    def test_getAcceptedTokens(self):
        self._set_governance()
        result = self.score.getAcceptedTokens()
        self.assertListEqual([Address.from_string('cx0000000000000000000000000000000000000000')], result)
        self._add_accepted_token()
        result = self.score.getAcceptedTokens()
        self.assertListEqual(
            [Address.from_string('cx0000000000000000000000000000000000000000'), MOCKED_ADDRESSES["TOKEN1"]], result)

    def test_addAcceptedTokens(self):
        self._set_governance()
        with self.assertRaises(SenderNotGovernance):
            self.score.addAcceptedTokens(MOCKED_ADDRESSES["TOKEN1"])
        self._add_accepted_token()
        self.assertEqual(Address.from_string("cx0000000000000000000000000000000000000000"),
                         self.score._accepted_tokens[0])
        self.assertEqual(MOCKED_ADDRESSES["TOKEN1"], self.score._accepted_tokens[1])

    def test_getDividendsCategories(self):
        self._set_governance()
        self._set_admin()
        result = self.score.getDividendsCategories()
        self.assertListEqual(['daofund', 'baln_holders'], result)

        self._add_dividends_category("apple")
        result = self.score.getDividendsCategories()
        self.assertListEqual(['daofund', 'baln_holders', "apple"], result)

    def test_addDividendsCategory(self):
        self._set_governance()
        self._set_admin()
        with self.assertRaises(SenderNotAuthorized):
            self.score.addDividendsCategory()

        self.set_msg(self.admin)
        with self.assertRaises(IconScoreException) as err:
            self.score.addDividendsCategory("daofund")
        self.assertEqual("Balanced Dividends: daofund is already added", err.exception.message)

        self._add_dividends_category("apple")
        self.assertEqual("apple", self.score._dividends_categories[2])

    def test_removeDividendsCategory(self):
        self._set_governance()
        self._set_admin()
        with self.assertRaises(SenderNotAuthorized):
            self.score.removeDividendsCategory()
        self._add_dividends_category("apple")
        self.set_msg(self.admin)
        with self.assertRaises(IconScoreException) as err:
            self.score.removeDividendsCategory("daofund")
        self.assertEqual("Balanced Dividends: Please make the category percentage to 0 before removing",
                         err.exception.message)
        with self.assertRaises(IconScoreException) as err:
            self.score.removeDividendsCategory("banana")
        self.assertEqual("Balanced Dividends: banana not found in the list of dividends categories",
                         err.exception.message)

        self.score.removeDividendsCategory("apple")
        self.assertListEqual(['daofund', 'baln_holders'], self.score.getDividendsCategories())

    def test_getDividendsPercentage(self):
        self._set_governance()
        self._set_admin()
        result = self.score.getDividendsPercentage()
        self.assertDictEqual({'daofund': 400000000000000000, 'baln_holders': 600000000000000000}, result)
        self.set_msg(self.admin)
        self.score.setDividendsCategoryPercentage([
            {"category": "daofund", "dist_percent": 300000000000000000},
            {"category": "baln_holders", "dist_percent": 700000000000000000},
        ])

        result = self.score.getDividendsPercentage()
        self.assertDictEqual({'daofund': 300000000000000000, 'baln_holders': 700000000000000000}, result)

    def test_setDividendsCategoryPercentage(self):
        self._set_governance()
        self._set_admin()
        with self.assertRaises(SenderNotAuthorized):
            self.score.setDividendsCategoryPercentage()

        self.set_msg(self.admin)
        with self.assertRaises(IconScoreException) as err:
            self.score.setDividendsCategoryPercentage([
                {"category": "daofund1", "dist_percent": 300000000000000000},
                {"category": "baln_holders", "dist_percent": 700000000000000000},
            ])
        self.assertEqual("Balanced Dividends: daofund1 is not a valid dividends category", err.exception.message)

        with self.assertRaises(IconScoreException) as err:
            self.score.setDividendsCategoryPercentage([
                {"category": "daofund", "dist_percent": 400000000000000000},
                {"category": "baln_holders", "dist_percent": 700000000000000000},
            ])
        self.assertEqual("Balanced Dividends: Total percentage doesn't sum up to 100 i.e. 10**18",
                         err.exception.message)

        self.score.setDividendsCategoryPercentage([
            {"category": "daofund", "dist_percent": 400000000000000000},
            {"category": "baln_holders", "dist_percent": 600000000000000000},
        ])
        self.assertEqual(400000000000000000, self.score._dividends_percentage["daofund"])
        self.assertEqual(600000000000000000, self.score._dividends_percentage["baln_holders"])

    def test_getDividendsBatchSize(self):
        self._set_governance()
        self._set_admin()
        self.assertEqual(0, self.score.getDividendsBatchSize())
        self.set_msg(self.admin)
        self.score.setDividendsBatchSize(12)
        self.assertEqual(12, self.score.getDividendsBatchSize())

    def test_setDividendsBatchSize(self):
        self._set_governance()
        self._set_admin()
        with self.assertRaises(SenderNotAuthorized):
            self.score.setDividendsBatchSize(12)
        self.set_msg(self.admin)
        with self.assertRaises(IconScoreException) as err:
            self.score.setDividendsBatchSize(-1)
        self.assertEqual("Balanced Dividends: Size can't be negative or zero", err.exception.message)
        self.score.setDividendsBatchSize(12)
        self.assertEqual(12, self.score._dividends_batch_size.get())

    def test_getSnapshotId(self):
        self.score._snapshot_id.set(12)
        self.assertEqual(12, self.score.getSnapshotId())

    def test_getDay(self):
        day = 24 * 60 * 60 * 10 ** 6
        self.set_block(1, day)
        result = self.score.getDay()
        self.assertEqual(1, result)
        self.set_block(1, 2 * day)
        result = self.score.getDay()
        self.assertEqual(2, result)

    def test_getTimeOffset(self):
        self._set_governance()
        self._set_admin()
        self._set_dex()

        result = self.score.getTimeOffset()
        self.assertEqual(0, result)

        patched_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.score._set_time_offset()
        result = self.score.getTimeOffset()
        self.assertEqual(12, result)

    def test_distribute(self):
        with mock.patch.object(self.score, "_check_for_new_day", return_value=None):
            result = self.score.distribute()
        self.assertTrue(result)

    def test_check_for_new_day(self):
        self._set_governance()
        self._set_admin()
        self._set_dex()

        day = 24 * 60 * 60 * 10 ** 6
        self.set_block(1, day)
        patch_cls = MockClass(10 * day)
        patch_cls2 = MockClass(20 * day)
        self.assertEqual(1, self.score._snapshot_id.get())
        with mock.patch.object(self.score, "create_interface_score", wraps=patch_cls.create_interface_score):
            self.set_block(2, 15 * day)
            self.score._check_for_new_day()
            self.assertEqual(10 * day, self.score._time_offset.get())
            self.assertEqual(5, self.score._snapshot_id.get())

        with mock.patch.object(self.score, "create_interface_score", wraps=patch_cls2.create_interface_score):
            self.set_block(3, 25 * day)
            self.score._check_for_new_day()
            self.assertEqual(10 * day, self.score._time_offset.get())
            self.assertEqual(15, self.score._snapshot_id.get())

    def test_transferDaofundDividends_error_cases(self):
        self.score._snapshot_id.set(12)
        with self.assertRaises(IconScoreException) as err:
            self.score.transferDaofundDividends()
        self.assertEqual("Balanced Dividends: Distribution is not activated. Can't transfer", err.exception.message)

        self._set_governance()
        self.set_msg(MOCKED_ADDRESSES["GOV_ADDR"])
        self.score.setDistributionActivationStatus(True)

        with self.assertRaises(IconScoreException) as err:
            self.score.transferDaofundDividends()
        self.assertEqual("Invalid value of start provided", err.exception.message)

        with self.assertRaises(IconScoreException) as err:
            self.score.transferDaofundDividends(1, 15)
        self.assertEqual("Invalid value of end provided", err.exception.message)

        with self.assertRaises(IconScoreException) as err:
            self.score.transferDaofundDividends(4, 3)
        self.assertEqual("Start must not be greater than or equal to end.", err.exception.message)

        with self.assertRaises(IconScoreException) as err:
            self.score.transferDaofundDividends(1, 10)
        self.assertEqual("Maximum allowed range is 0", err.exception.message)

    def test_transferDaofundDividends(self):
        self.score._snapshot_id.set(12)

        self.score._dividends_percentage["daofund"] = 10 * 10 ** 18
        for i in range(1, 10):
            self.score._daily_fees[i]["cx0000000000000000000000000000000000000000"] = 12 * 10 ** 18
            self.score._daily_fees[i]["cx1240124012401240124012401240124012401240"] = 12 * 10 ** 18

        self._set_governance()
        self._set_admin()
        self._add_accepted_token()
        self._set_baln()
        self._set_daofund()
        self.set_msg(MOCKED_ADDRESSES["GOV_ADDR"])
        self.score.setDistributionActivationStatus(True)
        self.set_msg(self.admin)
        self.score.setDividendsBatchSize(10)

        self.score._add_initial_categories()

        mock_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=mock_cls.create_interface_score):
            self.score.transferDaofundDividends(1, 10)
        self.assertEqual(43200000000000000000, mock_cls.token1.balanceOf(MOCKED_ADDRESSES["DAOFUND_ADDR"]))
        self.assertEqual(43200000000000000000, self.get_balance(MOCKED_ADDRESSES["DAOFUND_ADDR"]))

    def test_send_ICX(self):
        self.initialize_accounts({self.score.address: 12 * 10 ** 18})
        pre_distribution = self.get_balance(self.test_account1)
        self.set_msg(self.score.address)
        self.score._send_ICX(self.test_account1, 12 * 10 ** 18, "")
        post_distribution = self.get_balance(self.test_account1)
        self.assertEqual(pre_distribution + 12 * 10 ** 18, post_distribution)

    def test_send_token(self):
        mock_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=mock_cls.create_interface_score):
            self.score._send_token(self.test_account1, 12, MOCKED_ADDRESSES["TOKEN1"], '')
        self.assertEqual(12, mock_cls.balance["TOKEN1"][self.test_account1])

    def test_check_start_end(self):
        self.score._snapshot_id.set(4)
        self.score._dividends_batch_size.set(50)
        self.assertEqual((1, 4), self.score._check_start_end(0, 0), "Test Failed for 0,0 case")
        self.assertEqual((1, 4), self.score._check_start_end(1, 0), "Test Failed for 1,0 case")
        self.assertEqual((1, 2), self.score._check_start_end(0, 2), "Test Failed for 0,2 case")
        self.assertEqual((1, 2), self.score._check_start_end(1, 2))

        with self.assertRaises(IconScoreException) as invalid_start:
            self.score._check_start_end(-1, 5)
            self.score._check_start_end(3, 5)
        self.assertEqual("Invalid value of start provided", invalid_start.exception.message)

        with self.assertRaises(IconScoreException) as invalid_end:
            self.score._check_start_end(1, -1)
            self.score._check_start_end(1, 5)
        self.assertEqual("Invalid value of end provided", invalid_end.exception.message)

        with self.assertRaises(IconScoreException) as equal_start_end:
            self.score._check_start_end(2, 2)
        self.assertEqual("Start must not be greater than or equal to end.",
                         equal_start_end.exception.message)

        with self.assertRaises(IconScoreException) as equal_start_end:
            self.score._check_start_end(3, 1)
        self.assertEqual("Invalid value of end provided",
                         equal_start_end.exception.message)

        self.score._snapshot_id.set(101)
        self.assertEqual((51, 101), self.score._check_start_end(0, 0), "Test Failed for 0,0 case")
        self.assertEqual((1, 51), self.score._check_start_end(1, 0), "Test Failed for 1,0 case")
        self.assertEqual((10, 60), self.score._check_start_end(0, 60), "Test Failed for 0,60 case")
        self.assertEqual((5, 10), self.score._check_start_end(5, 10))

        with self.assertRaises(IconScoreException) as max_gap:
            self.score._check_start_end(12, 98)
        self.assertEqual("Maximum allowed range is 50", max_gap.exception.message)

    def test__add_dividends(self):
        self.assertDictEqual({}, self.score._add_dividends(None, None))

        param = {"cx0000000000000000000000000000000000000000": 1, "a": 12}
        self.assertDictEqual(param, self.score._add_dividends(param, None))
        self.assertDictEqual(param, self.score._add_dividends(None, param))
        self.assertDictEqual({"cx0000000000000000000000000000000000000000": 2},
                             self.score._add_dividends(param, param))

    def test_claimed_bit_map(self):
        self.score._set_claimed(self.test_account1, 1)
        self.assertTrue(self.score._is_claimed(self.test_account1, 1))
        self.assertFalse(self.score._is_claimed(self.test_account1, 2))
        self.assertFalse(self.score._is_claimed(self.test_account2, 1))
        self.assertFalse(self.score._is_claimed(self.mock_score_address, 2))

        self.score._set_claimed(self.mock_score_address, 2)
        self.assertTrue(self.score._is_claimed(self.mock_score_address, 2))

    def test_get_dividends_for_daofund(self):
        token1 = Address.from_string(f"cx{'0' * 40}")
        token2 = Address.from_string(f"cx{'12345' * 8}")
        self.score._accepted_tokens.put(token1)
        self.score._accepted_tokens.put(token2)
        self.score._daofund.set(Address.from_string(f"cx{'12345' * 8}"))
        day = 1
        self.score._daily_fees[day][str(token1)] = 5 * 10 ** 18
        self.score._daily_fees[day][str(token2)] = 10 * 10 ** 18

        expected_output = {str(token1): 2000000000000000000, str(token2): 4000000000000000000}
        self.assertEqual(expected_output, self.score._get_dividends_for_daofund(day))

        self.score._set_claimed(self.score.getDaofund(), day)
        self.assertEqual({}, self.score._get_dividends_for_daofund(day))

    def test__get_dividends_for_day(self):
        self.score._snapshot_id.set(12)
        self._set_governance()
        self._set_admin()
        self._set_baln()
        self._set_dex()
        self._set_daofund()

        self.score._dividends_percentage["daofund"] = 10 * 10 ** 18
        self.score._daily_fees[3]["cx0000000000000000000000000000000000000000"] = 12 * 10 ** 18
        mock_cls = MockClass(
            user_baln_stacked={
                Address.from_string("cx1237123712371237123712371237123712371237"):
                    {3: 1 * 10 ** 18}},
            baln_total={3: 10 * 10 ** 18},
            dex_balance_of_at={
                Address.from_string("cx1237123712371237123712371237123712371237"):
                    {3: {3: 1 * 10 ** 18}, 4: {3: 1 * 10 ** 18}}},
            dex_total_supply={3: {3: 10 * 10 ** 18}, 4: {3: 10 * 10 ** 18}},
            dex_baln_total={3: {3: 1 * 10 ** 18}, 4: {3: 1 * 10 ** 18}}
        )
        with mock.patch.object(self.score, "create_interface_score", wraps=mock_cls.create_interface_score):
            result = self.score._get_dividends_for_day(MOCKED_ADDRESSES["DAOFUND_ADDR"], 3)
        self.assertDictEqual({"cx0000000000000000000000000000000000000000": 720 * 10 ** 15}, result)

    def test__set_claimed(self):
        self.score._set_claimed(self.admin, 1)
        raise

    def test__is_claimed(self):
        self.score._is_claimed()
        raise

    def test_claim(self):
        self.score._snapshot_id.set(12)
        self.score._dividends_batch_size.set(10)
        self.score._dividends_percentage["baln_holders"] = 12 * 10 ** 18
        self.score._daily_fees[3]["cx0000000000000000000000000000000000000000"] = 60 * 10 ** 18
        self.score._daily_fees[3]["cx1240124012401240124012401240124012401240"] = 60 * 10 ** 18
        with self.assertRaises(IconScoreException) as err:
            self.score.claim(10, 11)
        self.assertEqual("Balanced Dividends: Claim has not been activated", err.exception.message)

        self.score._distribution_activate.set(True)
        self._set_governance()
        self._set_admin()
        self._set_dex()
        self._add_accepted_token()
        self._set_baln()
        mock_class = MockClass(
            user_baln_stacked={
                Address.from_string(str(self.test_account1)):
                    {3: 1 * 10 ** 18}},
            baln_total={3: 10 * 10 ** 18},
            dex_balance_of_at={
                Address.from_string(str(self.test_account1)):
                    {3: {3: 1 * 10 ** 18}, 4: {3: 1 * 10 ** 18}}},
            dex_total_supply={3: {3: 10 * 10 ** 18}, 4: {3: 10 * 10 ** 18}},
            dex_baln_total={3: {3: 1 * 10 ** 18}, 4: {3: 1 * 10 ** 18}}
        )
        with mock.patch.object(self.score, "create_interface_score", wraps=mock_class.create_interface_score):
            self.set_msg(self.test_account1)
            icx_before = self.get_balance(self.test_account1)
            token_1_before = mock_class.token1.balanceOf(self.test_account1)
            self.score.claim(3, 4)
        self.assertEqual(icx_before + 72 * 10 ** 18, self.get_balance(self.test_account1))
        self.assertEqual(token_1_before + 72 * 10 ** 18, mock_class.token1.balanceOf(self.test_account1))

    def test_tokenFallback(self):
        self._set_governance()
        self._set_admin()
        self._add_accepted_token()
        self._set_loans()
        self._set_dex()
        mock_cls = MockClass()

        with mock.patch.object(self.score, "create_interface_score", wraps=mock_cls.create_interface_score):
            day = self.score.getDay()
            self.set_msg(MOCKED_ADDRESSES["TOKEN1"])
            self.score.tokenFallback(MOCKED_ADDRESSES["TOKEN1"], 12 * 10 ** 18, None)
            self.set_msg(MOCKED_ADDRESSES["TOKEN2"])
            self.score.tokenFallback(MOCKED_ADDRESSES["TOKEN2"], 12 * 10 ** 18, None)
        self.assertIn(MOCKED_ADDRESSES["TOKEN2"], [i for i in self.score._accepted_tokens])
        self.assertEqual(12 * 10 ** 18, self.score._daily_fees[day][str(MOCKED_ADDRESSES["TOKEN1"])])
        self.assertEqual(12 * 10 ** 18, self.score._daily_fees[day][str(MOCKED_ADDRESSES["TOKEN2"])])
        self.assertTrue(self.score._amount_received_status.get())

    def test_fallback(self):
        self._set_governance()
        self._set_admin()
        self._set_dex()
        day = self.score.getDay()
        self.set_msg(self.test_account3, 12 * 10 ** 12)
        mock_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=mock_cls.create_interface_score):
            self.score.fallback()
        self.assertEqual(12 * 10 ** 12, self.score._daily_fees[day]["cx0000000000000000000000000000000000000000"])
        self.assertTrue(self.score._amount_received_status.get())

    def test_getUserDividends(self):
        self.score._snapshot_id.set(12)
        self.score._dividends_batch_size.set(12)
        self.score._distribution_activate.set(True)
        self.score._daily_fees[3]["cx0000000000000000000000000000000000000000"] = 60 * 10 ** 18
        self.score._daily_fees[3]["cx1240124012401240124012401240124012401240"] = 60 * 10 ** 18

        self._set_governance()
        self._set_admin()
        self._set_dex()
        self._add_accepted_token()
        self._set_baln()
        mock_class = MockClass(
            user_baln_stacked={
                Address.from_string(str(self.test_account1)):
                    {3: 1 * 10 ** 18}},
            baln_total={3: 10 * 10 ** 18},
            dex_balance_of_at={
                Address.from_string(str(self.test_account1)):
                    {3: {3: 1 * 10 ** 18}, 4: {3: 1 * 10 ** 18}}},
            dex_total_supply={3: {3: 10 * 10 ** 18}, 4: {3: 10 * 10 ** 18}},
            dex_baln_total={3: {3: 1 * 10 ** 18}, 4: {3: 1 * 10 ** 18}}
        )
        with mock.patch.object(self.score, "create_interface_score", wraps=mock_class.create_interface_score):
            self.set_msg(self.test_account1)
            result = self.score.getUserDividends(self.test_account1, 3, 4)
        self.assertDictEqual(
            {'cx0000000000000000000000000000000000000000': 3600000000000000000,
             'cx1240124012401240124012401240124012401240': 3600000000000000000},
            result
        )

    def test_getDaofundDividends(self):
        self.score._snapshot_id.set(12)
        self.score._dividends_batch_size.set(12)
        self.score._distribution_activate.set(True)
        self.score._daily_fees[3]["cx0000000000000000000000000000000000000000"] = 60 * 10 ** 18
        self.score._daily_fees[3]["cx1240124012401240124012401240124012401240"] = 60 * 10 ** 18

        self._set_governance()
        self._set_admin()
        self._set_dex()
        self._add_accepted_token()
        result = self.score.getDaofundDividends(3, 4)
        self.assertDictEqual({'cx0000000000000000000000000000000000000000': 24000000000000000000,
                              'cx1240124012401240124012401240124012401240': 24000000000000000000},
                             result)
