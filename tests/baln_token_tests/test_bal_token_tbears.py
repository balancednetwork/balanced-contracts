from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconservice import Address

import json
import os
import time

from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

DIR_PATH = os.path.abspath(os.path.dirname(__file__))
CORE_CONTRACTS_PATH = os.path.abspath(os.path.join(DIR_PATH, "../../core_contracts"))
TOKEN_CONTRACTS_PATH = os.path.abspath(os.path.join(DIR_PATH, "../../token_contracts"))

CORE_CONTRACTS = ["governance", "dex"]
TOKEN_CONTRACTS = ["baln"]
CONTRACTS = CORE_CONTRACTS + TOKEN_CONTRACTS

print(DIR_PATH)
test_file_name = "minting_staking_cases.json"


def read_file_data(filename, path):
    os.chdir(path)
    with open(filename, encoding="utf8") as data_file:
        json_data = json.load(data_file)
    return json_data


test_cases = read_file_data(test_file_name, DIR_PATH)
stories = test_cases['stories']
print('======================================================================')
print("Test Case: " + test_cases['title'])
print('======================================================================')


class TestScoreTest(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://18.144.108.38:9000/api/v3"

    # TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"

    def setUp(self):
        super().setUp()

        self.contracts = {}

        # self.icon_service = None
        self.test_account2 = KeyWallet.create()
        self._governance = self.test_account2.get_address()
        # If you want to send request to network, uncomment next line and set self.TEST_HTTP_ENDPOINT_URI_V3
        self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))

        # REQUIRED VARIABLES
        self._oracle_name = ""
        self._admin = ""

        # Deploy SCORE
        for num, value in enumerate(CONTRACTS):
            if value != 'baln':
                self.SCORE_PROJECT = CORE_CONTRACTS_PATH
                params = {}
                if value == 'dex':
                    params = {'_governance': self.contracts['governance']}
            else:
                self.SCORE_PROJECT = TOKEN_CONTRACTS_PATH
                params = {'_governance': self.contracts['governance']}
            self.SCORE_PROJECT = self.SCORE_PROJECT + "/" + value
            print('======================================================================')
            print(f"Deploying {value} Contract in Testnet")
            self.contracts[value] = self._deploy_score(params)['scoreAddress']
        self._setVariablesAndInterfaces()

    def _deploy_score(self, params: dict, to: str = SCORE_INSTALL_ADDRESS) -> dict:
        # Generates an instance of transaction for deploying SCORE.
        transaction = DeployTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(to) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .nonce(100) \
            .params(params) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(self.SCORE_PROJECT)) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)
        # process the transaction in local
        tx_result = self.process_transaction(signed_transaction)

        # print(tx_result)

        # check transaction result
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)

        print(f"SCORE Deployed: {tx_result['scoreAddress']} ")
        print('======================================================================')

        return tx_result

    def _setVariablesAndInterfaces(self):
        U_SECONDS_DAY = 86400 * 10 ** 6  # Microseconds in a day.
        DAY_ZERO = 18647
        DAY_START = 61200 * 10 ** 6  # 17:00 UTC
        offset = DAY_ZERO + 0
        day = (int(time.time()) * 10 ** 6 - DAY_START) // U_SECONDS_DAY - offset
        time_delta = DAY_START + U_SECONDS_DAY * (DAY_ZERO + day - 1)

        settings = [{'contract': 'dex', 'method': 'setTimeOffset',
                     'params': {'_delta_time': time_delta}},
                    {'contract': 'baln', 'method': 'setGovernance',
                     'params': {'_address': self._test1.get_address()}},
                    {'contract': 'baln', 'method': 'setAdmin',
                     'params': {'_admin': self._test1.get_address()}},
                    {'contract': 'baln', 'method': 'setDex',
                     'params': {"_address": self.contracts['dex']}},
                    {'contract': 'baln', 'method': 'setTimeOffset',
                     'params': {}},
                    {'contract': 'baln', 'method': 'toggleStakingEnabled',
                     'params': {}}]

        for sett in settings:
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
            tx_result = self.process_transaction(signed_transaction)
            self.assertTrue('status' in tx_result)
            self.assertEqual(1, tx_result['status'])

    def _mint_stake(self):
        for _cases in stories:
            _actions = _cases['actions']
            method_name = _actions['name']
            _address = self._test1.get_address()
            if method_name == 'mint':
                print("Title: " + _cases['description'])
                _amount = int(_actions['mint_token'])

                params = _actions['params']
                tx_hash = self._call_transaction_builder(method_name, params)

                self.assertEqual(1, tx_hash['status'])
                print(f"Expected Value: {_actions['expected_available_balance']} --> Added Value: "
                      f"{int(self._availableBalanceOf(_address), 16)}")
                self.assertEqual(int(_actions['expected_available_balance']),
                                 int(self._availableBalanceOf(_address), 16))
                print(f"{_amount} Minted Successfully.")
                print('----------------------------------------------------------------------')

            if method_name == 'stake':
                print("Title: " + _cases['description'])
                _amount = int(_actions['stake_token'])
                params = _actions['params']

                tx_result = self._call_transaction_builder(method_name, params)

                self.assertEqual(1, tx_result['status'])
                self.assertTrue('status' in tx_result)
                _stakedBalance = self._balanceOf(self._test1.get_address())['Staked balance']
                _totalBalance = self._balanceOf(self._test1.get_address())['Total balance']
                _availableBalance = self._balanceOf(self._test1.get_address())['Available balance']
                print(f"Expected Total Value: {_actions['expected_total_balance']} --> Obtained Value: "
                      f"{_totalBalance}")
                print(f"Expected Available Value: {_actions['expected_available_balance']} --> Obtained Value: "
                      f"{_availableBalance}")
                print(f"Expected Staked Value: {_actions['expected_staked_balance']} --> Obtained Value: "
                      f"{_stakedBalance}")
                self.assertEqual(int(_actions['expected_staked_balance']), _stakedBalance)
                print(f"{_amount} Staked Successfully.")
                print('----------------------------------------------------------------------')

        print('------------- Testing User Stake Snapshot -----------------')
        self.assertEqual(self._stakedBalanceOfAt(self._test1.get_address(), self._getDay()), 1000000000000000000000)
        print('------------- Testing Total Stake Snapshot -----------------')
        self.assertEqual(self._totalStakedBalanceOfAt(self._getDay()), 1000000000000000000000)
        print('----------------------------------------------------------------------')

        self._loadBalnStakeSnapshot()
        self._loadTotalStakeSnapshot()

    def _transfer(self, _to, _value: int, _data: bytes = None):
        params = {"_to": _to, "_amount": _value, "_data": _data}
        prev_balance = int(self._availableBalanceOf(_to), 16) + _value
        sender_prev_balance = int(self._availableBalanceOf(self._test1.get_address()), 16) + _value

        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['baln']) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_hash = self.process_transaction(signed_transaction)

        self.assertEqual(1, tx_hash['status'])
        self.assertEqual(prev_balance, int(self._availableBalanceOf(_to), 16))
        self.assertEqual(sender_prev_balance, int(self._availableBalanceOf(_to), 16))

    def _availableBalanceOf(self, _account):
        params = {"_owner": _account}
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['baln']) \
            .method("availableBalanceOf") \
            .params(params) \
            .build()

        result = self.process_call(call)
        return result

    def _balanceOf(self, _account):
        params = {"_owner": _account}
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['baln']) \
            .method("detailsBalanceOf") \
            .params(params) \
            .build()

        result = self.process_call(call)
        return result

    def _getGovernance(self):
        params = {}
        call = CallBuilder().from_(self.test_account2.get_address()) \
            .to(self.contracts['baln']) \
            .method("getGovernance") \
            .params(params) \
            .build()

        result = self.process_call(call)
        return result

    def _getStakingEnabled(self):
        params = {}
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['baln']) \
            .method("getStakingEnabled") \
            .params(params) \
            .build()

        result = self.process_call(call)
        return result

    def _getDay(self):
        params = {}
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['baln']) \
            .method("getDay") \
            .params(params) \
            .build()

        result = self.process_call(call)
        print("DAY", int(result, 0))
        return int(result, 0)

    def _stakedBalanceOfAt(self, _address: str, _day: int):
        params = {'_account': _address, '_day': _day}
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['baln']) \
            .method("stakedBalanceOfAt") \
            .params(params) \
            .build()

        result = self.process_call(call)
        print(f"{_day}: ", _address, f" --> {int(result, 0)}")
        return int(result, 0)

    def _totalStakedBalanceOfAt(self, _day):
        params = {'_day': _day}
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self.contracts['baln']) \
            .method("totalStakedBalanceOfAt") \
            .params(params) \
            .build()

        result = self.process_call(call)
        print(_day, f"---> {int(result, 0)}")
        return int(result, 0)

    def _call_transaction_builder(self, _method_name: str, params):
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['baln']) \
            .value(0) \
            .step_limit(10000000) \
            .nid(3) \
            .nonce(100) \
            .method(_method_name) \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction)

        return tx_result

    def test_loadBalnStakeSnapshot(self):
        _data = [{'_day': 2, '_address': self._test1.get_address(), '_amount': 3456},
                  {'_day': 2, '_address': self._governance, '_amount': 4455}]
        params = {'_data': _data}
        print('--------------------------------------------------------')
        print(f'----------------- Test : Setting User Stake Snapshot with data {_data}-----------------')
        print('--------------------------------------------------------')

        tx_result = self._call_transaction_builder('loadBalnStakeSnapshot', params)

        self.assertEqual(1, tx_result['status'], 'Transaction Failed.')

        print(f"----------------------- Status: {tx_result.get('status')}  -----------------------")
        print('--------------------------------------------------------')
        print(f'----------------- Test : Getting User Stake Snapshot of data {_data}-----------------')
        print(f"Day", "Address", f" --> Amount")
        self._stakedBalanceOfAt(self._test1.get_address(), 2)
        self._stakedBalanceOfAt(self._governance, 2)

        print('----------------- Setting and Getting User Stake Snapshot Passed -----------------')
        print('--------------------------------------------------------')

    def _loadTotalStakeSnapshot(self):
        _data = [{'_day': 2, '_amount': 3414}, {'_day': 3, '_amount': 9347}]
        params = {'_data': _data}

        print('--------------------------------------------------------')
        print(f'----------------- Test : Setting Total Stake Snapshot with data {_data}-----------------')
        print('--------------------------------------------------------')
        tx_result = self._call_transaction_builder('loadTotalStakeSnapshot', params)

        self.assertEqual(1, tx_result['status'], 'Transaction Failed.')

        print(f"----------------------- Status: {tx_result.get('status')}  -----------------------")
        print('--------------------------------------------------------')
        print(f'----------------- Test : Getting Total Stake Snapshot of data {_data}-----------------')
        print(f"Day", f" ---> Amount")
        self.assertEqual(self._totalStakedBalanceOfAt(2), 3414)
        self.assertEqual(self._totalStakedBalanceOfAt(3), 9347)

        print('----------------- Setting and Getting Total Stake Snapshot Passed -----------------')
        print('--------------------------------------------------------')
