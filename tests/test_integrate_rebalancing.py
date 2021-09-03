import re
import subprocess

from .test_integrate_base_rebalancing import BalancedTestBaseRebalancing
from .stories.rebalancing_stories import REBALANCING_STORIES
from iconservice import *
from iconsdk.wallet.wallet import KeyWallet


class BalancedTestLiquidation(BalancedTestBaseRebalancing):

    def patch_constants(self, current, replace_with):
        read_lines = 'data_for_dex = b\'{"method": "_swap", "params": {"toToken": "' + current + '"}}\'\n'
        with open("core_contracts/loans/utils/consts.py") as file:
            file_lines = file.readlines()

        if read_lines not in file_lines:
            raise
        file_lines = [i
                      if i != read_lines
                      else read_lines.replace(current, replace_with)
                      for i in file_lines]
        with open("core_contracts/loans/utils/consts.py", "w") as file:
            file_lines = file.writelines(file_lines)

    def setUp(self):
        super().setUp()
        bnUSD = self.get_bnusd_address()

        current_bnUSD_address = "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"
        new_bnUSD_address = bnUSD
        self.patch_constants(current_bnUSD_address, new_bnUSD_address)

    def tearDown(self):
        bnUSD = self.get_bnusd_address()

        current_bnUSD_address = bnUSD
        new_bnUSD_address = "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"
        self.patch_constants(current_bnUSD_address, new_bnUSD_address)

    def setAddresses(self):

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setRebalancing',
                     {"_address": self.contracts['rebalancing']})
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setGovernance',
                     {"_address": self.contracts['governance']})

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'rebalancingSetSicx',
                     {"_address": self.contracts['sicx']})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'rebalancingSetBnusd',
                     {"_address": self.contracts['bnUSD']})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'rebalancingSetLoans',
                     {"_address": self.contracts['loans']})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'rebalancingSetDex',
                     {"_address": self.contracts['dex']})

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setLoansRebalance',
                     {"_address": self.contracts['rebalancing']})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setLoansDex',
                     {"_address": self.contracts['dex']})

        # self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setRebalancingSicxThreshold',
        #              {"_value": 1000 * 10 ** 18})

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setRebalancingThreshold',
                     {"_value": 5 * 10 ** 17})
        # self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setRebalancingMaxSicxRetire',
        #              {"_value": 1000 * 10 ** 18})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setMaxRetireAmount',
                     {"_sicx_value": 1000 * 10 ** 18, "_bnusd_value": 1000 * 10 ** 18})

    def test_rebalance(self):
        self.score_update("loans")
        test_cases = REBALANCING_STORIES
        self.send_tx(self._test1, self.contracts['loans'], 1200000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 450000 * 10 ** 18})

        self.setAddresses()
        wallets = []

        for i in range(5):
            wallets.append(KeyWallet.create())

        for i in range(5):
            self.send_icx(self.btest_wallet, wallets[i].get_address(), 2500 * 10 ** 18)

        for i in range(5):
            self.send_tx(wallets[i], self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                         {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})

        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        # testing the condition where user1 deposits collateral taking 10 bnUSD loan
        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 50 * 10 ** 18})
        self.send_tx(self.user2, self.contracts['loans'], 2000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 200 * 10 ** 18})
        self.send_tx(self.user2, self.contracts['loans'], 0, 'returnAsset',
                     {'_symbol': 'bnUSD', '_value': 195 * 10 ** 18})

        for case in test_cases['stories']:
            print("############################################################################################")
            print(case['description'])

            before_sicx = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['loans']})
            loans_sicx_before_rebalancing = int(before_sicx, 0)

            self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

            dat = "{\"method\": \"_swap\", \"params\": {\"toToken\": \"" + self.contracts['sicx'] + "\"}}"
            data = dat.encode("utf-8")
            self.send_tx(self._test1, self.contracts['bnUSD'], 0, case['actions']['method'],
                         {'_to': self.contracts['dex'], '_value': case['actions']['amount'], "_data": data})

            self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

            status = self.call_tx(self.contracts['rebalancing'], 'getRebalancingStatus', {})
            self.assertEqual(int(status[0], 0), case['actions']['rebalancing_status'])

            # account positions after rebalancing
            before = {}
            wallet_dict = {}
            for i in range(len(wallets)):
                wallet_dict = {"user1": self.user1.get_address(), "user2": self.user2.get_address(),
                               "user3": self._test1.get_address(), "user4": wallets[i].get_address(),
                               "user5": wallets[i].get_address(), "user6": wallets[i].get_address(),
                               "user7": wallets[i].get_address(), "user8": wallets[i].get_address()}
            for key, value in wallet_dict.items():
                before[key] = self.get_account_position(value)

            rate = int(self.call_tx(self.contracts['dex'], 'getSicxBnusdPrice'), 0)

            rebabalce = self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'rebalance', {})

            event = (rebabalce['eventLogs'])
            total_batch_debt = 0
            total_debt_sold = 0
            total_collateral_sold = 0
            for i in event:
                res = (i["indexed"])
                for j in res:
                    if "Rebalance" in j:
                        total_batch_debt = int((i["data"][-1]), 0)
                        redeemed_bnusd_dict = (i["data"][-2])
                        redeemed_bnusd = str(redeemed_bnusd_dict).split('{')
                        for x in redeemed_bnusd:
                            if "debt" or "collateral" in x:
                                try:
                                    debt = int(re.search("debt':(.+?),", x).group(1))
                                    collateral = int(re.search("collateral':(.+?)}", x).group(1))
                                    total_debt_sold += debt
                                    total_collateral_sold += collateral
                                except AttributeError:
                                    pass

            # account positions after rebalancing
            after = {}
            for key, value in wallet_dict.items():
                after[key] = self.get_account_position(value)

            # users bnUSD retired percent
            before_list = list(before.keys())
            after_list = list(after.keys())
            change = []
            for i in range(len(wallet_dict)):
                if before[before_list[i]] != 0:
                    change.append((before[before_list[i]] - after[after_list[i]]) * 10**18 // (before[before_list[i]]) * 100)

            for i in range(len(change) - 1):
                self.assertEqual(change[i], change[i + 1], "Error in user's retired bnUSD percent ")

            sicx_after = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['loans']})
            loans_sicx_after_rebalancing = int(sicx_after, 0)

            _retire_amount = self.call_tx(self.contracts['loans'], 'getMaxRetireAmount')
            max_retire_amount = int(_retire_amount['sICX'], 0)
            expected = (10 * total_batch_debt * 10**18) // (rate * 10000)
            retired_sicx = min(int(status[1], 0), max_retire_amount, expected)

            self.assertEqual(abs(total_collateral_sold), retired_sicx, "The reduced value is not equal to the sicx sold")

            if int(status[0], 0) == 1:
                self.assertEqual((loans_sicx_before_rebalancing - retired_sicx), loans_sicx_after_rebalancing)

            self.call_tx(self.contracts['rebalancing'], 'getRebalancingStatus', {})

    def get_account_position(self, user: str) -> int:
        user_position = self.call_tx(self.contracts['loans'], 'getAccountPositions',
                                     {"_owner": user})
        if 'bnUSD' in user_position['assets']:
            return int(user_position['assets']['bnUSD'], 0)
        else:
            return 0

    # def test_rebalance_down(self):
    #     self.test_update()
    #     test_cases = REBALANCING_DOWN_STORIES
    #     self.send_tx(self._test1, self.contracts['loans'], 750000 * 10 ** 18, 'depositAndBorrow',
    #                  {'_asset': 'bnUSD', '_amount': 300000 * 10 ** 18})
    #     self.send_tx(self.btest_wallet, self.contracts['staking'], 5000 * 10 ** 18, 'stakeICX',
    #                  {"_to": self._test1.get_address()})
    #     self.send_tx(self.btest_wallet, self.contracts['staking'], 1000 * 10 ** 18, 'stakeICX',
    #                  {"_to": self.contracts['rebalancing']})
    #     self.send_tx(self._test1, self.contracts['bnUSD'], 0, 'transfer',
    #                  {'_to': self.contracts['rebalancing'], '_value': 1000*10**18})
    #
    #     self.setAddresses()
    #
    #     self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
    #     self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)
    #     self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
    #                  {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})
    #     self.send_tx(self.user2, self.contracts['loans'], 2000 * 10 ** 18, 'depositAndBorrow',
    #                  {'_asset': 'bnUSD', '_amount': 200 * 10 ** 18})
    #
    #     for case in test_cases['stories']:
    #         print("############################################################################################")
    #         print(case['description'])
    #
    #         res = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
    #         self.assertEqual(int(res, 0), case['actions']['initial_sicx_in_rebalancer'])
    #
    #         res = self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
    #         self.assertEqual(int(res, 0), case['actions']['initial_bnUSD_in_rebalancer'])
    #
    #         self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})
    #
    #         dat = "{\"method\": \"_swap\", \"params\": {\"toToken\": \""+self.contracts['bnUSD']+"\"}}"
    #         data = dat.encode("utf-8")
    #         self.send_tx(self._test1, self.contracts['sicx'], 0, case['actions']['method'],
    #                      {'_to': self.contracts['dex'], '_value': case['actions']['amount'], "_data": data})
    #
    #         self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})
    #
    #         status = self.call_tx(self.contracts['rebalancing'], 'getRebalancingStatus', {})
    #         self.assertEqual(int(status[0], 0), case['actions']['rebalancing_status'])
    #
    #         self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user1.get_address()})
    #         self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user2.get_address()})
    #
    #         self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'rebalance', {})
    #
    #         self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user1.get_address()})
    #         self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user2.get_address()})
    #
    #         res = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
    #         self.assertEqual(int(res, 0), case['actions']['final_sicx_in_rebalancer'])
    #
    #         res = self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
    #         self.assertEqual(int(res, 0), case['actions']['final_bnUSD_in_rebalancer'])
    #
    #         self.call_tx(self.contracts['rebalancing'], 'getRebalancingStatus', {})
