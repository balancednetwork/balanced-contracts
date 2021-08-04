from unittest import mock

from iconservice import Address
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice.base.exception import IconScoreException

from core_contracts.dividends.dividends import Dividends
from core_contracts.dividends.utils.consts import DAOFUND, BALN_HOLDERS
from core_contracts.dividends.utils.checks import SenderNotScoreOwnerError, SenderNotGovernance, SenderNotAuthorized

MOCKED_ADDRESSES = {
    "DEX_ADDR": Address.from_string(f"cx{'1234' * 10}"),
    "GOV_ADDR": Address.from_string(f"cx{'1235' * 10}"),
    "LOAN_ADDR": Address.from_string(f"cx{'1236' * 10}"),
    "DAOFUND_ADDR": Address.from_string(f"cx{'1237' * 10}"),
    "BALN_ADDR": Address.from_string(f"cx{'1238' * 10}"),
    "DEX_ADDR": Address.from_string(f"cx{'1239' * 10}"),
    "TOKEN1": Address.from_string(f"cx{'1240' * 10}"),
    "TOKEN2": Address.from_string(f"cx{'1241' * 10}"),
}


class MockClass():

    def __init__(self, time_offset=12):
        outer_cls = self
        self.time_offset = time_offset

        class DexMock:
            def getTimeOffset(self):
                return outer_cls.time_offset

        class LoansMock:
            def getAssetTokens(self):
                return {"TOKEN1": str(MOCKED_ADDRESSES["TOKEN1"]),
                        "TOKEN2": str(MOCKED_ADDRESSES["TOKEN2"])}

        class TokenMock:
            def balanceOf(self, _address):
                return 1

        self.dex = DexMock()
        self.loans = LoansMock()
        self.token1 = TokenMock()
        self.token2 = TokenMock()

    def create_interface_score(self, _address, _score):
        address_mapping = {
            MOCKED_ADDRESSES["DEX_ADDR"]: self.dex,
            MOCKED_ADDRESSES["LOAN_ADDR"]: self.loans,
            MOCKED_ADDRESSES["TOKEN1"]: self.token1,
            MOCKED_ADDRESSES["TOKEN2"]: self.token2,
        }
        return address_mapping[_address]


class TestDividends(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score_address = Address.from_string(f"cx{'1234' * 10}")

        self.admin = Address.from_string(f"hx{'12345' * 8}")
        self.owner = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.admin: 10 ** 21,
            self.owner: 10 ** 21}
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
            result = self.score.getBalances()
        expected = {'TOKEN1': 1, 'TOKEN2': 1, 'ICX': 0}
        self.assertDictEqual(expected, result)

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
        raise

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
        patch_cls = MockClass(10*day)
        snap=self.score._snapshot_id.get()
        print(snap)
        with mock.patch.object(self.score, "create_interface_score", wraps=patch_cls.create_interface_score):
            self.score._check_for_new_day()
            self.assertEqual(10*day, self.score._time_offset.get())

            snap=self.score._snapshot_id.get()
            print(snap)

        raise

    def test_transferDaofundDividends(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.transferDaofundDividends()
        self.assertEqual("Balanced Dividends: Distribution is not activated. Can't transfer",err.exception.message)

        self._set_governance()
        self.set_msg(MOCKED_ADDRESSES["GOV_ADDR"])
        self.score.setDistributionActivationStatus(True)

        with self.assertRaises(IconScoreException) as err:
            self.score.transferDaofundDividends()
        self.assertEqual("Invalid value of start provided",err.exception.message)
        raise

    def test_claim(self):
        raise
    def test_send_ICX(self):
        raise

    def test_tokenFallback(self):
        raise

    def test_getUserDividends(self):
        raise

    def test_getDaofundDividends(self):
        raise

    def test__check_start_end(self):
        self.score._check_start_end()

    def test__get_dividends_for_day(self):
        raise

    def test__add_dividends(self):
        raise

    def test__set_claimed(self):
        raise

    def test__is_claimed(self):
        raise