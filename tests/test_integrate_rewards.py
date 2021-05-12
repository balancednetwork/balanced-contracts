import time
from .test_integrate_base import BalancedTestBase
from .stories.rewards_stories import REWARDS_STORIES


class BalancedTestRewards(BalancedTestBase):

    def setUp(self):
        super().setUp()
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

    def test_getDataSourceNames(self):
        print('Testing getDataSourceNames method')
        res = self.call_tx(self.contracts['rewards'], 'getDataSourceNames', {})
        assert res == ['Loans', 'sICX/ICX', 'sICX/bnUSD'], "Data source name error"

    def test_getRecipients(self):
        print('Testing getRecipients method')
        res = self.call_tx(self.contracts['rewards'], 'getRecipients', {})
        assert res == ['Worker Tokens', 'Reserve Fund', 'DAOfund', 'Loans', 'sICX/ICX', 'sICX/bnUSD'], "Recipients name error"

    def test_getRecipientsSplit(self):
        print('Testing getRecipientsSplit method')
        res = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        assert res == {'Worker Tokens': '0x2c68af0bb140000',
                       'Reserve Fund': '0xb1a2bc2ec50000',
                       'DAOfund': '0x31f5c4ed2768000',
                       'Loans': '0x3782dace9d90000',
                       'sICX/ICX': '0x16345785d8a0000',
                       'sICX/bnUSD': '0x26db992a3b18000'}, "Recipients name error"

    def test_getDataSources(self):
        print('Testing getDataSources method')
        res = self.call_tx(self.contracts['rewards'], 'getDataSources', {})
        assert int(res['Loans']['dist_percent'], 0) == 250000000000000000, 'Loans distribution precent error'
        assert int(res['sICX/ICX']['dist_percent'], 0) == 100000000000000000, 'sICX/ICX distribution precent error'

    def test_getSourceData(self):
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
            assert res['contract_address'] == contract, 'Test case failed for ' + _name

    def getBalnHolding(self):
        for i in range(10):
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
        #         assert holdings[key][2] == total_amount , "Loans borrowers token distribution error"
        assert baln_balances['rewards'] == 52500 * day, "Loans borrowers token distribution error"
        assert baln_balances['reserve'] == 5000 * day, "Reserve not receiving proper rewards"
        assert baln_balances['bwt'] == 20000 * day, "Worker token distribution error"
        assert baln_balances['daofund'] == 22500 * day, "DAO Fund token distribution error"

    def test_getBalnHolding(self):
        print("Test case with only one user")
        self.send_tx(self.btest_wallet, self.contracts['loans'], 500 * 10**18, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 50 * 10**18})
        time.sleep(20)
        self.getBalnHolding()
        print("Test case with multiple users")
        self.send_tx(self.btest_wallet, self.contracts['loans'], 500 * 10**18, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 50 * 10**18})
        time.sleep(20)
        self.getBalnHolding()

    def test_zclaimRewards(self):
        print('Testing claim rewards method')
        claiming_addresses = {
            "stories": [
                {
                    "claiming_wallet": self.btest_wallet,

                },
                {
                    "claiming_wallet": self.user1,
                },
            ]
        }
        for case in claiming_addresses['stories']:
            self.send_tx(case['claiming_wallet'], self.contracts['rewards'], 0, 'claimRewards', {})
            res = self.call_tx(self.contracts['rewards'], 'getBalnHolding',
                                           {'_holder': case['claiming_wallet'].get_address()})
            assert int(res, 0) == 0, 'Rewards claiming issue'
            print('Test case passed while claiming rewards')