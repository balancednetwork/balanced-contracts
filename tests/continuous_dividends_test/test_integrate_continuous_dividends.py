import json
import time

from .test_integrate_base_dividends import BalancedTestBaseDividends


class BalancedTestDataMigration(BalancedTestBaseDividends):

    def setUp(self):
        super().setUp()
        self.maxDiff = 100000

    def test_user_continuous_dividends(self):
        self.send_icx(self._test1, self.user1.get_address(), 15_000 * self.icx_factor)
        self.send_icx(self._test1, self.user2.get_address(), 15_000 * self.icx_factor)

        self.send_tx(self.btest_wallet, self.contracts['baln'], 0, "setTimeOffset", {})

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setFeeProcessingInterval',
                     {"_interval": 2})
        tokens = [self.contracts['baln'], self.contracts['sicx'], self.contracts['bnUSD']]
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setAcceptedDividendTokens',
                     {"_tokens": tokens})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'enable_fee_handler',
                     {})

        self.send_tx(self.btest_wallet, self.contracts['loans'], 5000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 2000 * 10 ** 18})
        self.send_tx(self.user1, self.contracts['loans'], 5000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 2000 * 10 ** 18})
        self.send_tx(self.user2, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 200 * 10 ** 18})

        # calling dividends distribute in order to update snapshot id
        self.send_tx(self.btest_wallet, self.contracts['dividends'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['dividends'], 0, 'distribute', {})
        self.call_tx(self.contracts["dividends"], "getSnapshotId")

        self.day_roolOver(2)

        # create baln market
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'createBalnMarket',
                     {"_bnUSD_amount": 100 * 10 ** 18, "_baln_amount": 100 * 10 ** 18})

        self.send_tx(self.user1, self.contracts['rewards'], 0, "claimRewards", {})

        # supplying liquidity to BALN/bnUSD market from user2
        par = {'_to': self.user2.get_address(), '_value': 110 * 10 ** 18,
               '_data': json.dumps({"method": "_deposit"}).encode()}
        self.send_tx(self.user1, self.contracts['baln'], 0, 'transfer', par)

        baln_param = {'_to': self.contracts['dex'], '_value': 100 * 10 ** 18,
               '_data': json.dumps({"method": "_deposit"}).encode()}
        self.send_tx(self.user2, self.contracts['baln'], 0, 'transfer', baln_param)
        bnUSD_param = {'_to': self.contracts['dex'], '_value': 100 * 10 ** 18,
               '_data': json.dumps({"method": "_deposit"}).encode()}
        self.send_tx(self.user2, self.contracts['bnUSD'], 0, 'transfer', bnUSD_param)

        param = {'_baseToken': self.contracts['baln'], '_quoteToken': self.contracts['bnUSD'],
                 '_baseValue': 100 * 10 ** 18, '_quoteValue': 100 * 10 ** 18}
        self.send_tx(self.user2, self.contracts['dex'], 0, 'add', param)

        # doing some transactions in day 2
        self.send_tx(self.user1, self.contracts['loans'], 5000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 1000 * 10 ** 18})

        # calling dividends distribute in order to update snapshot id
        self.send_tx(self.btest_wallet, self.contracts['dividends'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['dividends'], 0, 'distribute', {})
        self.call_tx(self.contracts["dividends"], "getSnapshotId")

        # claiming rewards from user1 and staking BALN token
        self.send_tx(self.user1, self.contracts['rewards'], 0, "claimRewards", {})
        value = int(self.call_tx(self.contracts['baln'], "balanceOf", {"_owner": self.user1.get_address()}), 0)
        self.send_tx(self.btest_wallet, self.contracts['baln'], 0, "toggleEnableSnapshot", {})
        self.send_tx(self.user1, self.contracts['baln'], 0, "stake", {'_value': value})

        # self.call_tx(self.contracts['baln'], "stakedBalanceOf", {"_owner": self.user1.get_address()})
        self.call_tx(self.contracts['baln'], "getSnapshotEnabled", {})
        # self.call_tx(self.contracts['baln'], "stakedBalanceOfAt", {"_account": self.user1.get_address(), "_day": 2})

        # setting continuous rewards day and dividends to staked only to day 3
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": 3})
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setDividendsOnlyToStakedBalnDay",
                     {"_day": 3})

        self.day_roolOver(3)

        # calling dividends distribute in order to update snapshot id
        self.send_tx(self.btest_wallet, self.contracts['dividends'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['dividends'], 0, 'distribute', {})
        self.call_tx(self.contracts["dividends"], "getSnapshotId")

        # self.call_tx(self.contracts["dividends"], "getDividendsCategories")
        # self.call_tx(self.contracts["dividends"], "getAcceptedTokens")

        # getting users dividends up to day 2
        # Dividends calculation for previous day before enabling takes LP tokens into account
        upto_day2_lp_dividends = self.call_tx(self.contracts['dividends'], "getUserDividends",
                                              {"_account": self.user2.get_address(),
                                               "_start": 0, "_end": 3})
        upto_day2_baln_stake_dividends = self.call_tx(self.contracts['dividends'], "getUserDividends",
                                                      {"_account": self.user1.get_address(),
                                                       "_start": 0, "_end": 3})

        # doing some transactions in day 3
        self.send_tx(self.user1, self.contracts['loans'], 5000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 1000 * 10 ** 18})

        self.day_roolOver(4)

        # calling dividends distribute in order to update snapshot id
        self.send_tx(self.btest_wallet, self.contracts['dividends'], 0, 'distribute', {})
        self.send_tx(self.btest_wallet, self.contracts['dividends'], 0, 'distribute', {})

        # in this case only staked baln will receive dividends
        # After the day change dividends only going to the staked baln token
        upto_day3_lp_dividends = self.call_tx(self.contracts['dividends'], "getUserDividends",
                                              {"_account": self.user2.get_address(),
                                               "_start": 0, "_end": 4})
        day3_lp_dividends = self.call_tx(self.contracts['dividends'], "getUserDividends",
                                         {"_account": self.user2.get_address(),
                                          "_start": 3, "_end": 4})

        upto_day3_baln_stake_dividends = self.call_tx(self.contracts['dividends'], "getUserDividends",
                                                      {"_account": self.user1.get_address(),
                                                       "_start": 0, "_end": 4})
        day3_baln_stake_dividends = self.call_tx(self.contracts['dividends'], "getUserDividends",
                                                 {"_account": self.user1.get_address(),
                                                  "_start": 3, "_end": 4})

        self.assertEqual(upto_day3_lp_dividends, upto_day2_lp_dividends)
        self.assertEqual(day3_lp_dividends, {})
        result = self._add_dividends(upto_day2_baln_stake_dividends, day3_baln_stake_dividends)
        self.assertEqual(upto_day3_baln_stake_dividends, result)

    def day_roolOver(self, _day: int):
        day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        while day != _day:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        for i in range(6):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

    def _add_dividends(self, a: dict, b: dict) -> dict:
        _accepted_tokens = self.call_tx(self.contracts["dividends"], "getAcceptedTokens")
        if a and b:
            response = {}
            for token in _accepted_tokens:
                result = int(a.get(str(token), 0), 0) + int(b.get(str(token), 0), 0)
                response[str(token)] = hex(result)
            return response
        elif a:
            return a
        elif b:
            return b
        else:
            return {}
