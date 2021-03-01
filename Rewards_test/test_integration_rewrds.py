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

        self.wallets = [self._test1, self._test2, self._test3, self._test4, self._test5, self._test6]

        # wallet = KeyWallet.create()
        # print("address: ", wallet.get_address())  # Returns an address
        # print("private key: ", wallet.get_private_key())

        # with open('/home/sudeep/contracts-private/contracts_20210209104106.pkl', 'rb') as f:
        #     self.contracts = pickle.load(f)
        # print(self.contracts)

        # deploy SCORE
        # for address in DEPLOY:
        #     self.SCORE_PROJECT = self.SCORES + "/" + address
        #     print('Deploying ' + address + ' Contract in Testnet')
        #     self.contracts[address] = self._deploy_score()['scoreAddress']

        self.contracts = {'loans': {'zip': 'core_contracts/loans.zip',
                                    'SCORE': 'cx3c3fe6eeb1f69601edaf2de000ae1bff62f3dace'},
                          'staking': {'zip': 'core_contracts/staking.zip',
                                      'SCORE': 'cxdc140c1d6a4ba79037b76adff8b94970cdde2f25'},
                          'dividends': {'zip': 'core_contracts/dividends.zip',
                                        'SCORE': 'cx354c0ce44e543ebce9478bf0de3621c95473fc90'},
                          'reserve': {'zip': 'core_contracts/reserve.zip',
                                           'SCORE': 'cx0a478572e443bbfd66a35d124f63a2db9b637483'},
                          'rewards': {'zip': 'core_contracts/rewards.zip',
                                      'SCORE': 'cxe6074249f58898af2d6d00859ecb54e3f658ebe5'},
                          'dex': {'zip': 'core_contracts/dex.zip',
                                  'SCORE': 'cx4c73961fd85f13e822f72c2c96120c99e2e637d5'},
                          'governance': {'zip': 'core_contracts/governance.zip',
                                         'SCORE': 'cxeb7eb8d592ce76d0fcf1a3edd56b50ad2f1f72c5'},
                          'dummy_oracle': {'zip': 'core_contracts/dummy_oracle.zip',
                                           'SCORE': 'cx355d0e49525a681723ac0df9347189b5bb7814c8'},
                          'sicx': {'zip': 'token_contracts/sicx.zip',
                                   'SCORE': 'cxc60ef756b875786c9f820313ac4015e45726b47d'},
                          'icd': {'zip': 'token_contracts/icd.zip',
                                  'SCORE': 'cx14a00b375511d6bb1ad4e2c8eee41f4c8a167095'},
                          'bal': {'zip': 'token_contracts/bal.zip',
                                  'SCORE': 'cxbc2752abceba2bf179c1bfe0bc3f88caedcf2bd9'},
                          'bwt': {'zip': 'token_contracts/bwt.zip',
                                  'SCORE': 'cx0c6bb52e5e34ad8848de911be8ae52be38992363'}}

        # self.transferICX()
        # print(self.icon_service.get_balance(self._test2.get_address()) / 10 ** 18)

        # self._getAccountPositions(self._test2.get_address())
        # self._updateStanding()
        # self._addCollateral("{\"method\": \"_deposit_and_borrow\", \"params\": {\"_sender\": \"".encode("utf-8"),
        #                     "\", \"_asset\": \"ICD\", \"_amount\": 20000000000000000000}}".encode("utf-8"))

        # self._getAccountPositions(self._test2.get_address())
        # self._updateStanding()
        self._getBalnHoldings()
        self.getSnapshot()
        # self._claimRewards()
        self.getPositionByIndex()
        # self._getBalnHoldings()
        self._availableBalanceOf()
        # self._balanceOf()

        # self._recipient()
        # self._addNewDataSource()
        # self._getDataSources()

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
            .to(self._test6.get_address()) \
            .value(8000 * ICX) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        print("txHash: ", tx_hash)
        print("ICX transferred")

    # Adds collateral to the wallets
    def _addCollateral(self, data1: bytes, data2: bytes):
        for i in range(0, 6):
            params = {'_data1': data1, '_data2': data2}
            transaction = CallTransactionBuilder() \
                .from_(self.wallets[i].get_address()) \
                .to(self.contracts['loans']['SCORE']) \
                .value(500 * ICX) \
                .step_limit(10000000) \
                .nid(3) \
                .nonce(100) \
                .method("addCollateral") \
                .params(params) \
                .build()
            signed_transaction = SignedTransaction(transaction, self.wallets[i])
            tx_hash = self.icon_service.send_transaction(signed_transaction)
            _tx_result = self._get_tx_result(tx_hash)
            print(_tx_result)
            self.assertEqual(1, _tx_result['status'])
            print('added collateral')

    # Updates the position of the wallet
    def _updateStanding(self):
        for i in range(0, 6):
            params = {"_owner": self.wallets[i].get_address()}
            transaction = CallTransactionBuilder() \
                .from_(self.wallets[i].get_address()) \
                .to(self.contracts['loans']['SCORE']) \
                .value(0) \
                .step_limit(10000000) \
                .nid(3) \
                .nonce(100) \
                .method("updateStanding") \
                .params(params) \
                .build()
            signed_transaction = SignedTransaction(transaction, self.wallets[i])
            tx_hash = self.icon_service.send_transaction(signed_transaction)
            _tx_result = self._get_tx_result(tx_hash)
            print("updateStanding called")
            print(_tx_result)

    # Returns the BAL holding of the account
    def _getBalnHoldings(self):
        addresses = [wallet.get_address() for wallet in self.wallets]
        params = {'_holders': addresses}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['rewards']['SCORE']) \
            .method('getBalnHoldings') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("BAL holdings")
        print(result)

    # Claims the rewards of the called wallets and transfers the BAL to each addresses
    def _claimRewards(self):
        for i in range(0, 6):
            params = {}
            transaction = CallTransactionBuilder() \
                .from_(self.wallets[i].get_address()) \
                .to(self.contracts['rewards']['SCORE']) \
                .value(0) \
                .step_limit(10000000) \
                .nid(3) \
                .nonce(100) \
                .method("claimRewards") \
                .params(params) \
                .build()
            signed_transaction = SignedTransaction(transaction, self.wallets[i])
            tx_hash = self.icon_service.send_transaction(signed_transaction)
            _tx_result = self._get_tx_result(tx_hash)
            print("claiming rewards")
            print(_tx_result)

    # Returns the available BAL of the wallet
    def _availableBalanceOf(self):
        balances = {}
        for wallet in self.wallets[0: 6]:
            address = wallet.get_address()
            params = {'_owner': address}
            _call = CallBuilder().from_(address) \
                .to(self.contracts['bal']['SCORE']) \
                .method('availableBalanceOf') \
                .params(params) \
                .build()
            result = self.get_tx_result(_call)
            balances[address] = result
        print("Available BAL balance")
        print(balances)

    # Returns sicx balance of the wallet
    def _balanceOf(self):
        balances = {}
        for wallet in self.wallets[0: 6]:
            address = wallet.get_address()
            params = {'_owner': address}
            _call = CallBuilder().from_(address) \
                .to(self.contracts['sicx']['SCORE']) \
                .method('balanceOf') \
                .params(params) \
                .build()
            result = self.get_tx_result(_call)
            balances[address] = result
        print("Available sicx balance")
        print(balances)

    # Returns the snapshot of the provided snap id
    def getSnapshot(self):
        params = {'_snap_id': 9}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .method('getSnapshot') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("snapshot")
        print(result)

    # Calling account position by providing index and day
    def getPositionByIndex(self):
        params = {'_index': 154, "_day": 9}
        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['loans']['SCORE']) \
            .method('getPositionByIndex') \
            .params(params) \
            .build()
        result = self.get_tx_result(_call)
        print("Position index")
        print(result)

    # Returns the account position of the wallet
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

    # def _recipient(self):
    #     params = {}
    #     _call = CallBuilder().from_(self._test1.get_address()) \
    #         .to(self.contracts['rewards']['SCORE']) \
    #         .method('getRecipients') \
    #         .params(params) \
    #         .build()
    #     result = self.get_tx_result(_call)
    #     print("recipients ")
    #     print(result)
    #

    # def _addNewDataSource(self):
    #     params = {"_data_source_name": "user3 ", "_contract_address": "cx141a43c16a0bd307c26cbd561434de82e60cd2e3"}
    #     transaction = CallTransactionBuilder() \
    #         .from_(self._test1.get_address()) \
    #         .to(self.contracts['rewards']['SCORE']) \
    #         .value(0) \
    #         .step_limit(10000000) \
    #         .nid(3) \
    #         .nonce(100) \
    #         .method("addNewDataSource") \
    #         .params(params) \
    #         .build()
    #     signed_transaction = SignedTransaction(transaction, self._test1)
    #     tx_hash = self.icon_service.send_transaction(signed_transaction)
    #     _tx_result = self._get_tx_result(tx_hash)
    #     print("adding source")
    #     print(_tx_result)

    # def _dataSourceName(self):
    #     params = {}
    #     _call = CallBuilder().from_(self._test1.get_address()) \
    #         .to(self.contracts['rewards']['SCORE']) \
    #         .method('getDataSourceNames') \
    #         .params(params) \
    #         .build()
    #     result = self.get_tx_result(_call)
    #     print("sources")
    #     print(result)

    # def _getDataSources(self):
    #     params = {"_data_source_name": "Loans"}
    #     _call = CallBuilder().from_(self._test1.get_address()) \
    #         .to(self.contracts['rewards']['SCORE']) \
    #         .method('getDataSources') \
    #         .params(params) \
    #         .build()
    #     result = self.get_tx_result(_call)
    #     print("data sources")
    #     print(result)

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
