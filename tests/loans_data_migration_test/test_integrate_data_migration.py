import time

from .test_integrate_base_migration import BalancedTestBaseMigration


class BalancedTestDataMigration(BalancedTestBaseMigration):

    def setUp(self):
        super().setUp()
        self.maxDiff = 100000

    def test_read_methods_same_user_before_and_after_continuous_day(self):
        self.send_icx(self._test1, self.user1.get_address(), 5_000 * self.icx_factor)

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": 2})
        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})

        before = self._readOnly(self.user1.get_address())
        day = int(self.call_tx(self.contracts["loans"], "getDay"), 0)
        while day != 2:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)
        for i in range(6):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        self.send_tx(self.user1, self.contracts['loans'], 0, 'migrateUserData',
                     {'address': self.user1.get_address()})

        after = self._readOnly(self.user1.get_address())
        before['snapshot'] = {'snap_day': '0x1', 'snap_time': after['snapshot']['snap_time'],
                              'total_mining_debt': '0x34620ea0448941dc7',
                              'prices': {'sICX': '0xde0b6b3a7640000', 'bnUSD': '0x84c5d90848544bb'},
                              'mining_count': '0x1', 'precompute_index': '0x1', 'add_to_nonzero_count': '0x0',
                              'remove_from_nonzero_count': '0x0'}
        before['totalMiningDebtValue'] = before['snapshot']['total_mining_debt']
        before['checkValue'] = {'flag': {'sICX': '0x1', 'bnUSD': '0x1', 'BALN': '0x1'},
                                'old': before['checkValue']['old'],
                                'sICX': before['checkValue']['old']['sICX'],
                                'bnUSD': {'sICX': before['checkValue']['old']['bnUSD']},
                                'BALN': before['checkValue']['BALN']}

        self.assertDictEqual(before, after)

    def test_read_methods_same_user_in_continuous_day(self):
        self.send_icx(self._test1, self.user1.get_address(), 5_000 * self.icx_factor)

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": 2})
        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})
        day = int(self.call_tx(self.contracts["loans"], "getDay"), 0)
        while day != 2:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        for i in range(6):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        self.send_tx(self.user1, self.contracts['loans'], 0, 'migrateUserData',
                     {'address': self.user1.get_address()})

        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})

        before = self._readOnly(self.user1.get_address())
        after = {'dist_status': ('0x1', '0x1'), 'dead_market': [], 'posCount': '0x1',
                 'pos_standing': ('0x68c41d40891283b8e', '0x6c6b935b8bbd400000', '0xe5ca10e1b84e4987', 'Mining'),
                 'posAddr': 'hx6a9bdb75789556fe0fbdfb34bc9483056977ed6d',
                 'totalCollateral': '0x4906be40a91f0a64924a',
                 'acc_pos': ('0x6c6b935b8bbd400000', '0xaf35029c214e80000', '0x68c41d40891283b8e'),
                 'pos_by_index': ('0x3635c9adc5dea00000', '0x579a814e10a740000', '0x34620ea0448941dc7'),
                 'assets': 'bnUSD', 'assCount': '0x3', 'borrowCount': '0x2', 'debt': '0x1',
                 'snapshot': before['snapshot'], 'totalMiningDebtValue': before['snapshot']['total_mining_debt'],
                 'balance': ('0xaf35029c214e80000', '0x147b4616469074a7f7ae'),
                 'bnusdValue': '0x147b4616469074a7f7ae',
                 'checkValue': {'flag': {'sICX': '0x1', 'bnUSD': '0x1', 'BALN': '0x1'},
                                'old': {'sICX': '0x3635c9adc5dea00000', 'bnUSD': '0x579a814e10a740000',
                                        'BALN': '0x0'}, 'sICX': '0x6c6b935b8bbd400000',
                                'bnUSD': {'sICX': '0xaf35029c214e80000'}, 'BALN': '0x0'}}

        self.assertDictEqual(before, after)

    def test_read_methods_new_user_in_continuous_day(self):
        self.send_icx(self._test1, self.user1.get_address(), 5_000 * self.icx_factor)
        self.send_icx(self._test1, self.user2.get_address(), 5_000 * self.icx_factor)

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": 2})
        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})

        day = int(self.call_tx(self.contracts["loans"], "getDay"), 0)
        while day != 2:
            time.sleep(5)
            day = int(self.call_tx(self.contracts["loans"], "getDay"), 16)

        for i in range(6):
            self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})

        self.send_tx(self.user1, self.contracts['loans'], 0, 'migrateUserData',
                     {'address': self.user1.get_address()})

        self.send_tx(self.user2, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})

        before = self._readOnly(self.user2.get_address())
        after = {'dist_status': ('0x1', '0x1'), 'dead_market': [], 'posCount': '0x1',
                 'pos_standing': before['pos_standing'],
                 'posAddr': 'hx6a9bdb75789556fe0fbdfb34bc9483056977ed6d',
                 'totalCollateral': before['totalCollateral'],
                 'acc_pos': before['acc_pos'],
                 'pos_by_index': ('0x3635c9adc5dea00000', '0x579a814e10a740000', '0x34620ea0448941dc7'),
                 'assets': 'bnUSD', 'assCount': '0x3', 'borrowCount': '0x3', 'debt': '0x1',
                 'snapshot': before['snapshot'], 'totalMiningDebtValue': before['snapshot']['total_mining_debt'],
                 'balance': ('0x579a814e10a740000', '0x147b4616469074a7f7ae'),
                 'bnusdValue': '0x147b4616469074a7f7ae',
                 'checkValue': {'flag': {'sICX': '0x1', 'bnUSD': '0x1', 'BALN': '0x0'},
                                'old': {'sICX': '0x0', 'bnUSD': '0x0', 'BALN': '0x0'},
                                'sICX': before['checkValue']['sICX'], 'bnUSD': {'sICX': '0x579a814e10a740000'},
                                'BALN': '0x0'}}
        self.assertDictEqual(before, after)

    def _readOnly(self, address):
        dist = (self.call_tx(self.contracts['loans'], 'getDistributionsDone', {}))
        dist_status = (dist['Rewards'], dist['Dividends'])
        dead_market = (self.call_tx(self.contracts['loans'], 'checkDeadMarkets', {}))

        posCount = (self.call_tx(self.contracts['loans'], 'getNonzeroPositionCount', {}))

        Pos = (self.call_tx(self.contracts['loans'], 'getPositionStanding', {'_address': address}))
        pos_standing = (Pos['debt'], Pos['collateral'], Pos['ratio'], Pos['standing'])

        posAddr = (self.call_tx(self.contracts['loans'], 'getPositionAddress', {'_index': 2}))

        totalCollateral = (self.call_tx(self.contracts['loans'], 'getTotalCollateral', {}))

        AccPos = (self.call_tx(self.contracts['loans'], 'getAccountPositions', {'_owner': address}))
        acc_pos = (AccPos['assets']['sICX'], AccPos['assets']['bnUSD'], AccPos['total_debt'])

        index = (self.call_tx(self.contracts['loans'], 'getPositionByIndex', {'_index': 2, '_day': 1}))
        pos_by_index = (index['assets']['sICX'], index['assets']['bnUSD'], index['total_debt'])

        asset = (self.call_tx(self.contracts['loans'], 'getAvailableAssets', {}))
        assets = (asset['bnUSD']['symbol'])

        assCount = (self.call_tx(self.contracts['loans'], 'assetCount', {}))

        borrowCount = (self.call_tx(self.contracts['loans'], 'borrowerCount', {}))

        debt = (self.call_tx(self.contracts['loans'], 'hasDebt', {'_owner': address}))

        snapshot = (self.call_tx(self.contracts['loans'], 'getSnapshot', {'_snap_id': 1}))

        totalMiningDebtValue = (
            self.call_tx(self.contracts['loans'], 'getTotalValue', {'_name': 'a', '_snapshot_id': 1}))

        balance = (
            self.call_tx(self.contracts['loans'], 'getBalanceAndSupply', {'_name': 'Loans', '_owner': address}))
        balance = (balance['_balance'], balance['_totalSupply'])

        bnusdValue = (self.call_tx(self.contracts['loans'], 'getBnusdValue', {'_name': 'a'}))

        checkValue = (self.call_tx(self.contracts['loans'], 'userMigrationDetails', {'address': address}))

        return {'dist_status': dist_status, 'dead_market': dead_market, 'posCount': posCount,
                'pos_standing': pos_standing, 'posAddr': posAddr, 'totalCollateral': totalCollateral, 'acc_pos': acc_pos,
                'pos_by_index': pos_by_index, 'assets': assets, 'assCount': assCount, 'borrowCount': borrowCount,
                'debt': debt, 'snapshot': snapshot, 'totalMiningDebtValue': totalMiningDebtValue, 'balance': balance,
                'bnusdValue': bnusdValue, 'checkValue': checkValue}
