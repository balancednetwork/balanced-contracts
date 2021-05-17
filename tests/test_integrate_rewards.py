import subprocess
import time
from .test_integrate_base import BalancedTestBase
from .stories.rewards_stories import REWARDS_STORIES


class BalancedTestRewards(BalancedTestBase):

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

    def _getDataSourceNames(self):
        print('Testing getDataSourceNames method')
        res = self.call_tx(self.contracts['rewards'], 'getDataSourceNames', {})
        self.assertEqual(res, ['Loans', 'sICX/ICX', 'sICX/bnUSD'], "Data source name error")

    def _getRecipients(self):
        print('Testing getRecipients method')
        res = self.call_tx(self.contracts['rewards'], 'getRecipients', {})
        self.assertEqual(res, ['Worker Tokens', 'Reserve Fund', 'DAOfund', 'Loans', 'sICX/ICX', 'sICX/bnUSD'], "Recipients name error")

    def _getRecipientsSplit(self):
        print('Testing getRecipientsSplit method')
        res = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        self.assertEqual(res, {'Worker Tokens': '0x2c68af0bb140000',
                       'Reserve Fund': '0xb1a2bc2ec50000',
                       'DAOfund': '0x31f5c4ed2768000',
                       'Loans': '0x3782dace9d90000',
                       'sICX/ICX': '0x16345785d8a0000',
                       'sICX/bnUSD': '0x26db992a3b18000'}, "Recipients name error")

    def _getDataSources(self):
        print('Testing getDataSources method')
        res = self.call_tx(self.contracts['rewards'], 'getDataSources', {})
        self.assertEqual(int(res['Loans']['dist_percent'], 0), 250000000000000000, "Loans distribution precent error")
        self.assertEqual(int(res['sICX/ICX']['dist_percent'], 0), 100000000000000000, "sICX/ICX distribution precent error")

    def _getSourceData(self):
        test_cases = REWARDS_STORIES
        for case in test_cases['stories']:
            print(case['description'])
            _name = case['name']

            if _name == 'Loans':
                contract = self.contracts['loans']
            elif _name == 'sICX/ICX':
                contract = self.contracts['dex']
            else:
                contract = None

            res = self.call_tx(self.contracts['rewards'], 'getSourceData', {'_name': _name})
            self.assertEqual(res['contract_address'], contract, "Test case failed for " + _name)

    def _getBalnHolding(self):
        for i in range(5):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        borrowerCount = int(self.call_tx(self.contracts['loans'], 'borrowerCount', {}), 0)
        addresses = []
        daily_value = {}
        for i in range(1, borrowerCount + 1):
            position = self.call_tx(self.contracts['loans'], 'getPositionByIndex', {'_index': i, '_day': -1})
            addresses.append(position['address'])

        holders = self.call_tx(self.contracts['rewards'], 'getBalnHoldings', {'_holders': addresses})

        total_balances = 0
        baln_balances = {}
        for contract in ['rewards', 'reserve', 'bwt', 'dex', 'daofund']:
            result = int(self.call_tx(self.contracts['baln'], 'balanceOf', {'_owner': self.contracts[contract]}),
                         0)
            baln_balances[contract] = result / 10 ** 18
            total_balances += result

        i = 0
        holdings = {i: [key, int(holders[key], 0), int(holders[key], 0) / 10 ** 18] for i, key in
                    enumerate(holders.keys())}
        total = 0
        for key in holdings:
            total += holdings[key][1]
            print(f'{holdings[key]}')

        print(f'Total unclaimed: {total / 10 ** 18}')
        print(baln_balances)
        print(f'Total BALN: {total_balances / 10 ** 18}')

        res = self.call_tx(self.contracts['rewards'], 'distStatus', {})
        day = int(res['platform_day'], 0) - 1

        #     total_amount = 25000/borrowerCount
        #     for key in holdings:
        #         self.assertEqual(holdings[key][2], total_amount , "Loans borrowers token distribution error")
        self.assertEqual(baln_balances['rewards'], 52500 * day, "Loans borrowers token distribution error")
        self.assertEqual(baln_balances['reserve'], 5000 * day, "Reserve not receiving proper rewards")
        self.assertEqual(baln_balances['bwt'], 20000 * day, "Worker token distribution error")
        self.assertEqual(baln_balances['daofund'], 22500 * day, "DAO Fund token distribution error")

    def _claimRewards(self):
        print('Testing claim rewards method')
        claiming_addresses = {
            "stories": [
                {
                    "claiming_wallet": self.btest_wallet,

                },
                {
                    "claiming_wallet": self._test1,
                },
            ]
        }
        for case in claiming_addresses['stories']:
            self.send_tx(case['claiming_wallet'], self.contracts['rewards'], 0, 'claimRewards', {})
            res = self.call_tx(self.contracts['rewards'], 'getBalnHolding',
                                           {'_holder': case['claiming_wallet'].get_address()})
            self.assertEqual(int(res, 0), 0, "Rewards claiming issue")
            # print('Test case passed while claiming rewards')

    def test_getBalnHolding(self):
        self._getDataSourceNames()
        self._getRecipients()
        self._getRecipientsSplit()
        self._getDataSources()
        self._getSourceData()
        print("Test case with only one user")
        self.send_tx(self.btest_wallet, self.contracts['loans'], 500 * 10**18, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 50 * 10**18})
        time.sleep(5)
        self._getBalnHolding()
        print("Test case with multiple users")
        self.send_tx(self._test1, self.contracts['loans'], 500 * 10**18, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 50 * 10**18})
        time.sleep(2)
        self._getBalnHolding()

        self._claimRewards()
