import time

from ..test_integrate_base_loans import BalancedTestBaseLoans
from ..stories.loans.deposit_borrow_stories import DEPOSIT_AND_BORROW_STORIES


class BalancedTestDepositAndBorrow(BalancedTestBaseLoans):

    def setUp(self):
        super().setUp()

    # def test_addCollateral(self):
    #     # sending ICX to the wallet
    #     self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
    #     self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)
    #
    #     test_cases = DEPOSIT_AND_BORROW_STORIES
    #     for case in test_cases['stories']:
    #         _tx_result = {}
    #         print(case['description'])
    #         if case['actions']['sender'] == 'user1':
    #             wallet_address = self.user1.get_address()
    #             wallet = self.user1
    #         else:
    #             wallet_address = self.user2.get_address()
    #             wallet = self.user2
    #         data1 = case['actions']['args']
    #         params = {"_asset": data1['_asset'], "_amount": data1['_amount']}
    #
    #         # building transaction
    #         signed_transaction = self.build_tx(wallet, self.contracts['loans'], case['actions']['deposited_icx'],
    #                                            "depositAndBorrow", params)
    #         # process transaction
    #         _tx_result = self.process_transaction(signed_transaction, self.icon_service)
    #
    #         if 'revertMessage' in case['actions'].keys():
    #             self.assertEqual(_tx_result['failure']['message'], case['actions']['revertMessage'])
    #         else:
    #             bal_of_sicx = self.balanceOfTokens('sicx', self.contracts['loans'])
    #             bal_of_bnUSD = self.balanceOfTokens('bnUSD', self.user1.get_address())
    #
    #             # checks the status of tx
    #             self.assertEqual(1, _tx_result['status'])
    #
    #             # checks the minted sicx and bnusd amount
    #             self.assertEqual(case['actions']['expected_sicx_baln_loan'], int(bal_of_sicx, 16))
    #             self.assertEqual(case['actions']['expected_bnUSD_debt_baln_loan'], int(bal_of_bnUSD, 16))
    #
    #             account_position = self._getAccountPositions(self.user1.get_address())
    #             assets = account_position['assets']
    #             fee = self.balanceOfTokens('bnUSD', self.contracts['feehandler'])
    #             position_to_check = {'sICX': str(bal_of_sicx),
    #                                  'bnUSD': hex(int(bal_of_bnUSD, 16) + int(fee, 16))}
    #             self.assertEqual(position_to_check, assets)
    #
    #     # update loans and rewards and governance and dex
    #     self.update('loans')
    #     self.update('rewards')
    #     self.update('governance')
    #     self.update('dex')
    #
    #     day = (self.call_tx(self.contracts["loans"], "getDay"))
    #     # day changes each 2 minutes.
    #     # set continuous rewards day as next day of current day.
    #     self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay", {"_day": int(day, 16) +1})
    #     continuous_day = (self.call_tx(self.contracts["loans"], "getContinuousRewardsDay"))
    #     print("Waiting for day change")
    #     # code pauses for 60 sec
    #     time.sleep(60)
    #     # testing for continuous rewards starts from here
    #     current_day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
    #     # asserting the continuous rewards day
    #     self.assertEqual(int(continuous_day, 16), current_day)

    # def test_baln_holdings(self):
    #     self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
    #     self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)
    #
    #     day = (self.call_tx(self.contracts["loans"], "getDay"))
    #     params = {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18}
    #     self.send_tx(self.user2, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
    #     print(self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user2.get_address())}))
    #
    #     day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
    #     while day != 2:
    #         time.sleep(5)
    #         day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
    #     print(day)
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #
    #     print(self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user2.get_address())}))
    #     self.send_tx(self.user2, self.contracts['rewards'], 0, 'claimRewards', {})
    #     print(self.balanceOfTokens('baln', self.user2.get_address()))
    #
    #     self.update('loans')
    #     self.update('rewards')
    #     self.update('governance')
    #     self.update('dex')
    #
    #     continuous_day = day + 1
    #
    #     self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
    #                  {"_day": continuous_day})
    #
    #     while day != 3:
    #         time.sleep(5)
    #         day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
    #     print(self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user2.get_address())}))
    #     print(self.balanceOfTokens('baln', self.user2.get_address()))
    #     print(day)
    #
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #
    #     print(self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user2.get_address())}))
    #
    #     self.send_tx(self.user1, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
    #     print(self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user2.get_address())}))

        # tx = self.send_tx(self.user1, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
        # start = self.icon_service.get_transaction(tx['txHash'])['timestamp']
        #
        # before = time.time()
        # print(self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user1.get_address())}))
        # after = time.time()
        #
        # end = int(((before+after)/2) * 10**6)
        # elapsed_time = (end - start)
        # print(elapsed_time)
        # bnusd_supply = int(self.totalSupply('bnUSD'), 16)
        # print(bnusd_supply)
        # user_debt = 101 * 10 ** 18
        # daily_emission = 100000
        # sec_per_day = 120000000
        # loans_percent = 0.25
        #
        # # calculation of rewards
        # rewards = ((user_debt / bnusd_supply) * loans_percent * daily_emission * elapsed_time) / sec_per_day
        # print(rewards)

        # print(self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user2.get_address())}))
        # self.send_tx(self.user2, self.contracts['rewards'], 0, 'claimRewards', {})
        # self.send_tx(self.user2, self.contracts['rewards'], 0, 'claimRewards', {})
        # print(self.balanceOfTokens('baln', self.user2.get_address()))

    def test_snapshot_data(self):
        """
        There shouldn't be any snapshots from the day of continuous rewards activation.
        """

        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        day = int(self.call_tx(self.contracts["loans"], "getDay"), 0)
        params = {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18}
        self.send_tx(self.user1, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)

        while day != 2:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        self.send_tx(self.user2, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)

        self.update('loans')
        self.update('rewards')
        self.update('governance')
        self.update('dex')

        continuous_day = day + 1

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": continuous_day})

        while day != 3:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        self.send_tx(self.btest_wallet, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)

        # on the continuous rewards activation day, calling getSnapshot with snap_id 3
        snapshot = self.call_tx(self.contracts["loans"], "getSnapshot", {"_snap_id": 3})
        self.assertDictEqual(snapshot, {})


        while day != 4:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        # on the next day of continuous rewards activation day, calling getSnapshot with snap_id 3
        snapshot = self.call_tx(self.contracts["loans"], "getSnapshot", {"_snap_id": 3})
        self.assertDictEqual(snapshot, {})

    def test_user_rewards(self):
        '''
        User takes a loan on continuous rewards activation day and
        the rewards allocated for that user is tested.
        '''
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        day = int(self.call_tx(self.contracts["loans"], "getDay"), 0)
        params = {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18}

        self.update('loans')
        self.update('rewards')
        self.update('governance')
        self.update('dex')

        continuous_day = day + 1

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": continuous_day})

        while day != 2:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        # tx = self.send_tx(self.user1, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
        tx = self.send_tx(self.user1, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
        bheight = (self.icon_service.get_block(tx['blockHeight']))
        start = bheight['time_stamp']

        tx = self.send_tx(self.user1, self.contracts['rewards'], 0, 'claimRewards', {})
        # user balance is checked once user claims rewards.
        user_baln = int(self.balanceOfTokens('baln', self.user1.get_address()), 16)
        user_baln = user_baln/10**18

        bheight = (self.icon_service.get_block(tx['blockHeight']))
        end = bheight['time_stamp']
        elapsed_time = (end - start)
        bnusd_supply = int(self.totalSupply('bnUSD'), 16)
        user_debt = 101 * 10 ** 18
        daily_emission = 100000
        sec_per_day = 120000000
        loans_percent = 0.25

        # calculation of rewards
        rewards = ((user_debt / bnusd_supply) * loans_percent * daily_emission * elapsed_time) / sec_per_day
        change = rewards - user_baln
        self.assertEqual(change, 0)

    def test_mining_status(self):
        '''
        All the user that were previously in Not Mining state should be in mining state and
        also all the new users entered after continuous rewards should be in mining state.
        '''
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        day = (self.call_tx(self.contracts["loans"], "getDay"))

        # takes a loan so that the user standing remains not mining.
        params = {"_asset": 'bnUSD', "_amount": 200 * 10 ** 18}
        self.send_tx(self.user2, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
        acc_pos = self._getAccountPositions(self.user2.get_address())
        mining_status = acc_pos['standing']
        self.assertEqual(mining_status, 'Not Mining')

        # update to continuous rewards
        self.update('loans')
        self.update('rewards')
        self.update('governance')
        self.update('dex')
        continuous_day = int(day, 16) + 1
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": continuous_day})

        day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        while day != continuous_day:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        # continuous rewards is activated from here(day2)

        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        # another user takes same loans as that of the previous user but remains as mining instead of not mining
        params = {"_asset": 'bnUSD', "_amount": 200 * 10 ** 18}
        self.send_tx(self.user1, self.contracts['loans'], 500 * 10 ** 18, 'depositAndBorrow', params)
        acc_pos = (self._getAccountPositions(self.user1.get_address()))

        print(self.call_tx(self.contracts['loans'], "getPositionStanding", {"_address": self.user1.get_address()
                                                                            , "_snapshot": 1}))

        print(self.call_tx(self.contracts['loans'], "getPositionStanding", {"_address": self.user1.get_address()
                                                                            , "_snapshot": 2}))

        print(self.call_tx(self.contracts['loans'], "getPositionStanding", {"_address": self.user1.get_address()
                                                                            , "_snapshot": 3}))
        mining_status = acc_pos['standing']
        self.assertEqual(mining_status, 'Mining')

        # the previous user's standing is changed to mining as well.
        acc_pos = (self._getAccountPositions(self.user2.get_address()))
        mining_status = acc_pos['standing']
        self.assertEqual(mining_status, 'Mining')


        print(self.call_tx(self.contracts['loans'], "getPositionStanding", {"_address": self.user2.get_address()
                                                                            , "_snapshot": 1}))

        print(self.call_tx(self.contracts['loans'], "getPositionStanding", {"_address": self.user2.get_address()
                                                                            , "_snapshot": 2}))

        print(self.call_tx(self.contracts['loans'], "getPositionStanding", {"_address": self.user2.get_address()
                                                                            , "_snapshot": 3}))

        print(self.call_tx(self.contracts['loans'], "getPositionStanding", {"_address": self.user2.get_address()
                                                                            }))
        print(self.call_tx(self.contracts['loans'], "getPositionStanding", {"_address": self.user1.get_address()
                                                                            }))

        baln_rewards = int(
            self.call_tx(self.contracts['rewards'], 'getBalnHolding', {'_holder': str(self.user1.get_address())}), 16)

        # baln rewards for new user is available as soon as he enters into balanced i.e no 24hr lock.
        self.assertNotEqual(baln_rewards, 0)

    def test_loan_data_batch(self):
        '''
        new user comes to balanced on day 2 and on continuous rewards activation day i.e. day 3, loans getDataBatch
        function should return
        new user info if it's on mining state.
        '''

        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        day = (self.call_tx(self.contracts["loans"], "getDay"))
        params = {"_asset": 'bnUSD', "_amount": 100 * 10 ** 18}
        self.send_tx(self.user2, self.contracts['loans'], 2000 * 10 ** 18, 'depositAndBorrow', params)

        while day != 2:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        params = {"_asset": 'bnUSD', "_amount": 50 * 10 ** 18}
        self.send_tx(self.user1, self.contracts['loans'], 2000 * 10 ** 18, 'depositAndBorrow', params)

        self.update('loans')
        self.update('rewards')
        self.update('governance')
        self.update('dex')
        continuous_day = day + 1
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": continuous_day})

        day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        while day != continuous_day:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        # continuous rewards is activated from here(day3)

        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        user2_pos = (self._getAccountPositions(self.user2.get_address()))
        user1_pos = (self._getAccountPositions(self.user1.get_address()))

        expected_dict = {str(self.user2.get_address()): int(user2_pos['total_debt'], 0), str(self.user1.get_address()):
            int(user1_pos['total_debt'], 0)}

        result = (
            self.call_tx(self.contracts['loans'], "getDataBatch", {"_name": "aab", "_snapshot_id": 2, "_limit": 50}))
        data_batch = {}
        for k, v in result.items():
            v = int(v, 16)
            data_batch[k] = v
        self.assertDictEqual(expected_dict, data_batch)

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
