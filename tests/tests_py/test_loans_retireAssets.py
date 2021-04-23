
network = "custom"  # set this to one of mainnet, yeouido, euljiro, pagoda, or custom

connections = {
"mainnet": {"iconservice": "https://ctz.solidwallet.io",       "nid": 1},
"yeouido": {"iconservice": "https://bicon.net.solidwallet.io", "nid": 3},
"euljiro": {"iconservice": "https://test-ctz.solidwallet.io",  "nid": 2},
"pagoda":  {"iconservice": "https://zicon.net.solidwallet.io", "nid":80},
"custom":  {"iconservice": "http://18.144.108.38:9000",        "nid": 3}}

env = connections[network]


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

ICX = 1000000000000000000 # 10**18
GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
ORACLE = "cx61a36e5d10412e03c907a507d1e8c6c3856d9964"

@retry(JSONRPCException, tries=10, delay=1, back_off=2)
def get_tx_result(_tx_hash):
    tx_result = icon_service.get_transaction_result(_tx_hash)
    return tx_result


icon_service = IconService(HTTPProvider(env["iconservice"], 3))
NID = env["nid"]


wallet = KeyWallet.load("../../keystores/keystore_test1.json", "test1_Account")
# Balanced test wallet
with open("../../keystores/balanced_test.pwd", "r") as f:
    key_data = f.read()
btest_wallet = KeyWallet.load("../../keystores/balanced_test.json", key_data)

print(wallet.get_address())
print(icon_service.get_balance(wallet.get_address()) / 10**18)

print(btest_wallet.get_address())
print(icon_service.get_balance(btest_wallet.get_address()) / 10**18)

user1 = KeyWallet.load("../../keystores/user1.json","HelloWorld@1234")
# btest_wallet = KeyWallet.load("./balanced_test.json","HelloWorld@1234")

print(icon_service.get_balance(user1.get_address())/10**18)
print(user1.get_address())

# test2 = hx7a1824129a8fe803e45a3aae1c0e060399546187
private = "0a354424b20a7e3c55c43808d607bddfac85d033e63d7d093cb9f0a26c4ee022"
user2 = KeyWallet.load(bytes.fromhex(private))
print(icon_service.get_balance(user2.get_address())/10**18)
print(user2.get_address())

print("/==============================================="
              " ......Testing retire_assets method......./"
              "=================================================")

# The following addresses are those deployed to the private tbears server.

contracts = {'loans': {'zip': 'core_contracts/loans.zip',
  'SCORE': 'cxbbd36ca8d91aefbe1060c3be62fed4d1b848ca85'},
 'staking': {'zip': 'core_contracts/staking.zip',
  'SCORE': 'cxd8e05c1280bc2c32bf53ff61f3bb2e2ecc7d6df5'},
 'dividends': {'zip': 'core_contracts/dividends.zip',
  'SCORE': 'cx7c617e3fca4ba06b6ad203ce113245ae96a9d91e'},
 'reserve': {'zip': 'core_contracts/reserve.zip',
  'SCORE': 'cx70cd5c86f0182d5ac0bd224562d929cd968d9132'},
 'daofund': {'zip': 'core_contracts/daofund.zip',
  'SCORE': 'cxeb91bc377b0620356787d9c9eb68152eb0c62d8a'},
 'rewards': {'zip': 'core_contracts/rewards.zip',
  'SCORE': 'cxfd7511ece084744154fed19dc34732681ad078e6'},
 'dex': {'zip': 'core_contracts/dex.zip',
  'SCORE': 'cx9a3161c778eee2d5758371d3548c5599f76704ec'},
 'governance': {'zip': 'core_contracts/governance.zip',
  'SCORE': 'cx238cd1a1e3a9702d6c9c6dc130719472164db376'},
 'oracle': {'zip': 'core_contracts/oracle.zip',
  'SCORE': 'cx2780eeb8c800ac9886786baae281c3d23bb832fc'},
 'sicx': {'zip': 'token_contracts/sicx.zip',
  'SCORE': 'cxcff8bf80ab213fa9bbb350636a4d68f5cb4fd9c1'},
 'bnUSD': {'zip': 'token_contracts/bnUSD.zip',
  'SCORE': 'cx4c1beaa71b9377100c810c46059ddf5f3da37602'},
 'baln': {'zip': 'token_contracts/baln.zip',
  'SCORE': 'cx3825a86d52c5baf188ff29aa6a7fc2467e285885'},
 'bwt': {'zip': 'token_contracts/bwt.zip',
  'SCORE': 'cx140b49ea041457ebc4cd5e199f5723916bb50021'}}

# Define deploy and send_tx functions


def compress():
    """
    Compress all SCORE folders in the core_contracts and toekn_contracts folders
    """
    deploy = list(contracts.keys())[:]
    for directory in {"../../core_contracts", "../../token_contracts"}:
        with os.scandir(directory) as it:
            for file in it:
                archive_name = directory + "/" + file.name
                if file.is_dir() and file.name in deploy:
                    make_archive(archive_name, "zip", directory, file.name)
                    contracts[file.name]['zip'] = archive_name + '.zip'


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
    deploy_transaction = DeployTransactionBuilder()        .from_(wallet.get_address())        .to(dest)        .nid(NID)        .nonce(100)        .content_type("application/zip")        .content(gen_deploy_data_content(zip_file))        .params(params)        .build()

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
    return res.get('scoreAddress', '')


def send_tx(dest, value, method, params, wallet):
    """
    dest is the name of the destination contract.
    """
    print('------------------------------------------------------------------------------------------------------------------')
    print(f'Calling {method}, with parameters {params} on the {dest} contract.')
    print('------------------------------------------------------------------------------------------------------------------')
    transaction = CallTransactionBuilder()        .from_(wallet.get_address())        .to(contracts[dest]['SCORE'])        .value(value)        .step_limit(10000000)        .nid(NID)        .nonce(100)        .method(method)        .params(params)        .build()
    signed_transaction = SignedTransaction(transaction, wallet)
    tx_hash = icon_service.send_transaction(signed_transaction)

    res = get_tx_result(tx_hash)
    print(f'************************************************** Status: {res["status"]} **************************************************')
    if len(res["eventLogs"]) > 0:
        for item in res["eventLogs"]:
            print(f'{item} \n')
    if res['status'] == 0:
        print(f'Failure: {res["failure"]}')
    return res


def deploy_all(wallet):
    """
    Compress, Deploy and Configure all SCOREs
    """
    compress()

    deploy = list(contracts.keys())[:]
    deploy.remove('oracle')
    deploy.remove('staking')
    deploy.remove('sicx')
    deploy.remove('governance')

    governance = deploy_SCORE(contracts['governance'], {}, wallet, 0)
    contracts['governance']['SCORE'] = governance
    for score in deploy:
        contracts[score]['SCORE'] = deploy_SCORE(contracts[score], {'_governance': governance}, wallet, 0)
    contracts['staking']['SCORE'] = deploy_SCORE(contracts['staking'], {}, wallet, 0)
    contracts['sicx']['SCORE'] = deploy_SCORE(contracts['sicx'], {'_admin': contracts['staking']['SCORE']}, wallet, 0)

    config = list(contracts.keys())[:]
    config.remove('governance')
    addresses = {contract: contracts[contract]['SCORE'] for contract in config}

    txns = [{'contract': 'staking', 'value': 0, 'method': 'setSicxAddress',
             'params': {'_address': contracts['sicx']['SCORE']}},
            {'contract': 'staking', 'value': 0, 'method': 'toggleStakingOn', 'params': {}},
            {'contract': 'governance', 'value': 0, 'method': 'setAddresses', 'params': {'_addresses': addresses}},
            {'contract': 'governance', 'value': 0, 'method': 'launchBalanced', 'params': {}},
            {'contract': 'governance', 'value': 0, 'method': 'balanceToggleStakingEnabled', 'params': {}}]

    for tx in txns:
        res = send_tx(tx["contract"], tx["value"], tx["method"], tx["params"], wallet)
        results[f'{tx["contract"]}|{tx["method"]}|{tx["params"]}'] = res


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
    print('------------------------------------------------------------------------------------------------------------------')
    print(f'Reading {method}, with parameters {params} on the {dest} contract.')
    print('------------------------------------------------------------------------------------------------------------------')
    call = CallBuilder()        .from_(wallet.get_address())        .to(contracts[dest]['SCORE'])        .method(method)        .params(params)        .build()
    print(icon_service.call(call))
    return icon_service.call(call)


# Deploy and configure Balanced. Print results if anything goes wrong.
results = {}
deploy_all(btest_wallet)
print('------------------------------------------------------------------------------------------------------------------')
print(contracts)
print(get_scores_json(contracts))

# Deploy or Update a single SCORE

compress()
update = 1
contract = contracts['loans']
params = {}
# params = {'_governance': contracts['governance']['SCORE']}
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
                    "second_params": {"_symbol": "bnUSD", '_value': 4 * ICX},
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
