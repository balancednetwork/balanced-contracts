import time

from .test_integrate_base_liquidation import BalancedTestBaseLiquidation
from tests.stories.loans.liquidation_stories import LIQUIDATION_STORIES
from .stories.loans.retire_bad_debts_stories import BAD_DEBT_STORIES


class BalancedTestLiquidation(BalancedTestBaseLiquidation):
    def setUp(self):
        super().setUp()

    def test_liquidation(self):
        test_cases = LIQUIDATION_STORIES

        for case in test_cases['stories']:
            print("############################################################################################")
            print(case['description'])
            print(self.call_tx(self.contracts['oracle'], 'get_reference_data',
                               {'_base': "USD", "_quote": "ICX"}))
            icx = case['actions']['deposited_icx']
            oracle_data = case['actions']['oracle']
            self.send_tx(self.btest_wallet, self.contracts['loans'], icx, 'depositAndBorrow',
                         {'_asset': 'bnUSD', '_amount': 300 * 10 ** 18})
            account_position = self.call_tx(self.contracts['loans'], 'getAccountPositions',
                                            {'_owner': self.btest_wallet.get_address()})

            self.assertEqual(account_position['standing'], case['actions']['expected_initial_position'],
                             "Error in Account standing of the loan borrower")
            self.assertEqual(account_position['assets']['sICX'], hex(icx),
                             "Test Case failed for liquidation")

            self.send_tx(self._test1, self.contracts['oracle'], 0, 'set_reference_data',
                         {'_base': 'USD', '_quote': 'ICX', 'rate': oracle_data['rate'],
                          'last_update_base': oracle_data['last_update_base'],
                          'last_update_quote': oracle_data['last_update_quote']})
            account_position = self.call_tx(self.contracts['loans'], 'getAccountPositions',
                                            {'_owner': self.btest_wallet.get_address()})
            self.assertEqual(account_position['standing'], case['actions']['expected_position'],
                             "Expected position is not liquidate")
            time.sleep(25)
            self.send_tx(self._test1, self.contracts['loans'], method="liquidate",
                         params={'_owner': self.btest_wallet.get_address()})
            result = self.call_tx(self.contracts['loans'], "getAccountPositions",
                                  {'_owner': self.btest_wallet.get_address()})
            self.assertEqual(result['standing'], case['actions']['expected_result'])

        self._retireBadDebt()

    def _retireBadDebt(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_tx(self.user1, self.contracts['loans'], 600 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 20 * 10 ** 18})

        test_cases = BAD_DEBT_STORIES

        for case in test_cases['stories']:
            print("############################################################################################")
            print(case['description'])

            bad_bebt = self.call_tx(self.contracts['loans'], "getAvailableAssets", {})
            previous_bad_debt = int(bad_bebt['bnUSD']['bad_debt'], 0)
            bnusd = self.call_tx(self.contracts['bnUSD'], "balanceOf", {'_owner': self.user1.get_address()})
            previous_bnusd = int(bnusd, 0)

            params = case['actions']['args']
            self.send_tx(self.user1, self.contracts['loans'], 0, case['actions']['method'],
                         {'_symbol': params['_symbol'], '_value': params['_value']})
            _bad_debt = self.call_tx(self.contracts['loans'], "getAvailableAssets", {})
            new_bad_debt = int(_bad_debt['bnUSD']['bad_debt'], 0)
            self.assertEqual(new_bad_debt, (previous_bad_debt-10*10**18))
            _bnusd = self.call_tx(self.contracts['bnUSD'], "balanceOf", {'_owner': self.user1.get_address()})
            new_bnusd = int(_bnusd, 0)
            self.assertEqual(new_bnusd, (previous_bnusd-10 * 10**18))

