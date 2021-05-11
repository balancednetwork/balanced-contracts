import json
import os
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


class BalancedTestBase(IconIntegrateTestBase):

    CORE_CONTRACTS_PATH = os.path.abspath(os.path.join(DIR_PATH, "../core_contracts"))
    TOKEN_CONTRACTS_PATH = os.path.abspath(os.path.join(DIR_PATH, "../token_contracts"))

    CORE_CONTRACTS = ["loans", "staking", "dividends", "reserve", "daofund", "rewards", "dex", "governance", "oracle"]
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

        self._deploy_all()
        self._config_balanced()
        self._launch_balanced()
        self._createBnusdMarket()

    def _wallet_setup(self):
        self.icx_factor = 10 ** 18
        self.btest_wallet: 'KeyWallet' = KeyWallet.create()
        self.staking_wallet: 'KeyWallet' = KeyWallet.create()
        self.user1: 'KeyWallet' = KeyWallet.create()
        self.user2: 'KeyWallet' = KeyWallet.create()
        self.genesis_accounts = [
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
            .step_limit(3_000_000_000) \
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
        send_icx_transaction = TransactionBuilder(
            from_=from_.get_address(),
            to=to,
            value=value,
            step_limit=1000000,
            nid=self.nid,
            nonce=3
        ).build()

        signed_icx_transaction = SignedTransaction(send_icx_transaction, from_)
        tx_result = self.process_transaction(signed_icx_transaction, self.icon_service, self.BLOCK_INTERVAL)

        fee = tx_result['stepPrice'] * tx_result['cumulativeStepUsed']
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
        self.assertEqual(previous_to_balance + value, self.get_balance(to))
        self.assertEqual(previous_from_balance - value - fee, self.get_balance(from_.get_address()))

    def get_balance(self, address: str) -> int:
        if self.icon_service is not None:
            return self.icon_service.get_balance(address)
        params = {'address': Address.from_string(address)}
        response = self.icon_service_engine.query(method="icx_getBalance", params=params)
        return response

    def send_tx(self, from_: KeyWallet, to: str, value: int = 0, method: str = None, params: dict = None):
        print(f"------------Calling {method}, with params={params} to {get_key(self.contracts, to)} contract----------")
        signed_transaction = self.build_tx(from_, to, value, method, params)
        tx_result = self.process_transaction(signed_transaction, self.icon_service, self.BLOCK_INTERVAL)
        print(tx_result)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")

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
        print(f"-----Reading method={method}, with params={params} on the {get_key(self.contracts, to)} contract------")
        params = {} if params is None else params
        call = CallBuilder(
            to=to,
            method=method,
            params=params
        ).build()

        return self.process_call(call, self.icon_service)

    def _deploy_all(self):
        governance = "governance"
        core_contracts = ["daofund", "dex", "dividends", "loans", "reserve", "rewards"]
        external_contracts = ["oracle", "staking"]
        token_contracts = ["baln", "bnUSD", "bwt"]
        governed_contracts = core_contracts + token_contracts
        sicx = "sicx"
        all_contracts = governed_contracts + external_contracts

        governance_deploy_tx = self.process_deploy_tx(
            from_=self.btest_wallet,
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
                content=os.path.abspath(os.path.join(path, contract)),
                params={"_governance": self.contracts[governance]}
            )
            txs.append(deploy_tx)

        for contract in external_contracts:
            deploy_tx = self.build_deploy_tx(
                from_=self.staking_wallet,
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
            content=os.path.abspath(os.path.join(self.TOKEN_CONTRACTS_PATH, sicx)),
            params={"_admin": self.contracts['staking']}
        )
        self.contracts[sicx] = sicx_deploy_tx[SCORE_ADDRESS]
        print(json.dumps(self.contracts))

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

    def _createBnusdMarket(self):
        self.send_tx(self.btest_wallet, to=self.contracts['governance'], value=210 * self.icx_factor,
                     method='createBnusdMarket')
