from .test_integrate_base_rebalancing import BalancedTestBaseRebalancing
from iconservice import *
from iconsdk.wallet.wallet import KeyWallet


class BalancedTestSellCollateral(BalancedTestBaseRebalancing):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        pass

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

        self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'setRebalancingThreshold',
                     {"_value": 5 * 10 ** 17})

    def test_sellCollateralNotLocked(self):
        self.score_update("loans")
        self.send_tx(self._test1, self.contracts['loans'], 1200000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 450000 * 10 ** 18})
        self.setAddresses()

        totalSupply = int(self.call_tx(self.contracts['bnUSD'], 'totalSupply', {}), base=16)
    
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)

        collateral = 1000 * 10 ** 18
        collateralToBeSold = 100 * 10 ** 18
        debt = int((collateral*0.4)/2)
        self.send_tx(self.user1, self.contracts['loans'], collateral, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': debt})
        bnusd_before = self.get_account_position(self.user1.get_address())
        result = self.send_tx(self.user1, self.contracts['loans'], 0, 'sellCollateral',
                     {'_amount_of_collateral': collateralToBeSold})
        bnusd_sold = int(result["eventLogs"][-1]["indexed"][3], base=16)
        bnusd_after, collateral_after = self.get_account_positions(self.user1.get_address())
        self.assertEqual(collateral_after, collateral-collateralToBeSold)
        self.assertEqual(bnusd_after, bnusd_before-bnusd_sold)
        self.assertEqual(totalSupply+bnusd_after, int(self.call_tx(self.contracts['bnUSD'], 'totalSupply', {}), base=16))


    def test_sellCollateralLocked(self):
        self.score_update("loans")
        self.send_tx(self._test1, self.contracts['loans'], 1200000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 450000 * 10 ** 18})
        self.setAddresses()

        totalSupply = int(self.call_tx(self.contracts['bnUSD'], 'totalSupply', {}), base=16)
    
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)

        collateral = 1000 * 10 ** 18
        collateralToBeSold = 100 * 10 ** 18
        maxDebt = int(collateral*0.4)
        self.send_tx(self.user1, self.contracts['loans'], collateral, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': maxDebt})
        try:
            self.send_tx(self.user1, self.contracts['loans'], 0, 'withdrawCollateral',
                     { '_value': collateralToBeSold})
            self.assertTrue(False)
        except Exception as e:
            self.assertTrue("Requested withdrawal is more than available collateral." in str(e))


        bnusd_before = self.get_account_position(self.user1.get_address())

        result = self.send_tx(self.user1, self.contracts['loans'], 0, 'sellCollateral',
                     {'_amount_of_collateral': collateralToBeSold})
        bnusd_sold = int(result["eventLogs"][-1]["indexed"][3], base=16)
        bnusd_after, collateral_after = self.get_account_positions(self.user1.get_address())
        self.assertEqual(collateral_after, collateral-collateralToBeSold)
        self.assertEqual(bnusd_after, bnusd_before-bnusd_sold)
        self.assertEqual(totalSupply+bnusd_after, int(self.call_tx(self.contracts['bnUSD'], 'totalSupply', {}), base=16))

    def test_sellCollateraLargerThanLoan(self):
        self.score_update("loans")
        self.send_tx(self._test1, self.contracts['loans'], 1200000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 450000 * 10 ** 18})
        self.setAddresses()

        totalSupply = int(self.call_tx(self.contracts['bnUSD'], 'totalSupply', {}), base=16)

        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)

        collateral = 1000 * 10 ** 18
        collateralToBeSold = int(collateral/2)
        debt = int((collateral*0.4)/2)
        self.send_tx(self.user1, self.contracts['loans'], collateral, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': debt})
        bnusd_before = self.get_account_position(self.user1.get_address())

        try:
            self.send_tx(self.user1, self.contracts['loans'], 0, 'sellCollateral',
                     {'_amount_of_collateral': collateralToBeSold})
            self.assertTrue(False)
        except Exception as e:
            self.assertTrue(" Repaid amount is greater than the amount in the position of" in str(e))

        bnusd_after, collateral_after = self.get_account_positions(self.user1.get_address())
        self.assertEqual(collateral_after, collateral)
        self.assertEqual(bnusd_after, bnusd_before)
        self.assertEqual(totalSupply+bnusd_after, int(self.call_tx(self.contracts['bnUSD'], 'totalSupply', {}), base=16))

    def test_sellCollateralBaseReverts(self):
        self.score_update("loans")
        self.send_tx(self._test1, self.contracts['loans'], 1200000 * 10 ** 18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 450000 * 10 ** 18})
        self.setAddresses()

        totalSupply = int(self.call_tx(self.contracts['bnUSD'], 'totalSupply', {}), base=16)
        
 
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        try:
            self.send_tx(self.user1, self.contracts['loans'], 0, 'sellCollateral',
                     {'_amount_of_collateral': 100*10**18})
            self.assertTrue(False)
        except Exception as e:
            self.assertTrue("does not have a position in Balanced" in str(e))

        collateral = 100 * 10 ** 18
        debt = int(collateral*0.2)
        self.send_tx(self.user1, self.contracts['loans'], collateral, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': debt})
        minted_bnusd = self.get_account_position(self.user1.get_address())
        try:
            self.send_tx(self.user1, self.contracts['loans'], 0, 'sellCollateral',
                     {'_amount_of_collateral': 0})
            self.assertTrue(False)
        except Exception as e:
            self.assertTrue("Amount of Collateral must be greater than zero" in str(e))

        try:
            self.send_tx(self.user1, self.contracts['loans'], 0, 'sellCollateral',
                     {'_amount_of_collateral': collateral*2})
            self.assertTrue(False)
        except Exception as e:
            self.assertTrue("Deposited collateral must be equal or greater than amount to be sold" in str(e))

        self.assertEqual(totalSupply+minted_bnusd, int(self.call_tx(self.contracts['bnUSD'], 'totalSupply', {}), base=16))


    def get_account_position(self, user: str) -> int:
        user_position = self.call_tx(self.contracts['loans'], 'getAccountPositions',
                                     {"_owner": user})
        if 'bnUSD' in user_position['assets']:
            return int(user_position['assets']['bnUSD'], 0)
        else:
            return 0
    def get_account_positions(self, user: str) -> int:
        user_position = self.call_tx(self.contracts['loans'], 'getAccountPositions',
                                     {"_owner": user})
        if 'bnUSD' in user_position['assets']:
            return int(user_position['assets']['bnUSD'], 0),  int(user_position['assets']['sICX'], 0)
        else:
            return 0

