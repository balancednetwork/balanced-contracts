from test_integrate_base_origination import BalancedTestBaseOrigination


class BalancedTestDepositAndBorrow(BalancedTestBaseOrigination):

    def setUp(self):
        super().setUp()

    def test_origination_fee(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        self.send_tx(self.user1, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})

        pos = self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user1.get_address()})
        self.assertEqual(int(pos['assets']['bnUSD'], 0), 101000000000000000000)

        # setting a new origination fee
        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'set_origination_fee', {'symbol': 'sICX', '_value': 300})
        self.call_tx(self.contracts['loans'], 'get_origination_fee', {"symbol": 'sICX'})

        # borrow from different wallet with new origination fee
        self.send_tx(self.user2, self.contracts['loans'], 1000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})

        pos = self.call_tx(self.contracts['loans'], 'getAccountPositions', {"_owner": self.user2.get_address()})
        self.assertEqual(int(pos['assets']['bnUSD'], 0), 103000000000000000000)

