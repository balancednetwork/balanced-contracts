# If at all possible please test locally or on the private tbears server. The Testnet
# is becoming cluttered with many deployments of Balanced contracts.
# Note that running on the private tbears server will require the number of top P-Reps
# be set to 4 in the staking contract or it will fail to deploy.

network = "custom"  # set this to one of mainnet, yeouido, euljiro, pagoda, or custom

connections = {
    "mainnet": {"iconservice": "https://ctz.solidwallet.io", "nid": 1},
    "yeouido": {"iconservice": "https://bicon.net.solidwallet.io", "nid": 3},
    "gangnam": {"iconservice": "https://gicon.net.solidwallet.io", "nid": 3},
    "hannam": {"iconservice": "https://hannam.net.solidwallet.io", "nid": 3},
    "euljiro": {"iconservice": "https://test-ctz.solidwallet.io", "nid": 2},
    "pagoda": {"iconservice": "https://zicon.net.solidwallet.io", "nid": 80},
    "custom": {"iconservice": "http://18.144.108.38:9000", "nid": 3}}

env = connections[network]

import sys
sys.path.append("..")
from iconsdk.exception import JSONRPCException
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.utils.convert_type import convert_hex_str_to_int
from repeater import retry
from shutil import make_archive
import pickle as pkl
from datetime import datetime
from time import sleep
import json
import os

ICX = 1000000000000000000  # 10**18
GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
TEST_ORACLE = "cx61a36e5d10412e03c907a507d1e8c6c3856d9964"
MAIN_ORACLE = "cxe647e0af68a4661566f5e9861ad4ac854de808a2"
BALANCED_TEST = "hx3f01840a599da07b0f620eeae7aa9c574169a4be"


@retry(JSONRPCException, tries=10, delay=1, back_off=2)
def get_tx_result(_tx_hash):
    tx_result = icon_service.get_transaction_result(_tx_hash)
    return tx_result


icon_service = IconService(HTTPProvider(env["iconservice"], 3))
NID = env["nid"]

wallet = KeyWallet.load("../keystores/keystore_test1.json", "test1_Account")
# Balanced test wallet
with open("../keystores/balanced_test.pwd", "r") as f:
    key_data = f.read()
btest_wallet = KeyWallet.load("../keystores/balanced_test.json", key_data)

with open("../keystores/staking_test.pwd", "r") as f:
    key_data = f.read()
staking_wallet = KeyWallet.load("../keystores/staking_test.json", key_data)

print(wallet.get_address())
print(icon_service.get_balance(wallet.get_address()) / 10 ** 18)

print(btest_wallet.get_address())
print(icon_service.get_balance(btest_wallet.get_address()) / 10 ** 18)

user1 = KeyWallet.load("../keystores/user1.json", "HelloWorld@1234")
# btest_wallet = KeyWallet.load("./balanced_test.json","HelloWorld@1234")

print(icon_service.get_balance(user1.get_address()) / 10 ** 18)
print(user1.get_address())

# test2 = hx7a1824129a8fe803e45a3aae1c0e060399546187
private = "0a354424b20a7e3c55c43808d607bddfac85d033e63d7d093cb9f0a26c4ee022"
user2 = KeyWallet.load(bytes.fromhex(private))
print(icon_service.get_balance(user2.get_address()) / 10 ** 18)
print(user2.get_address())

print("==============================================="
      " ......Testing retireAssets method......."
      "=================================================")

# The following addresses are those deployed to the private tbears server.

contracts = {'loans': {'zip': 'core_contracts/loans.zip',
                       'SCORE': 'cxa0f715fb2c4bc8f4c6399c2cc26167a27be0aa61'},
             'staking': {'zip': 'core_contracts/staking.zip',
                         'SCORE': 'cxbabed822d59b605dbeb6322735c529b292baac3b'},
             'dividends': {'zip': 'core_contracts/dividends.zip',
                           'SCORE': 'cx1379084f45776301abda3849c6e374f460ee0155'},
             'reserve': {'zip': 'core_contracts/reserve.zip',
                         'SCORE': 'cx71dda2221bf88faddc8f84b72ffd6db296e5609e'},
             'daofund': {'zip': 'core_contracts/daofund.zip',
                         'SCORE': 'cxfd09787f23d23b945fa0c7eb55b5aa69425da1c8'},
             'rewards': {'zip': 'core_contracts/rewards.zip',
                         'SCORE': 'cx27aa3bf62145822e60d85fa5d18dabdcff5b9ada'},
             'dex': {'zip': 'core_contracts/dex.zip',
                     'SCORE': 'cx01eee12b6614e5328e0a84261652cb7f055e0176'},
             'governance': {'zip': 'core_contracts/governance.zip',
                            'SCORE': 'cxd7b3e71dcff3d75392216e208f28ef68e8a54ec0'},
             'oracle': {'zip': 'core_contracts/oracle.zip',
                        'SCORE': 'cxed97bdb35a7ca1b3993e400e4dba9e11610338f7'},
             'sicx': {'zip': 'token_contracts/sicx.zip',
                      'SCORE': 'cx799f724e02560a762b5f2bd3b6d2d8d59d7aecc1'},
             'bnUSD': {'zip': 'token_contracts/bnUSD.zip',
                       'SCORE': 'cx266bdc0c35828c8130cdf1cbaa3ad109f7694722'},
             'bnXLM': {'zip': 'token_contracts/bnXLM.zip',
                       'SCORE': 'cx266bdc0c35828c8130cdf1cbaa3ad109f7694722'},
             'bnDOGE': {'zip': 'token_contracts/bnDOGE.zip',
                        'SCORE': 'cx266bdc0c35828c8130cdf1cbaa3ad109f7694722'},
             'baln': {'zip': 'token_contracts/baln.zip',
                      'SCORE': 'cx4d0768508a7ff550de4405f27aebfb8831565c19'},
             'bwt': {'zip': 'token_contracts/bwt.zip',
                     'SCORE': 'cx663f9d59163846d9f6c6f7b586858c59aa8878a9'}}


# Define deploy and send_tx functions

def send_icx(to, amount, wallet):
    transaction = TransactionBuilder() \
        .from_(wallet.get_address()) \
        .to(to) \
        .value(amount) \
        .step_limit(1000000) \
        .nid(NID) \
        .nonce(2) \
        .version(3) \
        .build()
    signed_transaction = SignedTransaction(transaction, wallet)
    return icon_service.send_transaction(signed_transaction)


def compress():
    """
    Compress all SCORE folders in the core_contracts and token_contracts folders.
    Make sure the oracle address is correct.
    """
    deploy = list(contracts.keys())[:]
    for directory in {"../../core_contracts", "../../token_contracts"}:
        with os.scandir(directory) as it:
            for file in it:
                archive_name = directory + "/" + file.name
                if file.is_dir() and file.name in deploy:
                    make_archive(archive_name, "zip", directory, file.name)
                    contracts[file.name]['zip'] = archive_name + '.zip'
    if network == "yeouido":
        contracts['oracle']['SCORE'] = TEST_ORACLE
    elif network == "mainnet":
        contracts['oracle']['SCORE'] = MAIN_ORACLE


def deploy_SCORE(contract, params, wallet, update) -> str:
    """
    contract is of form {'zip': 'core_contracts/governance.zip', 'SCORE': 'cx1d81f93b3b8d8d2a6455681c46128868782ddd09'}
    params is a dicts
    wallet is a wallet file
    update is boolian
    """
    print(f'{contract["zip"]}')
    if update:
        dest = contract['SCORE']
    else:
        dest = GOVERNANCE_ADDRESS
    zip_file = contract['zip']
    step_limit = 4000100000
    deploy_transaction = DeployTransactionBuilder() \
        .from_(wallet.get_address()) \
        .to(dest) \
        .nid(NID) \
        .nonce(100) \
        .content_type("application/zip") \
        .content(gen_deploy_data_content(zip_file)) \
        .params(params) \
        .build()

    signed_transaction = SignedTransaction(deploy_transaction, wallet, step_limit)
    tx_hash = icon_service.send_transaction(signed_transaction)

    res = get_tx_result(tx_hash)
    print(f'Status: {res["status"]}')
    if len(res["eventLogs"]) > 0:
        for item in res["eventLogs"]:
            print(f'{item} \n')
    if res['status'] == 0:
        print(f'Failure: {res["failure"]}')
    print('')
    return res


def send_tx(dest, value, method, params, wallet):
    """
    dest is the name of the destination contract.
    """
    print(
        '------------------------------------------------------------------------------------------------------------------')
    print(f'Calling {method}, with parameters {params} on the {dest} contract.')
    print(
        '------------------------------------------------------------------------------------------------------------------')
    transaction = CallTransactionBuilder() \
        .from_(wallet.get_address()) \
        .to(contracts[dest]['SCORE']) \
        .value(value) \
        .step_limit(10000000) \
        .nid(NID) \
        .nonce(100) \
        .method(method) \
        .params(params) \
        .build()
    signed_transaction = SignedTransaction(transaction, wallet)
    tx_hash = icon_service.send_transaction(signed_transaction)

    res = get_tx_result(tx_hash)
    print(
        f'************************************************** Status: {res["status"]} **************************************************')
    if len(res["eventLogs"]) > 0:
        for item in res["eventLogs"]:
            print(f'{item} \n')
    if res['status'] == 0:
        print(f'Failure: {res["failure"]}')
    return res


def deploy_all(wallet, staking_wallet):
    """
    Compress and Deploy all SCOREs.
    """
    compress()

    deploy = list(contracts.keys())[:]
    deploy.remove('oracle')
    deploy.remove('staking')
    deploy.remove('sicx')
    deploy.remove('governance')
    if network == "mainnet":
        deploy.remove('bnXLM')
        deploy.remove('bnDOGE')

    results = {}
    res = deploy_SCORE(contracts['governance'], {}, wallet, 0)
    results[f'{contracts["governance"]}|deploy|{{}}'] = res
    governance = res.get('scoreAddress', '')
    contracts['governance']['SCORE'] = governance
    params = {'_governance': governance}
    for score in deploy:
        res = deploy_SCORE(contracts[score], params, wallet, 0)
        results[f'{contracts[score]}|deploy|{params}'] = res
        contracts[score]['SCORE'] = res.get('scoreAddress', '')

    res = deploy_SCORE(contracts['staking'], {}, staking_wallet, 0)
    results[f'{contracts["staking"]}|deploy|{{}}'] = res
    contracts['staking']['SCORE'] = res.get('scoreAddress', '')

    params = {'_admin': contracts['staking']['SCORE']}
    res = deploy_SCORE(contracts['sicx'], params, staking_wallet, 0)
    results[f'{contracts["sicx"]}|deploy|{params}'] = res
    contracts['sicx']['SCORE'] = res.get('scoreAddress', '')

    return results


def config_balanced(wallet, staking_wallet):
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
        res = send_tx(tx["contract"], tx["value"], tx["method"], tx["params"], tx["wallet"])
        results[f'{tx["contract"]}|{tx["method"]}|{tx["params"]}'] = res

    return results


def launch_balanced(wallet, staking_wallet):
    """
    Launch Balanced, turn on staking management, and set delegation for sICX on the Loans contract.
    """
    if network == "custom":
        preps = {
            "hx9eec61296a7010c867ce24c20e69588e2832bc52",  # ICX Station
            "hx000e0415037ae871184b2c7154e5924ef2bc075e"}  # iBriz-ICONOsphere
    elif network == "yeouido":
        preps = {
            "hx23823847f593ecb65c9e1ea81a789b02766280e8",  # ICX Station
            "hxe0cde6567eb6529fe31b0dc2f2697af84847f321",  # iBriz-ICONOsphere
            "hx83c0fc2bcac7ecb3928539e0256e29fc371b5078",  # Mousebelt
            "hx48b4636e84d8c491c88c18b65dceb7598c4600cc",  # Parrot 9
            "hxb4e90a285a79687ec148c29faabe6f71afa8a066"}  # ICONDAO
    elif network == "mainnet":
        preps = {
            "",  # ICX Station
            "",  # iBriz-ICONOsphere
            "",  # Mousebelt
            "",  # Parrot 9
            ""}  # ICONDAO
    else:
        return

    txns = [{'contract': 'governance', 'value': 0, 'method': 'launchBalanced', 'params': {}, 'wallet': wallet},
            {'contract': 'staking', 'value': 0, 'method': 'toggleStakingOn', 'params': {}, 'wallet': staking_wallet},
            {'contract': 'governance', 'value': 0, 'method': 'delegate', 'params': {
                '_delegations': [{'_address': prep, '_votes_in_per': str(100 * ICX // len(preps))} for prep in preps]},
             'wallet': wallet}]

    results = {}
    for tx in txns:
        res = send_tx(tx["contract"], tx["value"], tx["method"], tx["params"], tx["wallet"])
        results[f'{tx["contract"]}|{tx["method"]}|{tx["params"]}'] = res

    return results


def get_scores_json(contracts):
    """
    Prints out dictionary of SCORE addresses for use in testing UI.
    """
    scores = {}
    for score in contracts:
        scores[score] = contracts[score]['SCORE']
    return json.dumps(scores)


def call_tx(dest: str, method: str, params: dict = {}):
    """
    dest is the name of the destination contract.
    """
    print(
        '------------------------------------------------------------------------------------------------------------------')
    print(f'Reading {method}, with parameters {params} on the {dest} contract.')
    print(
        '------------------------------------------------------------------------------------------------------------------')
    call = CallBuilder() \
        .from_(wallet.get_address()) \
        .to(contracts[dest]['SCORE']) \
        .method(method) \
        .params(params) \
        .build()
    result = icon_service.call(call)
    print(result)
    return result


# Deploy and configure Balanced. Print results if anything goes wrong.
if network == 'custom':
    confirm = 'Yes'
else:
    confirm = input(f'Deploying Balanced to {network}. Proceed (Yes/No)? ')
if confirm == 'Yes':
    results = {}
    deploy_all(btest_wallet, staking_wallet)
    print(
        '------------------------------------------------------------------------------------------------------------------')
    print(contracts)
    print(
        '----------Contracts for Testing UI--------------------------------------------------------------------------------')
    print(get_scores_json(contracts))

# Configure Balanced
config_results = config_balanced(btest_wallet, staking_wallet)
print(config_results)

# Launch Balanced
# We may want to make this a payable method and have the governance SCORE borrow bnUSD,
# start and name the sICXbnUSD market, and add it as a rewards DataSource.
launch_results = launch_balanced(btest_wallet, staking_wallet)
print(launch_results)


def update():
    # Cell 8
    # Deploy or Update a single SCORE

    contract_name = 'rewards'
    update = 1
    params = {}
    if update == 0:
        params = {'_governance': contracts['governance']['SCORE']}

    compress()
    contract = contracts[contract_name]
    confirm = input(
        f'{"Updating" if update else "Deploying"} {contract_name} with params: {params} to {network}. Proceed (Yes/No)? ')
    if confirm == 'Yes':
        deploy_SCORE(contract, params, btest_wallet, update)


# 1.no bad debt for asset, retired from account user2 without a position on Balanced.
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})


# add collateral to user1 account
send_tx('loans', 2000*ICX, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 500 * ICX}, user1)

# gives maximum retire amount
call_tx('loans', 'getMaxRetireAmount', {'_symbol': 'bnUSD'})


def test_retireAssets():
    #  Now we try to retire maximum bnusd retirement allowed
    test_cases = {
        "stories": [
            {
                "description": "User2 tries to retire 10 bnusd",
                "actions": {
                    "sender": "user2",
                    "first_meth": "transfer",
                    "second_meth": "returnAsset",
                    "deposited_icx": "0",
                    "first_params": {'_to': user2.get_address(), '_value': 20 * ICX},
                    "second_params": {"_symbol": "bnUSD", '_value': 5 * ICX},
                    "expected_status_result": "1"
                }
            }
        ]
    }

    for case in test_cases['stories']:
        print(case['description'])
        _to = contracts['bnUSD']['SCORE']
        meth1 = case['actions']['first_meth']
        meth2 = case['actions']['second_meth']
        val = int(case['actions']['deposited_icx'])
        data1 = case['actions']['first_params']
        first_params = {"_to": data1['_to'], "_value": data1['_value']}

        data2 = case['actions']['second_params']
        second_params = {'_symbol': data2['_symbol'], '_value': data2['_value']}

        send_tx('bnUSD', 0, meth1, first_params, user1)
        sleep(2)
        res = send_tx('loans', 0, meth2, second_params, user2)
        assert res['status'] == int(
            case['actions']['expected_status_result']), 'Retired amount is greater than the current maximum allowed'
        print('Test case passed')


test_retireAssets()
