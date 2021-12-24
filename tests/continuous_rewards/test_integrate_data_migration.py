from ..test_integrate_base_loans import BalancedTestBaseLoans


class BalancedTestDataMigration(BalancedTestBaseLoans):

    def setUp(self):
        super().setUp()

    def test_read_methods(self):
        self.send_icx(self._test1, self.user1.get_address(), 5_000 * self.icx_factor)
        self.send_icx(self._test1, self.user2.get_address(), 5_000 * self.icx_factor)

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, "setContinuousRewardsDay",
                     {"_day": 2})
        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})

        before = self._readOnly(self.user1.get_address())
        print(before)
        self.send_tx(self.user1, self.contracts['loans'], 0, 'migrate_user_to_loans',
                     {'address': self.user1.get_address()})

        after = self._readOnly(self.user1.get_address())
        print(after)
        self.assertListEqual(before, after)

    def _readOnly(self, address):
        prev_dist = (self.call_tx(self.contracts['loans'], 'getDistributionsDone', {}))
        dist_status = (prev_dist['Rewards'], prev_dist['Dividends'])
        dead_market = (self.call_tx(self.contracts['loans'], 'checkDeadMarkets', {}))

        prev_posCount = (self.call_tx(self.contracts['loans'], 'getNonzeroPositionCount', {}))

        prev_Pos = (self.call_tx(self.contracts['loans'], 'getPositionStanding', {'_address': address}))
        pos_standing = (prev_Pos['debt'], prev_Pos['collateral'], prev_Pos['ratio'], prev_Pos['standing'])

        prev_PosAddr = (self.call_tx(self.contracts['loans'], 'getPositionAddress', {'_index': 2}))

        prev_assetToken = (self.call_tx(self.contracts['loans'], 'getAssetTokens', {}))
        asset_token = prev_assetToken['sICX']

        prev_Collateral = (self.call_tx(self.contracts['loans'], 'getCollateralTokens', {}))
        collateral_token = prev_Collateral['sICX']

        prev_TotalCollateral = (self.call_tx(self.contracts['loans'], 'getTotalCollateral', {}))

        prev_AccPos = (self.call_tx(self.contracts['loans'], 'getAccountPositions', {'_owner': address}))
        acc_pos = (prev_AccPos['assets']['sICX'], prev_AccPos['assets']['bnUSD'], prev_AccPos['total_debt'])

        prev_index = (self.call_tx(self.contracts['loans'], 'getPositionByIndex', {'_index': 2, '_day': 1}))
        pos_by_index = (prev_index['assets']['sICX'], prev_index['assets']['bnUSD'], prev_index['total_debt'])

        prev_asset = (self.call_tx(self.contracts['loans'], 'getAvailableAssets', {}))
        assets = (prev_asset['bnUSD']['symbol'], prev_asset['bnUSD']['address'])

        prev_assCount = (self.call_tx(self.contracts['loans'], 'assetCount', {}))

        prev_borrowCount = (self.call_tx(self.contracts['loans'], 'borrowerCount', {}))

        prev_debt = (self.call_tx(self.contracts['loans'], 'hasDebt', {'_owner': address}))

        prev_snap = (self.call_tx(self.contracts['loans'], 'getSnapshot', {}))
        snapshot = prev_snap['add_to_nonzero_count']

        prev_totalValue = (self.call_tx(self.contracts['loans'], 'getTotalValue', {'_name': 'a', '_snapshot_id': 1}))

        prev_balance = (self.call_tx(self.contracts['loans'], 'getBalanceAndSupply', {'_name': 'Loans', '_owner': address}))
        balance = (prev_balance['_balance'], prev_balance['_totalSupply'])

        prev_bnusdVAlue = (self.call_tx(self.contracts['loans'], 'getBnusdValue', {'_name': 'a'}))

        prev_Parameters = (self.call_tx(self.contracts['loans'], 'getParameters', {}))
        param = prev_Parameters['admin']

        prev_checkValue = (self.call_tx(self.contracts['loans'], 'checkValue', {'address': address}))
        checkValue = (prev_checkValue['old']['sICX'], prev_checkValue['old']['bnUSD'])

        return [dist_status, dead_market, prev_posCount, pos_standing, prev_PosAddr,asset_token, collateral_token,
                prev_TotalCollateral, acc_pos, pos_by_index, assets, prev_assCount, prev_borrowCount, prev_debt,
                snapshot, prev_totalValue, balance, prev_bnusdVAlue, param, checkValue]