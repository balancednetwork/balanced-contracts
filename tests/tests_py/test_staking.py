import json
import os
from shutil import make_archive
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


@retry(JSONRPCException, tries=10, delay=1, back_off=2)
def get_tx_result(_tx_hash):
    tx_result = icon_service.get_transaction_result(_tx_hash)
    return tx_result


def call_tx(dest: str, method: str, params: dict = {}):
    """
    dest is the name of the destination contract.
    """
    call = CallBuilder() \
        .to(dest) \
        .method(method) \
        .params(params) \
        .build()
    result = icon_service.call(call)
    return result


def send_tx(dest, value, method, params, wallet):
    """
    dest is the name of the destination contract.
    """
    transaction = CallTransactionBuilder() \
        .from_(wallet.get_address()) \
        .to(dest) \
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
    return res


def test_rate():
    with open('./test_scenarios/scenarios/sicxAddress_test.json') as f:
        test_cases = json.load(f)
    for case in test_cases['stories']:
        for unit in case['actions']['unit_test']:
            if unit['fn_name'] == "getSicxAddress":
                score_address = staking_address
                params = {'_address': token_address}
                output = token_address
            else:
                score_address = token_address
                params = {'_admin': staking_address}
                output = staking_address
        ab = send_tx(score_address, 0, case['actions']['name'], params, user2)
        if ab['status'] == 1:
            for unit in case['actions']['unit_test']:
                _result = call_tx(score_address, unit['fn_name'])
                assert _result == output, 'sICX address not Matched'
    _result = call_tx(staking_address, 'getTodayRate')
    assert int(_result, 16) == 1000000000000000000, 'Rate is not set to 1'

    ab = send_tx(score_address, 0, 'toggleStakingOn', {}, user2)
    assert ab['status'] == 1, 'Staking not enabled'


def test_stake_icx():
    with open('./test_scenarios/scenarios/stake_icx.json') as f:
        test_cases = json.load(f)
    network_delegations = {}
    for case in test_cases['stories']:
        if case['actions']['mint_to'] == "user1":
            wallet_address = user1.get_address()
            params = {"_to": wallet_address}
            deployer_wallet = user1
        else:
            wallet_address = user2.get_address()
            params = {"_to": wallet_address}
            deployer_wallet = user2

        ab = send_tx(staking_address, int(case['actions']['deposited_icx']), case['actions']['name'], params,
                     deployer_wallet)

        if ab['status'] == 1:
            method = ['balanceOf', 'getStake', 'totalSupply', 'getAddressDelegations']
            for each in method:
                if each == 'balanceOf':
                    score_address = token_address
                    params = {"_owner": wallet_address}
                elif each == 'getStake':
                    score_address = GOVERNANCE_ADDRESS
                    params = {"address": staking_address}
                elif each == 'getAddressDelegations':
                    score_address = staking_address
                    params = {"_address": wallet_address}
                else:
                    params = {}
                    score_address = token_address
                _result = call_tx(score_address, each, params)
                if each == 'balanceOf':
                    to_check = int(_result, 16)
                    output_json = int(case['actions']['expected_sicx_in_user'])
                    # to_print = f'{wallet_address} total sicx is {int(_result, 16)}. Passed '

                elif each == 'getStake':
                    to_check = int(_result['stake'], 16)
                    output_json = int(case['actions']['expected_icx_staked_from_staking_contract'])
                    # to_print = f'total ICX staked from contract is  {int(_result["stake"], 16)}. Passed '
                elif each == 'getAddressDelegations':
                    result = 0
                    dict1 = {}
                    for key, value in _result.items():
                        dict1[key] = int(value, 16)
                        result += int(value, 16)
                        if case['actions']['mint_to'] == 'user2':
                            network_delegations[key] += int(value, 16)
                        else:
                            network_delegations[key] = int(value, 16)
                    to_check = result
                    output_json = int(case['actions']['expected_sicx_in_user'])
                    # to_print = f'total ICX delegated evenly  {to_check}. Passed '

                else:
                    to_check = int(_result, 16)
                    output_json = int(case['actions']['total_supply_sicx'])
                    # to_print = f'total supply of sICX is  {int(_result, 16)}. Passed '
                assert to_check == output_json, f'{_result}, Failed in staking'
            for x in case['actions']['unit_test']:
                _result = call_tx(staking_address, 'getTotalStake')
                assert int(_result, 16) == int(x['getTotalStake']), f'{_result} Failed in staking'
            _result = call_tx(GOVERNANCE_ADDRESS, 'getDelegation', {'address': staking_address})
            delegation = {}
            for each in _result['delegations']:
                key = each['address']
                value = each['value']
                delegation[key] = int(value, 16)
            assert delegation == network_delegations, 'Delegations in network failed'
        wallet_list = [user1, user2]
        prep_delegations_dict = {}
        for i in wallet_list:
            _result = call_tx(staking_address, 'getAddressDelegations', {'_address': i.get_address()})
            for key, value in _result.items():
                if key not in prep_delegations_dict.keys():
                    prep_delegations_dict[key] = int(value, 16)
                else:
                    prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)
        _result = call_tx(staking_address, 'getPrepDelegations')
        prep_delegation = {}
        for key, value in _result.items():
            prep_delegation[key] = int(value, 16)
        assert prep_delegation == prep_delegations_dict, "Failed"


def test_delegations():
    with open('./test_scenarios/scenarios/delegations.json') as f:
        test_cases = json.load(f)
    network_delegations = {}
    previous_network_delegations = {}
    for case in test_cases['stories']:
        address_list = []
        add = case['actions']['params']['_user_delegations']
        for x in add:
            address_list.append(x['_address'])
        if case['actions']['user'] == "user1":
            wallet_address = user1.get_address()
            user = user1

        else:
            wallet_address = user2.get_address()
            user = user2
        _result = call_tx(GOVERNANCE_ADDRESS, "getDelegation", {'address': staking_address})
        delegation = _result['delegations']
        for each in delegation:
            previous_network_delegations[each['address']] = int(each['value'], 16)
        ab = send_tx(staking_address, 0, "delegate", case['actions']['params'], user)
        if ab['status'] == 1:
            _result = call_tx(staking_address, "getPrepList")
            for x in case['actions']['unit_test'][0]['output'].keys():
                if x not in _result:
                    print('prepList not updated')
                    raise e
            _result = call_tx(staking_address, "getAddressDelegations", {'_address': wallet_address})
            dict1 = {}
            for key, value in _result.items():
                dict1[key] = int(value, 16)
            assert dict(dict1) == dict(
                case['actions']['unit_test'][0]['output']), 'Test Case not passed for delegations'
            _result = call_tx(GOVERNANCE_ADDRESS, "getDelegation", {'address': staking_address})
            delegation = _result['delegations']
            for each in delegation:
                network_delegations[each['address']] = int(each['value'], 16)

            output = case['actions']['unit_test'][0]['output']
            for key, value in output.items():
                try:
                    assert network_delegations[key] != previous_network_delegations[key], 'Failed to delegate'
                except KeyError as e:
                    pass
        wallet_list = [user1, user2]
        prep_delegations_dict = {}
        for i in wallet_list:
            _result = call_tx(staking_address, "getAddressDelegations", {'_address': i.get_address()})
            for key, value in _result.items():
                if key not in prep_delegations_dict.keys():
                    prep_delegations_dict[key] = int(value, 16)
                else:
                    prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)

        _result = call_tx(staking_address, "getPrepDelegations")
        prep_delegation = {}
        for key, value in _result.items():
            prep_delegation[key] = int(value, 16)
            if key not in prep_delegations_dict.keys():
                prep_delegations_dict[key] = 0
        assert prep_delegation == prep_delegations_dict, "Failed"


# ## transfer test

# In[97]:

def test_transfer():
    with open('./test_scenarios/scenarios/transfers_sicx.json') as f:
        test_cases = json.load(f)
    for case in test_cases['stories']:
        dict1 = {}
        dict2 = {}
        if case['actions']['sender'] == 'user1':
            wallet_address = user1.get_address()
            deployer_wallet = user1
        else:
            wallet_address = user2.get_address()
            deployer_wallet = user2
        if case['actions']['receiver'] == 'user2':
            receiver_address = user2.get_address()
        else:
            receiver_address = case['actions']['receiver']
        params = {'_to': receiver_address, "_value": case['actions']['total_sicx_transferred'], "_data": ''}
        ab = send_tx(token_address, 0, "transfer", params, deployer_wallet)
        if ab['status'] == 1:
            _result = call_tx(token_address, "balanceOf", {"_owner": receiver_address})
            assert (int(_result, 16)) == int(
                case['actions']['curr_receiver_sicx']), 'The receiver did not receive the sICX from sender. Failed'

            _result = call_tx(token_address, "balanceOf", {"_owner": wallet_address})
            assert (int(_result, 16)) == int(
                case['actions']['curr_sender_sicx']), 'The sender failed to send the sICX to receiver. Failed'

            _result = call_tx(staking_address, 'getAddressDelegations', {"_address": wallet_address})
            for key, value in _result.items():
                dict1[key] = int(value, 16)
            assert dict1 == case['actions']["delegation_sender"], 'Delegation is changed for sender. Test Failed'
            _result = call_tx(staking_address, "getAddressDelegations", {"_address": receiver_address})
            for key, value in _result.items():
                dict2[key] = int(value, 16)
            if case['actions']["delegation_receiver"] != "evenly_distribute":
                assert dict2 == case['actions'][
                    "delegation_receiver"], 'Delegation is changed for receiver. Test Failed'
            else:
                _result = call_tx(staking_address, "getAddressDelegations", {"_address": receiver_address})

                _result2 = call_tx(staking_address, "getTopPreps")
                lis1 = []
                for x in _result.keys():
                    lis1.append(x)
                assert lis1 == _result2, 'delegations is not set to top preps for the random address'

            _result2 = call_tx(staking_address, "getTotalStake")

            assert int(_result2, 16) == 110000000000000000000, "Failed to stake"

        wallet_list = [user1, user2, 'user3']
        prep_delegations_dict = {}
        for i in wallet_list:
            if i == "user3":
                params = "hx72bff0f887ef183bde1391dc61375f096e75c74a"
            else:
                params = i.get_address()
            _result = call_tx(staking_address, "getAddressDelegations", {'_address': params})
            for key, value in _result.items():
                if key not in prep_delegations_dict.keys():
                    prep_delegations_dict[key] = int(value, 16)
                else:
                    prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)

        _result = call_tx(staking_address, "getPrepDelegations")
        prep_delegation = {}
        for key, value in _result.items():
            prep_delegation[key] = int(value, 16)
            if key not in prep_delegations_dict.keys():
                prep_delegations_dict[key] = 0
        assert prep_delegation == prep_delegations_dict, "Failed"
        top_prep_list = call_tx(staking_address, "getTopPreps")
        evenly_distributed_value = 0
        to_delete = []
        for key, value in prep_delegations_dict.items():
            if key not in top_prep_list:
                evenly_distributed_value += prep_delegations_dict[key]
                if key not in to_delete:
                    to_delete.append(key)
            if prep_delegations_dict[key] == 0:
                if key not in to_delete:
                    to_delete.append(key)

        for x in to_delete:
            del prep_delegations_dict[x]

        for key, value in prep_delegations_dict.items():
            prep_delegations_dict[key] += evenly_distributed_value // 20
        _result = call_tx(GOVERNANCE_ADDRESS, "getDelegation", {'address': staking_address})
        delegation = _result['delegations']
        network_delegations = {}
        for each in delegation:
            network_delegations[each['address']] = int(each['value'], 16)
        assert prep_delegations_dict == network_delegations, 'Failed to delegate in Network'


# ## unstake test

# In[98]:

def test_top_preps():
    _result1 = call_tx(staking_address, 'getTopPreps')
    _result2 = call_tx(GOVERNANCE_ADDRESS, 'getPReps', {'startRanking': 1, 'endRanking': 20})
    top_prep_in_network = []
    preps = (_result2['preps'])
    for prep in preps:
        top_prep_in_network.append(prep['address'])
    assert top_prep_in_network == _result1, 'Top preps not set properly'


def test_unstake():
    with open('./test_scenarios/scenarios/unstake_sicx.json') as f:
        test_cases = json.load(f)
    count = 0
    for case in test_cases['stories']:
        count += 1
        if case['actions']['sender'] == 'user1':
            wallet_address = user1.get_address()
            deployer_wallet = user1
        else:
            wallet_address = user2.get_address()
            deployer_wallet = user2
        #     data = "{\"method\": \"unstake\",\"user\":\"hx436106433144e736a67710505fc87ea9becb141d\"}".encode("utf-8")
        data = "{\"method\": \"unstake\"}".encode("utf-8")
        params = {'_to': staking_address, "_value": int(case['actions']['total_sicx_transferred']), "_data": data}
        ab = send_tx(token_address, 0, "transfer", params, deployer_wallet)
        if ab['status'] == 1:
            _result = call_tx(staking_address, "getUnstakingAmount")
            total_unstaking_amount = int(_result, 16)
            total_unstake_json = int(case['actions']['unit_test'][0]['output'])
            assert total_unstaking_amount == total_unstake_json, 'getUnstakingAmount function test failed'
            _result = call_tx(GOVERNANCE_ADDRESS, "getStake", {"address": staking_address})
            unstake_amount = 0
            for x in _result['unstakes']:
                unstake_amount += int(x['unstake'], 16)
            assert unstake_amount == int(
                case['actions']['unit_test'][0]['output']), 'Unstake request is not passed to the network. Failed'
            assert int(_result['stake'], 16) == int(
                case['actions']['curr_total_stake']), 'Total stake in the network is not decreased. Failed'
            _result = call_tx(token_address, "balanceOf", {"_owner": wallet_address})
            assert int(_result, 16) == int(case['actions']['curr_sender_sicx']), "sICX not burned"
            _result = call_tx(token_address, "totalSupply")
            assert int(_result, 16) == int(case['actions']['curr_total_stake']), "total supply not decreased"
            wallet_list = [user1, user2, 'user3']
            prep_delegations_dict = {}
            for i in wallet_list:
                if i == "user3":
                    params = "hx72bff0f887ef183bde1391dc61375f096e75c74a"
                else:
                    params = i.get_address()
                _result = call_tx(staking_address, "getAddressDelegations", {'_address': params})
                for key, value in _result.items():
                    if key not in prep_delegations_dict.keys():
                        prep_delegations_dict[key] = int(value, 16)
                    else:
                        prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)

            _result = call_tx(staking_address, "getPrepDelegations")
            prep_delegation = {}
            for key, value in _result.items():
                prep_delegation[key] = int(value, 16)
                if key not in prep_delegations_dict.keys():
                    prep_delegations_dict[key] = 0
            assert prep_delegation == prep_delegations_dict, "Failed in unstake of sicx"
            top_prep_list = call_tx(staking_address, "getTopPreps")
            evenly_distributed_value = 0
            to_delete = []
            for key, value in prep_delegations_dict.items():
                if key not in top_prep_list:
                    evenly_distributed_value += prep_delegations_dict[key]
                    if key not in to_delete:
                        to_delete.append(key)
                if prep_delegations_dict[key] == 0:
                    if key not in to_delete:
                        to_delete.append(key)

            for x in to_delete:
                del prep_delegations_dict[x]

            for key, value in prep_delegations_dict.items():
                prep_delegations_dict[key] += evenly_distributed_value // 20

            _result = call_tx(GOVERNANCE_ADDRESS, "getDelegation", {'address': staking_address})
            delegation = _result['delegations']
            network_delegations = {}
            for each in delegation:
                network_delegations[each['address']] = int(each['value'], 16)
            assert prep_delegations_dict == network_delegations, 'Failed to delegate in Network'
            linked_list = call_tx(staking_address, "getUnstakeInfo")
            if count == 2:
                linked_list.pop(0)
            for each in linked_list:
                assert int(each[1], 16) == int(case['actions']['total_sicx_transferred']), "Linked list failed"
                assert each[2] == wallet_address, "Linked list failed"

        else:
            print(f'Failed... {ab}')


def test_payout():
    params = {'_to': user2.get_address()}

    ab = send_tx(staking_address, 20000000000000000000, "stakeICX", params, user2)
    if ab['status'] == 1:
        _result = call_tx(staking_address, "getUnstakingAmount")
        total_unstaking_amount = int(_result, 16)
        assert total_unstaking_amount == 10000000000000000000, 'Failed'
        # print(
        #     "20 icx is deposited by user2 and as user1 has unstake request in top of the list. User1 will receive "
        #     "20 icx from the contract.")


def test_partial_payout():
    params = {'_to': user2.get_address()}

    ab = send_tx(staking_address, 3000000000000000000, "stakeICX", params, user2)
    if ab['status'] == 1:
        _result = call_tx(staking_address, "getUnstakingAmount")
        total_unstaking_amount = int(_result, 16)
        assert total_unstaking_amount == 7000000000000000000, 'Failed'
        # print(
        #     "3 icx is deposited partially by user2 and as user2 has unstake request in top of the list. User1 will receive 3 icx from the contract.")
        _result = call_tx(staking_address, "getUserUnstakeInfo", {'_address': user2.get_address()})
        for x in _result:
            assert int(x['amount'], 16) == 7000000000000000000


def test_complete_payout():
    params = {'_to': user2.get_address()}

    ab = send_tx(staking_address, 30000000000000000000, "stakeICX",params, user2)
    if ab['status'] == 1:
        _result = call_tx(staking_address, "getUnstakingAmount")
        total_unstaking_amount = int(_result, 16)
        assert total_unstaking_amount == 0, 'Failed'
        # print("Left 7 icx is transferred to user1")
        _result = call_tx(staking_address, "getUserUnstakeInfo", {'_address': user2.get_address()})
        assert _result == [], 'Failed'


def stake_icx_after_delegation():
    params = {'_to': user1.get_address()}
    ab = send_tx(staking_address, 30000000000000000000, "stakeICX", params, user1)
    if ab['status'] == 1:
        _result = call_tx(staking_address, "getAddressDelegations", {'_address': user1.get_address()})
        dict1 = {}
        for key, value in _result.items():
            dict1[key] = int(value, 16)

        assert dict1 == {"hx9eec61296a7010c867ce24c20e69588e2832bc52": 80000000000000000000}, 'Failed'


def test_delegation_by_new_user():
    with open('./test_scenarios/scenarios/new_user_delegations.json') as f:
        test_cases = json.load(f)
    for case in test_cases['stories']:
        address_list = []
        add = case['actions']['params']['_user_delegations']
        for x in add:
            address_list.append(x['_address'])
        wallet_address = user1.get_address()
        user = user1
        ab = send_tx(staking_address, 0, 'delegate', case['actions']['params'], user)
        if ab['status'] == 1:
            _result = call_tx(staking_address, 'getPrepList')

            for x in case['actions']['unit_test'][0]['output'].keys():
                if x not in _result:
                    print('prepList not updated')
                    raise e
            _result = call_tx(staking_address, 'getAddressDelegations', {'_address': wallet_address})
            dict1 = {}
            for key, value in _result.items():
                dict1[key] = int(value, 16)
            assert dict(dict1) == dict(
                case['actions']['unit_test'][0]['output']), 'Test Case not passed for delegations'


if __name__ == '__main__':
    # icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io", 3))
    icon_service = IconService(HTTPProvider("http://18.144.108.38:9000", 3))
    # NID = 80
    NID = 3
    user1 = KeyWallet.load("./keystores/keystore_test1.json", "test1_Account")
    with open("./keystores/balanced_test.pwd", "r") as f:
        key_data = f.read()
    user2 = KeyWallet.load("./keystores/balanced_test.json", key_data)
    GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
    contracts = {'staking': {'zip': 'core_contracts/staking.zip',
                             'SCORE': 'cxd8e05c1280bc2c32bf53ff61f3bb2e2ecc7d6df5'},
                 'sicx': {'zip': 'token_contracts/sicx.zip',
                          'SCORE': 'cxcff8bf80ab213fa9bbb350636a4d68f5cb4fd9c1'}
                 }
    deploy = list(['staking', 'sicx'])
    for directory in {"../core_contracts", "../token_contracts"}:
        with os.scandir(directory) as it:
            for file in it:
                archive_name = directory + "/" + file.name
                if file.is_dir() and file.name in deploy:
                    make_archive(archive_name, "zip", directory, file.name)
                    contracts[file.name]['zip'] = archive_name + '.zip'
    zip_file = contracts['staking']['zip']
    deploy_transaction = DeployTransactionBuilder().from_(user2.get_address()).to(GOVERNANCE_ADDRESS).nid(
        NID).nonce(100).content_type("application/zip").content(
        gen_deploy_data_content(zip_file)).build()

    estimate_step = icon_service.estimate_step(deploy_transaction)
    step_limit = estimate_step + 40000000
    signed_transaction = SignedTransaction(deploy_transaction, user2, step_limit)
    tx_hash = icon_service.send_transaction(signed_transaction)

    ab = get_tx_result(tx_hash)
    assert ab['status'] == 1, 'Staking contract not deployed'
    staking_address = ab['scoreAddress']
    # deployment of sICX contract
    zip_file = contracts['sicx']['zip']
    deploy_transaction = DeployTransactionBuilder().from_(user2.get_address()).to(GOVERNANCE_ADDRESS).nid(
        NID).nonce(100).content_type("application/zip").params({"_admin": staking_address}).content(
        gen_deploy_data_content(zip_file)).build()

    estimate_step = icon_service.estimate_step(deploy_transaction)
    step_limit = estimate_step + 40000000
    signed_transaction = SignedTransaction(deploy_transaction, user2, step_limit)
    tx_hash = icon_service.send_transaction(signed_transaction)
    ab = get_tx_result(tx_hash)
    assert ab['status'] == 1, 'sICX contract not deployed'
    token_address = ab['scoreAddress']
    test_top_preps()
    test_rate()
    # test_delegation_by_new_user()
    test_stake_icx()
    test_delegations()
    test_transfer()
    test_unstake()
    test_payout()
    test_partial_payout()
    test_complete_payout()
    stake_icx_after_delegation()
