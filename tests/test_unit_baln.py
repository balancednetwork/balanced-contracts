import time

from iconservice import Address
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from token_contracts.baln.balance import BalancedToken


class TestDividendsUnit(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score = Address.from_string(f"cx{'1234' * 10}")
        self.baln = self.get_score_instance(BalancedToken, self.test_account1,
                                            on_install_params={"_governance": self.mock_score})
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)

    def test_StakedBalanceOfAt(self):
        self.dex_mock = Address.from_string(f"cx{'abcd' * 10}")

        current_time = int(time.time() * 10**6)
        self.baln.setDex(self.dex_mock)
        self.set_msg(self.test_account1)
        self.patch_internal_method(self.dex_mock, "getTimeOffset", lambda: current_time)

        # Equivalent to day 1
        self.set_block(60)
        self.baln._update_snapshot_for_address(self.test_account1, 100 * 10**18)
        self.assertEqual(100 * 10**18, self.baln.stakedBalanceOfAt(self.test_account1, 60//30 - 1))

        # At block height 5000, looking for old snapshot id should return same staked amount
        self.set_block(5000)
        for i in range(60, 5000, 30):
            self.assertEqual(100 * 10**18, self.baln.stakedBalanceOfAt(self.test_account1, i//30 - 1))

        self.set_block(60)
        self.assertEqual(0, self.baln.stakedBalanceOfAt(self.test_account3, 60//30-1))

        self.baln._update_snapshot_for_address(self.test_account3, 100 * 10**18)
        self.assertEqual(100*10**18, self.baln.stakedBalanceOfAt(self.test_account3, 60//30 - 1))

        # Same day update
        self.baln._update_snapshot_for_address(self.test_account3, 120 * 10**18)
        self.assertEqual(120*10**18, self.baln.stakedBalanceOfAt(self.test_account3, 60//30-1))

        self.set_block(120)
        self.baln._update_snapshot_for_address(self.test_account3, 130*10**18)
        self.assertEqual(130*10**18, self.baln.stakedBalanceOfAt(self.test_account3, 120//30 - 1))

        # No update and shows the balance of previous day
        self.set_block(180)
        self.assertEqual(130*10**18, self.baln.stakedBalanceOfAt(self.test_account3, 180//30-1))

        self.set_block(240)
        self.baln._update_snapshot_for_address(self.test_account3, 50*10**18)
        self.assertEqual(50*10**18, self.baln.stakedBalanceOfAt(self.test_account3, 240//30-1))

        self.set_block(300)
        self.baln._update_snapshot_for_address(self.test_account3, 0)
        self.assertEqual(0, self.baln.stakedBalanceOfAt(self.test_account3, 300//240-1))

        self.set_block(10000)
        self.baln.loadBalnStakeSnapshot([{"address": self.test_account4, "amount": 500*10**18, "day": 32},
                                         {"address": self.test_account4, "amount": 600*10**18, "day": 33},
                                         {"address": self.test_account4, "amount": 700*10**18, "day": 34}])
        self.assertEqual(500*10**18, self.baln.stakedBalanceOfAt(self.test_account4, 32))
        self.assertEqual(600*10**18, self.baln.stakedBalanceOfAt(self.test_account4, 33))
        self.assertEqual(700*10**18, self.baln.stakedBalanceOfAt(self.test_account4, 34))

    def test_totalStakedBalanceOfAt(self):
        self.dex_mock = Address.from_string(f"cx{'abcd' * 10}")

        current_time = int(time.time() * 10**6)
        self.baln.setDex(self.dex_mock)
        self.set_msg(self.test_account1)
        self.patch_internal_method(self.dex_mock, "getTimeOffset", lambda: current_time)

        # Equivalent to day 1
        self.set_block(60)
        self.baln._update_total_staked_snapshot(100 * 10**18)
        self.assertEqual(100 * 10**18, self.baln.totalStakedBalanceOfAt(60//30 - 1))

        # At block height 5000, looking for old snapshot id should return same staked amount
        self.set_block(5000)
        for i in range(60, 5000, 30):
            self.assertEqual(100 * 10**18, self.baln.totalStakedBalanceOfAt(i//30 - 1))

        self.set_block(60)

        # Same day update
        self.baln._update_total_staked_snapshot(120 * 10**18)
        self.assertEqual(120*10**18, self.baln.totalStakedBalanceOfAt(60//30-1))

        self.set_block(120)
        self.baln._update_total_staked_snapshot(130*10**18)
        self.assertEqual(130*10**18, self.baln.totalStakedBalanceOfAt(120//30 - 1))

        # No update and shows the balance of previous day
        self.set_block(180)
        self.assertEqual(130*10**18, self.baln.totalStakedBalanceOfAt(180//30-1))

        self.set_block(240)
        self.baln._update_total_staked_snapshot(50*10**18)
        self.assertEqual(50*10**18, self.baln.totalStakedBalanceOfAt(240//30-1))

        self.set_block(300)
        self.baln._update_total_staked_snapshot(0)
        self.assertEqual(0, self.baln.totalStakedBalanceOfAt(300//240-1))

        self.set_block(10000)
        self.baln.loadTotalStakeSnapshot([{"amount": 5000*10**18, "day": 50}, {"amount": 6000*10**18, "day": 51},
                                          {"amount": 7000*10**18, "day": 52}])
        self.assertEqual(5000*10**18, self.baln.totalStakedBalanceOfAt(50))
        self.assertEqual(6000*10**18, self.baln.totalStakedBalanceOfAt(51))
        self.assertEqual(7000*10**18, self.baln.totalStakedBalanceOfAt(52))
