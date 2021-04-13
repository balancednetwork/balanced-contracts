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

# =====================NETWORKS======================================
network = "custom"  # set this to one of mainnet, yeouido, euljiro, pagoda, or custom

connections = {
    "mainnet": {"iconservice": "https://ctz.solidwallet.io", "nid": 1},
    "yeouido": {"iconservice": "https://bicon.net.solidwallet.io", "nid": 3},
    "euljiro": {"iconservice": "https://test-ctz.solidwallet.io", "nid": 2},
    "pagoda": {"iconservice": "https://zicon.net.solidwallet.io", "nid": 80},
    "custom": {"iconservice": "http://18.144.108.38:9000", "nid": 3}}

env = connections[network]

# =====================NETWORKS======================================


ICX = 1000000000000000000  # 10**18
GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
ORACLE = "cx61a36e5d10412e03c907a507d1e8c6c3856d9964"

icon_service = IconService(HTTPProvider(env["iconservice"], 3))
NID = env["nid"]


@retry(JSONRPCException, tries=10, delay=1, back_off=2)
def get_tx_result(_tx_hash):
    tx_result = icon_service.get_transaction_result(_tx_hash)
    return tx_result


# ========================== LOAD WALLETS ==========================
wallet = KeyWallet.load("../../keystores/keystore_test1.json", "test1_Account")
# Balanced test wallet
with open("../../keystores/balanced_test.pwd", "r") as f:
    key_data = f.read()
btest_wallet = KeyWallet.load("../../keystores/balanced_test.json", key_data)
print(icon_service.get_balance(wallet.get_address()) / 10 ** 18)
print(icon_service.get_balance(btest_wallet.get_address()) / 10 ** 18)
print(wallet.get_address())
print(icon_service.get_balance(wallet.get_address()) / 10 ** 18)

print(btest_wallet.get_address())
print(icon_service.get_balance(btest_wallet.get_address()) / 10 ** 18)

user1 = KeyWallet.load("../../keystores/user1.json", "HelloWorld@1234")
print(user1.get_address())
print(icon_service.get_balance(user1.get_address()) / 10 ** 18)

# test2 = hx7a1824129a8fe803e45a3aae1c0e060399546187
private = "0a354424b20a7e3c55c43808d607bddfac85d033e63d7d093cb9f0a26c4ee022"
user2 = KeyWallet.load(bytes.fromhex(private))
print(icon_service.get_balance(user2.get_address()) / 10 ** 18)
print(user2.get_address())

# ========================== LOAD WALLETS ==========================


# Cell 4
# Only necessary if running locally or on the private tbears server
# for the first time since reinitializing.

transaction = TransactionBuilder().from_(wallet.get_address()).to(user2.get_address()).value(10000 * ICX).step_limit(
    1000000).nid(NID).nonce(2).version(3).build()
signed_transaction = SignedTransaction(transaction, wallet)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

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
                        'SCORE': 'cx7171e2f5653c1b9c000e24228276b8d24e84f10d'},
             'sicx': {'zip': 'token_contracts/sicx.zip',
                      'SCORE': 'cxcff8bf80ab213fa9bbb350636a4d68f5cb4fd9c1'},
             'bnUSD': {'zip': 'token_contracts/bnUSD.zip',
                       'SCORE': 'cx4c1beaa71b9377100c810c46059ddf5f3da37602'},
             'baln': {'zip': 'token_contracts/baln.zip',
                      'SCORE': 'cx3825a86d52c5baf188ff29aa6a7fc2467e285885'},
             'bwt': {'zip': 'token_contracts/bwt.zip',
                     'SCORE': 'cx140b49ea041457ebc4cd5e199f5723916bb50021'}}

contracts = {'loans': {'zip': 'core_contracts/loans.zip', 'SCORE': 'cx764463174b4f7d44988968f93c08081881fcfc85'},
             'staking': {'zip': 'core_contracts/staking.zip', 'SCORE': 'cx686423d2293831a6cb2441959112a1a06b7462ba'},
             'dividends': {'zip': 'core_contracts/dividends.zip',
                           'SCORE': 'cxa6f208b9b7fecd68e7cf66675ba058ef68c00ef6'},
             'reserve': {'zip': 'core_contracts/reserve.zip', 'SCORE': 'cxedf87c1cd6811891016606c403418cf967340a51'},
             'daofund': {'zip': 'core_contracts/daofund.zip', 'SCORE': 'cxadedc487277793fe7cd73ac4cdfdbc2fee02e0e1'},
             'rewards': {'zip': 'core_contracts/rewards.zip', 'SCORE': 'cxbbf173efedf4338d0562edf67f3f563cd6f09b18'},
             'dex': {'zip': 'core_contracts/dex.zip', 'SCORE': 'cx2d8cd99b2ed00a8ec519a00a9d42dd314e72a04b'},
             'governance': {'zip': 'core_contracts/governance.zip',
                            'SCORE': 'cxbdfe800a34762f3e65bdef1be4f3058b893d6fe5'},
             'oracle': {'zip': 'core_contracts/oracle.zip', 'SCORE': 'cx7171e2f5653c1b9c000e24228276b8d24e84f10d'},
             'sicx': {'zip': 'token_contracts/sicx.zip', 'SCORE': 'cxf99f4ca65fda1cdfa461f473d60f729341524022'},
             'bnUSD': {'zip': 'token_contracts/bnUSD.zip', 'SCORE': 'cx0f493f0d561d14576f3705ff422c32fe305b2e6a'},
             'baln': {'zip': 'token_contracts/baln.zip', 'SCORE': 'cxdf5d7067e425b3e1a2c96659b3fd91bd1b5dd0d9'},
             'bwt': {'zip': 'token_contracts/bwt.zip', 'SCORE': 'cxf2c45e05c329bd9c0dd7780b8f14a15a1eaa78ff'}}


# # Deploy All Scores


# Cell 6
# Define deploy and send_tx functions

def compress():
    """
    Compress all SCORE folders in the core_contracts and token_contracts folders
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
    deploy_transaction = DeployTransactionBuilder().from_(wallet.get_address()).to(dest).nid(NID).nonce(
        100).content_type("application/zip").content(gen_deploy_data_content(zip_file)).params(params).build()

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
    print(
        f'************************************************** Status: {res["status"]} **************************************************')
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
            {'contract': 'governance', 'value': 0, 'method': 'setAddresses', 'params': {'_addresses': addresses}},
            {'contract': 'governance', 'value': 0, 'method': 'launchBalanced', 'params': {}}]

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
    print(
        '------------------------------------------------------------------------------------------------------------------')
    print(f'Reading {method}, with parameters {params} on the {dest} contract.')
    print(
        '------------------------------------------------------------------------------------------------------------------')
    call = CallBuilder().from_(wallet.get_address()).to(contracts[dest]['SCORE']).method(method).params(params).build()
    print(icon_service.call(call))
    return icon_service.call(call)


# Cell 7
# Deploy and configure Balanced. Print results if anything goes wrong.

results = {}
deploy_all(btest_wallet)
print(
    '------------------------------------------------------------------------------------------------------------------')
print(contracts)
print(get_scores_json(contracts))

# Update a score


# Cell 8
# Deploy or Update a single SCORE

compress()
update = 1
contract = contracts['loans']
params = {}
# params = {'_governance': contracts['governance']['SCORE']}
deploy_SCORE(contract, params, btest_wallet, update)

# Test getDebts method


# 1. Deposit collateral and mint loan from different accounts
# 2. call getDebts method on loans

send_tx('loans', 2500 * ICX, 'addCollateral', {'_asset': 'bnUSD', '_amount': 500 * ICX}, user1)
send_tx('loans', 2500 * ICX, 'addCollateral', {'_asset': 'bnUSD', '_amount': 1000 * ICX}, user2)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})

# call getDebts method
call_tx('loans', 'getDebts', {'_address_list': [user1.get_address(), user2.get_address()], '_day': 1})

# # Test Originate Loan


# Try originating loans with an account that doesn’t have a position in Balanced
call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()})
send_tx('loans', 0, 'originateLoan', {'_asset': 'bnUSD', '_amount': 50 * ICX}, btest_wallet)

# Try depositing 10 ICX and call originate loan of 50 bnUSD
call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()})
send_tx('loans', 10 * ICX, 'addCollateral', {'_asset': '', '_amount': 0}, btest_wallet)
send_tx('loans', 0, 'originateLoan', {'_asset': 'bnUSD', '_amount': 50 * ICX}, btest_wallet)

# Try depositing enough ICX to get a loan of 50 bnUSD and call originate loan of 50 bnUSD
call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()})
send_tx('loans', 250 * ICX, 'addCollateral', {'_asset': '', '_amount': 0}, btest_wallet)
send_tx('loans', 0, 'originateLoan', {'_asset': 'bnUSD', '_amount': 50 * ICX}, btest_wallet)
call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()})

call_tx('loans', 'getAccountPositions', {'_owner': wallet.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()})

# Trying to mint loan to account wallet from btest_wallet


send_tx('loans', 100 * ICX, 'addCollateral', {'_asset': '', '_amount': 0}, wallet)
send_tx('loans', 0, 'originateLoan', {'_asset': 'bnUSD', '_amount': 50 * ICX, '_from': wallet.get_address()},
        btest_wallet)
call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': wallet.get_address()})

# Try taking loan from user1 who has deposited 200 ICX and havent taken loan, calling from btest_wallet


# 1. Deposit only collateral to user1 wallet of 200 ICX
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
send_tx('loans', 200 * ICX, 'addCollateral', {'_asset': '', '_amount': 0}, user1)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
send_tx('loans', 0, 'originateLoan', {'_asset': 'bnUSD', '_amount': 50 * ICX, '_from': user1.get_address()},
        btest_wallet)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})

# # Retiring  an asset


# 1.no bad debt for asset, retired from account user2 without a position on Balanced.
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})

call_tx('loans', 'getMaxRetireAmount', {'_symbol': 'bnUSD'})

send_tx('loans', 1000 * ICX, 'addCollateral', {'_asset': 'bnUSD', '_amount': 500 * ICX}, user1)

# redeem 50 ICD from user2 that do not have position on Balanced. This will use up all
# of the liquidation pool and require some replay events to be recorded.


params = {'_to': user2.get_address(), '_value': 10 * ICX}
transaction = CallTransactionBuilder().from_(user1.get_address()).to(contracts['bnUSD']['SCORE']).value(0).step_limit(
    10000000).nid(NID).nonce(100).method("transfer").params(params).build()
signed_transaction = SignedTransaction(transaction, user1)
tx_hash = icon_service.send_transaction(signed_transaction)
sleep(2)
params = {"method": "_retire_asset", "params": {}}
data = json.dumps(params).encode("utf-8")
params = {'_to': contracts['loans']['SCORE'], '_value': 10 * ICX, '_data': data}
transaction = CallTransactionBuilder().from_(user2.get_address()).to(contracts['bnUSD']['SCORE']).value(0).step_limit(
    10000000).nid(NID).nonce(100).method("transfer").params(params).build()
signed_transaction = SignedTransaction(transaction, user2)
tx_hash = icon_service.send_transaction(signed_transaction)
sleep(1)

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')

call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})

# Gets the total number of borrowers in the system and iterates over them by index to update each one.

params = {}
call1 = CallBuilder().from_(wallet.get_address()).to(contracts['loans']['SCORE']).method("borrowerCount").params(
    params).build()
total_borrowers = int(icon_service.call(call1), 0)
for i in range(total_borrowers):
    params = {'_index': i + 1}
    call = CallBuilder().from_(wallet.get_address()).to(contracts['loans']['SCORE']).method(
        "getPositionAddress").params(params).build()
    params = {'_owner': icon_service.call(call)}
    transaction = CallTransactionBuilder().from_(wallet.get_address()).to(contracts['loans']['SCORE']).value(
        0).step_limit(10000000).nid(NID).nonce(100).method("updateStanding").params(params).build()
    signed_transaction = SignedTransaction(transaction, wallet)
    tx_hash = icon_service.send_transaction(signed_transaction)
    sleep(1)

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')

# 2. redeem 50 ICD from user1 that  have 50 bnUSD  on Balanced.
# a.deposite 800icx and mint 50 bnusd to both user1 and user2
# b.user2 tries to retire 50 bnusd(actual value of bnusd of user2 50.5 bnusd) 
send_tx('loans', 800 * ICX, 'addCollateral', {'_asset': 'bnUSD', '_amount': 50 * ICX}, user1)
send_tx('loans', 800 * ICX, 'addCollateral', {'_asset': 'bnUSD', '_amount': 50 * ICX}, user2)

call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})

# 2. redeem 50.5 bnusd from user1 that  have 50 bnUSD  on Balanced.


params = {'_to': user2.get_address(), '_value': 50500000000000000000}
transaction = CallTransactionBuilder().from_(user1.get_address()).to(contracts['bnUSD']['SCORE']).value(0).step_limit(
    10000000).nid(NID).nonce(100).method("transfer").params(params).build()
signed_transaction = SignedTransaction(transaction, user1)
tx_hash = icon_service.send_transaction(signed_transaction)
sleep(2)
params = {"method": "_retire_asset", "params": {}}
data = json.dumps(params).encode("utf-8")
params = {'_to': contracts['loans']['SCORE'], '_value': 50500000000000000000, '_data': data}
transaction = CallTransactionBuilder().from_(user2.get_address()).to(contracts['bnUSD']['SCORE']).value(0).step_limit(
    10000000).nid(NID).nonce(100).method("transfer").params(params).build()
signed_transaction = SignedTransaction(transaction, user2)
tx_hash = icon_service.send_transaction(signed_transaction)
sleep(1)

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')

# check the account position after retiring
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})

# 3.no bad debt for asset, retiring 50 bnUSD from account with a debt position > 50.
# a. user1 has  800 ICX and 50 bnusd loan 
# b.user2 has 800icx and 70 bnusd loan

call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})
send_tx('loans', 0, 'originateLoan', {'_asset': 'bnUSD', '_amount': 50 * ICX}, user2)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})

# c.user2 tries to retire 50 bnusd

test_cases = {

    "stories": [{
        "description": "User2 tres to retire 50 bnusd",
        "actions": {
            "sender": "user2",
            "first_meth": "transfer",
            "second_meth": "transfer",
            "deposited_icx": "0",
            "first_params": {'_to': user2.get_address(), '_value': 50 * ICX},
            "second_params": {"method": "_retire_asset", "params": {}, '_to': contracts['loans']['SCORE'],
                              '_value': 50 * ICX},
            "expected_bnusd_wallet": "20700000000000000000"

        }
    }

    ]
}

for case in test_cases['stories']:
    print(case['description'])
    if case['actions']['sender'] == 'user1':
        wallet_address = user1.get_address()
        wallet = user1
    else:
        wallet_address = user2.get_address()
        wallet = user2

    _to = contracts['bnUSD']['SCORE']
    meth1 = case['actions']['first_meth']
    meth2 = case['actions']['second_meth']
    val = int(case['actions']['deposited_icx'])
    data1 = case['actions']['first_params']
    first_params = {"_to": data1['_to'], "_value": data1['_value']}

    data2 = case['actions']['second_params']
    params = {"method": data2['method'], "params": data2['params']}
    data = json.dumps(params).encode("utf-8")
    second_params = {'_to': data2['_to'], '_value': data2['_value'], '_data': data}

    transaction = CallTransactionBuilder().from_(user1.get_address()).to(_to).value(val).step_limit(10000000).nid(
        NID).nonce(100).method(meth1).params(first_params).build()
    signed_transaction = SignedTransaction(transaction, user1)
    tx_hash = icon_service.send_transaction(signed_transaction)
    sleep(2)

    transaction = CallTransactionBuilder().from_(user2.get_address()).to(_to).value(val).step_limit(10000000).nid(
        NID).nonce(100).method(meth2).params(second_params).build()
    signed_transaction = SignedTransaction(transaction, user2)
    tx_hash = icon_service.send_transaction(signed_transaction)
    sleep(1)

    res = get_tx_result(tx_hash)
    print(f'Status: {res["status"]}')
    if len(res["eventLogs"]) > 0:
        for item in res["eventLogs"]:
            print(f'{item} \n')
    if res['status'] == 0:
        print(f'Failure: {res["failure"]}')

call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
res = call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})
print(res['assets']['bnUSD'])
if (res['assets']['bnUSD']) == hex(21200000000000000000):
    print('success')
else:
    print('fail')

# 4.Retiring 50 bnUSD, with bad_debt > 50 bnUSD for the asset, retired from account without a position on Balanced, liquidation pool > 1.1x the value of the retired asset.
# a. Liquidate an account with a bad_debt more than 50 bnusd

# Try liquidating an account user1

# 1. Deposit collateral to user1 wallet
# 2. Check the account standing after depositing collateral - Should be 'No Debt', and
#    holding '0x2a6f1a22364bbe8000' worth of sICX.
# 3a. Mints 200 ICD to the test address without checking collateralization ratio
#     With the above collateral deposit it will put the position in a standing of Liquidation.
# 4. Check the new standing of the account. Should have added '0xad78ebc5ac6200000' ICD and have standing of 'Liquidate'.

call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
send_tx('loans', 500 * ICX, 'addCollateral', {'_asset': '', '_amount': 0}, user1)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
send_tx('loans', 0, 'add_bad_test_position', {}, user1)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
send_tx('loans', 0, 'add_bad_test_position', {}, user1)
send_tx('loans', 0, 'add_bad_test_position', {}, user1)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})

# 5. Liquidate the account position.
# 6. Check the standing of the account after liquidation. Should now have zero balance for sICX and ICD.
# 7. Checking the debts should show the sum of the borrower debt and the bad debt equals the total supply.

call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
send_tx('loans', 0, 'liquidate', {'_owner': user1.get_address()}, user1)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'checkDebts', {})

# 8. after liquidating we have a bad_debt of 600 bnusd and supply of 600 bnusd.Now, we retire 50 bnusd from user2
#   that doesn't have position on balanced.


params = {'_to': user2.get_address(), '_value': 50 * ICX}
transaction = CallTransactionBuilder().from_(user1.get_address()).to(contracts['bnUSD']['SCORE']).value(0).step_limit(
    10000000).nid(NID).nonce(100).method("transfer").params(params).build()
signed_transaction = SignedTransaction(transaction, user1)
tx_hash = icon_service.send_transaction(signed_transaction)
sleep(2)
params = {"method": "_retire_asset", "params": {}}
data = json.dumps(params).encode("utf-8")
params = {'_to': contracts['loans']['SCORE'], '_value': 50 * ICX, '_data': data}
transaction = CallTransactionBuilder().from_(user2.get_address()).to(contracts['bnUSD']['SCORE']).value(0).step_limit(
    10000000).nid(NID).nonce(100).method("transfer").params(params).build()
signed_transaction = SignedTransaction(transaction, user2)
tx_hash = icon_service.send_transaction(signed_transaction)
sleep(1)

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')

call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})
call_tx('loans', 'checkDebts', {})

# Testing dead market


# 1.Try originating loan from the market which is dead, the transaction fails.
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
send_tx('loans', 0, 'originateLoan', {'_asset': 'bnUSD', '_amount': 50 * ICX}, user1)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})

#  Now we try to revive the dead market
# 1. Test with retiring less than enough to revive the market with bad_debt 550.25 bnusd 
# i.e user2 retires 100 bnusd

test_cases = {

    "stories": [{
        "description": "User2 tres to retire 100 bnusd",
        "actions": {
            "sender": "user2",
            "first_meth": "transfer",
            "second_meth": "transfer",
            "deposited_icx": "0",
            "first_params": {'_to': user2.get_address(), '_value': 100 * ICX},
            "second_params": {"method": "_retire_asset", "params": {}, '_to': contracts['loans']['SCORE'],
                              '_value': 100 * ICX},
            "expected_bnusd_wallet": "20700000000000000000"

        }
    },
        {
            "description": "User2 tries to retire 100 bnusd",
            "actions": {
                "sender": "user2",
                "first_meth": "transfer",
                "second_meth": "transfer",
                "deposited_icx": "0",
                "first_params": {'_to': user2.get_address(), '_value': 251750000000000000000},
                "second_params": {"method": "_retire_asset", "params": {}, '_to': contracts['loans']['SCORE'],
                                  '_value': 251250000000000000000},
                "expected_bnusd_wallet": "20700000000000000000"

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
    params = {"method": data2['method'], "params": data2['params']}
    data = json.dumps(params).encode("utf-8")
    second_params = {'_to': data2['_to'], '_value': data2['_value'], '_data': data}

    transaction = CallTransactionBuilder().from_(user1.get_address()).to(_to).value(val).step_limit(10000000).nid(
        NID).nonce(100).method(meth1).params(first_params).build()
    signed_transaction = SignedTransaction(transaction, user1)
    tx_hash = icon_service.send_transaction(signed_transaction)
    sleep(2)

    transaction = CallTransactionBuilder().from_(user2.get_address()).to(_to).value(val).step_limit(10000000).nid(
        NID).nonce(100).method(meth2).params(second_params).build()
    signed_transaction = SignedTransaction(transaction, user2)
    tx_hash = icon_service.send_transaction(signed_transaction)
    sleep(1)

    res = get_tx_result(tx_hash)
    print(f'Status: {res["status"]}')
    if len(res["eventLogs"]) > 0:
        for item in res["eventLogs"]:
            print(f'{item} \n')
    if res['status'] == 0:
        print(f'Failure: {res["failure"]}')

    tes = call_tx('loans', 'checkDebts', {})
    if tes['system']['bad_debt'] != hex(0):
        print("Market still dead")
    else:
        print("Market revived")

call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
send_tx('loans', 800 * ICX, 'addCollateral', {'_asset': '', '_amount': 0}, user1)
send_tx('loans', 0, 'originateLoan', {'_asset': 'bnUSD', '_amount': 50 * ICX}, user1)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})

call_tx('loans', 'checkDebts', {})
