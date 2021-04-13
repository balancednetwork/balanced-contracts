#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Cell 0

network = "yeouido"  # set this to one of mainnet, yeouido, euljiro, pagoda, or custom

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


# Cell 5
# The following addresses are those deployed to the testnet.

contracts = {'loans': {'zip': 'core_contracts/loans.zip',
  'SCORE': 'cx2594f06f668fa84804d94c1e5d4b378bfcf23b42'},
 'staking': {'zip': 'core_contracts/staking.zip',
  'SCORE': 'cx00093ced37e5c42b995c4df95fa0ce32290c9a36'},
 'dividends': {'zip': 'core_contracts/dividends.zip',
  'SCORE': 'cx39779100a6556ab3d161dfc95dab3839ac632c9a'},
 'reserve': {'zip': 'core_contracts/reserve.zip',
  'SCORE': 'cx6dd23ec8b6dc6f6c3dec784e200c097f842b8716'},
 'daofund': {'zip': 'core_contracts/daofund.zip',
  'SCORE': 'cxaa4593a3d37c12fe29bc7a9507b0a30593e66f65'},
 'rewards': {'zip': 'core_contracts/rewards.zip',
  'SCORE': 'cxdd1516deed20d0dca0b7ef8c19d2273c48406e86'},
 'dex': {'zip': 'core_contracts/dex.zip',
  'SCORE': 'cx774ddaf4e885782b56c2ddb1df8d8ce3f9ade09e'},
 'governance': {'zip': 'core_contracts/governance.zip',
  'SCORE': 'cx637d21599c04a4c93b390c7f9efb9e7c3a7fcfbb'},
 'oracle': {'zip': 'core_contracts/oracle.zip',
  'SCORE': 'cx61a36e5d10412e03c907a507d1e8c6c3856d9964'},
 'sicx': {'zip': 'token_contracts/sicx.zip',
  'SCORE': 'cx2e94568da72a0e4caf58d2baa1366476f05955ef'},
 'bnUSD': {'zip': 'token_contracts/bnUSD.zip',
  'SCORE': 'cx04afcd84c96ee03b30f6f88a60b2a1dee76c63fd'},
 'bnXLM': {'zip': 'token_contracts/bnXLM.zip',
  'SCORE': 'cx53098409b75594a73fb99badff2b34050a3090b6'},
 'bnDOGE': {'zip': 'token_contracts/bnDOGE.zip',
  'SCORE': 'cx82c8014c8eed1db391109fee2dd0ba11998cd3d2'},
 'baln': {'zip': 'token_contracts/baln.zip',
  'SCORE': 'cx66e56c4ed8a0e7da280867707dcd1ba9322d8c60'},
 'bwt': {'zip': 'token_contracts/bwt.zip',
  'SCORE': 'cx31bd70011e8ce26cb397ec017a339aabc7e7d049'}}


# In[ ]:


contracts = {'loans': {'zip': 'core_contracts/loans.zip', 'SCORE': 'cx936c3891a9fb3994017a5aec4bc177c3785f7cd1'}, 'staking': {'zip': 'core_contracts/staking.zip', 'SCORE': 'cxc586330cf2842983288789d4ee0907a1e211b1ab'}, 'dividends': {'zip': 'core_contracts/dividends.zip', 'SCORE': 'cx47200a38c304b595af42a16da1072a9c147e2584'}, 'reserve': {'zip': 'core_contracts/reserve.zip', 'SCORE': 'cxb2c91e1601f6f05fa080efda0aa53d948faef2c1'}, 'daofund': {'zip': 'core_contracts/daofund.zip', 'SCORE': 'cxa8472266ad01627af8395967e820c8aee58c4beb'}, 'rewards': {'zip': 'core_contracts/rewards.zip', 'SCORE': 'cx4a29d6d15acb6e4a1c6ad38c0742dd8fc9cc7286'}, 'dex': {'zip': 'core_contracts/dex.zip', 'SCORE': 'cx8b27346ec42e4f49ef18731d7f0d393876b0ceb7'}, 'governance': {'zip': 'core_contracts/governance.zip', 'SCORE': 'cx7f1d0edd9382fe80ddde3a80d6bc98808e0ae366'}, 'oracle': {'zip': 'core_contracts/oracle.zip', 'SCORE': 'cx61a36e5d10412e03c907a507d1e8c6c3856d9964'}, 'sicx': {'zip': 'token_contracts/sicx.zip', 'SCORE': 'cx2a64879449803a6a0c83828cbb8a45ee1674fa82'}, 'bnUSD': {'zip': 'token_contracts/bnUSD.zip', 'SCORE': 'cx384e06e3fe37ad7933d8bad35fd8835c643c17fd'}, 'bnXLM': {'zip': 'token_contracts/bnXLM.zip', 'SCORE': 'cxc9db156d46cb778692064752511a6a3b1c467557'}, 'bnDOGE': {'zip': 'token_contracts/bnDOGE.zip', 'SCORE': 'cx6a140794f90a3e02fa8bf6c3fe3084da2caa7ff8'}, 'baln': {'zip': 'token_contracts/baln.zip', 'SCORE': 'cxc2ab1a0fc9c4eb72530f6dacb74bf5cfc93b3022'}, 'bwt': {'zip': 'token_contracts/bwt.zip', 'SCORE': 'cxebab2e03164b95dedb1c0a0bf18bc581986fcac3'}}


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
    config.remove('bnDOGE')
    config.remove('bnXLM')
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
print('----------Contracts for Testing UI--------------------------------------------------------------------------------')
print(get_scores_json(contracts))


# In[ ]:


# Cell 8
# Deploy or Update a single SCORE

compress()
update = 1
contract = contracts['rewards']
params = {}
# params = {'_governance': contracts['governance']['SCORE']}
deploy_SCORE(contract, params, btest_wallet, update)


# In[ ]:


# Cell 10

call = CallBuilder().from_(wallet.get_address())                    .to(contracts['rewards']['SCORE'])                    .method('getRecipientsSplit')                    .params({})                     .build()
result = icon_service.call(call)
print(result)


# In[ ]:


contracts['dex']['SCORE']


# In[ ]:


# Cell 9
# transfer icx to dex

transaction = TransactionBuilder()    .from_(wallet.get_address())    .to(contracts['dex']['SCORE'])    .value(10 * ICX)    .step_limit(10000000)    .nid(NID)    .nonce(101)    .build()
signed_transaction = SignedTransaction(transaction, wallet)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 10

call = CallBuilder().from_(wallet.get_address())                    .to(contracts['dex']['SCORE'])                    .method('getICXBalance')                    .params({'_address': wallet.get_address()})                     .build()
result = icon_service.call(call)
int(result, 0) / 10**18


# # Creating OMM/sICX LP, OMM/IUSDC

# In[ ]:


# Cell 18a
# adding Second currency IUSDC in dex
transaction = CallTransactionBuilder()    .from_(btest_wallet.get_address())    .to(contracts['governance']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("dexAddQuoteCoin")    .params({'_address':'cx65f639254090820361da483df233f6d0e69af9b7'})     .build()
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


# In[ ]:


# Cell 18a
# adding Second currency USDB in dex
transaction = CallTransactionBuilder()    .from_(btest_wallet.get_address())    .to(contracts['governance']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("dexAddQuoteCoin")    .params({'_address':'cxaa068556df80f9917ef146e889f0b2c4b13ab634'})     .build()
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


# In[ ]:


# Cell 11
# transfer sicx to the wallet

params = {'_to': user1.get_address()}
transaction = CallTransactionBuilder()    .from_(wallet.get_address())    .to(contracts['staking']['SCORE'])    .value(100 * ICX)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("stakeICX")    .params(params)    .build()
signed_transaction = SignedTransaction(transaction, wallet)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 12
# check sicx balance

call = CallBuilder().from_(wallet.get_address())                    .to(contracts['sicx']['SCORE'])                    .method('balanceOf')                    .params({'_owner': user1.get_address()})                     .build()
result = icon_service.call(call)
int(result, 0) / 10**18


# In[ ]:


# Cell 13
# gives pools name

call = CallBuilder().from_(wallet.get_address())                    .to(contracts['dex']['SCORE'])                    .method('getNamedPools')                    .build()
result = icon_service.call(call)
print(result)


# In[ ]:


# Cell 14
# deposit sicx to the dex to create the pool

data = "{\"method\": \"_deposit\"}".encode("utf-8")
params = {'_to': contracts['dex']['SCORE'], '_value': 100 * ICX, '_data': data}
transaction = CallTransactionBuilder()    .from_(user1.get_address())    .to(contracts['sicx']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("transfer")    .params(params)    .build()
signed_transaction = SignedTransaction(transaction, user1)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 15
# get OMM balance for the wallet

call = CallBuilder().from_(wallet.get_address())                    .to('cx65f639254090820361da483df233f6d0e69af9b7')                    .method('balanceOf')                    .params({'_owner': wallet.get_address()})                     .build()
result = icon_service.call(call)
int(result, 0) / 10**6


# In[ ]:


# transfer iusdc to user1

# data = "{\"method\": \"_deposit\"}".encode("utf-8")
params = {'_to': user2.get_address(), '_value': 100 * 10**6}
transaction = CallTransactionBuilder()    .from_(wallet.get_address())    .to('cx65f639254090820361da483df233f6d0e69af9b7')    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("transfer")    .params(params)    .build()
signed_transaction = SignedTransaction(transaction, wallet)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 16a
# deposit ommtoken to dex to create a pool

data = "{\"method\": \"_deposit\"}".encode("utf-8")
params = {'_to': contracts['dex']['SCORE'], '_value': 50 * ICX, '_data': data}
transaction = CallTransactionBuilder()    .from_(user2.get_address())    .to('cx9f03e46d637fb0b1c7b539873c7f25db2ddc94e6')    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("transfer")    .params(params)    .build()
signed_transaction = SignedTransaction(transaction, user2)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 16b
# deposit iusdc to dex to create a pool

data = "{\"method\": \"_deposit\"}".encode("utf-8")
params = {'_to': contracts['dex']['SCORE'], '_value': 50 * 10**6, '_data': data}
transaction = CallTransactionBuilder()    .from_(user2.get_address())    .to('cx65f639254090820361da483df233f6d0e69af9b7')    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("transfer")    .params(params)    .build()
signed_transaction = SignedTransaction(transaction, user2)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 16c
# deposit usdb to dex to create a pool

data = "{\"method\": \"_deposit\"}".encode("utf-8")
params = {'_to': contracts['dex']['SCORE'], '_value': 50 * ICX, '_data': data}
transaction = CallTransactionBuilder()    .from_(wallet.get_address())    .to('cxaa068556df80f9917ef146e889f0b2c4b13ab634')    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("transfer")    .params(params)    .build()
signed_transaction = SignedTransaction(transaction, wallet)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)

print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 17a
# add base and quote token addresses for the paris that we want to create a pool of omm/sicx.

transaction = CallTransactionBuilder()    .from_(user2.get_address())    .to(contracts['dex']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("add")    .params({'_baseToken':'cx9f03e46d637fb0b1c7b539873c7f25db2ddc94e6' , '_quoteToken': contracts['sicx']['SCORE'], '_maxBaseValue': 15 * ICX, '_quoteValue': 1 * ICX})     .build()
signed_transaction = SignedTransaction(transaction, user2)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 17b
# add base and quote token addresses for the paris that we want to create a pool of omm/iusdc.

transaction = CallTransactionBuilder()    .from_(user2.get_address())    .to(contracts['dex']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("add")    .params({'_baseToken':'cx9f03e46d637fb0b1c7b539873c7f25db2ddc94e6' , '_quoteToken': 'cx65f639254090820361da483df233f6d0e69af9b7', '_maxBaseValue': 15 * ICX, '_quoteValue': 1 * 10**6})     .build()
signed_transaction = SignedTransaction(transaction, user2)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 17c
# add base and quote token addresses for the paris that we want to create a pool of omm/usdb.

transaction = CallTransactionBuilder()    .from_(user2.get_address())    .to(contracts['dex']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("add")    .params({'_baseToken':'cx9f03e46d637fb0b1c7b539873c7f25db2ddc94e6' , '_quoteToken': 'cxaa068556df80f9917ef146e889f0b2c4b13ab634', '_maxBaseValue': 15 * ICX, '_quoteValue': 1 * ICX})     .build()
signed_transaction = SignedTransaction(transaction, user2)
tx_hash = icon_service.send_transaction(signed_transaction)
tx_hash

res = get_tx_result(tx_hash)
print(f'Status: {res["status"]}')
if len(res["eventLogs"]) > 0:
    for item in res["eventLogs"]:
        print(f'{item} \n')
if res['status'] == 0:
    print(f'Failure: {res["failure"]}')


# In[ ]:


# Cell 18a
# setting market name for ommsICX pair

transaction = CallTransactionBuilder()    .from_(btest_wallet.get_address())    .to(contracts['governance']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("setMarketName")    .params({'_pid':2, '_name': 'OMMSICX'})     .build()
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


# Cell 18b
# setting market name for omm/iusdc pair

transaction = CallTransactionBuilder()    .from_(btest_wallet.get_address())    .to(contracts['governance']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("setMarketName")    .params({'_pid':3, '_name': 'OMMIUSDC'})     .build()
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


# Cell 18bc
# setting market name for omm/usdb pair

transaction = CallTransactionBuilder()    .from_(btest_wallet.get_address())    .to(contracts['governance']['SCORE'])    .value(0)    .step_limit(10000000)    .nid(NID)    .nonce(100)    .method("setMarketName")    .params({'_pid':4, '_name': 'OMMUSDB'})     .build()
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


# Cell 33

call = CallBuilder().from_(user1.get_address())                    .to(contracts['dex']['SCORE'])                    .method('getDataBatch')                    .params({'_name': 'OMMSICX', '_limit': 10, '_snapshot_id': 1})                     .build()
result = icon_service.call(call)
print(result)


# In[ ]:


# Cell 46

call = CallBuilder().from_(wallet.get_address())                    .to(contracts['dex']['SCORE'])                    .method('getPoolTotal')                    .params({'_pid': 4, '_token': 'cxaa068556df80f9917ef146e889f0b2c4b13ab634'})                     .build()
result = icon_service.call(call)
int(result, 0) / 10**18


# In[ ]:


# Cell 48
# gives total supply of quote token of the pool
call = CallBuilder().from_(wallet.get_address())                    .to(contracts['dex']['SCORE'])                    .method('totalSupply')                    .params({'_pid': 3})                     .build()
result = icon_service.call(call)
int(result, 0) / 10**18


# In[ ]:


# Cell 42

call = CallBuilder().from_(wallet.get_address())                    .to(contracts['dex']['SCORE'])                    .method('getPoolId')                    .params({'_token1Address':'cx9f03e46d637fb0b1c7b539873c7f25db2ddc94e6' , '_token2Address': contracts['sicx']['SCORE'] })                     .build()
result = icon_service.call(call)
print("pool w/ tokens: " + 'cx9f03e46d637fb0b1c7b539873c7f25db2ddc94e6' + ' & ' + str(contracts['sicx']['SCORE']))
print(result)


# In[ ]:


# Cell 15
# get OMM balance for the wallet

call = CallBuilder().from_(wallet.get_address())                    .to(contracts['loans']['SCORE'])                    .method('getDay')                    .params({})                     .build()
result = icon_service.call(call)
print(result)

