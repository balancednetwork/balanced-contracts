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
from repeater import retry

ICX = 1000000000000000000
DIR_PATH = os.path.abspath(os.path.dirname(__file__))
DEPLOY = ['loans', 'reserve_fund', 'dividends', 'dummy_oracle', 'staking', 'rewards', 'dex', 'governance']
# DEPLOY = ['loans', 'staking']
TOKEN = ['bal', 'bwt', 'icd', 'sicx']
UPDATE = ['loans']


class TestLoan(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://18.144.108.38:9000/api/v3"
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
        print(self.icon_service.get_balance(self._test1.get_address())/10**18)

        # test3 =  hx3d7ca00231a5ce61c6b33beae3eb492a647e8c11
        private_key3 = "329bbab70843831b870b0d27d0e53ad48bee0c09f86443451dc96b84c14f8abb"
        self._test3 = KeyWallet.load(bytes.fromhex(private_key3))

        # test4 = hx61d0e100c3c9e72f08de762ce42214a4bc3142e2
        private_key4 = "45d7d8ba320c68e231bb617a82f6c80b50ad3804cf029e167e764c9aa186ce82"
        self._test4 = KeyWallet.load(bytes.fromhex(private_key4))

        # test5 = hx7a8c328bc394fc423197f7b82a264a4d835bfec7
        private_key5 = "bf76b5c647348e60762cb0c6eb9ddaff6fe17f04a38166e9fbbbbafed38a4646"
        self._test5 = KeyWallet.load(bytes.fromhex(private_key5))

        # test6 = hxdee4f72386f7f337347d262319d85c19be40ea6b
        private_key6= "2c3b70deed76ba64a0376fa5cb1ea5f7afeddae4a2e38360a2bf8cee3b66f3ff"
        self._test6 = KeyWallet.load(bytes.fromhex(private_key6))

        # test7 = hx79741c762362268adc0ba58a073a10311b981149
        private_key7 = "551b108ce3cb9df598b24caec16849515c9a44f71a1307b28fd215a9b7dddd64"
        self._test7 = KeyWallet.load(bytes.fromhex(private_key7))

        # wallet = KeyWallet.create()
        # print("address: ", wallet.get_address())  # Returns an address
        # print("private key: ", wallet.get_private_key())

        # with open('/home/sudeep/contracts-private/contracts_20210209104106.pkl', 'rb') as f:
        #     self.contracts = pickle.load(f)
        # print(self.contracts)

        # deploy SCORE
        for address in DEPLOY:
            self.SCORE_PROJECT = self.SCORES + "/" + address
            print('Deploying ' + address + ' Contract in Testnet')
            self.contracts[address] = self._deploy_score()['scoreAddress']

        self.contracts = {'loans': {'zip': 'core_contracts/loans.zip',
                                    'SCORE': 'cx65e056cbf4617d55112782eba514cda419eb3e58'},
                          'staking': {'zip': 'core_contracts/staking.zip',
                                      'SCORE': 'cx2f9d704a86284462b9064a36ccacd14de11632fc'},
                          'dividends': {'zip': 'core_contracts/dividends.zip',
                                        'SCORE': 'cxb5b8908f2a11f90e06aa118cb7d9ff37686516c5'},
                          'reserve': {'zip': 'core_contracts/reserve.zip',
                                           'SCORE': 'cxc711aab3c50a1705e7d788e103fe0c595ff78360'},
                          'rewards': {'zip': 'core_contracts/rewards.zip',
                                      'SCORE': 'cxe84729d4626afbb75e362bcd30f2cf294f7b2409'},
                          'dex': {'zip': 'core_contracts/dex.zip',
                                  'SCORE': 'cx141a43c16a0bd307c26cbd561434de82e60cd2e3'},
                          'governance': {'zip': 'core_contracts/governance.zip',
                                         'SCORE': 'cx91a97ef597e387b0b42bc313724b57563c9a81a5'},
                          'dummy_oracle': {'zip': 'core_contracts/dummy_oracle.zip',
                                           'SCORE': 'cx7a11d2be1c04e2bdd40f2a327afd2d3d3cce9790'},
                          'sicx': {'zip': 'token_contracts/sicx.zip',
                                   'SCORE': 'cx36572eea4f88e3a467cd33ef0c3c4728bbdda2b9'},
                          'icd': {'zip': 'token_contracts/icd.zip',
                                  'SCORE': 'cx488460c8e76a796c1726f0dea63dfde71e165812'},
                          'bal': {'zip': 'token_contracts/bal.zip',
                                  'SCORE': 'cx5aef1c11efc99ff5dd318469d191f4f5ef731fb4'},
                          'bwt': {'zip': 'token_contracts/bwt.zip',
                                  'SCORE': 'cx96e5aeb61049d39a26549248b7e5666c47cb07f0'}}

        # self.transferICX()
        print(self.icon_service.get_balance(self._test2.get_address()) / 10 ** 18)
        # self._getAccountPositions(self._test1.get_address())
        # self._updateStanding()
        # self._addCollateral("{\"method\": \"_deposit_and_borrow\", \"params\": {\"_sender\": \"".encode("utf-8"),
        #                     "\", \"_asset\": \"ICD\", \"_amount\": 40000000000000000000}}".encode("utf-8"))
        # self._getAccountPositions(self._test2.get_address())

        # print(self.icon_service.get_balance(self._test5.get_address()) / 10 ** 18)
        self._recipient()
        # self._updateStanding()
        self._getBalnHoldings()
        self._getDataBatch()
        self._distribute()
        # self._claimRewards()
        # self._getBalnHoldings()
        self._availableBalanceOf()
        # self._stakedBalanceOf()
        # self._addNewDataSource()
        self._dataSourceName()
        self._getDataSources()

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def _get_tx_result(self, _tx_hash):
        tx_result = self.icon_service.get_transaction_result(_tx_hash)
        return tx_result

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(self, _call):
        tx_result = self.icon_service.call(_call)
        return tx_result

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
            .value(2000 * ICX) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        print("txHash: ", tx_hash)
        print("ICX transferred")

    def _addCollateral(self, data1: bytes, data2: bytes):
        params = {'_data1': data1, '_data2': data2}
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .value(800 * ICX) \
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

    def _getAccountPositions(self, to):
        params = {'_owner': to}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .method('getAccountPositions') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("position")
        print(result)

    def _recipient(self):
        params = {}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['rewards']['SCORE']) \
            .method('getRecipients') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("recipients ")
        print(result)

    def _claimRewards(self):
        params = {}
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['rewards']['SCORE']) \
            .value(0) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("claimRewards") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print("claiming rewards")
        print(_tx_result)

    def _availableBalanceOf(self):
        params = {'_owner': self._test1.get_address()}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['bal']['SCORE']) \
            .method('availableBalanceOf') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("BAL Called")
        print(result)

    def _stakedBalanceOf(self):
        params = {'_owner': self._test1.get_address()}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['bal']['SCORE']) \
            .method('stakedBalanceOf') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("BAL Called")
        print(result)

    def _getBalnHoldings(self):
        params = {'_holders': [self._test1.get_address(), self._test2.get_address()]}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['rewards']['SCORE']) \
            .method('getBalnHoldings') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("BAL holder Called")
        print(result)

    def _addNewDataSource(self):
        params = {"_data_source_name": "user3 ", "_contract_address": "cx141a43c16a0bd307c26cbd561434de82e60cd2e3"}
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['rewards']['SCORE']) \
            .value(0) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("addNewDataSource") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print("adding source")
        print(_tx_result)

    def _dataSourceName(self):
        params = {}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['rewards']['SCORE']) \
            .method('getDataSourceNames') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("sources")
        print(result)

    def _getDataSources(self):
        params = {"_data_source_name": "Loans"}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['rewards']['SCORE']) \
            .method('getDataSources') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("data sources")
        print(result)

    def _distribute(self):
        params = {}
        transaction = CallTransactionBuilder() \
            .from_(self._test2.get_address()) \
            .to(self.contracts['rewards']['SCORE']) \
            .value(0) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("distribute") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test2)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print("updateBalTokenDistPercentage called")
        print(_tx_result)

    def _updateStanding(self):
        params = {"_owner": self._test1.get_address()}
        transaction = CallTransactionBuilder() \
            .from_(self._test3.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .value(0) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("updateStanding") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test3)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result = self._get_tx_result(tx_hash)
        print("updateStanding called")
        print(_tx_result)

    def _getDataBatch(self):
        params = {"_name": "Loans", "_snapshot_id": 12, "_limit": 10, "_offset":0}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .method('getDataBatch') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("data batch")
        print(result)

    def test_call_name(self):
        # Generates a call instance using the CallBuilder
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['rewards']['SCORE']) \
            .method("name") \
            .build()

        # Sends the call request
        response = self.get_tx_result(_call)
        # check call result
        self.assertEqual("Rewards", response)
        print("okk")
