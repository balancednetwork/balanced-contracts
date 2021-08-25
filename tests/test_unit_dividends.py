from iconservice import Address
from iconservice.base.exception import IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from core_contracts.dividends.dividends import Dividends


class TestDividendsUnit(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score = Address.from_string(f"cx{'1234' * 10}")
        self.dividends = self.get_score_instance(Dividends, self.test_account1,
                                                 on_install_params={"_governance": self.mock_score})
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)
        self.daofund = Address.from_string(f"cx{'12345' * 8}")
        self.set_msg(self.test_account1)
        self.dividends.set_contract_addresses([{"name": "daofund", "address": self.daofund}])

    def test_check_start_end(self):
        self.dividends._snapshot_id.set(4)
        self.dividends._dividends_batch_size.set(50)
        self.assertEqual((1, 4), self.dividends._check_start_end(0, 0), "Test Failed for 0,0 case")
        self.assertEqual((1, 4), self.dividends._check_start_end(1, 0), "Test Failed for 1,0 case")
        self.assertEqual((1, 2), self.dividends._check_start_end(0, 2), "Test Failed for 0,2 case")
        self.assertEqual((1, 2), self.dividends._check_start_end(1, 2))

        with self.assertRaises(IconScoreException) as invalid_start:
            self.dividends._check_start_end(-1, 5)
            self.dividends._check_start_end(3, 5)
        self.assertEqual("Invalid value of start provided", invalid_start.exception.message)

        with self.assertRaises(IconScoreException) as invalid_end:
            self.dividends._check_start_end(1, -1)
            self.dividends._check_start_end(1, 5)
        self.assertEqual("Invalid value of end provided", invalid_end.exception.message)

        with self.assertRaises(IconScoreException) as equal_start_end:
            self.dividends._check_start_end(2, 2)
            self.dividends._check_start_end(3, 1)
        self.assertEqual("Start must not be greater than or equal to end.",
                         equal_start_end.exception.message)

        self.dividends._snapshot_id.set(101)
        self.assertEqual((51, 101), self.dividends._check_start_end(0, 0), "Test Failed for 0,0 case")
        self.assertEqual((1, 51), self.dividends._check_start_end(1, 0), "Test Failed for 1,0 case")
        self.assertEqual((10, 60), self.dividends._check_start_end(0, 60), "Test Failed for 0,60 case")
        self.assertEqual((5, 10), self.dividends._check_start_end(5, 10))

        with self.assertRaises(IconScoreException) as max_gap:
            self.dividends._check_start_end(12, 98)
        self.assertEqual("Maximum allowed range is 50", max_gap.exception.message)

    def test_claimed_bit_map(self):
        self.dividends._set_claimed(self.test_account1, 1)
        self.assertTrue(self.dividends._is_claimed(self.test_account1, 1))
        self.assertFalse(self.dividends._is_claimed(self.test_account1, 2))
        self.assertFalse(self.dividends._is_claimed(self.test_account3, 1))
        self.assertFalse(self.dividends._is_claimed(self.mock_score, 2))

        self.dividends._set_claimed(self.mock_score, 2)
        self.assertTrue(self.dividends._is_claimed(self.mock_score, 2))

    def test_add_dividends(self):
        token1 = Address.from_string(f"cx{'0' * 40}")
        token2 = Address.from_string(f"cx{'12345' * 8}")
        self.dividends._accepted_tokens.put(token1)
        self.dividends._accepted_tokens.put(token2)

        a = {str(token1): 5, str(token2): 10, "abcd": 15}
        a_output = {str(token1): 10, str(token2): 20}
        self.assertEqual({}, self.dividends._add_dividends({}, {}))
        self.assertEqual(a, self.dividends._add_dividends(a, {}))
        self.assertEqual(a, self.dividends._add_dividends({}, a))
        self.assertEqual(a_output, self.dividends._add_dividends(a, a))

    def test_get_dividends_for_daofund(self):
        token1 = Address.from_string(f"cx{'0' * 40}")
        token2 = Address.from_string(f"cx{'12345' * 8}")
        self.dividends._accepted_tokens.put(token1)
        self.dividends._accepted_tokens.put(token2)
        day = 1
        self.dividends._daily_fees[day][str(token1)] = 5 * 10 ** 18
        self.dividends._daily_fees[day][str(token2)] = 10 * 10 ** 18

        expected_output = {str(token1): 2000000000000000000, str(token2): 4000000000000000000}
        self.assertEqual(expected_output, self.dividends._get_dividends_for_daofund(day))

        self.dividends._set_claimed(self.dividends.getDaofund(), day)
        self.assertEqual({}, self.dividends._get_dividends_for_daofund(day))


