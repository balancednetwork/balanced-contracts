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


contracts = {'loans': {'zip': 'core_contracts/loans.zip', 'SCORE': 'cx764463174b4f7d44988968f93c08081881fcfc85'}, 'staking': {'zip': 'core_contracts/staking.zip', 'SCORE': 'cx686423d2293831a6cb2441959112a1a06b7462ba'}, 'dividends': {'zip': 'core_contracts/dividends.zip', 'SCORE': 'cxa6f208b9b7fecd68e7cf66675ba058ef68c00ef6'}, 'reserve': {'zip': 'core_contracts/reserve.zip', 'SCORE': 'cxedf87c1cd6811891016606c403418cf967340a51'}, 'daofund': {'zip': 'core_contracts/daofund.zip', 'SCORE': 'cxadedc487277793fe7cd73ac4cdfdbc2fee02e0e1'}, 'rewards': {'zip': 'core_contracts/rewards.zip', 'SCORE': 'cxbbf173efedf4338d0562edf67f3f563cd6f09b18'}, 'dex': {'zip': 'core_contracts/dex.zip', 'SCORE': 'cx2d8cd99b2ed00a8ec519a00a9d42dd314e72a04b'}, 'governance': {'zip': 'core_contracts/governance.zip', 'SCORE': 'cxbdfe800a34762f3e65bdef1be4f3058b893d6fe5'}, 'oracle': {'zip': 'core_contracts/oracle.zip', 'SCORE': 'cx7171e2f5653c1b9c000e24228276b8d24e84f10d'}, 'sicx': {'zip': 'token_contracts/sicx.zip', 'SCORE': 'cxf99f4ca65fda1cdfa461f473d60f729341524022'}, 'bnUSD': {'zip': 'token_contracts/bnUSD.zip', 'SCORE': 'cx0f493f0d561d14576f3705ff422c32fe305b2e6a'}, 'baln': {'zip': 'token_contracts/baln.zip', 'SCORE': 'cxdf5d7067e425b3e1a2c96659b3fd91bd1b5dd0d9'}, 'bwt': {'zip': 'token_contracts/bwt.zip', 'SCORE': 'cxf2c45e05c329bd9c0dd7780b8f14a15a1eaa78ff'}}


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
    print(icon_service.call(call))
    return icon_service.call(call)


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
update = 1
contract = contracts['loans']
params = {}
# params = {'_governance': contracts['governance']['SCORE']}
deploy_SCORE(contract, params, btest_wallet, update)


# In[ ]:





# In[ ]:


# 1.no bad debt for asset, retired from account user2 without a position on Balanced.
call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()})
call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()})


# In[ ]:


call_tx('loans', 'getMaxRetireAmount', {'_symbol': 'bnUSD'})


# In[ ]:


send_tx('loans', 1000*ICX, 'addCollateral', {'_asset': 'bnUSD', '_amount': 500 * ICX}, user1)


# In[ ]:


#  Now we try to revive the dead market
# 1. Test with retiring less than enough to revive the market with bad_debt 550.25 bnusd 
# i.e user2 retires 100 bnusd

test_cases =  { 
    
    "stories": [ {
      "description": "User2 tres to retire 100 bnusd",
      "actions": {
          "sender":"user2",
          "first_meth": "transfer",
          "second_meth":"transfer",
          "deposited_icx":"0",
          "first_params":{'_to': user2.get_address(), '_value': 100 * ICX},
          "second_params":{"method": "_retire_asset", "params": {},'_to': contracts['loans']['SCORE'], '_value': 100 * ICX},
          "expected_bnusd_wallet":"20700000000000000000"
          
      }
    },
        {
            "description": "User2 tries to retire 10 bnusd",
              "actions": {
                  "sender":"user2",
                  "first_meth": "transfer",
                  "second_meth":"transfer",
                  "deposited_icx":"0",
                  "first_params":{'_to': user2.get_address(), '_value': call_tx('loans', 'getMaxRetireAmount', {'_symbol': 'bnUSD'})},
                  "second_params":{"method": "_retire_asset", "params": {},'_to': contracts['loans']['SCORE'], '_value': call_tx('loans', 'getMaxRetireAmount', {'_symbol': 'bnUSD'})},
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

    send_tx('bnUSD', 0 ,meth1 , first_params, user1)
    sleep(2)
    res = send_tx('bnUSD', 0 ,meth2 , second_params, user2)
    assert res['status'] == 1 , 'Retired amount is greater than the current maximum allowed'
#     if res['status'] == 0:
#         print('Retired amount is greater than the current maximum allowed.')
#     else:
#         print('Test Success')

