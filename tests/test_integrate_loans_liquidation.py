import subprocess
import time

from core_contracts.loans.loans.loans import Loans
from .test_integrate_base_liquidation import BalancedTestBaseLiquidation
from tests.stories.loans.liquidation_stories import LIQUIDATION_STORIES


class BalancedTestLiquidation(BalancedTestBaseLiquidation):

    # val = """
    # @payable
    # @external
    # # def create_test_position(self, _address: Address, _asset: str, _amount: int) -> None:
    # #     # Create bad position for testing liquidation. Take out a loan that is too large.
    # #     # Add ICX collateral via staking contract.
    # #     pos = self._positions.get_pos(_address)
    # #     # Mint asset for this position.
    # #     if _amount > 0:
    # #         if pos.total_debt() == 0:
    # #             self._positions.add_nonzero(pos.id.get())
    # #         self._assets[_asset].mint(_address, _amount)
    # #         pos[_asset] = pos[_asset] + _amount
    # #     pos.update_standing()
    # #     self.check_dead_markets()
    # # """
    #
    # # exec(val)
    # # setattr(Loans, 'yet_another_method', yet_another_method)
    # # a = Loans()
    # # print(a.yet_another_method())
    #
    # def test_patch_constants(self):
    #     sed_cmd = '/def name/a' + "sudeep"
    #     subprocess.call(['sed', '-i', sed_cmd, "core_contracts/oracle/dummy_oracle.py"])
    #     # subprocess.call("sed -i -e 's/def name/a _loan/' core_contracts/loans/loans/loans.py", shell=True)

    def setUp(self):
        super().setUp()

    def test_liquidation(self):
        test_cases = LIQUIDATION_STORIES

        for case in test_cases['stories']:
            print("############################################################################################")
            print(case['description'])
            print(self.call_tx(self.contracts['oracle'], 'get_reference_data',
                                            {'_base': "USD", "_quote": "ICX"}))
            icx = case['actions']['deposited_icx']
            oracle_data = case['actions']['oracle']
            self.send_tx(self.btest_wallet, self.contracts['loans'], icx, 'depositAndBorrow',
                         {'_asset': 'bnUSD', '_amount': 300*10**18})
            account_position = self.call_tx(self.contracts['loans'], 'getAccountPositions',
                                            {'_owner': self.btest_wallet.get_address()})

            self.assertEqual(account_position['standing'], case['actions']['expected_initial_position'],
                             "Error in Account standing of the loan borrower")
            self.assertEqual(account_position['assets']['sICX'], hex(icx),
                             "Test Case failed for liquidation")

            self.send_tx(self._test1, self.contracts['oracle'], 0, 'set_reference_data',
                         {'_base': 'USD', '_quote': 'ICX', 'rate': oracle_data['rate'],
                          'last_update_base': oracle_data['last_update_base'], 'last_update_quote': oracle_data['last_update_quote']})
            account_position = self.call_tx(self.contracts['loans'], 'getAccountPositions',
                                            {'_owner': self.btest_wallet.get_address()})
            self.assertEqual(account_position['standing'], case['actions']['expected_position'],
                             "Expected position is not liquidate")

            self.send_tx(self._test1, self.contracts['loans'], method="liquidate",
                         params={'_owner': self.btest_wallet.get_address()})
            time.sleep(20)
            result = self.call_tx(self.contracts['loans'], "getAccountPositions",
                                  {'_owner': self.btest_wallet.get_address()})
            self.assertEqual(result['standing'], case['actions']['expected_result'])

    def test_setprice(self):
        self.call_tx(self.contracts['loans'], 'getAccountPositions',
                     {'_owner': self.btest_wallet.get_address()})
        self.send_tx(self.btest_wallet, self.contracts['loans'], method="liquidate",
                                  params={'_owner': self.btest_wallet.get_address()})
        # self.send_tx(self.btest_wallet, self.contracts['oracle'], 0, 'set_reference_data',
        #              {'_base': 'USD', '_quote': 'ICX', 'rate': int(5*10**18), 'last_update_base': 1802202277702605,
        #               'last_update_quote': 1802202290000000})
        # print(self.call_tx(self.contracts['oracle'], 'get_reference_data',
        #                    {'_base': "USD", "_quote": "ICX"}))
        self.call_tx(self.contracts['loans'], 'getAccountPositions',
                     {'_owner': self.btest_wallet.get_address()})