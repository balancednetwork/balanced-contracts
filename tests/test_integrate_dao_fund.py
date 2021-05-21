import time
from .test_integrate_base_rewards import BalancedTestBaseRewards


class BalancedTestReserveFund(BalancedTestBaseRewards):
    def setUp(self):
        super().setUp()

    def _add(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        # self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        self.send_tx(self.btest_wallet, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 50 * 10 ** 18})

    def get_loans(self):
        res = self.call_tx(self.contracts['daofund'], 'getLoans', {})
        self.assertEqual(res, self.contracts['loans'])

    def test_getBalances(self):
        self._add()
        self.get_loans()
        time.sleep(15)
        print('Testing rewards distribution and redeem method on reserve fund score')
        txs = []
        for i in range(10):
            deploy_tx = self.build_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
            txs.append(deploy_tx)
        self.process_transaction_bulk_without_txresult(txs, self.icon_service)

        total_balances = 0
        for contract in ['rewards', 'reserve', 'bwt', 'dex', 'daofund']:
            result = int(self.call_tx(self.contracts['baln'], 'balanceOf', {'_owner': self.contracts[contract]}), 0)
            total_balances += result

        print(f'Total BALN: {total_balances / 10 ** 18}')

        res = self.call_tx(self.contracts['rewards'], 'distStatus', {})
        day = int(res['platform_day'], 0) - 1

        res = self.call_tx(self.contracts['daofund'], 'getBalances', {})
        self.assertEqual(int(res['BALN'], 0) / 10 ** 18, 40000 * day, "Reserve not receiving proper rewards")

        self._disburse()

    def _disburse(self):
        print('Testing redeem method on dao fund score')
        test_cases = {
            "stories": [
                {
                    "address" : self.contracts['baln'],
                    "asset": "BALN",
                    "expected_result": 1
                },
                {
                    "address": self.contracts['bnUSD'],
                    "asset": "bnUSD",
                    "expected_result": 0,
                    "revertMessage": "DAOfund: Insufficient balance of asset bnUSD in DAOfund."
                }
            ]
        }
        for case in test_cases["stories"]:
            signed_transaction = self.build_tx(self.btest_wallet, self.contracts['governance'], 0, 'daoDisburse',
                                               {"_recipient": self.user1.get_address(), "_amounts": [{"address": case['address'], "amount": 15*10**18, "symbol":case['asset']}]})
            res = self.process_transaction(signed_transaction, self.icon_service)
            if 'revertMessage' in case.keys():
                self.assertEqual(res['failure']['message'], case['revertMessage'],
                                 "Error while calling disburse methods on daofund")
            else:
                self.assertEqual(res['status'], case['expected_result'])

        self._claim()

    def _claim(self):
        print('Testing claim method on dao fund score')
        signed_transaction = self.build_tx(self.user1, self.contracts['daofund'], 0, 'claim', {})
        self.process_transaction(signed_transaction, self.icon_service)
        user1_balance = int(self.call_tx(self.contracts['baln'], 'balanceOf', {"_owner": self.user1.get_address()}), 0)
        self.assertEqual(user1_balance, 15*10**18, "Dao fund disbursement claim error")
