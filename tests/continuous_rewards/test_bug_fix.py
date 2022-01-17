import time

from .test_integrate_base_loans import BalancedTestBaseLoans

daily_emission = 100000
sec_per_day = 180000000

class BalancedTestDepositAndBorrow(BalancedTestBaseLoans):

    def setUp(self):
        super().setUp()

    def stakeLpToken(self, wallet, address, basetoken, quotetoken):
        data = "{\"method\": \"_deposit\"}".encode("utf-8")
        print("sending bnusd and sicx to the user2 wallet")
        self.send_tx(self._test1, basetoken, 0, 'transfer', {"_to": address,
                                                                          "_value": 30 * 10 ** 18})
        self.send_tx(self._test1, quotetoken, 0, 'transfer', {"_to": address,
                                                                           "_value": 30 * 10 ** 18})

        print("deposits token to dex for bnusd/sicx pool")
        self.send_tx(wallet, quotetoken, 0, 'transfer', {"_to": self.contracts['dex'],
                                                                      "_value": 30 * 10 ** 18,
                                                                      "_data": data})
        self.send_tx(wallet, basetoken, 0, 'transfer', {"_to": self.contracts['dex'],
                                                                     "_value": 30 * 10 ** 18,
                                                                     "_data": data})

        print("Adds token to dex")
        par = {"_baseToken": basetoken,
               "_quoteToken": quotetoken
            , "_baseValue": 30 * 10 ** 18, "_quoteValue": 30 * 10 ** 18}
        self.send_tx(wallet, self.contracts['dex'], 0, 'add', par)

        data = "{\"method\": \"_stake\"}".encode("utf-8")

        print("stakes lp token")
        tx = self.send_tx(wallet, self.contracts['dex'], 0, 'transfer',
                          {"_to": self.contracts['stakedLp'], "_value": 5 * 10 ** 18, '_id': 2, "_data": data})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        return bheight['time_stamp']

    def claim_rewards(self, wallet):
        tx = self.send_tx(wallet, self.contracts['rewards'], 0, 'claimRewards', {})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        return bheight['time_stamp']

    def calculate_rewards(self, start_time, end_time, address, pool_id, pool_name):
        lp_user_balance = (self.call_tx(self.contracts['stakedLp'], 'balanceOf', {"_owner": address, "_id": pool_id}))
        totalsupply_lp = (self.call_tx(self.contracts['stakedLp'], 'totalSupply', {"_id": pool_id}))
        elapsed_time = (end_time - start_time)
        user_baln = int(self.balanceOfTokens('baln', address), 16)

        # calculation of rewards
        lp_user_balance = int(lp_user_balance, 16)
        totalsupply_lp = int(totalsupply_lp, 16)
        print(lp_user_balance)
        print(totalsupply_lp)
        print(elapsed_time)

        recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        percent = int(recipient[pool_name], 16) / 10 ** 18
        print(percent)

        rewards = elapsed_time * percent * daily_emission * lp_user_balance / (sec_per_day * totalsupply_lp)
        user_baln = user_baln / 10 ** 18
        print(rewards)
        print(user_baln)
        self.assertAlmostEqual(rewards, user_baln)

    def sicx_bnusd_allocation(self, wallet, address, flag: int = 0):
        data = "{\"method\": \"_deposit\"}".encode("utf-8")
        print("sending bnusd and sicx to the user2 wallet")
        self.send_tx(self._test1, self.contracts['sicx'], 0, 'transfer', {"_to": address,
                                                                          "_value": 30 * 10 ** 18})
        self.send_tx(self._test1, self.contracts['bnUSD'], 0, 'transfer', {"_to": address,
                                                                           "_value": 30 * 10 ** 18})

        print("deposits token to dex for bnusd/sicx pool")
        self.send_tx(wallet, self.contracts['bnUSD'], 0, 'transfer', {"_to": self.contracts['dex'],
                                                                          "_value": 30 * 10 ** 18,
                                                                          "_data": data})
        self.send_tx(wallet, self.contracts['sicx'], 0, 'transfer', {"_to": self.contracts['dex'],
                                                                         "_value": 30 * 10 ** 18,
                                                                         "_data": data})

        print("Adds token to dex")
        par = {"_baseToken": self.contracts['sicx'],
               "_quoteToken": self.contracts['bnUSD']
            , "_baseValue": 30 * 10 ** 18, "_quoteValue": 30 * 10 ** 18}
        self.send_tx(wallet, self.contracts['dex'], 0, 'add', par)

        data = "{\"method\": \"_stake\"}".encode("utf-8")

        print("stakes lp token")
        tx = self.send_tx(wallet, self.contracts['dex'], 0, 'transfer',
                          {"_to": self.contracts['stakedLp'], "_value": 5 * 10 ** 18, '_id': 2, "_data": data})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        start = bheight['time_stamp']
        lp_bal = (self.call_tx(self.contracts['stakedLp'], 'balanceOf', {"_owner": address, "_id": 2}))
        ts_lp = (self.call_tx(self.contracts['stakedLp'], 'totalSupply', {"_id": 2}))
        if flag == 1:
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
            while day != 6:
                time.sleep(5)
                day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        tx = self.send_tx(wallet, self.contracts['rewards'], 0, 'claimRewards', {})
        user_baln = int(self.balanceOfTokens('baln', address), 16)
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        end = bheight['time_stamp']
        elapsed_time = end - start

        user_lp_balance = int(lp_bal, 16)
        totalsupply_lp = int(ts_lp, 16)

        recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        percent = int(recipient['sICX/bnUSD'], 16)/10**18
        print(recipient)
        print(user_lp_balance)
        print(totalsupply_lp)
        print(user_baln)
        print(recipient)
        rewards = elapsed_time * percent * daily_emission * user_lp_balance / (sec_per_day * totalsupply_lp)
        user_baln = user_baln / 10 ** 18

        self.assertAlmostEqual(rewards, user_baln)

    def baln_bnusd_allocation(self, wallet , address):
        data = "{\"method\": \"_deposit\"}".encode("utf-8")

        print("sending bnusd and baln to the user1 wallet")
        self.send_tx(self._test1, self.contracts['baln'], 0, 'transfer', {"_to": address,
                                                                          "_value": 30 * 10 ** 18})
        self.send_tx(self._test1, self.contracts['bnUSD'], 0, 'transfer', {"_to": address,
                                                                           "_value": 30 * 10 ** 18})

        print("deposits token to dex for bnusd/baln pool")
        self.send_tx(wallet, self.contracts['bnUSD'], 0, 'transfer', {"_to": self.contracts['dex'],
                                                                          "_value": 30 * 10 ** 18,
                                                                          "_data": data})
        self.send_tx(wallet, self.contracts['baln'], 0, 'transfer', {"_to": self.contracts['dex'],
                                                                         "_value": 30 * 10 ** 18,
                                                                         "_data": data})

        par = {"_baseToken": self.contracts['baln'],
               "_quoteToken": self.contracts['bnUSD']
            , "_baseValue": 30 * 10 ** 18, "_quoteValue": 30 * 10 ** 18}
        print("Adds token to dex")
        self.send_tx(wallet, self.contracts['dex'], 0, 'add', par)

        data = "{\"method\": \"_stake\"}".encode("utf-8")
        print("stakes Lp Token")
        tx = self.send_tx(wallet, self.contracts['dex'], 0, 'transfer',
                          {"_to": self.contracts['stakedLp'], "_value": 5 * 10 ** 18, '_id': 3, "_data": data})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        start = bheight['time_stamp']

        lp_user_balance = (self.call_tx(self.contracts['stakedLp'], 'balanceOf', {"_owner": address, "_id": 3}))
        totalsupply_lp = (self.call_tx(self.contracts['stakedLp'], 'totalSupply', {"_id": 3}))

        tx = self.send_tx(wallet, self.contracts['rewards'], 0, 'claimRewards', {})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        end = bheight['time_stamp']
        elapsed_time = (end - start)
        user_baln = int(self.balanceOfTokens('baln', address), 16)

        # calculation of rewards
        lp_user_balance = int(lp_user_balance, 16)
        totalsupply_lp = int(totalsupply_lp, 16)

        recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        percent = int(recipient['BALN/bnUSD'], 16)/10**18

        rewards = elapsed_time * percent * daily_emission * lp_user_balance / (sec_per_day * totalsupply_lp)
        user_baln = user_baln / 10 ** 18
        self.assertAlmostEqual(rewards, user_baln)

    def baln_sicx_allocation(self, wallet, address):
        data = "{\"method\": \"_deposit\"}".encode("utf-8")

        print("sending bnusd and baln to the user1 wallet")
        self.send_tx(self._test1, self.contracts['baln'], 0, 'transfer', {"_to": address,
                                                                          "_value": 30 * 10 ** 18})
        self.send_tx(self.btest_wallet, self.contracts['sicx'], 0, 'transfer', {"_to": address,
                                                                           "_value": 30 * 10 ** 18})
        print("deposits token to dex for sicx/baln pool")
        self.send_tx(wallet, self.contracts['baln'], 0, 'transfer', {"_to": self.contracts['dex'],
                                                                          "_value": 30 * 10 ** 18,
                                                                          "_data": data})
        self.send_tx(wallet, self.contracts['sicx'], 0, 'transfer', {"_to": self.contracts['dex'],
                                                                         "_value": 30 * 10 ** 18,
                                                                         "_data": data})

        par = {"_baseToken": self.contracts['baln'],
               "_quoteToken": self.contracts['sicx']
            , "_baseValue": 30 * 10 ** 18, "_quoteValue": 30 * 10 ** 18}
        self.send_tx(wallet, self.contracts['dex'], 0, 'add', par)

        data = "{\"method\": \"_stake\"}".encode("utf-8")
        tx = self.send_tx(wallet, self.contracts['dex'], 0, 'transfer',
                          {"_to": self.contracts['stakedLp'], "_value": 5 * 10 ** 18, '_id': 4, "_data": data})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        start = bheight['time_stamp']

        lp_user_balance = (
            self.call_tx(self.contracts['stakedLp'], 'balanceOf', {"_owner": address, "_id": 4}))
        totalsupply_lp = (self.call_tx(self.contracts['stakedLp'], 'totalSupply', {"_id": 4}))

        tx = self.send_tx(wallet, self.contracts['rewards'], 0, 'claimRewards', {})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        end = bheight['time_stamp']
        elapsed_time = (end - start)
        user_baln = int(self.balanceOfTokens('baln', address), 16)

        # calculation of rewards
        lp_user_balance = int(lp_user_balance, 16)
        totalsupply_lp = int(totalsupply_lp, 16)
        recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        percent = int(recipient['BALN/sICX'], 16)/10**18
        rewards = elapsed_time * percent * daily_emission * lp_user_balance / (sec_per_day * totalsupply_lp)
        user_baln = user_baln / 10 ** 18
        self.assertAlmostEqual(rewards, user_baln)

    def icx_sicx_allocation(self):
        tx = self.send_icx(self.user4, self.contracts['dex'], 50 * 10 **18)
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        start = bheight['time_stamp']

        tx = self.send_tx(self.user4, self.contracts['rewards'], 0, 'claimRewards', {})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        end = bheight['time_stamp']
        elapsed_time = (end - start)
        user_baln = int(self.balanceOfTokens('baln', self.user4.get_address()), 16)

        # calculation of rewards
        recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        percent = int(recipient['sICX/ICX'], 16) / 10 ** 18

        rewards = elapsed_time * percent * daily_emission  / (sec_per_day )
        user_baln = user_baln / 10 ** 18
        print(rewards)
        # print(user_baln)
        self.assertAlmostEqual(rewards, user_baln)

    def borrower_allocation(self, wallet, address):
        params = {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18}
        print("Taking loans from user4 wallet")
        tx = self.send_tx(wallet, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        start = bheight['time_stamp']
        tx = self.send_tx(wallet, self.contracts['rewards'], 0, 'claimRewards', {})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        end = bheight['time_stamp']
        elapsed_time = (end - start)

        user_baln = int(self.balanceOfTokens('baln', address), 16)
        user_baln = user_baln / 10 ** 18
        bnusd_supply = int(self.totalSupply('bnUSD'), 16)
        recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        loans_percent = int(recipient['Loans'], 16)/10**18
        pos = self._getAccountPositions(address)
        user_debt = int(pos['assets']['bnUSD'], 16)
        # calculation of rewards
        rewards = ((user_debt / bnusd_supply) * loans_percent * daily_emission * elapsed_time) / sec_per_day
        self.assertAlmostEqual(rewards, user_baln)

    def test_data_source_allocation(self):

        print("Setting continuous day as 1")

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": 2})
        day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        while day != 2:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        params = {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18}
        for i in range(20):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        # print("Taking loans from btest_wallet")
        # self.send_tx(self.btest_wallet, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
        #
        print("Taking loans from _test1")
        self.send_tx(self._test1, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow',
                     {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18})

        print("create Bnusd Market on day 1")
        self.send_tx(self.btest_wallet, self.contracts['governance'], 1000 * 10 ** 18, 'createBnusdMarket', {})
        day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        while day != 3:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        for i in range(15):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self._test1, self.contracts['staking'], 500 * 10 ** 18, 'stakeICX', {})

        # print("create baln market")
        # self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'createBalnMarket',
        #              {"_bnUSD_amount": 50 * 10 ** 18, "_baln_amount": 50 * 10 ** 18})
        #
        # self.send_tx(self.btest_wallet, self.contracts['staking'], 500 * 10 ** 18, 'stakeICX', {})
        # self.send_tx(self.btest_wallet, self.contracts['sicx'], 0, 'transfer', {"_to": self.contracts['governance'],
        #                                                                         "_value": 51 * 10 ** 18})
        # print("create baln/sicx market")
        # self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'createBalnSicxMarket',
        #              {"_sicx_amount": 50 * 10 ** 18, "_baln_amount": 50 * 10 ** 18})

        # print("distribution percentage is changed")
        # self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'updateBalTokenDistPercentage',
        #              {"_recipient_list": [{'recipient_name': 'Loans', 'dist_percent': 10 * 10 ** 16},
        #                                   {'recipient_name': 'sICX/ICX', 'dist_percent': 5 * 10 ** 16},
        #                                   {'recipient_name': 'Worker Tokens', 'dist_percent': 20 * 10 ** 16},
        #                                   {'recipient_name': 'Reserve Fund', 'dist_percent': 1 * 10 ** 16},
        #                                   {'recipient_name': 'DAOfund', 'dist_percent': 20 * 10 ** 16},
        #                                   {'recipient_name': 'sICX/bnUSD', 'dist_percent': 145 * 10 ** 15},
        #                                   {'recipient_name': 'BALN/bnUSD', 'dist_percent': 145 * 10 ** 15},
        #                                   {'recipient_name': 'BALN/sICX', 'dist_percent': 15 * 10 ** 16}]})
        # self.send_tx(self._test1, self.contracts['rewards'], 0, 'claimRewards', {})
        # self.send_tx(self._test1, self.contracts['staking'], 500 * 10 ** 18, 'stakeICX', {})
        print(
            f"Before day is changed , get baln holding is {self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user4.get_address())})}")

        user4_start = self.stakeLpToken(self.user4, self.user4.get_address(), self.contracts['sicx'], self.contracts['bnUSD'])

        while day != 4:
            time.sleep(5)
            print(f"while day is changing , get baln holding is {self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user4.get_address())})}")
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        print(
            f"After day is changed , get baln holding is {self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user4.get_address())})}")
        for i in range(15):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        print(
            f"After distribute is called , get baln holding is {self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user4.get_address())})}")
        user4_end = self.claim_rewards(self.user4)
        print(f"After distribute is called , get baln holding is {self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user4.get_address())})}")
        self.calculate_rewards(user4_start, user4_end, self.user4.get_address(), 2, 'sICX/bnUSD')
        raise e

    def balanceOfTokens(self, name, address):
        params = {
            "_owner": address
        }
        response = self.call_tx(self.contracts[name], "balanceOf", params)
        return response

    def totalSupply(self, name):
        response = self.call_tx(self.contracts[name], "totalSupply", {})
        return response

    def _getAccountPositions(self, address) -> dict:
        params = {'_owner': address}
        result = self.call_tx(self.contracts['loans'], "getAccountPositions", params)
        return result
