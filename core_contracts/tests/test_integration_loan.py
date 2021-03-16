# import os
# import pickle
# from time import sleep
#
# from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS
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
# # DEPLOY = ['loans', 'reserve', 'dividends', 'dummy_oracle', 'staking', 'rewards', 'dex', 'governance']
# DEPLOY = ['loans', 'staking']
# TOKEN = ['bal', 'bwt', 'icd', 'sicx']
# UPDATE = ['loans']
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
#
#         # hx2bcb7c0d9d349f896060b3f57e717b80dc2938d8
#         private_key3 = "5b0f34e519db3bce2ded999e9176a943ee4b3ae15a7efa6e2e8cea514ac04bf8"
#         self._test3 = KeyWallet.load(bytes.fromhex(private_key3))
#
#         # wallet = KeyWallet.create()
#         # print("address: ", wallet.get_address())  # Returns an address
#         # print("private key: ", wallet.get_private_key())
#
#         # deploy SCORE
#         # for address in DEPLOY:
#         #     self.SCORE_PROJECT = self.SCORES + "/" + address
#         #     print('Deploying ' + address + ' Contract in Testnet')
#         #     self.contracts[address] = self._deploy_score()['scoreAddress']
#         # print(self.contracts)
#         # for addr in TOKEN:
#         #     self.SCORES = os.path.abspath(os.path.join(DIR_PATH, '../../token_contracts'))
#         #     self.SCORE_PROJECT = self.SCORES + "/" + addr
#         #     print('Deploying ' + addr + ' Contract in Testnet')
#         #     self.contracts[addr] = self._deploy_score()['scoreAddress']
#
#         # with open('/home/sudeep/contracts-private/contracts_20210208131139.pkl', 'rb') as f:
#         #     self.contracts = pickle.load(f)
#         # print(self.contracts)
#         self.contracts = {'loans': {'zip': 'core_contracts/loans.zip',
#                                     'SCORE': 'cx3c3fe6eeb1f69601edaf2de000ae1bff62f3dace'},
#                           'staking': {'zip': 'core_contracts/staking.zip',
#                                       'SCORE': 'cxdc140c1d6a4ba79037b76adff8b94970cdde2f25'},
#                           'dividends': {'zip': 'core_contracts/dividends.zip',
#                                         'SCORE': 'cx354c0ce44e543ebce9478bf0de3621c95473fc90'},
#                           'reserve': {'zip': 'core_contracts/reserve.zip',
#                                       'SCORE': 'cx0a478572e443bbfd66a35d124f63a2db9b637483'},
#                           'rewards': {'zip': 'core_contracts/rewards.zip',
#                                       'SCORE': 'cxe6074249f58898af2d6d00859ecb54e3f658ebe5'},
#                           'dex': {'zip': 'core_contracts/dex.zip',
#                                   'SCORE': 'cx4c73961fd85f13e822f72c2c96120c99e2e637d5'},
#                           'governance': {'zip': 'core_contracts/governance.zip',
#                                          'SCORE': 'cxeb7eb8d592ce76d0fcf1a3edd56b50ad2f1f72c5'},
#                           'dummy_oracle': {'zip': 'core_contracts/dummy_oracle.zip',
#                                            'SCORE': 'cx355d0e49525a681723ac0df9347189b5bb7814c8'},
#                           'sicx': {'zip': 'token_contracts/sicx.zip',
#                                    'SCORE': 'cxc60ef756b875786c9f820313ac4015e45726b47d'},
#                           'icd': {'zip': 'token_contracts/icd.zip',
#                                   'SCORE': 'cx14a00b375511d6bb1ad4e2c8eee41f4c8a167095'},
#                           'bal': {'zip': 'token_contracts/bal.zip',
#                                   'SCORE': 'cxbc2752abceba2bf179c1bfe0bc3f88caedcf2bd9'},
#                           'bwt': {'zip': 'token_contracts/bwt.zip',
#                                   'SCORE': 'cx0c6bb52e5e34ad8848de911be8ae52be38992363'}}
#
#         # self._setVariablesAndInterfaces()
#         # print("done")
#         self.transferICX()
#         # self._updateStanding()
#         # self._getAccountPositions()
#         # self._addCollateral("{\"method\": \"_deposit_and_borrow\", \"params\": {\"_sender\": \"".encode("utf-8"),
#         #                     "\", \"_asset\": \"ICD\", \"_amount\": -100000000000000000000}}".encode("utf-8"))
#         # # self._addTestCollateral()
#         # self._getAccountPositions()
#
#         # self._getTestAccountPosition()
#         # self._retireAssets()
#         # self._score_update()
#         # self._getTestAccountPosition()
#         # self._repayloan()
#         # self._withdrawCollateral()
#         # self._getAvailableAssets()
#         # self._liquidate()
#         # self._updateStanding()
#         # self._getAccountPositions()
#         # self._getTestAccountPosition()
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
#         addresses = {'loans': self.contracts['loans']['SCORE'],
#                      'dex': self.contracts['dex']['SCORE'],
#                      'staking': self.contracts['staking']['SCORE'],
#                      'rewards': self.contracts['rewards']['SCORE'],
#                      'reserve': self.contracts['reserve']['SCORE'],
#                      'dividends': self.contracts['dividends']['SCORE'],
#                      'oracle': self.contracts['dummy_oracle']['SCORE'],
#                      'sicx': self.contracts['sicx']['SCORE'],
#                      'icd': self.contracts['icd']['SCORE'],
#                      'bal': self.contracts['bal']['SCORE'],
#                      'bwt': self.contracts['bwt']['SCORE']
#                      }
#
#         settings = [{'contract': 'sicx', 'method': 'setAdmin', 'params': {'_admin': self.contracts['staking']['SCORE']}},
#                     {'contract': 'sicx', 'method': 'setStakingAddress',
#                      'params': {'_address': self.contracts['staking']['SCORE']}},
#                     {'contract': 'staking', 'method': 'setSicxAddress',
#                      'params': {'_address': self.contracts['sicx']['SCORE']}},
#                     {'contract': 'icd', 'method': 'setGovernance',
#                      'params': {'_address': self.contracts['governance']['SCORE']}},
#                     {'contract': 'bal', 'method': 'setGovernance',
#                      'params': {'_address': self.contracts['governance']['SCORE']}},
#                     {'contract': 'bwt', 'method': 'setGovernance',
#                      'params': {'_address': self.contracts['governance']['SCORE']}},
#                     {'contract': 'dex', 'method': 'setGovernance',
#                      'params': {'_address': self.contracts['governance']['SCORE']}},
#                     {'contract': 'reserve', 'method': 'setGovernance',
#                      'params': {'_address': self.contracts['governance']['SCORE']}},
#                     {'contract': 'rewards', 'method': 'setGovernance',
#                      'params': {'_address': self.contracts['governance']['SCORE']}},
#                     {'contract': 'dividends', 'method': 'setGovernance',
#                      'params': {'_address': self.contracts['governance']['SCORE']}},
#                     {'contract': 'loans', 'method': 'setGovernance',
#                      'params': {'_address': self.contracts['governance']['SCORE']}},
#                     {'contract': 'governance', 'method': 'setAddresses', 'params': {'_addresses': addresses}},
#                     {'contract': 'governance', 'method': 'launchBalanced', 'params': {}}]
#
#         for sett in settings:
#             print(sett)
#             transaction = CallTransactionBuilder() \
#                 .from_(self._test1.get_address()) \
#                 .to(self.contracts[sett['contract']]) \
#                 .value(0) \
#                 .step_limit(10000000) \
#                 .nid(3) \
#                 .nonce(100) \
#                 .method(sett['method']) \
#                 .params(sett['params']) \
#                 .build()
#             signed_transaction = SignedTransaction(transaction, self._test1)
#             tx_hash = self.icon_service.send_transaction(signed_transaction)
#             _tx_result = self._get_tx_result(tx_hash)
#             self.assertTrue('status' in _tx_result)
#             self.assertEqual(1, _tx_result['status'])
#
#     def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS, _type: str = 'install') -> dict:
#         # Generates an instance of transaction for deploying SCORE.
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
#         tx_hash = self.icon_service.send_transaction(signed_transaction)
#         _tx_result = self._get_tx_result(tx_hash)
#
#         # check transaction result
#         self.assertTrue('status' in _tx_result)
#         self.assertEqual(1, _tx_result['status'])
#         self.assertTrue('scoreAddress' in _tx_result)
#
#         return _tx_result
#
#     def _score_update(self):
#         # update SCORE
#         for address in UPDATE:
#             print('======================================================================')
#             print('Test Score Update('+address+')')
#             print('----------------------------------------------------------------------')
#             self.SCORES = os.path.abspath(os.path.join(DIR_PATH, '../../core_contracts'))
#             self.SCORE_PROJECT = self.SCORES + "/" + address
#             SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..')) + "/" + address
#             tx_result = self._deploy_score(self.contracts[address], 'update')
#             self.assertEqual(
#                 self.contracts[address], tx_result['scoreAddress'])
#
#     def transferICX(self):
#         transaction = TransactionBuilder() \
#             .from_(self._test1.get_address()) \
#             .to('hxe62d11fa19a0e8575ad92f06bc8fd42edbfe27db') \
#             .value(50000 * ICX) \
#             .step_limit(10000000) \
#             .nid(3) \
#             .nonce(100) \
#             .build()
#         signed_transaction = SignedTransaction(transaction, self._test1)
#         tx_hash = self.icon_service.send_transaction(signed_transaction)
#         print("txHash: ", tx_hash)
#         print("ICX transferred")
#
#     # Adding collateral to wallet _test1
#     def _addCollateral(self, data1: bytes, data2: bytes):
#         # data1 = "{\"method\": \"_deposit_and_borrow\", \"params\": {\"_sender\": \"".encode("utf-8")
#         # data2 = "\", \"_asset\": \"ICD\", \"_amount\": 40000000000000000000}}".encode("utf-8")
#         params = {'_data1': data1, '_data2': data2}
#         transaction = CallTransactionBuilder() \
#             .from_(self._test3.get_address()) \
#             .to(self.contracts['loans']['SCORE']) \
#             .value(100 * ICX) \
#             .step_limit(10000000) \
#             .nid(3) \
#             .nonce(100) \
#             .method("addCollateral") \
#             .params(params) \
#             .build()
#         signed_transaction = SignedTransaction(transaction, self._test3)
#         tx_hash = self.icon_service.send_transaction(signed_transaction)
#         _tx_result = self._get_tx_result(tx_hash)
#         print(_tx_result)
#         self.assertEqual(1, _tx_result['status'])
#         print('added collateral')
#
#     def test_call_name(self):
#         # Generates a call instance using the CallBuilder
#         _call = CallBuilder().from_(self._test1.get_address()) \
#             .to(self.contracts['loans']['SCORE']) \
#             .method("name") \
#             .build()
#
#         # Sends the call request
#         response = self.get_tx_result(_call)
#         # check call result
#         self.assertEqual("BalancedLoans", response)
#         print("okk")
#
#     # Returns the available assets that balanced supports
#     def _getAvailableAssets(self):
#         # Generates a call instance using the CallBuilder
#         _call = CallBuilder().from_(self._test1.get_address()) \
#             .to(self.contracts['loans']['SCORE']) \
#             .method("getAvailableAssets") \
#             .build()
#
#         # Sends the call request
#         response = self.get_tx_result(_call)
#         print("assets")
#         print(response)
#
#     # Returns the account position of the wallet
#     def _getAccountPositions(self):
#         params = {'_owner': self._test3.get_address()}
#         _call = CallBuilder().from_(self._test1.get_address()) \
#             .to(self.contracts['loans']['SCORE']) \
#             .method('getAccountPositions') \
#             .params(params) \
#             .build()
#         result = self.get_tx_result(_call)
#         print("position")
#         print(result)
#
#     # Repays the amount of loans given as the arguments
#     def _repayloan(self):
#         data = "{\"method\": \"_repay_loan\", \"params\": {}}".encode("utf-8")
#         params = {'_to': self.contracts['loans']['SCORE'], '_value': 3 * ICX, '_data': data}
#         transaction = CallTransactionBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(self.contracts['icd']['SCORE']) \
#             .value(0) \
#             .step_limit(10000000) \
#             .nid(3) \
#             .nonce(100) \
#             .method("transfer") \
#             .params(params) \
#             .build()
#         signed_transaction = SignedTransaction(transaction, self._test1)
#         tx_hash = self.icon_service.send_transaction(signed_transaction)
#         _tx_result = self._get_tx_result(tx_hash)
#         print(_tx_result)
#         print(" ICX repaid")
#
#     # Function to call while user wants to withdraw collateral
#     def _withdrawCollateral(self):
#         params = {'_value': 16 * ICX}
#         transaction = CallTransactionBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(self.contracts['loans']['SCORE']) \
#             .value(0) \
#             .step_limit(10000000) \
#             .nid(3) \
#             .nonce(100) \
#             .method("withdrawCollateral") \
#             .params(params) \
#             .build()
#         signed_transaction = SignedTransaction(transaction, self._test1)
#         tx_hash = self.icon_service.send_transaction(signed_transaction)
#         _tx_result = self._get_tx_result(tx_hash)
#         print(_tx_result)
#         print(" collateral withdrawn")
#
#     # Updates the position of the wallet
#     def _updateStanding(self):
#         params = {"_owner": self._test1.get_address()}
#         transaction = CallTransactionBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(self.contracts['loans']['SCORE']) \
#             .value(0) \
#             .step_limit(10000000) \
#             .nid(3) \
#             .nonce(100) \
#             .method("updateStanding") \
#             .params(params) \
#             .build()
#         signed_transaction = SignedTransaction(transaction, self._test1)
#         tx_hash = self.icon_service.send_transaction(signed_transaction)
#         _tx_result = self._get_tx_result(tx_hash)
#         print("updateStanding called")
#         print(_tx_result)
#
#     def _updateStanding(self):
#         print("Calling updateStanding method")
#         params = {"_owner": self._test1.get_address()}
#         transaction = CallTransactionBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(self.contracts['loans']['SCORE']) \
#             .value(0) \
#             .step_limit(10000000) \
#             .nid(3) \
#             .nonce(100) \
#             .method("updateStanding") \
#             .params(params) \
#             .build()
#         signed_transaction = SignedTransaction(transaction, self._test1)
#         tx_hash = self.icon_service.send_transaction(signed_transaction)
#         _tx_result = self._get_tx_result(tx_hash)
#         self.assertEqual(1, _tx_result['status'])
#         print("updateStanding success")
#         # print(_tx_result)
