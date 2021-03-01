import os
import pickle

from iconservice import IconScoreException
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.exception import JSONRPCException
from .repeater import retry

ICX = 1000000000000000000
DIR_PATH = os.path.abspath(os.path.dirname(__file__))
DEPLOY = ['loans', 'reserve_fund', 'dividends', 'dummy_oracle', 'staking', 'rewards', 'dex', 'governance']
# DEPLOY = ['loans', 'staking']
TOKEN = ['bal', 'bwt', 'icd', 'sicx']
UPDATE = ['loans']


class TestLoan(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://52.53.175.151:9000/api/v3"
    SCORES = os.path.abspath(os.path.join(DIR_PATH, '..'))

    def setUp(self):
        super().setUp()
        # self.contracts = {}
        # test2 = hx7a1824129a8fe803e45a3aae1c0e060399546187
        private = "0a354424b20a7e3c55c43808d607bddfac85d033e63d7d093cb9f0a26c4ee022"
        self._test2 = KeyWallet.load(bytes.fromhex(private))

        # test3 =  hx3d7ca00231a5ce61c6b33beae3eb492a647e8c11
        private_key3 = "329bbab70843831b870b0d27d0e53ad48bee0c09f86443451dc96b84c14f8abb"
        self._test3 = KeyWallet.load(bytes.fromhex(private_key3))

        # self._test3 = KeyWallet.create()
        # print("address: ", self._test3.get_address())  # Returns an address
        # print("private key: ", self._test3.get_private_key())

        self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))
        # self.icon_service = None
        print(self._test1.get_address())

        # deploy SCORE
        # for address in DEPLOY:
        #     self.SCORE_PROJECT = self.SCORES + "/" + address
        #     print('Deploying ' + address + ' Contract in Testnet')
        #     self.contracts[address] = self._deploy_score()['scoreAddress']
        #
        # for addr in TOKEN:
        #     self.SCORES = os.path.abspath(os.path.join(DIR_PATH, '../../token_contracts'))
        #     self.SCORE_PROJECT = self.SCORES + "/" + addr
        #     print('Deploying ' + addr + ' Contract in Testnet')
        #     self.contracts[addr] = self._deploy_score()['scoreAddress']

        # self.contracts = {'loans': 'cx89a5719cd7e89a6dbae333b6c65e6d483ca8fae8',
        # 'staking': 'cx6ebb33adc84ffc01324a981d4069e7fe03553836',
        # 'dividends': 'cx692962908cc8b04013de73177f97a008945f065e',
        # 'reserve_fund': 'cx62c522261eff90badb5db73852826a11cecf8bfb',
        # 'rewards': 'cx384710f1d207616e9f775a0ec9529592d90bcd6b',
        # 'dex': 'cx5a4621a959c57020edb8f3e6e19ac8b12a7bf31f',
        # 'governance': 'cx93854b36d28a592c53bc202f76250e7cb80be2c9',
        # 'dummy_oracle': 'cx56b6ab9ac9898b3008816a0ec9c36b4a5bde515d',
        # 'sicx': 'cx9c6325d2a9e7d52cfa1bd5ae3d970c338dcc2086',
        # 'icd': 'cxe942868be1b66d93cd6015655847a0420a85cb57',
        # 'bal': 'cx6b9b1b9300f1213cfd4575c45d22b81d32fe2a69',
        # 'bwt': 'cxb8726e735adb91611069a1cb09bab14608c9fc0c'}

        with open('/home/sudeep/contracts-private/contracts_20210209104106.pkl', 'rb') as f:
            self.contracts = pickle.load(f)
        print(self.contracts)

        # self.transferICX()
        # self._setVariablesAndInterfaces()

        self._getAvailableAssets()
        # self._getTestAccountPosition()
        # self._updateStanding()
        self._getTestAccountPosition()
        self._addTestCollateral()
        self._getTestAccountPosition()

        self._score_update()
        self._getTestAccountPosition()

        self._liquidate()

        self._getTestAccountPosition()

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def _get_tx_result(self, _tx_hash):
        tx_result = self.icon_service.get_transaction_result(_tx_hash)
        return tx_result

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(self, _call):
        tx_result = self.icon_service.call(_call)
        return tx_result

    def _setVariablesAndInterfaces(self):
        addresses = {'loans': self.contracts['loans']['SCORE'],
                     'dex': self.contracts['dex']['SCORE'],
                     'staking': self.contracts['staking']['SCORE'],
                     'rewards': self.contracts['rewards']['SCORE'],
                     'reserve_fund': self.contracts['reserve_fund']['SCORE'],
                     'dividends': self.contracts['dividends']['SCORE'],
                     'oracle': self.contracts['dummy_oracle']['SCORE'],
                     'sicx': self.contracts['sicx']['SCORE'],
                     'icd': self.contracts['icd']['SCORE'],
                     'baln': self.contracts['bal']['SCORE'],
                     'bwt': self.contracts['bwt']['SCORE'],
                     }

        settings = [{'contract': 'sicx', 'method': 'setAdmin', 'params': {'_admin': self.contracts['staking']['SCORE']}},
                    {'contract': 'sicx', 'method': 'setStakingAddress',
                     'params': {'_address': self.contracts['staking']['SCORE']}},
                    {'contract': 'icd', 'method': 'setAdmin', 'params': {'_admin': self.contracts['loans']['SCORE']}},
                    {'contract': 'icd', 'method': 'setOracle',
                     'params': {'_address': self.contracts['dummy_oracle']['SCORE'], '_name': 'BandChain'}},
                    {'contract': 'bal', 'method': 'setAdmin', 'params': {'_admin': self._test1.get_address()}},
                    {'contract': 'bal', 'method': 'mint', 'params': {'_amount': 10 * ICX}},
                    {'contract': 'bwt', 'method': 'setAdmin', 'params': {'_admin': self.contracts['governance']['SCORE']}},
                    {'contract': 'staking', 'method': 'setSicxAddress',
                     'params': {'_address': self.contracts['sicx']['SCORE']}},
                    {'contract': 'reserve_fund', 'method': 'setLoansScore',
                     'params': {'_address': self.contracts['loans']['SCORE']}},
                    {'contract': 'reserve_fund', 'method': 'setBalnToken',
                     'params': {'_address': self.contracts['bal']['SCORE']}},
                    {'contract': 'reserve_fund', 'method': 'setSicxToken',
                     'params': {'_address': self.contracts['sicx']['SCORE']}},
                    {'contract': 'bal', 'method': 'mintTo',
                     'params': {'_account': self.contracts['reserve_fund']['SCORE'], '_amount': 10 * ICX}},
                    {'contract': 'bal', 'method': 'mintTo',
                     'params': {'_account': self._test1.get_address(), '_amount': 50 * ICX}},
                    {'contract': 'bal', 'method': 'setAdmin', 'params': {'_admin': self.contracts['rewards']['SCORE']}},
                    {'contract': 'dividends', 'method': 'setLoansScore',
                     'params': {'_address': self.contracts['loans']['SCORE']}},
                    {'contract': 'rewards', 'method': 'setBalnAddress',
                     'params': {'_address': self.contracts['bal']['SCORE']}},
                    {'contract': 'rewards', 'method': 'setBwtAddress',
                     'params': {'_address': self.contracts['bwt']['SCORE']}},
                    {'contract': 'rewards', 'method': 'setBatchSize', 'params': {'_batch_size': 30}},
                    {'contract': 'rewards', 'method': 'setGovernance',
                     'params': {'_address': self.contracts['governance']['SCORE']}},
                    {'contract': 'rewards', 'method': 'addNewDataSource',
                     'params': {'_data_source_name': 'Loans', '_contract_address': self.contracts['loans']['SCORE']}},
                    {'contract': 'rewards', 'method': 'addNewDataSource',
                     'params': {'_data_source_name': 'SICXICX', '_contract_address': self.contracts['dex']['SCORE']}},
                    {'contract': 'dex', 'method': 'setGovernance',
                     'params': {'_address': self.contracts['governance']['SCORE']}},
                    {'contract': 'dex', 'method': 'setAdmin', 'params': {'_admin': self._test1.get_address()}},
                    {'contract': 'dex', 'method': 'setRewards', 'params': {'_address': self.contracts['rewards']['SCORE']}},
                    {'contract': 'dex', 'method': 'setStaking', 'params': {'_address': self.contracts['staking']['SCORE']}},
                    {'contract': 'dex', 'method': 'setSicx', 'params': {'_address': self.contracts['sicx']['SCORE']}},
                    {'contract': 'dex', 'method': 'setDividends',
                     'params': {'_address': self.contracts['dividends']['SCORE']}},
                    {'contract': 'dex', 'method': 'setIcd', 'params': {'_address': self.contracts['icd']['SCORE']}},
                    {'contract': 'loans', 'method': 'setAdmin', 'params': {'_admin': self._test1.get_address()}},
                    {'contract': 'loans', 'method': 'setGovernance',
                     'params': {'_address': self.contracts['governance']['SCORE']}},
                    {'contract': 'loans', 'method': 'setDividends',
                     'params': {'_address': self.contracts['dividends']['SCORE']}},
                    {'contract': 'loans', 'method': 'setReserve',
                     'params': {'_address': self.contracts['reserve_fund']['SCORE']}},
                    {'contract': 'loans', 'method': 'setRewards',
                     'params': {'_address': self.contracts['rewards']['SCORE']}},
                    {'contract': 'loans', 'method': 'setStaking',
                     'params': {'_address': self.contracts['staking']['SCORE']}},
                    # {'contract': 'loans', 'method': 'addAsset',
                    #  'params': {'_token_address': self.contracts['sicx']['SCORE'], 'is_active': 1, 'is_collateral': 1}},
                    # {'contract': 'loans', 'method': 'addAsset',
                    #  'params': {'_token_address': self.contracts['icd']['SCORE'], 'is_active': 1, 'is_collateral': 0}},
                    # {'contract': 'loans', 'method': 'addAsset',
                    #  'params': {'_token_address': self.contracts['bal']['SCORE'], 'is_active': 0, 'is_collateral': 1}},
                    {'contract': 'governance', 'method': 'setAddresses', 'params': {'_addresses': addresses}},
                    # {'contract': 'governance', 'method': 'launchBalanced', 'params': {}}

        ]

        for sett in settings:
            print(sett)
            transaction = CallTransactionBuilder() \
                .from_(self._test1.get_address()) \
                .to(self.contracts[sett['contract']]['SCORE']) \
                .value(0) \
                .step_limit(10000000) \
                .nid(3) \
                .nonce(100) \
                .method(sett['method']) \
                .params(sett['params']) \
                .build()
            signed_transaction = SignedTransaction(transaction, self._test1)
            tx_hash = self.icon_service.send_transaction(signed_transaction)
            _tx_result = self._get_tx_result(tx_hash)
            # print(_tx_result)
            self.assertTrue('status' in _tx_result)
            self.assertEqual(1, _tx_result['status'])

    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS, _type: str = 'install') -> dict:
        # Generates an instance of transaction for deploying SCORE.
        transaction = DeployTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(to) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(self.SCORE_PROJECT)) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        # process the transaction in local
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        # tx_result = self.process_transaction(signed_transaction)

        # check transaction result
        self.assertTrue('status' in _tx_result)
        self.assertEqual(1, _tx_result['status'])
        self.assertTrue('scoreAddress' in _tx_result)

        return _tx_result

    def _score_update(self):
        # update SCORE
        contract = 'loans'
        update = self.contracts[contract]['SCORE']
        # zip_file = self.contracts[contract]['zip']
        zip_file = '/home/sudeep/contracts-private/core_contracts/loans'
        transaction = DeployTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(update) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(zip_file)) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        # tx_result = self.process_transaction(signed_transaction)

        # check transaction result
        self.assertTrue('status' in _tx_result)
        self.assertEqual(1, _tx_result['status'])
        self.assertTrue('scoreAddress' in _tx_result)
        self.assertEqual(
                self.contracts[contract]['SCORE'], _tx_result['scoreAddress'])
        print('Test Score Update')
        # for address in UPDATE:
        #     print('======================================================================')
        #     print('Test Score Update('+address+')')
        #     print('----------------------------------------------------------------------')
        #     self.SCORES = os.path.abspath(os.path.join(DIR_PATH, '../../core_contracts'))
        #     self.SCORE_PROJECT = self.SCORES + "/" + address
        #     SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..')) + "/" + address
        #     tx_result = self._deploy_score(self.contracts[address]['SCORE'], 'update')
        #     self.assertEqual(
        #         self.contracts[address], tx_result['scoreAddress'])

    def transferICX(self):
        transaction = TransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._test3.get_address()) \
            .value(1000 * ICX) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        # tx_result = self.process_transaction(signed_transaction)

        print("txHash: ", tx_hash)
        print("ICX transferred")

    def _getAvailableAssets(self):
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .method("getAvailableAssets") \
            .build()

        # Sends the call request
        response = self.get_tx_result(_call)
        print("assets")
        print(response)

    def _updateStanding(self):
        params = {"_owner": self._test3.get_address()}
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .value(0) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("updateStanding") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print("updateStanding called")
        print(_tx_result)

    # Test liquidation for wallet _test2
    def _addTestCollateral(self):
        data1 = "{\"method\": \"_deposit_and_borrow\", \"params\": {\"_sender\": \"".encode("utf-8")
        data2 = "\", \"_asset\": \"\", \"_amount\": 0}}".encode("utf-8")
        params = {'_data1': data1, '_data2': data2}
        transaction = CallTransactionBuilder() \
            .from_(self._test3.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .value(782769 * ICX // 1000) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("addCollateral") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test3)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        # tx_result = self.process_transaction(signed_transaction)
        print(_tx_result)
        self.assertEqual(1, _tx_result['status'])
        print('added collateral to test2 account')

    def _getTestAccountPosition(self):
        params = {'_owner': self._test3.get_address()}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .method('getAccountPositions') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("test position")
        print(result)

    def _liquidate(self):
        params = {'_owner': self._test3.get_address()}
        transaction = CallTransactionBuilder() \
            .from_(self._test3.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .value(0) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("liquidate") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test3)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        # tx_result = self.process_transaction(signed_transaction)
        print("liquidate called")
        print(_tx_result)

    def test_call_name(self):
        # Generates a call instance using the CallBuilder
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .method("name") \
            .build()

        # Sends the call request
        response = self.get_tx_result(_call)
        # check call result
        self.assertEqual("BalancedLoans", response)
        print("okk")

