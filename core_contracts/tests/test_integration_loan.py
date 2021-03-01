import os
import pickle
from time import sleep

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
        self.contracts = {}
        # test2 = hx7a1824129a8fe803e45a3aae1c0e060399546187
        private = "0a354424b20a7e3c55c43808d607bddfac85d033e63d7d093cb9f0a26c4ee022"
        self._test2 = KeyWallet.load(bytes.fromhex(private))
        # self._test2 = KeyWallet.create()
        self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))
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

        with open('/home/sudeep/contracts-private/contracts_20210208131139.pkl', 'rb') as f:
            self.contracts = pickle.load(f)
        print(self.contracts)

        # self._setVariablesAndInterfaces()
        # self.transferICX()
        self._addCollateral("{\"method\": \"_deposit_and_borrow\", \"params\": {\"_sender\": \"".encode("utf-8"),
                            "\", \"_asset\": \"ICD\", \"_amount\": -10000000000000000000}}".encode("utf-8"))
        # self._addTestCollateral()
        self._getAccountPositions()
        # self._getTestAccountPosition()
        self._retireAssets()
        # self._score_update()
        # self._getTestAccountPosition()
        # self._repayloan()
        # self._withdrawCollateral()
        # self._getAvailableAssets()
        # self._liquidate()
        # self._updateStanding()
        self._getAccountPositions()
        # self._getTestAccountPosition()

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def _get_tx_result(self, _tx_hash):
        tx_result = self.icon_service.get_transaction_result(_tx_hash)
        return tx_result

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(self, _call):
        tx_result = self.icon_service.call(_call)
        return tx_result

    def _setVariablesAndInterfaces(self):
        addresses = {'loans': self.contracts['loans'],
                     'dex': self.contracts['dex'],
                     'staking': self.contracts['staking'],
                     'rewards': self.contracts['rewards'],
                     'reserve_fund': self.contracts['reserve_fund'],
                     'dividends': self.contracts['dividends'],
                     'oracle': self.contracts['dummy_oracle'],
                     'sicx': self.contracts['sicx'],
                     'icd': self.contracts['icd'],
                     'baln': self.contracts['bal'],
                     'bwt': self.contracts['bwt'],
                     }

        settings = [{'contract': 'sicx', 'method': 'setAdmin', 'params': {'_admin': self.contracts['staking']}},
                    {'contract': 'sicx', 'method': 'setStakingAddress',
                     'params': {'_address': self.contracts['staking']}},
                    {'contract': 'icd', 'method': 'setAdmin', 'params': {'_admin': self.contracts['loans']}},
                    {'contract': 'icd', 'method': 'setOracle',
                     'params': {'_address': self.contracts['dummy_oracle'], '_name': 'BandChain'}},
                    {'contract': 'bal', 'method': 'setAdmin', 'params': {'_admin': self._test1.get_address()}},
                    {'contract': 'bal', 'method': 'mint', 'params': {'_amount': 10 * ICX}},
                    {'contract': 'bwt', 'method': 'setAdmin', 'params': {'_admin': self.contracts['governance']}},
                    {'contract': 'staking', 'method': 'setSicxAddress',
                     'params': {'_address': self.contracts['sicx']}},
                    {'contract': 'reserve_fund', 'method': 'setLoansScore',
                     'params': {'_address': self.contracts['loans']}},
                    {'contract': 'reserve_fund', 'method': 'setBalnToken',
                     'params': {'_address': self.contracts['bal']}},
                    {'contract': 'reserve_fund', 'method': 'setSicxToken',
                     'params': {'_address': self.contracts['sicx']}},
                    {'contract': 'bal', 'method': 'mintTo',
                     'params': {'_account': self.contracts['reserve_fund'], '_amount': 10 * ICX}},
                    {'contract': 'bal', 'method': 'mintTo',
                     'params': {'_account': self._test1.get_address(), '_amount': 50 * ICX}},
                    {'contract': 'bal', 'method': 'setAdmin', 'params': {'_admin': self.contracts['rewards']}},
                    {'contract': 'dividends', 'method': 'setLoansScore',
                     'params': {'_address': self.contracts['loans']}},
                    {'contract': 'rewards', 'method': 'setBalnAddress',
                     'params': {'_address': self.contracts['bal']}},
                    {'contract': 'rewards', 'method': 'setBwtAddress',
                     'params': {'_address': self.contracts['bwt']}},
                    {'contract': 'rewards', 'method': 'setBatchSize', 'params': {'_batch_size': 30}},
                    {'contract': 'rewards', 'method': 'setGovernance',
                     'params': {'_address': self.contracts['governance']}},
                    {'contract': 'rewards', 'method': 'addNewDataSource',
                     'params': {'_data_source_name': 'Loans', '_contract_address': self.contracts['loans']}},
                    {'contract': 'rewards', 'method': 'addNewDataSource',
                     'params': {'_data_source_name': 'SICXICX', '_contract_address': self.contracts['dex']}},
                    {'contract': 'dex', 'method': 'setGovernance',
                     'params': {'_address': self.contracts['governance']}},
                    {'contract': 'dex', 'method': 'setAdmin', 'params': {'_admin': self._test1.get_address()}},
                    {'contract': 'dex', 'method': 'setRewards', 'params': {'_address': self.contracts['rewards']}},
                    {'contract': 'dex', 'method': 'setStaking', 'params': {'_address': self.contracts['staking']}},
                    {'contract': 'dex', 'method': 'setSicx', 'params': {'_address': self.contracts['sicx']}},
                    {'contract': 'dex', 'method': 'setDividends',
                     'params': {'_address': self.contracts['dividends']}},
                    {'contract': 'dex', 'method': 'setIcd', 'params': {'_address': self.contracts['icd']}},
                    {'contract': 'loans', 'method': 'setAdmin', 'params': {'_admin': self._test1.get_address()}},
                    {'contract': 'loans', 'method': 'setGovernance',
                     'params': {'_address': self.contracts['governance']}},
                    {'contract': 'loans', 'method': 'setDividends',
                     'params': {'_address': self.contracts['dividends']}},
                    {'contract': 'loans', 'method': 'setReserve',
                     'params': {'_address': self.contracts['reserve_fund']}},
                    {'contract': 'loans', 'method': 'setRewards',
                     'params': {'_address': self.contracts['rewards']}},
                    {'contract': 'loans', 'method': 'setStaking',
                     'params': {'_address': self.contracts['staking']}},
                    {'contract': 'loans', 'method': 'addAsset',
                     'params': {'_token_address': self.contracts['sicx'], 'is_active': 1, 'is_collateral': 1}},
                    {'contract': 'loans', 'method': 'addAsset',
                     'params': {'_token_address': self.contracts['icd'], 'is_active': 1, 'is_collateral': 0}},
                    {'contract': 'loans', 'method': 'addAsset',
                     'params': {'_token_address': self.contracts['bal'], 'is_active': 0, 'is_collateral': 1}},
                    {'contract': 'governance', 'method': 'setAddresses', 'params': {'_addresses': addresses}},
                    {'contract': 'governance', 'method': 'launchBalanced', 'params': {}}

        ]

        for sett in settings:
            print(sett)
            transaction = CallTransactionBuilder() \
                .from_(self._test1.get_address()) \
                .to(self.contracts[sett['contract']]) \
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

        # check transaction result
        self.assertTrue('status' in _tx_result)
        self.assertEqual(1, _tx_result['status'])
        self.assertTrue('scoreAddress' in _tx_result)

        return _tx_result

    def _score_update(self):
        # update SCORE
        for address in UPDATE:
            print('======================================================================')
            print('Test Score Update('+address+')')
            print('----------------------------------------------------------------------')
            self.SCORES = os.path.abspath(os.path.join(DIR_PATH, '../../core_contracts'))
            self.SCORE_PROJECT = self.SCORES + "/" + address
            SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..')) + "/" + address
            tx_result = self._deploy_score(self.contracts[address], 'update')
            self.assertEqual(
                self.contracts[address], tx_result['scoreAddress'])

    def transferICX(self):
        transaction = TransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._test2.get_address()) \
            .value(1000 * ICX) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        print("txHash: ", tx_hash)
        print("ICX transferred")

    def _addCollateral(self, data1: bytes, data2: bytes):
        # data1 = "{\"method\": \"_deposit_and_borrow\", \"params\": {\"_sender\": \"".encode("utf-8")
        # data2 = "\", \"_asset\": \"ICD\", \"_amount\": 40000000000000000000}}".encode("utf-8")
        params = {'_data1': data1, '_data2': data2}
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .value(200 * ICX) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("addCollateral") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print(_tx_result)
        self.assertEqual(1, _tx_result['status'])
        print('added collateral')

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

    def _getAvailableAssets(self):
        # Generates a call instance using the CallBuilder
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .method("getAvailableAssets") \
            .build()

        # Sends the call request
        response = self.get_tx_result(_call)
        print("assets")
        print(response)

    def _getAccountPositions(self):
        params = {'_owner': self._test1.get_address()}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .method('getAccountPositions') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("position")
        print(result)

    def _repayloan(self):
        data = "{\"method\": \"_repay_loan\", \"params\": {}}".encode("utf-8")
        params = {'_to': self.contracts['loans']['SCORE'], '_value': 3 * ICX, '_data': data}
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['icd']['SCORE']) \
            .value(0) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print(_tx_result)
        print(" ICX repaid")

    def _withdrawCollateral(self):
        params = {'_value': 16 * ICX}
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .value(0) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("withdrawCollateral") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print(_tx_result)
        print(" collateral withdrawn")

    def _updateStanding(self):
        params = {"_owner": self._test1.get_address()}
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


