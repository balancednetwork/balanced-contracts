from iconservice import Address
from iconservice.base.exception import IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from core_contracts.dividends.dividends import Dividends


class TestDividendsUnit(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score = Address.from_string(f"cx{'1234'*10}")
        self.dividends = self.get_score_instance(Dividends, self.test_account1,
                                                 on_install_params={"_governance": self.mock_score})
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)

    def test_check_start_end(self):
        self.dividends._snapshot_id.set(4)
        self.dividends._dividends_batch_size.set(50)
        self.assertEqual((1, 4), self.dividends._check_start_end(0, 0), "Test Failed for 0,0 case")
        self.assertEqual((1, 4), self.dividends._check_start_end(1, 0), "Test Failed for 1,0 case")
        self.assertEqual((1, 2+1), self.dividends._check_start_end(0, 2), "Test Failed for 0,2 case")
        self.assertEqual((1, 2+1), self.dividends._check_start_end(1, 2))

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
        self.assertEqual("Neither start and end can't be same nor start can be greater",
                         equal_start_end.exception.message)

        self.dividends._snapshot_id.set(101)
        self.assertEqual((51, 101), self.dividends._check_start_end(0, 0), "Test Failed for 0,0 case")
        self.assertEqual((1, 51), self.dividends._check_start_end(1, 0), "Test Failed for 1,0 case")
        self.assertEqual((11, 61), self.dividends._check_start_end(0, 60), "Test Failed for 0,60 case")
        self.assertEqual((5, 11), self.dividends._check_start_end(5, 10))

