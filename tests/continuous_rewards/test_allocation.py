import time

from .test_allocation_base import BalancedTestBaseAllocation

daily_emission = 100000
sec_per_day = 180000000


class BalancedTestDepositAndBorrow(BalancedTestBaseAllocation):

    def setUp(self):
        super().setUp()

    def stakeLpToken(self, wallet, address, basetoken, quotetoken, pool_id):
        data = "{\"method\": \"_deposit\"}".encode("utf-8")
        print("sending bnusd and sicx to the wallet")
        self.send_tx(self._test1, basetoken, 0, 'transfer', {"_to": address,
                                                             "_value": 30 * 10 ** 18})
        self.send_tx(self._test1, quotetoken, 0, 'transfer', {"_to": address,
                                                              "_value": 30 * 10 ** 18})

        print("deposits token to dex ")
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
                          {"_to": self.contracts['stakedLp'], "_value": 20 * 10 ** 18, '_id': pool_id, "_data": data})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        return bheight['time_stamp']

    def claim_rewards(self, wallet):
        print("Claiming rewards")
        tx = self.send_tx(wallet, self.contracts['rewards'], 0, 'claimRewards', {})
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        return bheight['time_stamp']

    def calculate_rewards(self, start_time, end_time, address, pool_id, pool_name, old_recipient={},
                          old_rewards=0, previous_day_sum=0):
        lp_user_balance = (self.call_tx(self.contracts['stakedLp'], 'balanceOf', {"_owner": address, "_id": pool_id}))
        totalsupply_lp = (self.call_tx(self.contracts['stakedLp'], 'totalSupply', {"_id": pool_id}))
        elapsed_time = (end_time - start_time)
        user_baln = int(self.balanceOfTokens('baln', address), 16)
        user_baln = user_baln - old_rewards
        # calculation of rewards
        lp_user_balance = int(lp_user_balance, 16)
        totalsupply_lp = int(totalsupply_lp, 16)

        if old_recipient != {}:
            recipient = old_recipient
            percent = int(recipient[pool_name], 16) / 10 ** 18
            rewards = elapsed_time * percent * daily_emission * lp_user_balance / (sec_per_day * totalsupply_lp)
            return rewards

        else:
            recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        percent = int(recipient[pool_name], 16) / 10 ** 18
        print("Calculation of rewards")
        rewards = elapsed_time * percent * daily_emission * lp_user_balance / (sec_per_day * totalsupply_lp)
        user_baln = user_baln / 10 ** 18
        if previous_day_sum != 0:
            rewards = rewards + previous_day_sum
        self.assertAlmostEqual(rewards, user_baln)
        return rewards

    def borrow_loan(self, wallet):
        params = {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18}
        print("Taking loans from wallet")
        tx = self.send_tx(wallet, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        start = bheight['time_stamp']
        return start

    def loan_rewards(self, start_time, end_time, address, old_recipient={},
                     old_rewards=0, previous_day_sum=0):
        elapsed_time = (end_time - start_time)

        user_baln = int(self.balanceOfTokens('baln', address), 16)
        user_baln = user_baln - old_rewards
        user_baln = user_baln / 10 ** 18
        bnusd_supply = int(self.totalSupply('bnUSD'), 16)
        pos = self._getAccountPositions(address)
        user_debt = int(pos['assets']['bnUSD'], 16)
        if old_recipient != {}:
            recipient = old_recipient
            loans_percent = int(recipient['Loans'], 16) / 10 ** 18
            rewards = ((user_debt / bnusd_supply) * loans_percent * daily_emission * elapsed_time) / sec_per_day
            return rewards
        else:
            recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        loans_percent = int(recipient['Loans'], 16) / 10 ** 18
        # calculation of rewards
        print("calculation of loan rewards")
        rewards = ((user_debt / bnusd_supply) * loans_percent * daily_emission * elapsed_time) / sec_per_day
        if previous_day_sum != 0:
            rewards = rewards + previous_day_sum
        self.assertAlmostEqual(rewards, user_baln)
        return rewards

    def test_data_source_allocation(self):

        print("Setting continuous day as 2")
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": 2})
        params = {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18}

        print("Taking loans from btest_wallet")
        self.send_tx(self.btest_wallet, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
        print(int(self.totalSupply('bnUSD'), 16))

        print("Taking loans from _test1")
        self.send_tx(self._test1, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow',
                     {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18})

        reserve_rewards = (int(self.balanceOfTokens('baln', self.contracts['reserve']), 16))
        bwt_rewards = (int(self.balanceOfTokens('baln', self.contracts['bwt']), 16))
        daofund_rewards = (int(self.balanceOfTokens('baln', self.contracts['daofund']), 16))

        rewards_dict_expected = {'DAOfund': daofund_rewards, 'Reserve Fund': reserve_rewards,
                                 'Worker Tokens': bwt_rewards}
        print("create Bnusd Market on day 1")
        self.send_tx(self.btest_wallet, self.contracts['governance'], 1000 * 10 ** 18, 'createBnusdMarket', {})
        day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        while day != 2:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        for i in range(15):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        rewards_dict = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        for k, v in rewards_dict.items():
            if k in rewards_dict_expected.keys():
                v = int(v, 16)
                rewards_dict_expected[k] += v * 100000 * 2
        rewards_amount = {}
        rewards_amount['Reserve Fund'] = int(self.balanceOfTokens('baln', self.contracts['reserve']), 16)
        rewards_amount['Worker Tokens'] = int(self.balanceOfTokens('baln', self.contracts['bwt']), 16)
        rewards_amount['DAOfund'] = int(self.balanceOfTokens('baln', self.contracts['daofund']), 16)
        self.assertDictEqual(rewards_amount, rewards_dict_expected)

        print("create baln market")
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'createBalnMarket',
                     {"_bnUSD_amount": 50 * 10 ** 18, "_baln_amount": 50 * 10 ** 18})

        self.send_tx(self.btest_wallet, self.contracts['staking'], 500 * 10 ** 18, 'stakeICX', {})
        self.send_tx(self.btest_wallet, self.contracts['sicx'], 0, 'transfer', {"_to": self.contracts['governance'],
                                                                                "_value": 51 * 10 ** 18})
        print("create baln/sicx market")
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'createBalnSicxMarket',
                     {"_sicx_amount": 50 * 10 ** 18, "_baln_amount": 50 * 10 ** 18})

        print("distribution percentage is changed")
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'updateBalTokenDistPercentage',
                     {"_recipient_list": [{'recipient_name': 'Loans', 'dist_percent': 10 * 10 ** 16},
                                          {'recipient_name': 'sICX/ICX', 'dist_percent': 5 * 10 ** 16},
                                          {'recipient_name': 'Worker Tokens', 'dist_percent': 20 * 10 ** 16},
                                          {'recipient_name': 'Reserve Fund', 'dist_percent': 1 * 10 ** 16},
                                          {'recipient_name': 'DAOfund', 'dist_percent': 20 * 10 ** 16},
                                          {'recipient_name': 'sICX/bnUSD', 'dist_percent': 145 * 10 ** 15},
                                          {'recipient_name': 'BALN/bnUSD', 'dist_percent': 145 * 10 ** 15},
                                          {'recipient_name': 'BALN/sICX', 'dist_percent': 15 * 10 ** 16}]})
        self.send_tx(self._test1, self.contracts['rewards'], 0, 'claimRewards', {})
        self.send_tx(self._test1, self.contracts['staking'], 500 * 10 ** 18, 'stakeICX', {})

        while day != 3:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        for i in range(15):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        rewards_dict = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        for k, v in rewards_dict.items():
            if k in rewards_dict_expected.keys():
                v = int(v, 16)
                rewards_dict_expected[k] += v * 100000

        rewards_amount = {}
        rewards_amount['Reserve Fund'] = int(self.balanceOfTokens('baln', self.contracts['reserve']), 16)
        rewards_amount['Worker Tokens'] = int(self.balanceOfTokens('baln', self.contracts['bwt']), 16)
        rewards_amount['DAOfund'] = int(self.balanceOfTokens('baln', self.contracts['daofund']), 16)

        self.assertDictEqual(rewards_amount, rewards_dict_expected)

        user4_start = self.stakeLpToken(self.user4, self.user4.get_address(), self.contracts['sicx'],
                                        self.contracts['bnUSD'], 2)
        user3_start = self.stakeLpToken(self.user3, self.user3.get_address(), self.contracts['baln'],
                                        self.contracts['bnUSD'], 3)
        user2_start = self.stakeLpToken(self.user2, self.user2.get_address(),
                                        self.contracts['baln'], self.contracts['sicx'], 4)
        user5_start = self.borrow_loan(self.user5)
        print("user1 supplies ICX into ICX/sICX pool")
        tx = self.send_icx(self.user1, self.contracts['dex'], 50 * 10 ** 18)
        bheight = self.icon_service.get_block(tx['blockHeight'])
        user1_start = bheight['time_stamp']
        start_timestamp = self.call_tx(self.contracts['rewards'], 'getTimeOffset', {})
        day_end_ts = (4 * 180 * 10 ** 6) + int(start_timestamp, 16)


        while day != 4:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        for i in range(15):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        rewards_dict = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        for k, v in rewards_dict.items():
            if k in rewards_dict_expected.keys():
                v = int(v, 16)
                rewards_dict_expected[k] += v * 100000

        rewards_amount = {}
        rewards_amount['Reserve Fund'] = int(self.balanceOfTokens('baln', self.contracts['reserve']), 16)
        rewards_amount['Worker Tokens'] = int(self.balanceOfTokens('baln', self.contracts['bwt']), 16)
        rewards_amount['DAOfund'] = int(self.balanceOfTokens('baln', self.contracts['daofund']), 16)

        self.assertDictEqual(rewards_amount, rewards_dict_expected)

        user4_end = self.claim_rewards(self.user4)
        user5_end = self.claim_rewards(self.user5)
        user3_end = self.claim_rewards(self.user3)
        user2_end = self.claim_rewards(self.user2)
        user1_end = self.claim_rewards(self.user1)

        print('user5 loans calculation')
        self.loan_rewards(user5_start, user5_end, self.user5.get_address())
        elapsed_time_user1 = (user1_end - user1_start)
        user_baln = int(self.balanceOfTokens('baln', self.user1.get_address()), 16)

        # calculation of rewards
        recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        percent = int(recipient['sICX/ICX'], 16) / 10 ** 18

        rewards = elapsed_time_user1 * percent * daily_emission / sec_per_day

        user_baln = user_baln / 10 ** 18
        self.assertAlmostEqual(rewards, user_baln)

        self.calculate_rewards(user4_start, user4_end, self.user4.get_address(), 2, 'sICX/bnUSD')
        self.calculate_rewards(user3_start, user3_end, self.user3.get_address(), 3, 'BALN/bnUSD')
        self.calculate_rewards(user2_start, user2_end, self.user2.get_address(), 4, 'BALN/sICX')
        old_recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        print("distribution percentage is changed")
        tx = self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'updateBalTokenDistPercentage',
                          {"_recipient_list": [{'recipient_name': 'Loans', 'dist_percent': 20 * 10 ** 16},
                                               {'recipient_name': 'sICX/ICX', 'dist_percent': 145 * 10 ** 15},
                                               {'recipient_name': 'Worker Tokens', 'dist_percent': 10 * 10 ** 16},
                                               {'recipient_name': 'Reserve Fund', 'dist_percent': 20 * 10 ** 16},
                                               {'recipient_name': 'DAOfund', 'dist_percent': 1 * 10 ** 16},
                                               {'recipient_name': 'sICX/bnUSD', 'dist_percent': 10 * 10 ** 16},
                                               {'recipient_name': 'BALN/bnUSD', 'dist_percent': 10 * 10 ** 16},
                                               {'recipient_name': 'BALN/sICX', 'dist_percent': 145 * 10 ** 15}]})

        start_timestamp = self.call_tx(self.contracts['rewards'], 'getTimeOffset', {})
        day_end_ts = (5 * 180 * 10 ** 6) + int(start_timestamp, 16)
        user2_rewards_first = self.calculate_rewards(user2_end, day_end_ts, self.user2.get_address(), 4, 'BALN/sICX',
                                                     old_recipient)
        t2 = day_end_ts - user2_end
        user4_rewards_first = self.calculate_rewards(user4_end, day_end_ts, self.user4.get_address(), 2, 'sICX/bnUSD',
                                                     old_recipient)
        t4 = day_end_ts - user4_end
        user3_rewards_first = self.calculate_rewards(user3_end, day_end_ts, self.user3.get_address(), 3, 'BALN/bnUSD',
                                                     old_recipient)
        t3 = day_end_ts - user3_end
        user5_rewards_first = self.loan_rewards(user5_end, day_end_ts, self.user5.get_address(), old_recipient)
        t5 = day_end_ts - user5_end
        percent = int(old_recipient['sICX/ICX'], 16) / 10 ** 18
        elapsed_time_user1 = day_end_ts - user1_end
        user1_rewards_first = elapsed_time_user1 * percent * daily_emission / sec_per_day

        while day != 5:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        for i in range(15):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        time.sleep(5)

        old_rewards_user2 = self.balanceOfTokens('baln', self.user2.get_address())
        old_rewards_user2 = int(old_rewards_user2, 16)
        old_rewards_user3 = self.balanceOfTokens('baln', self.user3.get_address())
        old_rewards_user3 = int(old_rewards_user3, 16)
        old_rewards_user4 = self.balanceOfTokens('baln', self.user4.get_address())
        old_rewards_user4 = int(old_rewards_user4, 16)
        old_rewards_user5 = self.balanceOfTokens('baln', self.user5.get_address())
        old_rewards_user5 = int(old_rewards_user5, 16)
        old_rewards_user1 = self.balanceOfTokens('baln', self.user1.get_address())
        old_rewards_user1 = int(old_rewards_user1, 16)

        user4_end = self.claim_rewards(self.user4)
        user2_end = self.claim_rewards(self.user2)
        user3_end = self.claim_rewards(self.user3)
        user5_end = self.claim_rewards(self.user5)
        user1_end = self.claim_rewards(self.user1)

        user2_rewards_second = self.calculate_rewards(day_end_ts, user2_end, self.user2.get_address(), 4, 'BALN/sICX'
                                                      , {}, old_rewards_user2, user2_rewards_first)
        user4_rewards_second = self.calculate_rewards(day_end_ts, user4_end, self.user4.get_address(), 2, 'sICX/bnUSD'
                                                      , {}, old_rewards_user4, user4_rewards_first)
        user3_rewards_second = self.calculate_rewards(day_end_ts, user3_end, self.user3.get_address(), 3, 'BALN/bnUSD'
                                                      , {}, old_rewards_user3, user3_rewards_first)
        t1 = elapsed_time_user1
        elapsed_time_user1 = (user1_end - day_end_ts)
        # p1 = elapsed_time_user1 + t1
        # p2 = t2 + user2_end - day_end_ts
        # p3 = t3 + user3_end - day_end_ts
        # p4 = t4 + user4_end - day_end_ts
        # p5 = t5 + user5_end - day_end_ts
        # print(f'user1 time elapsed {p1}')
        # print(f'user2 time elapsed {p2}')
        # print(f'user3 time elapsed {p3}')
        # print(f'user4 time elapsed {p4}')
        # print(f'user5 time elapsed {p5}')
        user_baln = int(self.balanceOfTokens('baln', self.user1.get_address()), 16)
        user_baln = user_baln - old_rewards_user1
        user_baln = user_baln / 10 ** 18
        # calculation of rewards
        recipient = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        percent = int(recipient['sICX/ICX'], 16) / 10 ** 18

        rewards = elapsed_time_user1 * percent * daily_emission / sec_per_day
        x = rewards + user1_rewards_first
        self.assertAlmostEqual(x, user_baln)
        user5_rewards_second = self.loan_rewards(day_end_ts, user5_end, self.user5.get_address()
                                                 , {}, old_rewards_user5, user5_rewards_first)
        rewards_dict = self.call_tx(self.contracts['rewards'], 'getRecipientsSplit', {})
        for k, v in rewards_dict.items():
            if k in rewards_dict_expected.keys():
                v = int(v, 16)
                rewards_dict_expected[k] += v * 100000

        rewards_amount = {}
        rewards_amount['Reserve Fund'] = int(self.balanceOfTokens('baln', self.contracts['reserve']), 16)
        rewards_amount['Worker Tokens'] = int(self.balanceOfTokens('baln', self.contracts['bwt']), 16)
        rewards_amount['DAOfund'] = int(self.balanceOfTokens('baln', self.contracts['daofund']), 16)

        self.assertDictEqual(rewards_amount, rewards_dict_expected)

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



