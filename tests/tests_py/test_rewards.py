# If at all possible please test locally or on the private tbears server. The Testnet
# is becoming cluttered with many deployments of Balanced contracts.
# Note that running on the private tbears server will require the number of top P-Reps 
# be set to 4 in the staking contract or it will fail to deploy.
import time

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

filename = './scenarios/tests_py/loans-rewards.json'


def read_file_data(filename):
    with open(filename, encoding="utf8") as data_file:
        json_data = json.load(data_file)
    return json_data


test_cases = read_file_data(filename)


@retry(JSONRPCException, tries=10, delay=1, back_off=2)
def get_tx_result(_tx_hash):
    tx_result = icon_service.get_transaction_result(_tx_hash)
    return tx_result


icon_service = IconService(HTTPProvider(env["iconservice"], 3))
NID = env["nid"]

wallet = KeyWallet.load("./keystores/keystore_test1.json", "test1_Account")
# Balanced test wallet
with open("./keystores/balanced_test.pwd", "r") as f:
    key_data = f.read()
btest_wallet = KeyWallet.load("./keystores/balanced_test.json", key_data)
with open("./keystores/staking_test.pwd", "r") as f:
    key_data = f.read()
staking_wallet = KeyWallet.load("./keystores/staking_test.json", key_data)

print("Test Wallet address 1:", wallet.get_address())
print("Test Wallet address 2:", btest_wallet.get_address())

user1 = KeyWallet.load("./keystores/user1.json", "HelloWorld@1234")
# btest_wallet = KeyWallet.load("./balanced_test.json","HelloWorld@1234")

# test2 = hx7a1824129a8fe803e45a3aae1c0e060399546187
private = "0a354424b20a7e3c55c43808d607bddfac85d033e63d7d093cb9f0a26c4ee022"
user2 = KeyWallet.load(bytes.fromhex(private))


dict_list = []


def create_wallets():
    for i in range(0, 5):
        data = {}
        wallet2 = KeyWallet.create()
        address = wallet2.get_address()
        private_key = wallet2.get_private_key()
        data[address] = private_key
        dict_list.append(data)
    with open('./tests_py/wallet2.json', 'a') as f:
        json.dump(dict_list, f, ensure_ascii=False, indent=4)


with open('./tests_py/wallet2.json') as f:
    data = json.load(f)


def transfer_icx():
    for dict in data:
        for items in dict.items():
            print(items[0])
            set_div_per = TransactionBuilder().from_(wallet.get_address()).to(items[0]).nid(NID).nonce(100).value(
                5000 * 10 ** 18).build()
            estimate_step = icon_service.estimate_step(set_div_per)
            step_limit = estimate_step + 10000000
            signed_transaction = SignedTransaction(set_div_per, wallet, step_limit)

            tx_hash = icon_service.send_transaction(signed_transaction)
            ab = get_tx_result(tx_hash)

print("==============================================="
      " ......Testing Rewards contract......."
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


# In[51]:


# Cell 6
# Define deploy and send_tx functions

def send_icx(to, amount, wallet):
    transaction = TransactionBuilder().from_(wallet.get_address()).to(to).value(amount).step_limit(1000000).nid(
        NID).nonce(2).version(3).build()
    signed_transaction = SignedTransaction(transaction, wallet)
    return icon_service.send_transaction(signed_transaction)


def compress():
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
    step_limit = 3000000000
    deploy_transaction = DeployTransactionBuilder().from_(wallet.get_address()).to(dest).nid(NID).nonce(
        100).content_type("application/zip").content(gen_deploy_data_content(zip_file)).params(params).build()

    signed_transaction = SignedTransaction(deploy_transaction, wallet, step_limit)
    tx_hash = icon_service.send_transaction(signed_transaction)

    res = get_tx_result(tx_hash)
    print(f'Status: {res["status"]}')
    # if len(res["eventLogs"]) > 0:
    #     for item in res["eventLogs"]:
    #         print(f'{item} \n')
    if res['status'] == 0:
        print(f'Failure: {res["failure"]}')
    print('')
    return res


def send_tx(dest, value, method, params, wallet, _print=True):
    """
    dest is the name of the destination contract.
    """
    if _print:
        print(
            '------------------------------------------------------------------------------------------------------------------')
        print(f'Calling {method}, with parameters {params} on the {dest} contract.')
        print(
            '------------------------------------------------------------------------------------------------------------------')
    transaction = CallTransactionBuilder().from_(wallet.get_address()).to(contracts[dest]['SCORE']).value(
        value).step_limit(10000000).nid(NID).nonce(100).method(method).params(params).build()
    signed_transaction = SignedTransaction(transaction, wallet)
    tx_hash = icon_service.send_transaction(signed_transaction)

    res = get_tx_result(tx_hash)
    if _print:
        print(
            f'************************************************** Status: {res["status"]} **************************************************')
    # if len(res["eventLogs"]) > 0:
    #     for item in res["eventLogs"]:
    #         print(f'{item} \n')
    if res['status'] == 0:
        if _print:
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
        if 'bnXLM' in deploy:
            deploy.remove('bnXLM')
        if 'bnDOGE' in deploy:
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
            "hxfba37e91ccc13ec1dab115811f73e429cde44d48",  # ICX Station
            "hx231a795d1c719b9edf35c46b9daa4e0b5a1e83aa",  # iBriz-ICONOsphere
            "hxbc9c73670c79e8f6f8060551a792c2cf29a8c491",  # Mousebelt
            "hx28c08b299995a88756af64374e13db2240bc3142"}  # Parrot 9
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


def call_tx(dest: str, method: str, params: dict = {}, _print=True):
    """
    dest is the name of the destination contract.
    """
    if _print:
        print(
            '------------------------------------------------------------------------------------------------------------------')
        print(f'Reading {method}, with parameters {params} on the {dest} contract.')
        print(
            '------------------------------------------------------------------------------------------------------------------')
    call = CallBuilder().from_(btest_wallet.get_address()).to(contracts[dest]['SCORE']).method(method).params(
        params).build()
    result = icon_service.call(call)
    if _print:
        print(result)
    return result


def fast_send_tx(dest, value, method, params, wallet, _print=False):
    """
    dest is the name of the destination contract.
    """
    if _print:
        print(
            '------------------------------------------------------------------------------------------------------------------')
        print(f'Calling {method}, with parameters {params} on the {dest} contract.')
        print(
            '------------------------------------------------------------------------------------------------------------------')
    transaction = CallTransactionBuilder().from_(wallet.get_address()).to(contracts[dest]['SCORE']).value(
        value).step_limit(10000000).nid(NID).nonce(100).method(method).params(params).build()
    signed_transaction = SignedTransaction(transaction, wallet)
    tx_hash = icon_service.send_transaction(signed_transaction)

    res = get_tx_result(tx_hash)
    if _print:
        print(
            f'************************************************** Status: {res["status"]} **************************************************')
    # if len(res["eventLogs"]) > 0:
    #     for item in res["eventLogs"]:
    #         print(f'{item} \n')
    if res['status'] == 0:
        if _print:
            print(f'Failure: {res["failure"]}')
    return res


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
# print(config_results)

# Launch Balanced
# We may want to make this a payable method and have the governance SCORE borrow bnUSD,
# start and name the sICXbnUSD market, and add it as a rewards DataSource.

launch_results = launch_balanced(btest_wallet, staking_wallet)
# print(launch_results)


def update():
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


def test_getBalnHolding():
    for i in range(10):
        fast_send_tx('rewards', 0, 'distribute', {}, btest_wallet)

    borrowerCount = int(call_tx('loans', 'borrowerCount', {}, False), 0)
    addresses = []
    daily_value = {}
    for i in range(1, borrowerCount + 1):
        position = call_tx('loans', 'getPositionByIndex', {'_index': i, '_day': -1}, False)
        addresses.append(position['address'])

    holders = call_tx('rewards', 'getBalnHoldings', {'_holders': addresses}, False)

    total_balances = 0
    baln_balances = {}
    for contract in ['rewards', 'reserve', 'bwt', 'dex', 'daofund']:
        result = int(call_tx('baln', 'balanceOf', {'_owner': contracts[contract]['SCORE']}, False), 0)
        baln_balances[contract] = result / 10 ** 18
        total_balances += result

    i = 0
    holdings = {i: [key, int(holders[key], 0), int(holders[key], 0) / 10 ** 18] for i, key in enumerate(holders.keys())}
    total = 0
    for key in holdings:
        total += holdings[key][1]
        print(f'{holdings[key]}')

    print(f'Total unclaimed: {total / 10 ** 18}')
    print(baln_balances)
    print(f'Total BALN: {total_balances / 10 ** 18}')

    res = call_tx('rewards', 'distStatus', {}, False)
    day = int(res['platform_day'], 0) - 1

    #     total_amount = 25000/borrowerCount
    #     for key in holdings:
    #         assert holdings[key][2] == total_amount , "Loans borrowers token distribution error"
    assert baln_balances['rewards'] == 35000 * day, "Loans borrowers token distribution error"
    assert baln_balances['reserve'] == 5000 * day, "Reserve not receiving proper rewards"
    assert baln_balances['bwt'] == 20000 * day, "Worker token distribution error"
    assert baln_balances['daofund'] == 40000 * day, "DAO Fund token distribution error"

    print("Test case passed")


def test_getDataSourceNames():
    print('Testing getDataSourceNames method')
    res = call_tx('rewards', 'getDataSourceNames', {}, False)
    assert res == ['Loans', 'sICX/ICX'], "Data source name error"
    print('Test case passed')


def test_getRecipients():
    print('Testing getRecipients method')
    res = call_tx('rewards', 'getRecipients', {}, False)
    assert res == ['Worker Tokens', 'Reserve Fund', 'DAOfund', 'Loans', 'sICX/ICX'], "Recipients name error"
    print('Test case passed')


def test_getRecipientsSplit():
    print('Testing getRecipientsSplit method')
    res = call_tx('rewards', 'getRecipientsSplit', {}, False)
    assert res == {'Worker Tokens': '0x2c68af0bb140000',
                   'Reserve Fund': '0xb1a2bc2ec50000',
                   'DAOfund': '0x58d15e176280000',
                   'Loans': '0x3782dace9d90000',
                   'sICX/ICX': '0x16345785d8a0000'}, "Recipients name error"

    print('Test case passed')


def test_getDataSources():
    print('Testing getDataSources method')
    res = call_tx('rewards', 'getDataSources', {}, False)
    assert int(res['Loans']['dist_percent'], 0) == 250000000000000000, 'Loans distribution precent error'
    assert int(res['sICX/ICX']['dist_percent'], 0) == 100000000000000000, 'sICX/ICX distribution precent error'

    print('Test case passed')


def test_getSourceData():
    cases = test_cases['stories']
    for case in cases:
        print(case['description'])
        _name = case['name']

        if _name == 'Loans':
            contract = contracts['loans']['SCORE']
        elif _name == 'sICX/ICX':
            contract = contracts['dex']['SCORE']
        else:
            contract = None

        res = call_tx('rewards', 'getSourceData', {'_name': _name}, False)
        assert res['contract_address'] == contract, 'Test case failed for ' + _name
        print('Test case passed')


def test_claimRewards():
    claiming_addresses = {
        "stories": [
            {
                "claiming_wallet": btest_wallet,

            },
            {
                "claiming_wallet": user1,
            },
        ]
    }
    for case in claiming_addresses['stories']:
        send_tx('rewards', 0, 'claimRewards', {}, case['claiming_wallet'])
        res = call_tx('rewards', 'getBalnHolding', {'_holder': case['claiming_wallet'].get_address()}, False)
        assert int(res, 0) == 0, 'Rewards claiming issue'
        print('Test case passed while claiming rewards')


test_getSourceData()
test_getRecipients()
test_getDataSources()
test_getRecipientsSplit()
test_getDataSourceNames()

# Test case 1 with one borrower
send_tx('loans', 500 * ICX, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 50 * ICX}, btest_wallet)
time.sleep(40)
test_getBalnHolding()

# Test case 2 with two borrowers
send_tx('loans', 500 * ICX, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 50 * ICX}, user1)
time.sleep(20)
test_getBalnHolding()

# claim rewards
test_claimRewards()
