import os

from iconsdk.builder.transaction_builder import DeployTransactionBuilder
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.icon_service import IconService
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS
from iconsdk.exception import JSONRPCException
import json

from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.utils.convert_type import convert_hex_str_to_int
import time
from .repeater import retry

DIR_PATH = os.path.abspath(os.path.dirname(__file__))
DEPLOY = ['sicx','staking']

folder_path = {'sicx':'token_contracts','staking':'core_contracts'}

class TestTest(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "https://zicon.net.solidwallet.io/api/v3"
    SCORES = os.path.abspath(os.path.join(DIR_PATH, '..'))

    def setUp(self):
        super().setUp()
        self.contracts = {}
        self.test_account2 = KeyWallet.create()
        # WARNING: ICON service emulation is not working with IISS.
        # You can stake and delegate but can't get any I-Score for reward.
        # If you want to test IISS stuff correctly, set self.icon_service and send requests to the network
        # self.icon_service = None

        self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))
        # If you want to send requests to the network, un   comment next line and set self.TEST_HTTP_ENDPOINT_URI_V3
        # # install SCORE
        # self._score_address = self._deploy_score()['scoreAddress']

        # Deploy SCORE
        for address in DEPLOY:
            self.SCORE_PROJECT = self.SCORES + "/" + folder_path[address] + "/" + address
            print(self.SCORE_PROJECT)
            self.contracts[address] = self._deploy_score()['scoreAddress']
        self._setVariablesAndInterface()


    #Process the transaction in pagoda testnet
    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def _get_tx_result(self,_tx_hash):
        tx_result = self.icon_service.get_transaction_result(_tx_hash)
        return tx_result

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(self,_call):
        tx_result = self.icon_service.call(_call)
        return tx_result    

    def _setVariablesAndInterface(self):
        print('starting set variables and interface')
        settings = [{'contract': 'staking', 'method': 'set_sICX_address',
                     'params': {'_address': self.contracts['sicx']}},
                    {'contract': 'sicx', 'method': 'setAdmin',
                     'params': {'_admin': self.contracts['staking']}}]
        for sett in settings:
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

            _tx_result= self._get_tx_result(tx_hash)

            self.assertTrue('status' in _tx_result)
            self.assertEqual(1, _tx_result['status'])


    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS, _type: str = 'install') -> dict:
        print(SCORE_INSTALL_ADDRESS)
        params = {}
        # Generates an instance of transaction for deploying SCORE.
        transaction = DeployTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(to) \
            .step_limit(100_000_000_000) \
            .nid(80) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(self.SCORE_PROJECT)) \
            .params(params) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)
        # process the transaction
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result= self._get_tx_result(tx_hash)
        print(_tx_result)
        # checks Transaction result
        self.assertEqual(True, _tx_result['status'])
        self.assertTrue('scoreAddress' in _tx_result)
        return _tx_result

    # def test_score_update(self):
    #     print('Testing Score Update')
    #     # update SCORE
    #     for address in DEPLOY:
    #         self.SCORE_PROJECT = self.SCORES + "/" + address
    #         SCORE_PROJECT = os.path.abspath(
    #             os.path.join(DIR_PATH, '..')) + "/" + address
    #         tx_result = self._deploy_score(self.contracts[address], 'update')
    #         self.assertEqual(
    #             self.contracts[address], tx_result['scoreAddress'])

    def test_get_sICX_address(self):
        print('get sICX address')
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['staking']) \
            .method("get_sICX_address") \
            .build()

        response = self.get_tx_result(_call)
        # check call result
        print (response)
        self.assertEqual(self.contracts['sicx'], response)
