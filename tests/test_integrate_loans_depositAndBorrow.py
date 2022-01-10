from .test_integrate_base_loans import BalancedTestBaseLoans
from tests.stories.loans.deposit_borrow_stories import DEPOSIT_AND_BORROW_STORIES


class BalancedTestDepositAndBorrow(BalancedTestBaseLoans):

    def setUp(self):
        super().setUp()

    # # Adding collateral to the wallets
    def test_addCollateral(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        test_cases = DEPOSIT_AND_BORROW_STORIES
        for case in test_cases['stories']:
            _tx_result = {}
            print(case['description'])
            if case['actions']['sender'] == 'user1':
                wallet_address = self.user1.get_address()
                wallet = self.user1
            else:
                wallet_address = self.user2.get_address()
                wallet = self.user2
            data1 = case['actions']['args']
            params = {"_asset": data1['_asset'], "_amount": data1['_amount']}
            signed_transaction = self.build_tx(wallet, self.contracts['loans'], case['actions']['deposited_icx'], "depositAndBorrow", params)
            _tx_result = self.process_transaction(signed_transaction, self.icon_service)
            if 'revertMessage' in case['actions'].keys():
                self.assertEqual(_tx_result['failure']['message'], case['actions']['revertMessage'])
                # print('Revert Matched')
            else:
                bal_of_sicx = self.balanceOfTokens('sicx')
                bal_of_bnUSD = self.balanceOfTokens('bnUSD')
                self.assertEqual(1, _tx_result['status'])
                self.assertEqual(case['actions']['expected_sicx_baln_loan'], int(bal_of_sicx, 16))
                self.assertEqual(case['actions']['expected_bnUSD_debt_baln_loan'], int(bal_of_bnUSD, 16))
                account_position = self._getAccountPositions()
                assets = account_position['assets']
                position_to_check = {'sICX': str(bal_of_sicx),
                                     'bnUSD': hex(int(bal_of_bnUSD, 16) + int(self.getBalances()['bnUSD'], 16))}
                self.assertEqual(position_to_check, assets)

    def balanceOfTokens(self, name):
        params = {
            "_owner": self.user1.get_address()
        }
        if name == 'sicx':
            contract = self.contracts['sicx']
            params = {
                "_owner": self.contracts['loans']
            }
        elif name == 'dividends':
            contract = self.contracts['dividends']
        else:
            contract = self.contracts['bnUSD']
        response = self.call_tx(contract, "balanceOf", params)
        if name == 'sicx':
            print('Balance of sicx token is ' + str(int(response, 16)))
        else:
            print("Balance of bnUSD is " + str(int(response, 16)))
        return response

    def _getAccountPositions(self) -> dict:
        params = {'_owner': self.user1.get_address()}
        result = self.call_tx(self.contracts['loans'], "getAccountPositions", params)
        return result

    def getBalances(self):
        result = self.call_tx(self.contracts['dividends'], "getBalances", {})
        return result