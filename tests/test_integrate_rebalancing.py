import subprocess

from .test_integrate_base_rebalancing import BalancedTestBaseRebalancing
from .stories.rebalancing_stories import REBALANCING_STORIES, REBALANCING_DOWN_STORIES
from iconservice import *


class BalancedTestLiquidation(BalancedTestBaseRebalancing):

    def patch_constants(self, file_name, old_value, new_value):
        subprocess.call("sed -i -e 's/^" + old_value + ".*/" + new_value + "/' " + file_name, shell=True)

    def setUp(self):
        super().setUp()
        bnUSD = self.get_bnusd_address()
        sicx = self.get_sicx_address()
        # old = 'data_bytes = b'+"'"+'{"method": "_swap", "params": {"toToken": "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"}}'+"'"
        old = 'data = {"method": "_swap", "params": {"toToken": "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"}}'
        # old = ['data = {"method": "_swap", "params": {"toToken": "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"}}',
        #        'data_sicx = {"method": "_swap", "params": {"toToken": "cx2609b924e33ef00b648a409245c7ea394c467824"}}']
        # new = 'data_bytes = b'+"'"+'{"method": "_swap", "params": {"toToken": "'+bnUSD+'"}}'+"'"
        new = 'data = {"method": "_swap", "params": {"toToken": "'+bnUSD+'"}}'
        print(old,new)
        # new = ['data = {"method": "_swap", "params": {"toToken": "' + bnUSD + '"}}',
        #        'data_sicx = {"method": "_swap", "params": {"toToken": "' + sicx + '"}}']

        # for i in range(0, 2):
        self.patch_constants("core_contracts/loans/utils/consts.py", old, new)

    def tearDown(self):
        bnUSD = self.get_bnusd_address()
        sicx = self.get_sicx_address()
        old = 'data = {"method": "_swap", "params": {"toToken": "'+bnUSD+'"}}'
        # old = ['data = {"method": "_swap", "params": {"toToken": "' + bnUSD + '"}}',
        #        'data_sicx = {"method": "_swap", "params": {"toToken": "' + sicx + '"}}']
        #
        # new = ['data = {"method": "_swap", "params": {"toToken": "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"}}',
        #        'data_sicx = {"method": "_swap", "params": {"toToken": "cx2609b924e33ef00b648a409245c7ea394c467824"}}']
        new = 'data = {"method": "_swap", "params": {"toToken": "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"}}'
        # for i in range(0, 2):
        self.patch_constants("core_contracts/loans/utils/consts.py", old, new)

    def setAddresses(self):
        self.send_tx(self.btest_wallet, self.contracts['loans'], 0, 'setRebalance',
                     {"_address": self.contracts['rebalancing']})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setRebalancing',
                     {"_address": self.contracts['rebalancing']})
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setGovernance',
                     {"_address": self.contracts['governance']})

        self.send_tx(self.btest_wallet, self.contracts['loans'], 0, 'setRebalance',
                     {"_address": self.contracts['rebalancing']})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'rebalancingSetSicx',
                     {"_address": self.contracts['sicx']})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'rebalancingSetBnusd',
                     {"_address": self.contracts['bnUSD']})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'rebalancingSetLoans',
                     {"_address": self.contracts['loans']})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'rebalancingSetDex',
                     {"_address": self.contracts['dex']})

        self.send_tx(self.btest_wallet, self.contracts['loans'], 0, 'setDex',
                     {"_address": self.contracts['dex']})

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setRebalancingSicx',
                     {"_value": 1000 * 10**18})
        # self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setRebalancingBnusd',
        #              {"_value": 1000 * 10 ** 18})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setRebalancingThreshold',
                     {"_value": 5 * 10 ** 17})

    def test_rebalance(self):
        self.test_update()
        test_cases = REBALANCING_STORIES
        self.send_tx(self._test1, self.contracts['loans'], 750000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 300000 * 10 ** 18})
        self.send_tx(self.btest_wallet, self.contracts['staking'], 1000 * 10 ** 18, 'stakeICX',
                     {"_to": self.contracts['rebalancing']})
        # self.send_tx(self._test1, self.contracts['bnUSD'], 0, 'transfer',
        #              {'_to': self.contracts['rebalancing'], '_value': 1000*10**18})

        self.setAddresses()

        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})
        self.send_tx(self.user2, self.contracts['loans'], 2000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 200 * 10 ** 18})

        for case in test_cases['stories']:
            print("############################################################################################")
            print(case['description'])

            # res = self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            # self.assertEqual(int(res, 0), case['actions']['initial_bnUSD_in_rebalancer'])

            res = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            self.assertEqual(int(res, 0), case['actions']['initial_sicx_in_rebalancer'])

            self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

            dat = "{\"method\": \"_swap\", \"params\": {\"toToken\": \""+self.contracts['sicx']+"\"}}"
            data = dat.encode("utf-8")
            self.send_tx(self._test1, self.contracts['bnUSD'], 0, case['actions']['method'],
                         {'_to': self.contracts['dex'], '_value': case['actions']['amount'], "_data": data})

            self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

            status = self.call_tx(self.contracts['rebalancing'], 'getRebalancingStatus', {})
            self.assertEqual(str(status[0]), case['actions']['rebalancing_status'])

            # account positions after rebalancing
            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user1.get_address()})
            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user2.get_address()})
            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self._test1.get_address()})

            self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'rebalance', {})

            # account positions after rebalancing
            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user1.get_address()})
            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user2.get_address()})
            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self._test1.get_address()})

            # res = self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            # self.assertEqual(int(res, 0), case['actions']['final_bnUSD_in_rebalancer'])

            res = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            self.assertEqual(int(res, 0), case['actions']['final_sicx_in_rebalancer'])

            self.call_tx(self.contracts['rebalancing'], 'getRebalancingStatus', {})

    def test_rebalance_down(self):
        self.test_update()
        test_cases = REBALANCING_DOWN_STORIES
        self.send_tx(self._test1, self.contracts['loans'], 750000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 300000 * 10 ** 18})
        self.send_tx(self.btest_wallet, self.contracts['staking'], 5000 * 10 ** 18, 'stakeICX',
                     {"_to": self._test1.get_address()})
        self.send_tx(self.btest_wallet, self.contracts['staking'], 1000 * 10 ** 18, 'stakeICX',
                     {"_to": self.contracts['rebalancing']})
        self.send_tx(self._test1, self.contracts['bnUSD'], 0, 'transfer',
                     {'_to': self.contracts['rebalancing'], '_value': 1000*10**18})

        self.setAddresses()

        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)
        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})
        self.send_tx(self.user2, self.contracts['loans'], 2000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 200 * 10 ** 18})

        for case in test_cases['stories']:
            print("############################################################################################")
            print(case['description'])

            res = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            self.assertEqual(int(res, 0), case['actions']['initial_sicx_in_rebalancer'])

            res = self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            self.assertEqual(int(res, 0), case['actions']['initial_bnUSD_in_rebalancer'])

            self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

            dat = "{\"method\": \"_swap\", \"params\": {\"toToken\": \""+self.contracts['bnUSD']+"\"}}"
            data = dat.encode("utf-8")
            self.send_tx(self._test1, self.contracts['sicx'], 0, case['actions']['method'],
                         {'_to': self.contracts['dex'], '_value': case['actions']['amount'], "_data": data})

            self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

            status = self.call_tx(self.contracts['rebalancing'], 'getRebalancingStatus', {})
            self.assertEqual(int(status[0], 0), case['actions']['rebalancing_status'])

            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user1.get_address()})
            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user2.get_address()})

            self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'rebalance', {})

            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user1.get_address()})
            self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user2.get_address()})

            res = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            self.assertEqual(int(res, 0), case['actions']['final_sicx_in_rebalancer'])

            res = self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
            self.assertEqual(int(res, 0), case['actions']['final_bnUSD_in_rebalancer'])

            self.call_tx(self.contracts['rebalancing'], 'getRebalancingStatus', {})