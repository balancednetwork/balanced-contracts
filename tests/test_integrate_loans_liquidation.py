from .test_integrate_base import BalancedTestBase
from .stories.liquidation_stories import LIQUIDATION_STORIES


class BalancedTestLiquidation(BalancedTestBase):

    def setUp(self):
        super().setUp()

    def test_liquidation(self):
        test_cases = LIQUIDATION_STORIES

        for case in test_cases['stories']:
            print("############################################################################################")
            print(case['description'])

            icx = case['actions']['deposited_icx']
            test_icx = case['actions']['test_icx']
            test_bnUSD = case['actions']['test_bnUSD']

            self.send_tx(self.btest_wallet, self.contracts['loans'], icx, 'depositAndBorrow',
                         {'_asset': '', '_amount': 0})
            account_position = self.call_tx(self.contracts['loans'], 'getAccountPositions',
                                            {'_owner': self.btest_wallet.get_address()})
            self.assertEqual(account_position['standing'], case['actions']['expected_initial_position'],
                             "Error in Account standing of the loan borrower")
            self.assertEqual(account_position['assets']['sICX'], hex(icx),
                             "Test Case failed for liquidation")

            # This method requires a test method `create_test_position` in the loans contract. If the method is not
            # available, the test case will fail
            self.send_tx(self.btest_wallet, self.contracts['loans'], test_icx, 'create_test_position',
                         {'_address': self.btest_wallet.get_address(), '_asset': 'bnUSD', '_amount': test_bnUSD})
            account_position = self.call_tx(self.contracts['loans'], 'getAccountPositions',
                                            {'_owner': self.btest_wallet.get_address()})
            self.assertEqual(account_position['standing'], case['actions']['expected_position'],
                             "Expected position is not liquidate")

            self.send_tx(self.btest_wallet, self.contracts['loans'], method="liquidate",
                         params={'_owner': self.btest_wallet.get_address()})
            result = self.call_tx(self.contracts['loans'], "getAccountPositions",
                                  {'_owner': self.btest_wallet.get_address()})
            self.assertEqual(result['standing'], case['actions']['expected_result'])
