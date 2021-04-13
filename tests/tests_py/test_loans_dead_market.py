#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Cell 0

network = "custom"  # set this to one of mainnet, yeouido, euljiro, pagoda, or custom

connections = {
"mainnet": {"iconservice": "https://ctz.solidwallet.io",       "nid": 1},
"yeouido": {"iconservice": "https://bicon.net.solidwallet.io", "nid": 3},
"euljiro": {"iconservice": "https://test-ctz.solidwallet.io",  "nid": 2},
"pagoda":  {"iconservice": "https://zicon.net.solidwallet.io", "nid":80},
"custom":  {"iconservice": "http://18.144.108.38:9000",        "nid": 3}}

env = connections[network]


# In[ ]:


# Cell 1

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


# In[ ]:


# Cell 2

icon_service = IconService(HTTPProvider(env["iconservice"], 3))
NID = env["nid"]


# In[ ]:


# Cell 3

wallet = KeyWallet.load("keystores/keystore_test1.json", "test1_Account")
# Balanced test wallet
with open("keystores/balanced_test.pwd", "r") as f:
    key_data = f.read()
btest_wallet = KeyWallet.load("keystores/balanced_test.json", key_data)
print(icon_service.get_balance(wallet.get_address())/10**18)
print(icon_service.get_balance(btest_wallet.get_address())/10**18)


# In[ ]:


print(wallet.get_address())
print(icon_service.get_balance(wallet.get_address()) / 10**18)


# In[ ]:


print(btest_wallet.get_address())
print(icon_service.get_balance(btest_wallet.get_address()) / 10**18)


# In[ ]:


user1 = KeyWallet.load("keystores/user1.json","HelloWorld@1234")
# btest_wallet = KeyWallet.load("./balanced_test.json","HelloWorld@1234")

print(icon_service.get_balance(user1.get_address())/10**18)
print(user1.get_address())

# test2 = hx7a1824129a8fe803e45a3aae1c0e060399546187
private = "0a354424b20a7e3c55c43808d607bddfac85d033e63d7d093cb9f0a26c4ee022"
user2 = KeyWallet.load(bytes.fromhex(private))
print(icon_service.get_balance(user2.get_address())/10**18)
print(user2.get_address())


# In[ ]:


# Cell 4
# Only necessary if running locally or on the private tbears server
# for the first time since reinitializing.

transaction = TransactionBuilder()    .from_(wallet.get_address())    .to(user1.get_address())    .value(1000000 * ICX)    .step_limit(1000000)     .nid(NID)     .nonce(2)     .version(3)     .build()
signed_transaction = SignedTransaction(transaction, wallet)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash


# In[ ]:


# The following addresses are those deployed to the private tbears server.

contracts = {'loans': {'zip': 'core_contracts/loans.zip', 'SCORE': 'cx55f2ab7a026bd070d117233f32fbc614bd904a20'}, 'staking': {'zip': 'core_contracts/staking.zip', 'SCORE': 'cxd0c708c7c7c2ed97b10bc0a1772f7036d351a5c5'}, 'dividends': {'zip': 'core_contracts/dividends.zip', 'SCORE': 'cx3d1fa0db471e68dc5df110455660a1c476e46eec'}, 'reserve': {'zip': 'core_contracts/reserve.zip', 'SCORE': 'cx8d447de699e8c40bafe0fd35d498cd3c58c99425'}, 'daofund': {'zip': 'core_contracts/daofund.zip', 'SCORE': 'cxfd51e9df2e7a10df873009a2a6bf80c13a0508af'}, 'rewards': {'zip': 'core_contracts/rewards.zip', 'SCORE': 'cx5c3c476f9a097589d7108fe2e9b71ada7161ad78'}, 'dex': {'zip': 'core_contracts/dex.zip', 'SCORE': 'cxd9f12ee8e9a3d0774e929b3118c568555a419385'}, 'governance': {'zip': 'core_contracts/governance.zip', 'SCORE': 'cx5c0170c8a2059a8678e65297fd4188b3de631b74'}, 'oracle': {'zip': 'core_contracts/oracle.zip', 'SCORE': 'cx7171e2f5653c1b9c000e24228276b8d24e84f10d'}, 'sicx': {'zip': 'token_contracts/sicx.zip', 'SCORE': 'cx51b3add2ab11c541b628fd8eca22dd362b11f54c'}, 'bnUSD': {'zip': 'token_contracts/bnUSD.zip', 'SCORE': 'cx228a83c7dabe2a34424de5d963944b1a1e55d09e'}, 'baln': {'zip': 'token_contracts/baln.zip', 'SCORE': 'cxcacc2eef044822a9f000a1566f3585fe26f35af2'}, 'bwt': {'zip': 'token_contracts/bwt.zip', 'SCORE': 'cx2c79be5145135b056d49990ed3259adfb4acef75'}}


# In[ ]:


# Cell 6
# Define deploy and send_tx functions

def compress():
    """
    Compress all SCORE folders in the core_contracts and toekn_contracts folders
    """
    deploy = list(contracts.keys())[:]
    for directory in {"core_contracts", "token_contracts"}:
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

    txns = [{'contract': 'staking', 'value': 0, 'method': 'setSicxAddress', 'params': {'_address': contracts['sicx']['SCORE']}},
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
    print('------------------------------------------------------------------------------------------------------------------')
    print(f'Reading {method}, with parameters {params} on the {dest} contract.')
    print('------------------------------------------------------------------------------------------------------------------')
    call = CallBuilder()        .from_(wallet.get_address())        .to(contracts[dest]['SCORE'])        .method(method)        .params(params)        .build()
    result = icon_service.call(call)
    print(result)
    return result


# In[ ]:


# Cell 7
# Deploy and configure Balanced. Print results if anything goes wrong.

results = {}
deploy_all(btest_wallet)
print('------------------------------------------------------------------------------------------------------------------')
print(contracts)
print(get_scores_json(contracts))


# In[ ]:


# Cell 8
# Deploy or Update a single SCORE

compress()
update = 0
contract = contracts['reserve']
params = {}
params = {'_governance': contracts['governance']['SCORE']}
deploy_SCORE(contract, params, btest_wallet, update)


# In[ ]:


# 1.Add 500icx collateral and mint 50 bnusd of loans from account user2.
# 2.call add_test_position method and add bnusd until account is in dead market state from account user1.
# 3.after this the asset bnusd will be dead

send_tx('loans', 2500 * ICX , 'addCollateral', {'_asset': 'bnUSD', '_amount': 50 * ICX}, user2)
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})
# send_tx('loans', 500 * ICX , 'addCollateral', {'_asset': '', '_amount': 0}, user1)
# send_tx('loans', 0, 'toggleTestMode', {}, btest_wallet)
# send_tx('loans', 600, 'create_test_position', {'_address': user1.get_address(), '_asset': 'bnUSD', '_amount': 1000 * ICX}, user1)
# call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})


# In[ ]:


# call_tx('loans', 'checkDebts', {})
# send_tx('loans', 0, 'add_bad_test_position', {}, user1)
call_tx('loans', 'checkDebts', {})
send_tx('loans', 0, 'liquidate', {'_owner': user1.get_address()}, user1)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'checkDebts', {})


# In[ ]:


# send_tx('loans', 500 * ICX , 'addCollateral', {'_asset': 'bnUSD', '_amount': 50 * ICX}, btest_wallet)
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})


# In[ ]:


transaction = CallTransactionBuilder()    .from_(btest_wallet.get_address())    .to(contracts['governance']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("setMarketName")    .params({'_pid':3, '_name': 'BALNbnUSD'})     .build()
signed_transaction = SignedTransaction(transaction, btest_wallet)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')
print('\n')

call = CallBuilder().from_(wallet.get_address())                    .to(contracts['dex']['SCORE'])                    .method('getNamedPools')                    .build()
result = icon_service.call(call)
print(result)


# In[ ]:


# Cell 44

transaction = CallTransactionBuilder()    .from_(btest_wallet.get_address())    .to(contracts['governance']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("setMarketName")    .params({'_pid':3, '_name': 'BALNbnUSD'})     .build()
signed_transaction = SignedTransaction(transaction, btest_wallet)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')
print('\n')

call = CallBuilder().from_(wallet.get_address())                    .to(contracts['dex']['SCORE'])                    .method('getNamedPools')                    .build()
result = icon_service.call(call)
print(result)


# In[ ]:


# Cell 13
# 1. Check that there is a Dead Market
# 2. Check the bad debt, liquidation pool and dead_market state of the asset.
# 3. Retire enough of the bad debt to get the asset out of the dead_market state.
# 4. Again, check the bad debt, liquidation pool and dead_market state of the asset.

call_tx('loans', 'checkDeadMarkets', {})
call_tx('loans', 'getAvailableAssets', {})
send_tx('bnUSD', 0, 'transfer', {'_to': contracts['loans']['SCORE'], '_value': 50 * ICX, '_data': json.dumps({"method": "_retire_asset", "params": {}}).encode()}, btest_wallet)
call_tx('loans', 'getAvailableAssets', {})


# In[ ]:


#  Now we try to revive the dead market
# 1. Test with retiring less than enough to revive the market with bad_debt 550.25 bnusd 
# i.e user2 retires 100 bnusd

test_cases =  { 
    
    "stories": [ {
      "description": "btest_wallet retire 1000 bnusd",
      "actions": {
          "sender":"user2",
          "first_meth": "transfer",
          "second_meth":"transfer",
          "deposited_icx":"0",
          "first_params":{'_to': btest_wallet.get_address(), '_value': 1000 * ICX},
          "second_params":{"method": "_retire_asset", "params": {},'_to': contracts['loans']['SCORE'], '_value': 1000 * ICX},
          "expected_bnusd_wallet":"20700000000000000000"
          
      }
    },
        {
            "description": "btest_wallet retire 100 bnusd",
              "actions": {
                  "sender":"user2",
                  "first_meth": "transfer",
                  "second_meth":"transfer",
                  "deposited_icx":"0",
                  "first_params":{'_to': btest_wallet.get_address(), '_value': 100 *ICX},
                  "second_params":{"method": "_retire_asset", "params": {},'_to': contracts['loans']['SCORE'], '_value': 100 * ICX},
                  "expected_bnusd_wallet":"20700000000000000000"

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


    transaction = CallTransactionBuilder()        .from_(user2.get_address())        .to(_to)        .value(val)        .step_limit(10000000)        .nid(NID)        .nonce(100)        .method(meth1)        .params(first_params)        .build()
    signed_transaction = SignedTransaction(transaction, user2)
    tx_hash = icon_service.send_transaction(signed_transaction)
    sleep(2)

    transaction = CallTransactionBuilder()        .from_(btest_wallet.get_address())        .to(_to)        .value(val)        .step_limit(10000000)        .nid(NID)        .nonce(100)        .method(meth2)        .params(second_params)        .build()
    signed_transaction = SignedTransaction(transaction, btest_wallet)
    tx_hash = icon_service.send_transaction(signed_transaction)
    sleep(1)

    res = get_tx_result(tx_hash)
    print(f'Status: {res["status"]}')
    if len(res["eventLogs"]) > 0:
        for item in res["eventLogs"]:
            print(f'{item} \n')
    if res['status'] == 0:
        print(f'Failure: {res["failure"]}')
    
    tes= call_tx('loans', 'checkDebts', {})
    if tes['system']['bad_debt'] != hex(0):
        print("Market still dead")
    else:
        print("Market revived")
    


# In[ ]:


# call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})

send_tx('staking',  800*ICX, 'stakeICX', {'_to':contracts['reserve']['SCORE']}, user1)

# send_tx('loans', 500 * ICX , 'addCollateral', {'_asset': 'bnUSD', '_amount': 50 * ICX}, btest_wallet)


# In[ ]:


# send_tx('loans',  0, 'updateStanding', {'_owner':user2.get_address()}, user2)
# send_tx('rewards',  0, 'claimRewards', {}, user2)
# call_tx('rewards','getBalnHoldings', {'_holders': [user1.get_address(),contracts['reserve']['SCORE']]})
call_tx('baln', 'availableBalanceOf', {'_owner': user2.get_address()})
# call_tx('rewards', 'getRecipientsSplit', {})
res =call_tx('baln', 'totalSupply', {})
int(res, 0) /10**18


# In[ ]:





# In[ ]:


for _ in range(100):
    params = {'_index': 1}
    call = CallBuilder().from_(wallet.get_address())                        .to(contracts['loans']['SCORE'])                        .method("getPositionAddress")                        .params(params)                        .build()
    params = {'_owner': icon_service.call(call)}
    transaction = CallTransactionBuilder()        .from_(user2.get_address())        .to(contracts['loans']['SCORE'])        .value(0)        .step_limit(10000000)        .nid(NID)        .nonce(100)        .method("updateStanding")        .params(params)        .build()
    signed_transaction = SignedTransaction(transaction, user2)
    tx_hash = icon_service.send_transaction(signed_transaction)

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Check BALN that has been distributed on the rewards SCORE, and to platform contract addresses.

params = {}
call = CallBuilder().from_(user2.get_address())                    .to(contracts['loans']['SCORE'])                    .method("borrowerCount")                    .params(params)                    .build()
borrowerCount = int(icon_service.call(call), 0)

addresses = []
for i in range(1, borrowerCount + 1):
    params = {'_index': i, '_day': -1}
    call = CallBuilder().from_(user2.get_address())                        .to(contracts['loans']['SCORE'])                        .method("getPositionByIndex")                        .params(params)                        .build()
    position = icon_service.call(call)
    addresses.append(position['address'])

params = {'_holders': addresses}
call = CallBuilder().from_(user2.get_address())                    .to(contracts['rewards']['SCORE'])                    .method("getBalnHoldings")                    .params(params)                    .build()
holders = icon_service.call(call)

total_balances = 0
baln_balances = {}
for contract in ['rewards', 'reserve', 'bwt']:
    params = {'_owner': contracts[contract]['SCORE']}
    call = CallBuilder().from_(user2.get_address())                        .to(contracts['baln']['SCORE'])                        .method("balanceOf")                        .params(params)                        .build()
    result = int(icon_service.call(call), 0)
    baln_balances[contract] = result / 10**18
    total_balances += result

i = 0
holdings = {i: [key, int(holders[key], 0), int(holders[key], 0) / 10**18] for i, key in enumerate(holders.keys())}
total = 0
for key in holdings:
    total += holdings[key][1]
    print(f'{holdings[key]}')

print(f'Total unclaimed: {total / 10**18}')
print(baln_balances)
print(f'Total BALN: {total_balances / 10**18}')

