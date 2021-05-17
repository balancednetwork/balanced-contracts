import time
from .test_integrate_base_loans import BalancedTestBaseLoans
import subprocess


class BalancedTestReserveFund(BalancedTestBaseLoans):
    constants = {"dex": [
        {"WITHDRAW_LOCK_TIMEOUT": ["WITHDRAW_LOCK_TIMEOUT = 30000000", "WITHDRAW_LOCK_TIMEOUT = 86400 * (10 ** 6)"]},
        {"U_SECONDS_DAY": ["U_SECONDS_DAY= 30000000", "U_SECONDS_DAY = 86400 * (10 ** 6)"]}],
                 "governance": [{"U_SECONDS_DAY": ["U_SECONDS_DAY = 30000000", "U_SECONDS_DAY = 86400 * (10 ** 6)"]},
                                {"DAY_ZERO": ["DAY_ZERO = 18647 * 2880", "DAY_ZERO = 18647"]}],
                 "loans": [{"U_SECONDS_DAY": ["U_SECONDS_DAY = 30000000", "U_SECONDS_DAY = 86400 * (10 ** 6)"]}],
                 "rewards": [{"DAY_IN_MICROSECONDS": ["DAY_IN_MICROSECONDS = 30000000",
                                                      "DAY_IN_MICROSECONDS = 86400 * (10 ** 6)"]}]}

    def patch_constants(self, file_name, old_value, new_value):
        subprocess.call("sed -i -e 's/^" + old_value + ".*/" + new_value + "/' " + file_name, shell=True)

    def setUp(self):
        super().setUp()
        for key, value in self.constants.items():
            # print(value)
            for i in value:
                lis1 = []
                for x, y in i.items():
                    lis1.append(x)
                    # lis1.append(y)
                    self.patch_constants("core_contracts/" + key + "/utils/consts.py", lis1[0], y[0])

            self.update(key)

    def tearDown(self):
        for key, value in self.constants.items():
            # print(value)
            for i in value:
                lis1 = []
                for x, y in i.items():
                    lis1.append(x)
                    # lis1.append(y)
                    self.patch_constants("core_contracts/" + key + "/utils/consts.py", lis1[0], y[1])

    def _add(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        # self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        self.send_tx(self.btest_wallet, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 50 * 10 ** 18})

    def test_getBalances(self):
        self._add()
        time.sleep(5)
        print('Testing rewards distribution and redeem method on reserve fund score')
        for i in range(5):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        total_balances = 0
        for contract in ['rewards', 'reserve', 'bwt', 'dex', 'daofund']:
            result = int(self.call_tx(self.contracts['baln'], 'balanceOf', {'_owner': self.contracts[contract]}), 0)
            total_balances += result

        print(f'Total BALN: {total_balances / 10 ** 18}')

        res = self.call_tx(self.contracts['rewards'], 'distStatus', {})
        day = int(res['platform_day'], 0) - 1

        res = self.call_tx(self.contracts['reserve'], 'getBalances', {})
        self.assertEqual(int(res['BALN'], 0) / 10 ** 18, 5000 * day, "Reserve not receiving proper rewards")

        self._redeem()

    # Testing redeem method
    def _redeem(self):
        # print('Testing redeem method on reserve fund score')
        signed_transaction = self.build_tx(self.btest_wallet, self.contracts['reserve'], 0, 'redeem',
                                           {'_to': self.user1.get_address(), '_amount': 10 * 10 ** 18, '_sicx_rate': 2})
        res = self.process_transaction(signed_transaction, self.icon_service)
        self.assertEqual(res['failure'][
                             'message'],
                         'BalancedReserveFund: The redeem method can only be called by the Loans SCORE.',
                         "Redeem methos can only be called from loans")
