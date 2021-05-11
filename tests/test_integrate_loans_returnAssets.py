from .test_integrate_base import BalancedTestBase
from .stories.loan_retireAssets import RETURN_ASSETS_STORIES


class BalancedTestLiquidation(BalancedTestBase):

    def setUp(self):
        super().setUp()

    def test_retire(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10**18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10**18)

        self.call_tx(self.contracts['loans'], 'getAccountPositions', {'_owner': self.user1.get_address()})
        self.call_tx(self.contracts['loans'], 'getAccountPositions', {'_owner': self.user2.get_address()})

        # add collateral to user1 account
        self.send_tx(self.user1, self.contracts['loans'], 2000 * 10**18, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 500 * 10**18})

        # gives maximum retire amount
        self.call_tx(self.contracts['loans'], 'getMaxRetireAmount', {'_symbol': 'bnUSD'})
        test_cases = RETURN_ASSETS_STORIES

        for case in test_cases['stories']:
            print(case['description'])
            meth1 = case['actions']['first_meth']
            meth2 = case['actions']['second_meth']
            val = int(case['actions']['deposited_icx'])
            data1 = case['actions']['first_params']
            first_params = {"_to": data1['_to'], "_value": data1['_value']}

            data2 = case['actions']['second_params']
            second_params = {'_symbol': data2['_symbol'], '_value': data2['_value']}

            self.send_tx(self.user1, self.contracts['bnUSD'], 0, meth1, first_params)
            res = self.send_tx(self.user2, self.contracts['loans'], 0, meth2, second_params)
            assert res['status'] == int(
                case['actions']['expected_status_result']), 'Retired amount is greater than the current maximum allowed'
            print('Test case passed')

