import json
import os
import subprocess
from typing import Union

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import TransactionBuilder, DeployTransactionBuilder, CallTransactionBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconservice.base.address import Address
from tbears.libs.icon_integrate_test import Account
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider

DIR_PATH = os.path.abspath(os.path.dirname(__file__))
SCORE_ADDRESS = "scoreAddress"


def get_key(my_dict: dict, value: Union[str, int]):
    return list(my_dict.keys())[list(my_dict.values()).index(value)]


class BalancedTestBaseLoans(IconIntegrateTestBase):
    CORE_CONTRACTS_PATH = os.path.abspath(os.path.join(DIR_PATH, "../core_contracts"))
    TOKEN_CONTRACTS_PATH = os.path.abspath(os.path.join(DIR_PATH, "../token_contracts"))
    constants = {"dex": [
        {"WITHDRAW_LOCK_TIMEOUT": ["WITHDRAW_LOCK_TIMEOUT = 180000000",
                                   "WITHDRAW_LOCK_TIMEOUT = 86400 * (10 ** 6)"]},
        {"U_SECONDS_DAY": ["U_SECONDS_DAY= 180000000", "U_SECONDS_DAY = 86400 * (10 ** 6)"]}],
        "governance": [{"U_SECONDS_DAY": ["U_SECONDS_DAY = 180000000", "U_SECONDS_DAY = 86400 * (10 ** 6)"]},
                       {"DAY_ZERO": ["DAY_ZERO = 18647 * 2880", "DAY_ZERO = 18647"]}],
        "loans": [{"U_SECONDS_DAY": ["U_SECONDS_DAY = 180000000", "U_SECONDS_DAY = 86400 * (10 ** 6)"]}],
        "staking": [{"TOP_PREP_COUNT": ["TOP_PREP_COUNT = 2", "TOP_PREP_COUNT = 100"]}],
        "rewards": [{"DAY_IN_MICROSECONDS": ["DAY_IN_MICROSECONDS = 180000000",
                                             "DAY_IN_MICROSECONDS = 86400 * (10 ** 6)"]}]}

    def patch_constants(self, file_name, old_value, new_value):
        subprocess.call("sed -i -e 's/^" + old_value + ".*/" + new_value + "/' " + file_name, shell=True)

    CORE_CONTRACTS = ["loans", "staking", "dividends", "reserve", "daofund", "rewards", "dex", "governance", "oracle"
        ,"rebalancing", "router", "feehandler", 'stakedLp']
    TOKEN_CONTRACTS = ["sicx", "bnUSD", "baln", "bwt"]
    CONTRACTS = CORE_CONTRACTS + TOKEN_CONTRACTS

    BLOCK_INTERVAL = 4
    PREPS = {
        "hx9eec61296a7010c867ce24c20e69588e2832bc52",
        "hx000e0415037ae871184b2c7154e5924ef2bc075e"
    }

    def setUp(self):
        self._wallet_setup()
        self.contracts = {}
        super().setUp(genesis_accounts=self.genesis_accounts,
                      block_confirm_interval=2,
                      network_delay_ms=0,
                      network_only=True)
        self.icon_service = IconService(HTTPProvider("http://127.0.0.1:9000", 3))
        self.nid = 3
        self.send_icx(self._test1, self.btest_wallet.get_address(), 1_000_000 * self.icx_factor)
        self.send_icx(self._test1, self.staking_wallet.get_address(), 1_000_000 * self.icx_factor)
        for key, value in self.constants.items():
            # print(value)
            for i in value:
                lis1 = []
                for x, y in i.items():
                    lis1.append(x)
                    # lis1.append(y)
                    self.patch_constants("core_contracts/" + key + "/utils/consts.py", lis1[0], y[0])
        # if os.path.exists(os.path.join(DIR_PATH, "scores_address.json")):
        #     with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
        #         self.contracts = json.load(file)
        #     return
        # else:
        self._deploy_all()
        self._config_balanced()
        self._launch_balanced()
        self._create_bnusd_market()

    def tearDown(self):
        for key, value in self.constants.items():
            # print(value)
            for i in value:
                lis1 = []
                for x, y in i.items():
                    lis1.append(x)
                    # lis1.append(y)
                    self.patch_constants("core_contracts/" + key + "/utils/consts.py", lis1[0], y[1])

    def _wallet_setup(self):
        self.icx_factor = 10 ** 18
        self.btest_wallet: 'KeyWallet' = self._wallet_array[5]
        self.staking_wallet: 'KeyWallet' = self._wallet_array[6]
        self.user1: 'KeyWallet' = self._wallet_array[7]
        self.user2: 'KeyWallet' = self._wallet_array[8]
        self.genesis_accounts = [
            Account("test1", Address.from_string(self._test1.get_address()), 800_000_0000 * self.icx_factor),
            Account("btest_wallet", Address.from_string(self.btest_wallet.get_address()), 1_000_000 * self.icx_factor),
            Account("staking_wallet", Address.from_string(self.staking_wallet.get_address()),
                    1_000_000 * self.icx_factor),
            Account("user1", Address.from_string(self.user1.get_address()), 1_000_000 * self.icx_factor),
            Account("user2", Address.from_string(self.user2.get_address()), 1_000_000 * self.icx_factor),
        ]

    def process_deploy_tx(self,
                          from_: KeyWallet,
                          to: str = SCORE_INSTALL_ADDRESS,
                          value: int = 0,
                          content: str = None,
                          params: dict = None) -> dict:

        signed_transaction = self.build_deploy_tx(from_, to, value, content, params)
        tx_result = self.process_transaction(signed_transaction, network=self.icon_service,
                                             block_confirm_interval=self.BLOCK_INTERVAL)
        print(tx_result)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def build_deploy_tx(self,
                        from_: KeyWallet,
                        to: str = SCORE_INSTALL_ADDRESS,
                        value: int = 0,
                        content: str = None,
                        params: dict = None) -> SignedTransaction:
        print(f"---------------------------Deploying contract: {content}---------------------------------------")
        params = {} if params is None else params
        transaction = DeployTransactionBuilder() \
            .from_(from_.get_address()) \
            .to(to) \
            .value(value) \
            .step_limit(2_500_000_000_000) \
            .nid(self.nid) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(content)) \
            .params(params) \
            .build()

        signed_transaction = SignedTransaction(transaction, from_)
        return signed_transaction

    def send_icx(self, from_: KeyWallet, to: str, value: int):
        previous_to_balance = self.get_balance(to)
        previous_from_balance = self.get_balance(from_.get_address())

        signed_icx_transaction = self.build_send_icx(from_, to, value)
        tx_result = self.process_transaction(signed_icx_transaction, self.icon_service, self.BLOCK_INTERVAL)

        fee = tx_result['stepPrice'] * tx_result['cumulativeStepUsed']
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
        self.assertEqual(previous_to_balance + value, self.get_balance(to))
        self.assertEqual(previous_from_balance - value - fee, self.get_balance(from_.get_address()))

    def build_send_icx(self, from_: KeyWallet, to: str, value: int) -> SignedTransaction:
        send_icx_transaction = TransactionBuilder(
            from_=from_.get_address(),
            to=to,
            value=value,
            step_limit=1000000,
            nid=self.nid,
            nonce=3
        ).build()
        signed_icx_transaction = SignedTransaction(send_icx_transaction, from_)
        return signed_icx_transaction

    def get_balance(self, address: str) -> int:
        if self.icon_service is not None:
            return self.icon_service.get_balance(address)
        params = {'address': Address.from_string(address)}
        response = self.icon_service_engine.query(method="icx_getBalance", params=params)
        return response

    def send_tx(self, from_: KeyWallet, to: str, value: int = 0, method: str = None, params: dict = None) -> dict:
        print(f"------------Calling {method} contract----------")
        signed_transaction = self.build_tx(from_, to, value, method, params)
        tx_result = self.process_transaction(signed_transaction, self.icon_service, self.BLOCK_INTERVAL)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
        return tx_result

    def build_tx(self, from_: KeyWallet, to: str, value: int = 0, method: str = None, params: dict = None) \
            -> SignedTransaction:
        params = {} if params is None else params
        tx = CallTransactionBuilder(
            from_=from_.get_address(),
            to=to,
            value=value,
            step_limit=3_000_000_000,
            nid=self.nid,
            nonce=5,
            method=method,
            params=params
        ).build()
        signed_transaction = SignedTransaction(tx, from_)
        return signed_transaction

    def call_tx(self, to: str, method: str, params: dict = None):

        params = {} if params is None else params
        call = CallBuilder(
            to=to,
            method=method,
            params=params
        ).build()
        response = self.process_call(call, self.icon_service)
        print(f"-----Reading method={method} contract------")
        # print(f"-------------------The output is: : {response}")
        return response

    def _deploy_all(self):
        governance = "governance"
        core_contracts = ["daofund", "dex", "dividends", "loans", "reserve", "rewards", "rebalancing", "router", "feehandler", "stakedLp"]
        external_contracts = ["oracle", "staking"]
        token_contracts = ["baln", "bnUSD", "bwt"]
        governed_contracts = core_contracts + token_contracts
        sicx = "sicx"
        all_contracts = governed_contracts + external_contracts

        governance_deploy_tx = self.process_deploy_tx(
            from_=self.btest_wallet,
            to=self.contracts.get(governance, SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.CORE_CONTRACTS_PATH, governance))
        )
        self.contracts[governance] = governance_deploy_tx[SCORE_ADDRESS]

        txs = []
        for contract in governed_contracts:
            if contract in core_contracts:
                path = self.CORE_CONTRACTS_PATH
            else:
                path = self.TOKEN_CONTRACTS_PATH
            deploy_tx = self.build_deploy_tx(
                from_=self.btest_wallet,
                to=self.contracts.get(contract, SCORE_INSTALL_ADDRESS),
                content=os.path.abspath(os.path.join(path, contract)),
                params={"_governance": self.contracts[governance]}
            )
            txs.append(deploy_tx)

        for contract in external_contracts:
            deploy_tx = self.build_deploy_tx(
                from_=self.staking_wallet,
                to=self.contracts.get(contract, SCORE_INSTALL_ADDRESS),
                content=os.path.abspath(os.path.join(self.CORE_CONTRACTS_PATH, contract))
            )
            txs.append(deploy_tx)

        results = self.process_transaction_bulk(
            requests=txs,
            network=self.icon_service,
            block_confirm_interval=self.BLOCK_INTERVAL
        )

        for idx, tx_result in enumerate(results):
            self.assertTrue('status' in tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
            self.contracts[all_contracts[idx]] = tx_result[SCORE_ADDRESS]

        sicx_deploy_tx = self.process_deploy_tx(
            from_=self.staking_wallet,
            to=self.contracts.get(sicx, SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.TOKEN_CONTRACTS_PATH, sicx)),
            params={"_admin": self.contracts['staking']}
        )
        self.contracts[sicx] = sicx_deploy_tx[SCORE_ADDRESS]
        self.contracts["system"] = SCORE_INSTALL_ADDRESS
        print(json.dumps(self.contracts))
        with open(os.path.join(DIR_PATH, "scores_address.json"), "w") as file:
            json.dump(self.contracts, file, indent=4)

    def _config_balanced(self):
        print("-------------------------------Configuring balanced----------------------------------------------------")
        config = self.CONTRACTS.copy()
        config.remove('governance')
        addresses = {contract: self.contracts[contract] for contract in config}

        txs = [self.build_tx(self.btest_wallet, to=self.contracts['governance'],
                             method='setAddresses', params={'_addresses': addresses}),
               self.build_tx(self.staking_wallet, to=self.contracts['staking'],
                             method='setSicxAddress', params={'_address': self.contracts['sicx']}),
               self.build_tx(self.btest_wallet, to=self.contracts['governance'], method='configureBalanced')]

        results = self.process_transaction_bulk(txs, self.icon_service, self.BLOCK_INTERVAL)

        for tx_result in results:
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")

    def _launch_balanced(self):
        print("------------------------------------Launching balanced------------------------------------------------")
        txs = [self.build_tx(self.btest_wallet, to=self.contracts['governance'], method='launchBalanced'),
               self.build_tx(self.staking_wallet, to=self.contracts['staking'], method='toggleStakingOn'),
               self.build_tx(self.btest_wallet, to=self.contracts['governance'], method='delegate',
                             params={'_delegations': [{'_address': prep,
                                                       '_votes_in_per': str(100 * self.icx_factor // len(self.PREPS))}
                                                      for prep in self.PREPS]})]
        results = self.process_transaction_bulk(
            requests=txs,
            network=self.icon_service,
            block_confirm_interval=self.BLOCK_INTERVAL
        )

        for tx_result in results:
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")

    def _create_bnusd_market(self):
        contract = "governance"
        print(f"----------------------------Calling {contract} contract-------------------------------------------")
        self.send_tx(self.btest_wallet, to=self.contracts[contract], value=4000000 * self.icx_factor,
                     method='createBnusdMarket')

    def update(self, name):
        # self.build_deploy_tx(self.btest_wallet, self.contracts[name] )
        core_contracts = ["governance", "daofund", "dex", "dividends", "loans", "reserve", "rewards"]
        external_contracts = ["oracle", "staking"]
        token_contracts = ["baln", "bnUSD", "bwt"]
        governed_contracts = core_contracts + token_contracts
        sicx = "sicx"
        all_contracts = governed_contracts + external_contracts
        cx_add = self.contracts[name]
        name2 = name
        if name == 'dex':
            name2 = name+'.zip'
        print(name)
        if name in governed_contracts:
            if name in core_contracts:
                path = os.path.abspath(os.path.join(DIR_PATH, "../continuous_rewards"))
            else:
                path = self.TOKEN_CONTRACTS_PATH
            res = self.process_deploy_tx(
                from_=self.btest_wallet,
                to=self.contracts.get(name2, cx_add),
                value=0,
                content=os.path.abspath(os.path.join(path, name2)),
                params={}
            )
