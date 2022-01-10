from .test_integrate_base_loans import BalancedTestBaseLoans
from tests.stories.loans.return_assets_stories import RETURN_ASSETS


class BalancedTestRepayLoan(BalancedTestBaseLoans):

    def setUp(self):
        super().setUp()

    # Repay loan from account wallet
    def test_repayLoan(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10 ** 18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10 ** 18)

        test_cases = RETURN_ASSETS
        for case in test_cases['stories']:
            _tx_result = {}
            print(case['description'])
            if case['actions']['sender'] == 'user1':
                wallet_address = self.user1.get_address()
                wallet = self.user1
            else:
                wallet_address = self.user2.get_address()
                wallet = self.user2
                self.send_tx(self.btest_wallet, self.contracts['loans'], 100*10**18, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount':10*10**18})
                self.send_tx(self.btest_wallet, self.contracts['bnUSD'], 0, 'transfer', {'_to': self.user2.get_address(), '_value':10*10**18})
            if case['actions']['name'] == 'depositAndBorrow':
                _to = self.contracts['loans']
                meth = case['actions']['name']
                val = case['actions']['deposited_icx']
                data1 = case['actions']['args']
                params = {"_asset": data1['_asset'], "_amount": data1['_amount']}
            else:
                _to = self.contracts['loans']
                meth = case['actions']['name']
                val = case['actions']['deposited_icx']
                data2 = case['actions']['args']
                params = {'_symbol': data2['_symbol'], '_value': data2['_value']}

            signed_transaction = self.build_tx(wallet, _to, val, meth, params)
            _tx_result = self.process_transaction(signed_transaction, self.icon_service)
            # print("Status:", _tx_result['status'])
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
                position_to_check = {'sICX': str(bal_of_sicx), 'bnUSD': hex(int(bal_of_bnUSD, 16) + int(self.getBalances()['bnUSD'], 16))}
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