# import os
# import pickle
# from shutil import make_archive
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
#
# filename = 'test_scenarios/scenarios/loan-repayLoan.json'
#
# GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
# ORACLE = "cx61a36e5d10412e03c907a507d1e8c6c3856d9964"
#
#
# def read_file_data(filename):
#     with open(filename, encoding="utf8") as data_file:
#         json_data = json.load(data_file)
#     return json_data
#
#
# test_cases = read_file_data(filename)
#
#
# class TestLoan(IconIntegrateTestBase):
#     TEST_HTTP_ENDPOINT_URI_V3 = "http://18.144.108.38:9000/api/v3"
#
#     def setUp(self):
#         super().setUp()
#         self.contracts = {}
#
#         self.wallet = KeyWallet.load("../keystores/keystore_test1.json", "test1_Account")
#         # Balanced test wallet
#         with open("../keystores/balanced_test.pwd", "r") as f:
#             key_data = f.read()
#         self.btest_wallet = KeyWallet.load("../keystores/balanced_test.json", key_data)
#
#         # test2 = hx7a1824129a8fe803e45a3aae1c0e060399546187
#         private = "0a354424b20a7e3c55c43808d607bddfac85d033e63d7d093cb9f0a26c4ee022"
#         self._test2 = KeyWallet.load(bytes.fromhex(private))
#         # self._test2 = KeyWallet.create()
#         self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))
#         print(self._test1.get_address())
#         print(self._test2.get_address())
#
#         self.results = {}
#
#         self.contracts = {'loans': {'zip': 'core_contracts/loans.zip',
#                                     'SCORE': 'cxa0f715fb2c4bc8f4c6399c2cc26167a27be0aa61'},
#                           'staking': {'zip': 'core_contracts/staking.zip',
#                                       'SCORE': 'cxbabed822d59b605dbeb6322735c529b292baac3b'},
#                           'dividends': {'zip': 'core_contracts/dividends.zip',
#                                         'SCORE': 'cx1379084f45776301abda3849c6e374f460ee0155'},
#                           'reserve': {'zip': 'core_contracts/reserve.zip',
#                                       'SCORE': 'cx71dda2221bf88faddc8f84b72ffd6db296e5609e'},
#                           'daofund': {'zip': 'core_contracts/daofund.zip',
#                                       'SCORE': 'cxfd09787f23d23b945fa0c7eb55b5aa69425da1c8'},
#                           'rewards': {'zip': 'core_contracts/rewards.zip',
#                                       'SCORE': 'cx27aa3bf62145822e60d85fa5d18dabdcff5b9ada'},
#                           'dex': {'zip': 'core_contracts/dex.zip',
#                                   'SCORE': 'cx01eee12b6614e5328e0a84261652cb7f055e0176'},
#                           'governance': {'zip': 'core_contracts/governance.zip',
#                                          'SCORE': 'cxd7b3e71dcff3d75392216e208f28ef68e8a54ec0'},
#                           'oracle': {'zip': 'core_contracts/oracle.zip',
#                                      'SCORE': 'cx7171e2f5653c1b9c000e24228276b8d24e84f10d'},
#                           'sicx': {'zip': 'token_contracts/sicx.zip',
#                                    'SCORE': 'cx799f724e02560a762b5f2bd3b6d2d8d59d7aecc1'},
#                           'bnUSD': {'zip': 'token_contracts/bnUSD.zip',
#                                     'SCORE': 'cx266bdc0c35828c8130cdf1cbaa3ad109f7694722'},
#                           'bnXLM': {'zip': 'token_contracts/bnXLM.zip',
#                                     'SCORE': 'cx266bdc0c35828c8130cdf1cbaa3ad109f7694722'},
#                           'bnDOGE': {'zip': 'token_contracts/bnDOGE.zip',
#                                      'SCORE': 'cx266bdc0c35828c8130cdf1cbaa3ad109f7694722'},
#                           'baln': {'zip': 'token_contracts/baln.zip',
#                                    'SCORE': 'cx4d0768508a7ff550de4405f27aebfb8831565c19'},
#                           'bwt': {'zip': 'token_contracts/bwt.zip',
#                                   'SCORE': 'cx663f9d59163846d9f6c6f7b586858c59aa8878a9'}}
#
#         self.deploy_all(self.btest_wallet)
#         print(
#             '------------------------------------------------------------------------------------------------------------------')
#         print(self.contracts)
#         print(
#             '----------Contracts for Testing UI--------------------------------------------------------------------------------')
#         print(self.get_scores_json(self.contracts))
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
#     def compress(self):
#         """
#         Compress all SCORE folders in the core_self.contracts and toekn_self.contracts folders
#         """
#         deploy = list(self.contracts.keys())[:]
#         for directory in {"../core_contracts", "../token_contracts"}:
#             with os.scandir(directory) as it:
#                 for file in it:
#                     archive_name = directory + "/" + file.name
#                     if file.is_dir() and file.name in deploy:
#                         make_archive(archive_name, "zip", directory, file.name)
#                         self.contracts[file.name]['zip'] = archive_name + '.zip'
#
#     def deploy_SCORE(self, contract, params, wallet, update) -> str:
#         """
#         contract is of form {'zip': 'core_self.contracts/governance.zip', 'SCORE': 'cx1d81f93b3b8d8d2a6455681c46128868782ddd09'}
#         params is a dicts
#         wallet is a wallet file
#         update is boolian
#         """
#         print(f'{contract["zip"]}')
#         if update:
#             dest = contract['SCORE']
#         else:
#             dest = GOVERNANCE_ADDRESS
#         zip_file = contract['zip']
#         step_limit = 4000100000
#         deploy_transaction = DeployTransactionBuilder() \
#             .from_(wallet.get_address()) \
#             .to(dest) \
#             .nid(3) \
#             .nonce(100) \
#             .content_type("application/zip") \
#             .content(gen_deploy_data_content(zip_file)) \
#             .params(params) \
#             .build()
#
#         signed_transaction = SignedTransaction(deploy_transaction, wallet, step_limit)
#         tx_hash = self.icon_service.send_transaction(signed_transaction)
#         res = self._get_tx_result(tx_hash)
#         print(f'Status: {res["status"]}')
#         if len(res["eventLogs"]) > 0:
#             for item in res["eventLogs"]:
#                 print(f'{item} \n')
#         if res['status'] == 0:
#             print(f'Failure: {res["failure"]}')
#         print('')
#         return res.get('scoreAddress', '')
#
#     def send_tx(self, dest, value, method, params, wallet):
#         """
#         dest is the name of the destination contract.
#         """
#         print(
#             '------------------------------------------------------------------------------------------------------------------')
#         print(f'Calling {method}, with parameters {params} on the {dest} contract.')
#         print(
#             '------------------------------------------------------------------------------------------------------------------')
#         transaction = CallTransactionBuilder() \
#             .from_(wallet.get_address()) \
#             .to(self.contracts[dest]['SCORE']) \
#             .value(value) \
#             .step_limit(10000000) \
#             .nid(3) \
#             .nonce(100) \
#             .method(method) \
#             .params(params) \
#             .build()
#         signed_transaction = SignedTransaction(transaction, wallet)
#         tx_hash = self.icon_service.send_transaction(signed_transaction)
#
#         res = self._get_tx_result(tx_hash)
#         print(
#             f'************************************************** Status: {res["status"]} **************************************************')
#         if len(res["eventLogs"]) > 0:
#             for item in res["eventLogs"]:
#                 print(f'{item} \n')
#         if res['status'] == 0:
#             print(f'Failure: {res["failure"]}')
#         return res
#
#     def deploy_all(self, wallet):
#         """
#         Compress, Deploy and Configure all SCOREs
#         """
#         self.compress()
#
#         deploy = list(self.contracts.keys())[:]
#         deploy.remove('oracle')
#         deploy.remove('staking')
#         deploy.remove('sicx')
#         deploy.remove('governance')
#
#         governance = self.deploy_SCORE(self.contracts['governance'], {}, wallet, 0)
#         self.contracts['governance']['SCORE'] = governance
#         for score in deploy:
#             self.contracts[score]['SCORE'] = self.deploy_SCORE(self.contracts[score], {'_governance': governance},
#                                                                wallet, 0)
#         self.contracts['staking']['SCORE'] = self.deploy_SCORE(self.contracts['staking'], {}, wallet, 0)
#         self.contracts['sicx']['SCORE'] = self.deploy_SCORE(self.contracts['sicx'],
#                                                             {'_admin': self.contracts['staking']['SCORE']}, wallet,
#                                                             0)
#
#         config = list(self.contracts.keys())[:]
#         config.remove('governance')
#         config.remove('bnDOGE')
#         config.remove('bnXLM')
#         addresses = {contract: self.contracts[contract]['SCORE'] for contract in config}
#
#         txns = [{'contract': 'staking', 'value': 0, 'method': 'setSicxAddress',
#                  'params': {'_address': self.contracts['sicx']['SCORE']}},
#                 {'contract': 'governance', 'value': 0, 'method': 'setAddresses', 'params': {'_addresses': addresses}},
#                 {'contract': 'governance', 'value': 0, 'method': 'launchBalanced', 'params': {}}]
#
#         for tx in txns:
#             res = self.send_tx(tx["contract"], tx["value"], tx["method"], tx["params"], wallet)
#             self.results[f'{tx["contract"]}|{tx["method"]}|{tx["params"]}'] = res
#
#     def get_scores_json(self, contracts):
#         """
#         Prints out dictionary of SCORE addresses for use in testing UI.
#         """
#         scores = {}
#         for score in contracts:
#             scores[score] = self.contracts[score]['SCORE']
#         return json.dumps(scores)
#
#     def call_tx(self, dest: str, method: str, params: dict = {}):
#         """
#         dest is the name of the destination contract.
#         """
#         print(
#             '------------------------------------------------------------------------------------------------------------------')
#         print(f'Reading {method}, with parameters {params} on the {dest} contract.')
#         print(
#             '------------------------------------------------------------------------------------------------------------------')
#         call = CallBuilder() \
#             .from_(self.wallet.get_address()) \
#             .to(self.contracts[dest]['SCORE']) \
#             .method(method) \
#             .params(params) \
#             .build()
#         result = self.icon_service.call(call)
#         print(result)
#         return result
#
#     # def _score_update(self):
#     #     # update SCORE
#     #     for address in UPDATE:
#     #         print('======================================================================')
#     #         print('Test Score Update(' + address + ')')
#     #         print('----------------------------------------------------------------------')
#     #         self.SCORES = os.path.abspath(os.path.join(DIR_PATH, '../../core_contracts'))
#     #         self.SCORE_PROJECT = self.SCORES + "/" + address
#     #         SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..')) + "/" + address
#     #         tx_result = self._deploy_score(self.contracts[address], 'update')
#     #         self.assertEqual(
#     #             self.contracts[address], tx_result['scoreAddress'])
#
#     # # Adding collateral to wallet _test1
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
#                 params = {"_asset": data1['_asset'], "_amount": int(data1['_amount'])}
#             else:
#                 _to = self.contracts['bnUSD']['SCORE']
#                 meth = case['actions']['name']
#                 val = 0
#                 data2 = case['actions']['args']
#                 param = {"method": data2['method'], "params": data2['params']}
#                 data = json.dumps(param).encode("utf-8")
#                 print(data2['_to'])
#                 params = {'_to': self.contracts['loans']['SCORE'], '_value': int(data2['_value']), '_data': data}
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
#                 bal_of_sicx = self.balanceOfTokens('sicx')
#                 bal_of_icd = self.balanceOfTokens('bnUSD')
#                 self.assertEqual(1, _tx_result['status'])
#                 self.assertEqual(int(case['actions']['expected_sicx_baln_loan']), int(bal_of_sicx, 16))
#                 self.assertEqual(int(case['actions']['expected_icd_debt_baln_loan']), int(bal_of_icd, 16))
#                 account_position = self._getAccountPositions()
#                 assets = account_position['assets']
#                 position_to_check = {'sICX': str(bal_of_sicx), 'bnUSD': hex(int(bal_of_icd, 16) + int(self.getBalances()['bnUSD'], 16))}
#                 self.assertEqual(position_to_check, assets)
#                 print('loans repaid')
#
#     def balanceOfTokens(self, name):
#         params = {
#             "_owner": self._test1.get_address()
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
#             print("Balance of icd is " + str(int(response, 16)))
#         return response
#
#     def _getAccountPositions(self) -> dict:
#         params = {'_owner': self._test1.get_address()}
#         _call = CallBuilder().from_(self._test1.get_address()) \
#             .to(self.contracts['loans']['SCORE']) \
#             .method('getAccountPositions') \
#             .params(params) \
#             .build()
#         result = self.get_tx_result(_call)
#         return result
#
#     def getBalances(self):
#         _call = CallBuilder().from_(self._test1.get_address()) \
#             .to(self.contracts['dividends']['SCORE']) \
#             .method('getBalances') \
#             .build()
#         result = self.get_tx_result(_call)
#         return result