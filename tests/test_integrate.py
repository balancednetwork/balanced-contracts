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





class TestTest(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "https://zicon.net.solidwallet.io/api/v3"
    SCORES = os.path.abspath(os.path.join(DIR_PATH, '..'))

    def setUp(self):
        super().setUp()
        self.contracts = {}
        # WARNING: ICON service emulation is not working with IISS.
        # You can stake and delegate but can't get any I-Score for reward.
        # If you want to test IISS stuff correctly, set self.icon_service and send requests to the network
        # self.icon_service = None

        self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))
        # If you want to send requests to the network, un   comment next line and set self.TEST_HTTP_ENDPOINT_URI_V3
        # # install SCORE
        # self._score_address = self._deploy_score()['scoreAddress']

        # Deploy SCORE
        for  x in range(3):
            for address in DEPLOY:
                self.SCORE_PROJECT = self.SCORES + "/" + address
                sNo = address + str(x+1)
                print(self.SCORE_PROJECT)
                print('======================================================================')
                print('Deploying '+ sNo + ' Contract in Testnet')
                print('----------------------------------------------------------------------')
                self.contracts[sNo] = self._deploy_score()['scoreAddress']
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
        print('======================================================================')
        print('Set Variable and Interface')
        print('----------------------------------------------------------------------')

        for x in range(3):
            a=x+1
            b = 'staking'+str(a)
            c = 'sicx'+str(a)
            print(b)
            settings = [{'contract': b, 'method': 'setSicxAddress',
                         'params': {'_address': self.contracts[c]}},
                        {'contract': c, 'method': 'setAdmin',
                         'params': {'_admin': self.contracts[b]}}]
            print('Hello')
            for sett in settings:
                print('----------------------------------------------------------------------')
                print(sett['method']+' For '+ b)
                print('----------------------------------------------------------------------')

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
    #     # update SCORE
    #     for address in DEPLOY:
    #         print('======================================================================')
    #         print('Test Score Update('+address+')')
    #         print('----------------------------------------------------------------------')
    #         self.SCORE_PROJECT = self.SCORES + "/" + address
    #         SCORE_PROJECT = os.path.abspath(
    #             os.path.join(DIR_PATH, '..')) + "/" + address
    #         tx_result = self._deploy_score(self.contracts[address], 'update')
    #         self.assertEqual(
    #             self.contracts[address], tx_result['scoreAddress'])

    def test_get_sICX_address(self):
        print('======================================================================')
        print('Test Get sICX Address')
        print('----------------------------------------------------------------------')

        _call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['staking']) \
            .method("getSicxAddress") \
            .build()

        response = self.get_tx_result(_call)
        # check call result
        print (response)
        self.assertEqual(self.contracts['sicx'], response)


    def test_add_collateral(self):
        print('======================================================================')
        print('Test Add Collateral')
        print('----------------------------------------------------------------------')
        settings = [{'name': 'Test Case 1.1', 'wAddress':'staking1', 'params' : {'_to': self._test1.get_address(),'_user_delegations':[{'_address': 'hx95248f3757afcb50efa99f529183ba401a82273c',  '_votes_in_per' : "50"},
                                                                    {'_address': 'hxc89dfd4bf903b39ca98db905443ca9020f955e8c',  '_votes_in_per' : "100"}]}},
                    {'name': 'Test Case 1.2', 'wAddress':'staking1', 'params' : {'_to': self._test1.get_address(),'_user_delegations':[{'_address': 'hx95248f3757afcb50efa99f529183ba401a82273c',  '_votes_in_per' : "50"},
                                                                    {'_address': 'hxc89dfd4bf903b39ca98db905443ca9020f955e8c',  '_votes_in_per' : "100"}]}},
                    {'name': 'Test Case 1.3', 'wAddress':'staking1', 'params' : {'_to': self._test1.get_address(),'_user_delegations':[{'_address': 'hx4917005bf4b8188b9591da520fc1c6dab8fe717f',  '_votes_in_per' : "50"},
                                                                    {'_address': 'hx7cc2bb9d84ff3b5843f83d07818ebcff31be29e5',  '_votes_in_per' : "50"}]}},
                    {'name': 'Test Case 1.4', 'wAddress':'staking1', 'params' : {'_to': self._test1.get_address(),'_user_delegations':[{'_address': 'hx9a24e7a53e031ab6aa7b831b1dbe4200bd3f9483',  '_votes_in_per' : "50"},
                                                                    {'_address': 'hx8573a132f3df5c34a292fc16cb33737ffe10b367',  '_votes_in_per' : "50"}]}},
                    {'name': 'Test Case 1.5', 'wAddress':'staking1', 'params' : {'_to': self._test1.get_address(),'_user_delegations':[{'_address': 'hx91de10325dd4b9a104c94ebc2ad9ceca279da8b6',  '_votes_in_per' : "50"},
                                                                    {'_address': 'hx8573a132f3df5c34a292fc16cb33737ffe10b367',  '_votes_in_per' : "50"}]}},
                    {'name': 'Test Case 1.6', 'wAddress':'staking1', 'params' : {'_to': self._test1.get_address()}},
                    {'name': 'Test Case 2.1', 'wAddress':'staking2', 'params' : {'_to': self._test1.get_address()}},
                    {'name': 'Test Case 2.2', 'wAddress':'staking2', 'params' : {'_to': self._test1.get_address(),'_user_delegations':[{'_address': 'hx9a24e7a53e031ab6aa7b831b1dbe4200bd3f9483',  '_votes_in_per' : "50"},
                                                                    {'_address': 'hx8573a132f3df5c34a292fc16cb33737ffe10b367',  '_votes_in_per' : "50"}]}},
                    {'name': 'Test Case 2.3', 'wAddress':'staking2', 'params' : {'_to': self._test1.get_address(),'_user_delegations':[{'_address': 'hx9a24e7a53e031ab6aa7b831b1dbe4200bd3f9483',  '_votes_in_per' : "50"},
                                                                    {'_address': 'hx8573a132f3df5c34a292fc16cb33737ffe10b367',  '_votes_in_per' : "50"}]}},
                    {'name': 'Test Case 2.4', 'wAddress':'staking2', 'params' : {'_to': self._test1.get_address()}}
                    ]                                                
        
        for sett in settings:
            print('======================================================================')
            print(sett['name'])
            print('----------------------------------------------------------------------')
            
            transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts[sett['wAddress']]) \
            .value (10 * 10 ** 18) \
            .step_limit(10000000) \
            .nid(80) \
            .nonce(100) \
            .method('addCollateral') \
            .params(sett['params']) \
            .build()

            # Returns the signed transaction object having a signature
            signed_transaction = SignedTransaction(transaction, self._test1)

            # process the transaction in zicon
            tx_hash = self.icon_service.send_transaction(signed_transaction)
            _tx_result= self._get_tx_result(tx_hash)
             #check Transaction result
            print (_tx_result)
            if sett['name'] == 'Test Case 1.1' or sett['name'] == 'Test Case 1.2' or sett['name'] == 'Test Case 1.5':
                self.assertEqual(_tx_result,_tx_result)
            else:
                self.assertTrue('status' in _tx_result)
                self.assertEqual(True, _tx_result['status'])

                delegation_call = CallBuilder().from_(self._test1.get_address()) \
                    .to(self.contracts[sett['wAddress']]) \
                    .method("getPrepDelegations") \
                    .build()
        
                contract_delegation_call = CallBuilder().from_(self._test1.get_address()) \
                    .to(self.contracts[sett['wAddress']]) \
                    .method("getDelegationFromNetwork") \
                    .build()
                response_delegation = self.get_tx_result(delegation_call)
                response_delegation_contract = self.get_tx_result(contract_delegation_call)
                print('----------------------------------------------------------------------')
                print('Delegation List')
                print('----------------------------------------------------------------------')
                print (response_delegation)
                print('----------------------------------------------------------------------')
                print('Delegation List from Network')
                print('----------------------------------------------------------------------')
                delegation_from_contract = {}
                #Iterating through contract delegations
                for i in response_delegation_contract["delegations"]:
                    delegation_from_contract[i['address']] = i['value']
                print(delegation_from_contract)

                # check call result
                # if sett['name'] == 'Test Case 1.3':
                #     self.assertEqual(response_delegation,delegation_from_contract)
                
    def test_update_delegation(self):
        print('======================================================================')
        print(' *******************Test Update Delegations***************************')
        print('----------------------------------------------------------------------')
        settings = [{'name': 'Test Case 1.1', 'wAddress':'staking3', 'params' : {'_user_delegations':[{'_address': 'hxc5772df538f620e1f61ef2cc3cddcea9d6ff5063',  '_votes_in_per' : "50"},
                                                                  {'_address': 'hx7ce8e9c5e1ee02c6167b99b5bb4d00bdf63d0a30',  '_votes_in_per' : "50"}]}},
                    {'name': 'Test Case 2.1', 'wAddress':'staking1', "params" : {'_user_delegations':[{'_address': 'hxc5772df538f620e1f61ef2cc3cddcea9d6ff5063',  '_votes_in_per' : "5"},{'_address': 'hx7ce8e9c5e1ee02c6167b99b5bb4d00bdf63d0a30',  '_votes_in_per' : "10"},
                                                                  {'_address': 'hxbdc3baae0632fad453d62130d3379900a323f5b4',  '_votes_in_per' : "15"}]}},
                    {'name': 'Test Case 2.2', 'wAddress':'staking1', 'params' : {'_user_delegations':[{'_address': 'hx95248f3757afcb50efa99f529183ba401a82273c',  '_votes_in_per' : "50"},{'_address': 'hx95248f3757afcb50efa99f529183ba401a82273c',  '_votes_in_per' : "50"}, 
                                                                  {'_address': 'hxc89dfd4bf903b39ca98db905443ca9020f955e8c',  '_votes_in_per' : "50"}]}},
                    {'name': 'Test Case 2.3', 'wAddress':'staking1', 'params' : {}},
                    {'name': 'Test Case 2.4', 'wAddress':'staking1', 'params' : {'_user_delegations':[{'_address': 'hx4917005bf4b8188b9591da520fc1c6dab8fe717f',  '_votes_in_per' : "50"},
                                                                  {'_address': 'hx9a24e7a53e031ab6aa7b831b1dbe4200bd3f9483',  '_votes_in_per' : "50"}]}},
                    {'name': 'Test Case 2.5', 'wAddress':'staking1', 'params' : {'_user_delegations':[{'_address': 'hx8573a132f3df5c34a292fc16cb33737ffe10b367',  '_votes_in_per' : "40"},{'_address': 'hx6bd3a3b1390e99194ced786725e0f0725fc1960b',  '_votes_in_per' : "15"},
                                                                  {'_address': 'hx7cc2bb9d84ff3b5843f83d07818ebcff31be29e5',  '_votes_in_per' : "45"}]}},
                    {'name': 'Test Case 2.6', 'wAddress':'staking1', 'params' : {'_user_delegations':[{'_address': 'hx23dfce82d36268f4cc3b943fa65d4c9632d23e76',  '_votes_in_per' : "100"}]}},                       
                    ]   
        for sett in settings:
            print('======================================================================')
            print(sett['name'])
            print('----------------------------------------------------------------------')
            
            call_transaction = CallTransactionBuilder() \
                .from_(self._test1.get_address()) \
                .to(self.contracts[sett['wAddress']]) \
                .nid(80) \
                .step_limit(10000000) \
                .nonce(100) \
                .method('updateDelegations') \
                .params(sett['params']) \
                .build()
            # Returns the signed transaction object having a signature
            signed_transaction = SignedTransaction(call_transaction, self._test1)
            # process the transaction in zicon
            tx_hash = self.icon_service.send_transaction(signed_transaction)
            _tx_result= self._get_tx_result(tx_hash)
             #check Transaction result
            print (_tx_result)
            if sett['name'] == 'Test Case 1.1' or sett['name'] == 'Test Case 2.1' or sett['name'] == 'Test Case 2.2' or sett['name'] == 'Test Case 2.3':
                self.assertEqual(_tx_result,_tx_result)
            else:
                self.assertTrue('status' in _tx_result)
                self.assertEqual(True, _tx_result['status'])
                delegation_call = CallBuilder().from_(self._test1.get_address()) \
                    .to(self.contracts[sett['wAddress']]) \
                    .method("getPrepDelegations") \
                    .build()
        
                contract_delegation_call = CallBuilder().from_(self._test1.get_address()) \
                    .to(self.contracts[sett['wAddress']]) \
                    .method("getDelegationFromNetwork") \
                    .build()
                response_delegation = self.get_tx_result(delegation_call)
                response_delegation_contract = self.get_tx_result(contract_delegation_call)
                print('----------------------------------------------------------------------')
                print('Delegation List')
                print('----------------------------------------------------------------------')
                print (response_delegation)
                print('----------------------------------------------------------------------')
                print('Delegation List from Network')
                print('----------------------------------------------------------------------')
                delegation_from_contract = {}
                #Iterating through contract delegations
                for i in response_delegation_contract["delegations"]:
                    delegation_from_contract[i['address']] = i['value']
                print(delegation_from_contract)
    
    def test_wclaim_iscore(self):
        print('======================================================================')
        print(' **********************Test Claim IScore*****************************')
        print('----------------------------------------------------------------------')

        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['staking1']) \
            .step_limit(10000000) \
            .nid(80) \
            .nonce(100) \
            .method('_claim_iscore') \
            .build()
        # # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        # # process the transaction in zicon
        tx_hash = self.icon_service.send_transaction(signed_transaction)
        _tx_result= self._get_tx_result(tx_hash)
        print (_tx_result)
        # #check Transaction result
        self.assertTrue('status' in _tx_result)
        self.assertEqual(True, _tx_result['status'])

        delegation_call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['staking1']) \
            .method("getPrepDelegations") \
            .build()
        
        contract_delegation_call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['staking1']) \
            .method("getDelegationFromNetwork") \
            .build()
        response_delegation = self.get_tx_result(delegation_call)
        response_delegation_contract = self.get_tx_result(contract_delegation_call)

        print('----------------------------------------------------------------------')
        print('Delegation List')
        print('----------------------------------------------------------------------')
        print (response_delegation)
        print('----------------------------------------------------------------------')
        print('Delegation List from Network')
        print('----------------------------------------------------------------------')
        delegation_from_contract = {}
        #Iterating through contract delegations
        for i in response_delegation_contract["delegations"]:
            delegation_from_contract[i['address']] = i['value']
        print(delegation_from_contract)
        # check call result
        for i in list(delegation_from_contract.keys()):
            self.assertTrue(i in list(response_delegation.keys()))
