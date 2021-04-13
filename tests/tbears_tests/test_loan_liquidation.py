# import os
# import pickle
# from time import sleep
# from iconservice import *
# from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS
# import json
#
# # raise e
#
#
# from iconsdk.builder.call_builder import CallBuilder
# from iconsdk.libs.in_memory_zip import gen_deploy_data_content
# from iconsdk.signed_transaction import SignedTransaction
# from iconsdk.icon_service import IconService
# from iconsdk.providers.http_provider import HTTPProvider
# from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
# from iconsdk.wallet.wallet import KeyWallet
# from iconsdk.exception import JSONRPCException
# from .repeater import retry
#
# ICX = 1000000000000000000
# DIR_PATH = os.path.abspath(os.path.dirname(__file__))
# DEPLOY = ['loans', 'reserve', 'dividends', 'dummy_oracle', 'staking', 'rewards', 'dex', 'governance']
# TOKEN = ['bal', 'bwt', 'bnUSD', 'sicx']
# UPDATE = ['loans']
#
# path = '/home/sudeep/contracts-private/core_contracts/tests'
# filename = '/home/sudeep/contracts-private/test_scenarios/scenarios/loan-liquidationCheck.json'
#
#
# def read_file_data(filename, path):
#     os.chdir(path)
#     with open(filename, encoding="utf8") as data_file:
#         json_data = json.load(data_file)
#     return json_data
#
#
# test_cases = read_file_data(filename, path)
#
#
# class TestLoan(IconIntegrateTestBase):
#     TEST_HTTP_ENDPOINT_URI_V3 = "http://18.144.108.38:9000/api/v3"
#     SCORES = os.path.abspath(os.path.join(DIR_PATH, '..'))
#
#     def setUp(self):
#         super().setUp()
#         self.contracts = {}
#         # test2 = hx7a1824129a8fe803e45a3aae1c0e060399546187
#         private = "0a354424b20a7e3c55c43808d607bddfac85d033e63d7d093cb9f0a26c4ee022"
#         self._test2 = KeyWallet.load(bytes.fromhex(private))
#         # self._test2 = KeyWallet.create()
#         self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))
#         print(self._test1.get_address())
#         print(self._test2.get_address())
#         # deploy SCORE
#         for address in DEPLOY:
#             self.SCORE_PROJECT = self.SCORES + "/" + address
#             print('Deploying ' + address + ' Contract in Testnet')
#             self.contracts[address] = self._deploy_score()['scoreAddress']
#             print('Deployed Successfully')
#
#         for addr in TOKEN:
#             self.SCORES = os.path.abspath(os.path.join(DIR_PATH, '../../token_contracts'))
#             self.SCORE_PROJECT = self.SCORES + "/" + addr
#             print('Deploying ' + addr + ' Contract in Testnet')
#             self.contracts[addr] = self._deploy_score()['scoreAddress']
#         self.contracts = {
#             'loans':
#                 {'zip': 'core_contracts/loans.zip',
#                  'SCORE': self.contracts['loans']},
#             'staking': {'zip': 'core_contracts/staking.zip',
#                         'SCORE': self.contracts['staking']},
#             'dividends': {'zip': 'core_contracts/dividends.zip',
#                           'SCORE': self.contracts['dividends']},
#             'reserve': {'zip': 'core_contracts/reserve.zip',
#                         'SCORE': self.contracts['reserve']},
#             'rewards': {'zip': 'core_contracts/rewards.zip',
#                         'SCORE': self.contracts['rewards']},
#             'dex': {'zip': 'core_contracts/dex.zip',
#                     'SCORE': self.contracts['dex']},
#             'governance': {'zip': 'core_contracts/governance.zip',
#                            'SCORE': self.contracts['governance']},
#             'oracle': {'zip': 'core_contracts/oracle.zip',
#                              'SCORE': self.contracts['dummy_oracle']},
#             'sicx': {'zip': 'token_contracts/sicx.zip',
#                      'SCORE': self.contracts['sicx']},
#             'bnUSD': {'zip': 'token_contracts/bnUSD.zip',
#                     'SCORE': self.contracts['bnUSD']},
#             'bal': {'zip': 'token_contracts/bal.zip',
#                     'SCORE': self.contracts['bal']},
#             'bwt': {'zip': 'token_contracts/bwt.zip',
#                     'SCORE': self.contracts['bwt']}
#         }
#
#         self._setVariablesAndInterfaces()
#
#     @retry(JSONRPCException, tries=10, delay=1, back_off=2)
#     def _get_tx_result(self, _tx_hash):
#         tx_result = self.icon_service.get_transaction_result(_tx_hash)
#         return tx_result
#
#     @retry(JSONRPCException, tries=10, delay=1, back_off=2)
#     def get_tx_result(self, _call):
#         tx_result = self.icon_service.call(_call)
#         return tx_result
#
#     def _setVariablesAndInterfaces(self):
#         addresses = {
#             'loans': self.contracts['loans']['SCORE'],
#             'dex': self.contracts['dex']['SCORE'],
#             'staking': self.contracts['staking']['SCORE'],
#             'rewards': self.contracts['rewards']['SCORE'],
#             'reserve': self.contracts['reserve']['SCORE'],
#             'dividends': self.contracts['dividends']['SCORE'],
#             'oracle': self.contracts['oracle']['SCORE'],
#             'sicx': self.contracts['sicx']['SCORE'],
#             'bnUSD': self.contracts['bnUSD']['SCORE'],
#             'bal': self.contracts['bal']['SCORE'],
#             'bwt': self.contracts['bwt']['SCORE']
#         }
#
#         settings = [
#             {'contract': 'sicx', 'method': 'setAdmin',
#              'params': {'_admin': self.contracts['staking']['SCORE']}
#              },
#             {'contract': 'sicx', 'method': 'setStakingAddress',
#              'params': {'_address': self.contracts['staking']['SCORE']}},
#             {'contract': 'staking', 'method': 'setSicxAddress',
#              'params': {'_address': self.contracts['sicx']['SCORE']}},
#             {'contract': 'bnUSD', 'method': 'setGovernance',
#              'params': {'_address': self.contracts['governance']['SCORE']}},
#             {'contract': 'bal', 'method': 'setGovernance',
#              'params': {'_address': self.contracts['governance']['SCORE']}},
#             {'contract': 'bwt', 'method': 'setGovernance',
#              'params': {'_address': self.contracts['governance']['SCORE']}},
#             {'contract': 'dex', 'method': 'setGovernance',
#              'params': {'_address': self.contracts['governance']['SCORE']}},
#             {'contract': 'reserve', 'method': 'setGovernance',
#              'params': {'_address': self.contracts['governance']['SCORE']}},
#             {'contract': 'rewards', 'method': 'setGovernance',
#              'params': {'_address': self.contracts['governance']['SCORE']}},
#             {'contract': 'dividends', 'method': 'setGovernance',
#              'params': {'_address': self.contracts['governance']['SCORE']}},
#             {'contract': 'loans', 'method': 'setGovernance',
#              'params': {'_address': self.contracts['governance']['SCORE']}},
#             {'contract': 'governance', 'method': 'setAddresses', 'params': {'_addresses': addresses}},
#             {'contract': 'governance', 'method': 'launchBalanced', 'params': {}
#              }
#         ]
#         for sett in settings:
#             print(sett)
#             transaction = CallTransactionBuilder() \
#                 .from_(self._test1.get_address()) \
#                 .to(self.contracts[sett['contract']]['SCORE']) \
#                 .value(0) \
#                 .step_limit(10000000) \
#                 .nid(3) \
#                 .nonce(100) \
#                 .method(sett['method']) \
#                 .params(sett['params']) \
#                 .build()
#             signed_transaction = SignedTransaction(transaction, self._test1)
#             _tx_result = self.process_transaction(signed_transaction, self.icon_service)
#             self.assertTrue('status' in _tx_result)
#             self.assertEqual(1, _tx_result['status'])
#
#     def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS, _type: str = 'install') -> dict:
#         transaction = DeployTransactionBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(to) \
#             .step_limit(100_000_000_000) \
#             .nid(3) \
#             .nonce(100) \
#             .content_type("application/zip") \
#             .content(gen_deploy_data_content(self.SCORE_PROJECT)) \
#             .build()
#
#         # Returns the signed transaction object having a signature
#         signed_transaction = SignedTransaction(transaction, self._test1)
#
#         # process the transaction in local
#         _tx_result = self.process_transaction(signed_transaction, self.icon_service)
#         # _tx_result = self._get_tx_result(tx_hash)
#         # print(_tx_result)
#
#         # check transaction result
#         self.assertEqual(1, _tx_result['status'])
#         if self.assertEqual(1, _tx_result['status']):
#             print('Deployed Successfully')
#
#         return _tx_result
#
#     def _score_update(self):
#         # update SCORE
#         for address in UPDATE:
#             print('======================================================================')
#             print('Test Score Update(' + address + ')')
#             print('----------------------------------------------------------------------')
#             self.SCORES = os.path.abspath(os.path.join(DIR_PATH, '../../core_contracts'))
#             self.SCORE_PROJECT = self.SCORES + "/" + address
#             SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..')) + "/" + address
#             tx_result = self._deploy_score(self.contracts[address], 'update')
#             self.assertEqual(
#                 self.contracts[address], tx_result['scoreAddress'])
#
#     # # Adding collateral to wallet _test1 and testing withdraw collateral from _test1
#     def test_addCollateral(self):
#         cases = test_cases['stories']
#         for case in cases:
#             _tx_result = {}
#             print(case['description'])
#             if case['actions']['sender'] == 'user1':
#                 wallet_address = self._test1.get_address()
#                 wallet = self._test1
#             else:
#                 wallet_address = self._test2.get_address()
#                 wallet = self._test2
#             if case['actions']['name'] == 'addCollateral':
#                 _to = self.contracts['loans']['SCORE']
#                 meth = case['actions']['name']
#                 val = int(case['actions']['deposited_icx'])
#                 data1 = case['actions']['args']
#                 params = {"_asset": data1['_asset'], "_amount": data1['_amount']}
#             elif case['actions']['name'] == 'add_bad_test_position':
#                 _to = self.contracts['loans']['SCORE']
#                 meth = case['actions']['name']
#                 val = 0
#                 data2 = case['actions']['args']
#                 params = {}
#             else:
#                 _to = self.contracts['loans']['SCORE']
#                 meth = case['actions']['name']
#                 val = 0
#                 data2 = case['actions']['args']
#                 params = {"_owner": self._test1.get_address()}
#
#             transaction = CallTransactionBuilder() \
#                 .from_(wallet_address) \
#                 .to(_to) \
#                 .value(val) \
#                 .step_limit(10000000) \
#                 .nid(3) \
#                 .nonce(100) \
#                 .method(meth) \
#                 .params(params) \
#                 .build()
#             signed_transaction = SignedTransaction(transaction, wallet)
#             _tx_result = self.process_transaction(signed_transaction, self.icon_service)
#             print(_tx_result)
#             if 'revertMessage' in case['actions'].keys():
#                 self.assertEqual(_tx_result['failure']['message'], case['actions']['revertMessage'])
#                 print('Revert Matched')
#             else:
#                 bal_of_sicx = self.balanceOfTokens('sicx', wallet_address)
#                 bal_of_icd = self.balanceOfTokens('bnUSD', wallet_address)
#                 self.assertEqual(1, _tx_result['status'])
#                 self.assertEqual(int(case['actions']['expected_sicx_baln_loan']), int(bal_of_sicx, 16))
#                 self.assertEqual(int(case['actions']['expected_icd_bal_wallet']), int(bal_of_icd, 16))
#                 account_position = self._getAccountPositions(wallet_address)
#                 assets = account_position['assets']
#                 if 'sICX' and 'ICD' in assets:
#                     position_to_check = {'sICX': str(bal_of_sicx), 'ICD': hex(int(bal_of_icd, 16))}
#                 else:
#                     position_to_check = {'sICX': str(bal_of_sicx)}
#                 self.assertEqual(position_to_check, assets)
#
#                 self.assertEqual(case['actions']['standing'], account_position['standing'])
#                 print('liquidating account 2.....')
#
#     def balanceOfTokens(self, name, owner):
#         params = {
#             "_owner": owner
#         }
#         if name == 'sicx':
#             contract = self.contracts['sicx']['SCORE']
#             params = {
#                 "_owner": self.contracts['loans']['SCORE']
#             }
#         elif name == 'dividends':
#             contract = self.contracts['dividends']['SCORE']
#         else:
#             contract = self.contracts['bnUSD']['SCORE']
#         _call = CallBuilder().from_(self._test1.get_address()) \
#             .to(contract) \
#             .method("balanceOf") \
#             .params(params) \
#             .build()
#         response = self.get_tx_result(_call)
#         if name == 'sicx':
#             print('Balance of sicx token is ' + str(int(response, 16)))
#         else:
#             print("Balance of bnUSD is " + str(int(response, 16)))
#         return response
#
#     def _getAccountPositions(self, owner) -> dict:
#         params = {'_owner': owner}
#         _call = CallBuilder().from_(self._test1.get_address()) \
#             .to(self.contracts['loans']['SCORE']) \
#             .method('getAccountPositions') \
#             .params(params) \
#             .build()
#         result = self.get_tx_result(_call)
#         print(result)
#         return result
#
#     def getBalances(self):
#         _call = CallBuilder().from_(self._test1.get_address()) \
#             .to(self.contracts['dividends']['SCORE']) \
#             .method('getBalances') \
#             .build()
#         result = self.get_tx_result(_call)
#         print(result)
#         return result