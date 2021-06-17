
from .test_integrate_base_rebalancing import BalancedTestBaseRebalancing
from .stories.rebalancing_stories import REBALANCING_STORIES
from iconservice import *


class BalancedTestLiquidation(BalancedTestBaseRebalancing):

    def setUp(self):
        super().setUp()

    def setAddresses(self):
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setSicx',
                     {"_address": self.contracts['sicx']})
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setbnUSD',
                     {"_address": self.contracts['bnUSD']})
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setLoans',
                     {"_address": self.contracts['loans']})
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setDex',
                     {"_address": self.contracts['dex']})
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setOracle',
                     {"_address": self.contracts['oracle']})

    def test_rebalance(self):
        test_cases = REBALANCING_STORIES
        self.send_tx(self._test1, self.contracts['loans'], 750000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 300000 * 10 ** 18})

        self.send_tx(self.btest_wallet, self.contracts['staking'], 1000 * 10 ** 18, 'stakeICX',
                     {"_to": self.contracts['rebalancing']})
        self.setAddresses()

        for case in test_cases['stories']:
            print("############################################################################################")
            print(case['description'])

            # self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['rebalancing']})

            res = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            self.assertEqual(int(res, 0), case['actions']['initial_sicx_in_rebalancer'])

            self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

            dat = "{\"method\": \"_swap\", \"params\": {\"toToken\": \""+self.contracts['sicx']+"\"}}"
            data = dat.encode("utf-8")
            self.send_tx(self._test1, self.contracts['bnUSD'], 0, case['actions']['method'],
                         {'_to': self.contracts['dex'], '_value': case['actions']['amount'], "_data": data})

            self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

            self.call_tx(self.contracts['rebalancing'], '_calculate_sicx_to_retire', {})

            self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'rebalance', {})

            res = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            # self.assertEqual(int(res, 0), case['actions']['final_sicx_in_rebalancer'])

            # self.call_tx(self.contracts['dex'], 'getPriceByName', {"_name": "sICX/bnUSD"})
            res = self.call_tx(self.contracts['rebalancing'], '_calculate_sicx_to_retire', {})
            self.assertEqual(res/10**18, case['actions']['sicx_to_retire'])
