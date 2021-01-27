import os
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

from iconsdk.builder.transaction_builder import DeployTransactionBuilder
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
DEPLOY = ['loans', 'reserve_fund', 'dividends', 'dummy_oracle', 'staking']
# DEPLOY = ['loans', ]
TOKEN = ['bal', 'bwt', 'icd', 'sicx']


class TestLoan(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "https://zicon.net.solidwallet.io/api/v3"
    SCORES = os.path.abspath(os.path.join(DIR_PATH, '..'))

    def setUp(self):
        super().setUp()
        self.contracts = {}
        # self.tokens = {}
        self._test2 = KeyWallet.create()
        self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))
        # deploy SCORE
        # self._score_address = self._deploy_score()['scoreAddress']

        # balance = self.icon_service.get_balance(self._test1.get_address())
        # print("balance of test1: ", balance / 10 ** 18)
        # transaction = TransactionBuilder() \
        #     .from_(self._test1.get_address()) \
        #     .to(self._test2.get_address()) \
        #     .value(100 * ICX) \
        #     .step_limit(1000000) \
        #     .nid(80) \
        #     .nonce(2) \
        #     .version(3) \
        #     .build()
        # signed_transaction = SignedTransaction(transaction, self._test1)
        # tx_hash = self.icon_service.send_transaction(signed_transaction)
        # print(tx_hash)
        # print("icx transfered")
        # balance = self.icon_service.get_balance(self._test2.get_address())
        # print("balance of test 2: ", balance / 10 ** 18)
        print(self._test1.get_address())
        # deploy SCORE
        for address in DEPLOY:
            self.SCORE_PROJECT = self.SCORES + "/" + address
            self.contracts[address] = self._deploy_score()['scoreAddress']

        for addr in TOKEN:
            self.SCORES = os.path.abspath(os.path.join(DIR_PATH, '../../token_contracts'))
            self.SCORE_PROJECT = self.SCORES + "/" + addr
            self.contracts[addr] = self._deploy_score()['scoreAddress']

        self._setVariablesAndInterfaces()
        self.transferICX()

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def _get_tx_result(self, _tx_hash):
        tx_result = self.icon_service.get_transaction_result(_tx_hash)
        return tx_result

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(self, _call):
        tx_result = self.icon_service.call(_call)
        return tx_result

    def transferICX(self):
        balance = self.icon_service.get_balance(self._test2.get_address())
        print("balance of test1: ", balance)
        transaction = TransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._test2.get_address()) \
            .value(100 * ICX) \
            .step_limit(1000000) \
            .nid(80) \
            .nonce(2) \
            .version(3) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        print(tx_hash)
        print("icx transfered")
        balance = self.icon_service.get_balance(self._test2.get_address())
        print("balance of test 2: ", balance)


    def _setVariablesAndInterfaces(self):
        settings = [
            {'contract': 'sicx', 'method': 'setAdmin',
             'params': {'_admin': self.contracts['staking']}},
            {'contract': 'icd', 'method': 'setAdmin',
             'params': {'_admin': self.contracts['loans']}},
            {'contract': 'bal', 'method': 'setAdmin',
             'params': {'_admin': self._test1.get_address()}},
            {'contract': 'loans', 'method': 'setAdmin',
             'params': {'_admin': self._test1.get_address()}},
            {'contract': 'icd', 'method': 'set_oracle_address',
             'params': {'_address': self.contracts['dummy_oracle']}},
            {'contract': 'staking', 'method': 'setSicxAddress',
             'params': {'_address': self.contracts['sicx']}},
            {'contract': 'reserve_fund', 'method': 'set_loans_score',
             'params': {'_address': self.contracts['loans']}},
            {'contract': 'reserve_fund', 'method': 'set_baln_token',
             'params': {'_address': self.contracts['bal']}},
            {'contract': 'reserve_fund', 'method': 'set_sicx_token',
             'params': {'_address': self.contracts['sicx']}},
            {'contract': 'sicx', 'method': 'set_staking_address',
             'params': {'_address': self.contracts['staking']}},
            {'contract': 'bal', 'method': 'mint',
             'params': {'_amount': 10 * ICX}},
            {'contract': 'bal', 'method': 'mintTo',
             'params': {'_account': self.contracts['reserve_fund'], '_amount': 1000 * ICX}},
            {'contract': 'loans', 'method': 'toggle_loans_on',
             'params': {}},
            {'contract': 'loans', 'method': 'add_asset',
             'params': {'_token_address': self.contracts['sicx'], 'is_active': 1, 'is_collateral': 1}},
            {'contract': 'loans', 'method': 'add_asset',
             'params': {'_token_address': self.contracts['icd'], 'is_active': 1, 'is_collateral': 0}},
            {'contract': 'loans', 'method': 'add_asset',
             'params': {'_token_address': self.contracts['bal'], 'is_active': 0, 'is_collateral': 1}},
            {'contract': 'loans', 'method': 'set_dividends',
             'params': {'_address': self.contracts['dividends']}},
            {'contract': 'loans', 'method': 'set_reserve',
             'params': {'_address': self.contracts['reserve_fund']}},
            {'contract': 'loans', 'method': 'set_origination_fee',
             'params': {'_fee': 50}},
            {'contract': 'loans', 'method': 'set_replay_batch_size',
             'params': {'_size': 10}},
        ]

        for sett in settings:
            # print(sett)
            transaction = CallTransactionBuilder() \
                .from_(self._test1.get_address()) \
                .to(self.contracts[sett['contract']]) \
                .value(0) \
                .step_limit(10000000) \
                .nid(80) \
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
            .nid(80) \
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

    # def test_call_name(self):
    #     # Generates a call instance using the CallBuilder
    #     _call = CallBuilder().from_(self._test1.get_address()) \
    #         .to(self.contracts['loans']) \
    #         .method("name") \
    #         .build()
    #
    #     # Sends the call request
    #     response = self.get_tx_result(_call)
    #     # check call result
    #     self.assertEqual("BalancedLoans", response)

    # def test_getSicxAddress(self):
    #     # Generates a call instance using the CallBuilder
    #     _call = CallBuilder().from_(self._test1.get_address()) \
    #         .to(self.contracts['staking']) \
    #         .method("getSicxAddress") \
    #         .build()
    #
    #     # Sends the call request
    #     response = self.get_tx_result(_call)
    #     print(response)
    #     # check call result
    #     self.assertEqual(self.contracts['sicx'], response)

    def test_addCollateral(self):
        data = "{\"method\": \"_deposit_and_borrow\", \"params\": {\"_asset\": \"ICD\"," \
               " \"_amount\": 2000000000000000000}}".encode("utf-8")
        params = {'_to': self.contracts['loans'], '_data': data}
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['staking']) \
            .value(80 * ICX) \
            .step_limit(10000000) \
            .nid(80) \
            .nonce(100) \
            .method("addCollateral") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print(_tx_result)
        print('added collateral')

    # def test_getAvailableAssets(self):
    #     # Generates a call instance using the CallBuilder
    #     _call = CallBuilder().from_(self._test1.get_address()) \
    #         .to(self.contracts['loans']) \
    #         .method("getAvailableAssets") \
    #         .build()
    #
    #     # Sends the call request
    #     response = self.get_tx_result(_call)
    #     print(response)
    #
    def test_TestCollateral(self):
        data = "{\"method\": \"_deposit_and_borrow\", \"params\": {\"_asset\": \"sICX\", \"_amount\": 200000000000000000}}".encode("utf-8")
        params = {'_to': self.contracts['loans'], '_data': data}
        transaction = CallTransactionBuilder() \
            .from_(self._test2.get_address()) \
            .to(self.contracts['staking']) \
            .value(10 * ICX) \
            .step_limit(10000000) \
            .nid(80) \
            .nonce(100) \
            .method("addCollateral") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test2)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print(_tx_result)
        print('test account collateral added')

    def test_getAccountPositions(self):
        params = {'_owner': self._test2.get_address()}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']) \
            .method('getAccountPositions') \
            .params(params) \
            .build()
        result = self.icon_service.call(_call)
        print(result)

