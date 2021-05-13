import time
from .test_integrate_base import BalancedTestBase


class BalancedTestReserveFund(BalancedTestBase):

    def setUp(self):
        super().setUp()

    def test_add(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        # self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        self.send_tx(self.btest_wallet, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 50 * 10 ** 18})

    # Note: After depositing collateral and taking loan we need to wait 15 minutes to change the day
    # and complete rewards distribution and run the below tests.
    time.sleep(20)

    def test_getBalances(self):
        print('Testing rewards distribution on reserve fund score')
        for i in range(10):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        total_balances = 0
        for contract in ['rewards', 'reserve', 'bwt', 'dex', 'daofund']:
            result = int(self.call_tx(self.contracts['baln'], 'balanceOf', {'_owner': self.contracts[contract]}),0)
            total_balances += result

        print(f'Total BALN: {total_balances / 10 ** 18}')

        res = self.call_tx(self.contracts['rewards'], 'distStatus', {})
        day = int(res['platform_day'], 0) - 1

        res = self.call_tx(self.contracts['reserve'], 'getBalances', {})
        self.assertEqual(int(res['BALN'], 0) / 10 ** 18, 5000 * day, "Reserve not receiving proper rewards")

    # Testing redeem method
    def test_redeem(self):
        print('Testing redeem method on reserve fund score')
        signed_transaction = self.build_tx(self.btest_wallet, self.contracts['reserve'], 0, 'redeem',
                           {'_to': self.user1.get_address(), '_amount': 10 * 10**18, '_sicx_rate': 2})
        res = self.process_transaction(signed_transaction, self.icon_service)
        self.assertEqual(res['failure'][
                   'message'], 'BalancedReserveFund: The redeem method can only be called by the Loans SCORE.',
                         "Redeem methos can only be called from loans")


