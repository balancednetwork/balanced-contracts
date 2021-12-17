import re

from iconsdk.wallet.wallet import KeyWallet

from ..test_integrate_base_loans import BalancedTestBaseLoans


class BalancedTestRebalancing(BalancedTestBaseLoans):

    def setUp(self):
        super().setUp()

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

    def test_continuous_rebalance(self):
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

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": 2})

        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})

        self.send_tx(self.user2, self.contracts['loans'], 2000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 200 * 10 ** 18})

        before_bnusd = self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['loans']})
        loans_bnusd_before_rebalancing = int(before_bnusd, 0)
        self.assertEqual(0, loans_bnusd_before_rebalancing, "Loans cannot have bnUSD")

        before_sicx = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['loans']})
        loans_sicx_before_rebalancing = int(before_sicx, 0)

        self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

        dat = "{\"method\": \"_swap\", \"params\": {\"toToken\": \"" + self.contracts['sicx'] + "\"}}"
        data = dat.encode("utf-8")
        self.send_tx(self._test1, self.contracts['bnUSD'], 0, 'transfer',
                     {'_to': self.contracts['dex'], '_value': 400000 * 10**18, "_data": data})

        self.call_tx(self.contracts['dex'], 'getPoolStats', {"_id": 2})

        status = self.call_tx(self.contracts['rebalancing'], 'getRebalancingStatus', {})
        self.assertEqual(int(status[0], 0), 1)

        # account positions before rebalancing
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
        # checking users continuous rewards before rebalancing
        if int(status[0], 0) == 1:
            self._user_rewards(101*10**18)

        rebabalce = self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'rebalance', {})

        # checking users continuous rewards after rebalancing
        if int(status[0], 0) == 1:
            self._user_rewards(100003445656492295363)

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
                        if "d" and "c" in x:
                            debt = int(re.search("d':(.+?),", x).group(1))
                            collateral = int(re.search("c':(.+?)}", x).group(1))
                            total_debt_sold += debt
                            total_collateral_sold += collateral

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
                change.append(
                    (before[before_list[i]] - after[after_list[i]]) * 10 ** 18 // (before[before_list[i]]) * 100)

        for i in range(len(change) - 1):
            self.assertEqual(change[i], change[i + 1], "Error in user's retired bnUSD percent ")

        sicx_after = self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['loans']})
        loans_sicx_after_rebalancing = int(sicx_after, 0)

        bnusd_after = self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['loans']})
        loans_bnusd_after_rebalancing = int(bnusd_after, 0)
        self.assertEqual(0, loans_bnusd_after_rebalancing, "Loans cannot have bnUSD")

        expected = (100 * total_batch_debt * 10 ** 18) // (rate * 10000)
        retired_sicx = min(int(status[1], 0), expected)

        self.assertEqual(abs(total_collateral_sold), retired_sicx,
                         "The reduced value is not equal to the sicx sold")

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

    def _user_rewards(self, user_loan: int):
        '''
        User takes a loan on continuous rewards activation day and
        the rewards allocated for that user is tested.
        '''

        tx = self.send_tx(self.user1, self.contracts['rewards'], 0, 'claimRewards', {})

        # user balance is checked once user claims rewards.
        prev_user_baln = int(self.balanceOfTokens('baln', self.user1.get_address()), 16)
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        start = bheight['time_stamp']

        tx = self.send_tx(self.user1, self.contracts['rewards'], 0, 'claimRewards', {})

        # user balance is checked once user claims rewards.
        cur_user_baln = int(self.balanceOfTokens('baln', self.user1.get_address()), 16)
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        end = bheight['time_stamp']

        user_baln = (cur_user_baln - prev_user_baln) / 10 ** 18

        elapsed_time = (end - start)
        bnusd_supply = int(self.totalSupply('bnUSD'), 16)
        user_debt = user_loan
        daily_emission = 100000
        sec_per_day = 180000000
        loans_percent = 0.25

        # calculation of rewards
        rewards = ((user_debt / bnusd_supply) * loans_percent * daily_emission * elapsed_time) / sec_per_day
        change = rewards - user_baln
        self.assertAlmostEqual(change, 0)

    def totalSupply(self, name):
        response = self.call_tx(self.contracts[name], "totalSupply", {})
        return response

    def balanceOfTokens(self, name, address):
        params = {
            "_owner": address
        }
        response = self.call_tx(self.contracts[name], "balanceOf", params)
        return response