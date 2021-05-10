import json
import os
from shutil import make_archive
import sys

from iconsdk.wallet.wallet import KeyWallet

sys.path.append("./utils/")
from iconsdk.exception import JSONRPCException
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.signed_transaction import SignedTransaction

from repeater import retry
from helpers import read_file_data, print_d_msg

import os
from dotenv import load_dotenv

# CONSTANTS


ICX = 1000000000000000000  # 10**18
GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
TEST_ORACLE = "cx61a36e5d10412e03c907a507d1e8c6c3856d9964"
MAIN_ORACLE = "cxe647e0af68a4661566f5e9861ad4ac854de808a2"
BALANCED_TEST = "hx3f01840a599da07b0f620eeae7aa9c574169a4be"

_contracts_dir = "./utils/contracts_info.json"

# Load Deployed contracts
contracts = read_file_data(_contracts_dir)

# WALLETS
load_dotenv()

wallet = KeyWallet.load(bytes.fromhex(os.getenv('main_wallet')))
btest_wallet = KeyWallet.load(bytes.fromhex(os.getenv('balanced_test_wallet1')))
staking_wallet = KeyWallet.load(bytes.fromhex(os.getenv('balanced_test_wallet1')))
user1 = KeyWallet.load(bytes.fromhex(os.getenv('balanced_test_wallet2')))
user2 = KeyWallet.load(bytes.fromhex(os.getenv('balanced_test_wallet3')))


class BalancedIconService:
    def __init__(self, url, network, nid):
        self.icon_service = IconService(HTTPProvider(url, 3))
        self.nid = nid
        self.network = network

    def send_icx(self, to, amount, wallet):
        transaction = TransactionBuilder() \
            .from_(wallet.get_address()) \
            .to(to) \
            .value(amount) \
            .step_limit(1000000) \
            .nid(self.nid) \
            .nonce(2) \
            .version(3) \
            .build()
        signed_transaction = SignedTransaction(transaction, wallet)
        return self.icon_service.send_transaction(signed_transaction)

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(self, _tx_hash):
        tx_result = self.icon_service.get_transaction_result(_tx_hash)
        return tx_result

    def compress(self):
        """
        Compress all SCORE folders in the core_contracts and token_contracts folders.
        Make sure the oracle address is correct.
        """
        deploy = list(contracts.keys())[:]
        for directory in {"../core_contracts", "../token_contracts"}:
            with os.scandir(directory) as it:
                for file in it:
                    archive_name = directory + "/" + file.name
                    if file.is_dir() and file.name in deploy:
                        make_archive(archive_name, "zip", directory, file.name)
                        contracts[file.name]['zip'] = archive_name + '.zip'
        if self.network == "yeouido":
            contracts['oracle']['SCORE'] = TEST_ORACLE
        elif self.network == "mainnet":
            contracts['oracle']['SCORE'] = MAIN_ORACLE

    def deploy_SCORE(self, contract, params, wallet, update) -> str:
        """
        contract is of form {'zip': 'core_contracts/governance.zip', 'SCORE': 'cx1d81f93b3b8d8d2a6455681c46128868782ddd09'}
        params is a dicts
        wallet is a wallet file
        update is boolian
        """
        print_d_msg(f'{contract["zip"]}')
        if update:
            dest = contract['SCORE']
        else:
            dest = GOVERNANCE_ADDRESS
        zip_file = contract['zip']
        step_limit = 3000000000
        deploy_transaction = DeployTransactionBuilder().from_(wallet.get_address()).to(dest).nid(self.nid).nonce(
            100).content_type("application/zip").content(gen_deploy_data_content(zip_file)).params(params).build()

        signed_transaction = SignedTransaction(deploy_transaction, wallet, step_limit)
        tx_hash = self.icon_service.send_transaction(signed_transaction)

        res = self.get_tx_result(tx_hash)
        print_d_msg(f'Status: {res["status"]}')
        # if len(res["eventLogs"]) > 0:
        #     for item in res["eventLogs"]:
        #         print_d_msg(f'{item} \n')
        if res['status'] == 0:
            print_d_msg(f'Failure: {res["failure"]}')
        print('')
        return res

    def send_tx(self, dest, value, method, params, wallet, _print=True):
        """
        dest is the name of the destination contract.
        """
        if _print:
            print_d_msg(
                '------------------------------------------------------------------------------------------------------------------')
            print_d_msg(f'Calling {method}, with parameters {params} on the {dest} contract.')
            print_d_msg(
                '------------------------------------------------------------------------------------------------------------------')
        transaction = CallTransactionBuilder().from_(wallet.get_address()).to(contracts[dest]['SCORE']).value(
            value).step_limit(10000000).nid(self.nid).nonce(100).method(method).params(params).build()
        signed_transaction = SignedTransaction(transaction, wallet)
        tx_hash = self.icon_service.send_transaction(signed_transaction)

        res = self.get_tx_result(tx_hash)
        if _print:
            print_d_msg(
                f'************************************************** Status: {res["status"]} **************************************************')
        # if len(res["eventLogs"]) > 0:
        #     for item in res["eventLogs"]:
        #         print_d_msg(f'{item} \n')
        if res['status'] == 0:
            if _print:
                print_d_msg(f'Failure: {res["failure"]}')
        return res

    def deploy_all(self, wallet, staking_wallet):
        """
        Compress and Deploy all SCOREs.
        """
        self.compress()

        deploy = list(contracts.keys())[:]
        deploy.remove('oracle')
        deploy.remove('staking')
        deploy.remove('sicx')
        deploy.remove('governance')
        if self.network == "mainnet":
            if 'bnXLM' in deploy:
                deploy.remove('bnXLM')
            if 'bnDOGE' in deploy:
                deploy.remove('bnDOGE')

        results = {}
        res = self.deploy_SCORE(contracts['governance'], {}, wallet, 0)
        results[f'{contracts["governance"]}|deploy|{{}}'] = res
        governance = res.get('scoreAddress', '')
        contracts['governance']['SCORE'] = governance
        params = {'_governance': governance}
        for score in deploy:
            res = self.deploy_SCORE(contracts[score], params, wallet, 0)
            results[f'{contracts[score]}|deploy|{params}'] = res
            contracts[score]['SCORE'] = res.get('scoreAddress', '')

        res = self.deploy_SCORE(contracts['staking'], {}, staking_wallet, 0)
        results[f'{contracts["staking"]}|deploy|{{}}'] = res
        contracts['staking']['SCORE'] = res.get('scoreAddress', '')

        params = {'_admin': contracts['staking']['SCORE']}
        res = self.deploy_SCORE(contracts['sicx'], params, staking_wallet, 0)
        results[f'{contracts["sicx"]}|deploy|{params}'] = res
        contracts['sicx']['SCORE'] = res.get('scoreAddress', '')

        return results

    def config_balanced(self, wallet, staking_wallet):
        """
        Configure all SCOREs before launch.
        """
        config = list(contracts.keys())[:]
        config.remove('governance')
        config.remove('bnDOGE')
        config.remove('bnXLM')
        addresses = {contract: contracts[contract]['SCORE'] for contract in config}
        txns = [{'contract': 'governance', 'value': 0, 'method': 'setAddresses', 'params': {'_addresses': addresses},
                 'wallet': wallet},
                {'contract': 'staking', 'value': 0, 'method': 'setSicxAddress',
                 'params': {'_address': contracts['sicx']['SCORE']}, 'wallet': staking_wallet},
                {'contract': 'governance', 'value': 0, 'method': 'configureBalanced', 'params': {}, 'wallet': wallet}]

        results = {}
        for tx in txns:
            res = self.send_tx(tx["contract"], tx["value"], tx["method"], tx["params"], tx["wallet"])
            results[f'{tx["contract"]}|{tx["method"]}|{tx["params"]}'] = res

        return results

    def launch_balanced(self, wallet, staking_wallet):
        """
        Launch Balanced, turn on staking management, and set delegation for sICX on the Loans contract.
        """
        if self.network == "custom":
            preps = {
                "hx9eec61296a7010c867ce24c20e69588e2832bc52",  # ICX Station
                "hx000e0415037ae871184b2c7154e5924ef2bc075e"}  # iBriz-ICONOsphere
        elif self.network == "yeouido":
            preps = {
                "hx23823847f593ecb65c9e1ea81a789b02766280e8",  # ICX Station
                "hxe0cde6567eb6529fe31b0dc2f2697af84847f321",  # iBriz-ICONOsphere
                "hx83c0fc2bcac7ecb3928539e0256e29fc371b5078",  # Mousebelt
                "hx48b4636e84d8c491c88c18b65dceb7598c4600cc",  # Parrot 9
                "hxb4e90a285a79687ec148c29faabe6f71afa8a066"}  # ICONDAO
        elif self.network == "mainnet":
            preps = {
                "hxfba37e91ccc13ec1dab115811f73e429cde44d48",  # ICX Station
                "hx231a795d1c719b9edf35c46b9daa4e0b5a1e83aa",  # iBriz-ICONOsphere
                "hxbc9c73670c79e8f6f8060551a792c2cf29a8c491",  # Mousebelt
                "hx28c08b299995a88756af64374e13db2240bc3142"}  # Parrot 9
        else:
            return

        txns = [{'contract': 'governance', 'value': 0, 'method': 'launchBalanced', 'params': {}, 'wallet': wallet},
                {'contract': 'staking', 'value': 0, 'method': 'toggleStakingOn', 'params': {},
                 'wallet': staking_wallet},
                {'contract': 'governance', 'value': 0, 'method': 'delegate', 'params': {
                    '_delegations': [{'_address': prep, '_votes_in_per': str(100 * ICX // len(preps))} for prep in
                                     preps]},
                 'wallet': wallet}]

        results = {}
        for tx in txns:
            res = self.send_tx(tx["contract"], tx["value"], tx["method"], tx["params"], tx["wallet"])
            results[f'{tx["contract"]}|{tx["method"]}|{tx["params"]}'] = res

        return results

    def get_scores_json(self, contracts):
        """
        print_d_msgs out dictionary of SCORE addresses for use in testing UI.
        """
        scores = {}
        for score in contracts:
            scores[score] = contracts[score]['SCORE']
        return json.dumps(scores)

    def call_tx(self, dest: str, method: str, params: dict = {}, _print=True):
        """
        dest is the name of the destination contract.
        """
        if _print:
            print_d_msg(
                '------------------------------------------------------------------------------------------------------------------')
            print_d_msg(f'Reading {method}, with parameters {params} on the {dest} contract.')
            print_d_msg(
                '------------------------------------------------------------------------------------------------------------------')
        call = CallBuilder().from_(wallet.get_address()).to(contracts[dest]['SCORE']).method(method).params(
            params).build()
        result = self.icon_service.call(call)
        if _print:
            print_d_msg(result)
        return result

    def fast_send_tx(self, dest, value, method, params, wallet, _print=False):
        """
        dest is the name of the destination contract.
        """
        if _print:
            print_d_msg(
                '------------------------------------------------------------------------------------------------------------------')
            print_d_msg(f'Calling {method}, with parameters {params} on the {dest} contract.')
            print_d_msg(
                '------------------------------------------------------------------------------------------------------------------')
        transaction = CallTransactionBuilder().from_(wallet.get_address()).to(contracts[dest]['SCORE']).value(
            value).step_limit(10000000).nid(self.nid).nonce(100).method(method).params(params).build()
        signed_transaction = SignedTransaction(transaction, wallet)
        tx_hash = self.icon_service.send_transaction(signed_transaction)

        res = self.get_tx_result(tx_hash)
        if _print:
            print_d_msg(
                f'************************************************** Status: {res["status"]} **************************************************')
        # if len(res["eventLogs"]) > 0:
        #     for item in res["eventLogs"]:
        #         print_d_msg(f'{item} \n')
        if res['status'] == 0:
            if _print:
                print_d_msg(f'Failure: {res["failure"]}')
        return res

    def deploy_and_launch_balanced(self):
        if self.network == 'custom':
            confirm = 'Yes'
        else:
            confirm = input(f'Deploying Balanced to {self.network}. Proceed (Yes/No)? ')
        if confirm == 'Yes':
            results = {}
            self.deploy_all(btest_wallet, staking_wallet)
            print_d_msg(
                '------------------------------------------------------------------------------------------------------------------')
            print_d_msg(contracts)
            # print_d_msg(
            #     '----------Contracts for Testing UI--------------------------------------------------------------------------------')
            # print_d_msg(get_scores_json(contracts))


        # Configure Balanced
        config_results = self.config_balanced(btest_wallet, staking_wallet)
        # print_d_msg(config_results)

        # Launch Balanced
        # We may want to make this a payable method and have the governance SCORE borrow bnUSD,
        # start and name the sICXbnUSD market, and add it as a rewards DataSource.
        launch_results = self.launch_balanced(btest_wallet, staking_wallet)

        # print_d_msg(launch_results)

    def update(self):
        # Cell 8
        # Deploy or Update a single SCORE

        contract_name = 'rewards'
        update = 1
        params = {}
        if update == 0:
            params = {'_governance': contracts['governance']['SCORE']}

        self.compress()
        contract = contracts[contract_name]
        confirm = input(
            f'{"Updating" if update else "Deploying"} {contract_name} with params: {params} to {self.network}. Proceed (Yes/No)? ')
        if confirm == 'Yes':
            self.deploy_SCORE(contract, params, btest_wallet, update)