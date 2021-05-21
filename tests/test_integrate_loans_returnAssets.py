from .test_integrate_base_loans import BalancedTestBaseLoans
from tests.stories.loans.retire_assets_stories import RETURN_ASSETS_STORIES


class BalancedTestReturnAssets(BalancedTestBaseLoans):

    def setUp(self):
        super().setUp()

    def test_retire(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10**18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10**18)

        # add collateral to user1 account
        self.send_tx(self.user1, self.contracts['loans'], 2000 * 10**18, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 500 * 10**18})

        # gives maximum retire amount
        # max = self.call_tx(self.contracts['loans'], 'getMaxRetireAmount', {'_symbol': 'bnUSD'})
        test_cases = RETURN_ASSETS_STORIES

        for case in test_cases['stories']:
            print(case['description'])
            meth1 = case['actions']['first_meth']
            meth2 = case['actions']['second_meth']
            val = int(case['actions']['deposited_icx'])
            data1 = case['actions']['first_params']
            first_params = {"_to": self.user2.get_address(), "_value": data1['_value']}

            data2 = case['actions']['second_params']
            second_params = {'_symbol': data2['_symbol'], '_value': data2['_value']}

            # transfer some amount to user2 to retire
            signed_transaction = self.build_tx(self.user1, self.contracts['bnUSD'], 0, meth1, first_params)
            res = self.process_transaction(signed_transaction, self.icon_service)
            if res['status'] == 0:
                self.assertEqual(res['failure']['message'], case['actions']['revertMessage'])
            else:
                # retire some amount from user2
                signed_transaction = self.build_tx(self.user2, self.contracts['loans'], 0, meth2, second_params)
                res = self.process_transaction(signed_transaction, self.icon_service)
                if 'revertMessage' in case['actions'].keys():
                    self.assertEqual(res['failure']['message'], case['actions']['revertMessage'])
                else:
                    self.assertEqual(res['status'], int(case['actions']['expected_status_result']))

