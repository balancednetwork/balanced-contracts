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


def test_rate():
    test_cases = {
        "stories": [
            {
                "description": "sICX address is set in staking contract",
                "actions": {
                    "name": "setSicxAddress",
                    "unit_test": [
                        {
                            "fn_name": "getSicxAddress",
                            "output": "token_address"
                        }
                    ]
                }
            }
        ]
    }
    for case in test_cases['stories']:
        print(case['description'])
        for unit in case['actions']['unit_test']:
            if unit['fn_name'] == "getSicxAddress":
                score_address = staking_address
                params = {'_address': token_address}
                output = token_address
            else:
                score_address = token_address
                params = {'_admin': staking_address}
                output = staking_address

        set_div_per = CallTransactionBuilder().from_(user2.get_address()).to(score_address).nid(NID).nonce(
            100).method(case['actions']['name']).params(params).build()
        estimate_step = icon_service.estimate_step(set_div_per)
        step_limit = estimate_step + 10000000
        signed_transaction = SignedTransaction(set_div_per, user2, step_limit)

        tx_hash = icon_service.send_transaction(signed_transaction)

        @retry(JSONRPCException, tries=10, delay=1, back_off=2)
        def get_tx_result(_tx_hash):
            tx_result = icon_service.get_transaction_result(_tx_hash)
            return tx_result

        ab = get_tx_result(tx_hash)
        if ab['status'] == 1:
            for unit in case['actions']['unit_test']:
                _call = CallBuilder().from_(user2.get_address()).to(score_address).method(unit['fn_name']).build()

                _result = icon_service.call(_call)
                assert _result == output, 'sICX address not Matched'
    #             if _result == output:
    #                 print('Test Passed')
    #             print(output)

    print('Testing Rate of sICX')
    _call = CallBuilder().from_(user2.get_address()).to(staking_address).method('getTodayRate').build()

    _result = icon_service.call(_call)
    assert int(_result, 16) == 1000000000000000000, 'Rate is not set to 1'


# ## stakeICX Test

# In[95]:

def test_stake_icx():
    test_cases = {
        "title": "Staking: stakeICX",
        "description": "Test cases for the stakeICX function.",
        "stories": [
            {
                "description": "User 1 deposits 50 ICX as collateral and mints sicx to own wallet address.",
                "actions": {
                    "mint_to": "user1",
                    "prev_sicx_in_user": "0",
                    "prev_total_supply_sicx": "0",
                    "prev_icx_staked_from_staking_contract": "0",
                    "name": "stakeICX",
                    "deposited_icx": "50000000000000000000",
                    "expected_sicx_in_user": "50000000000000000000",
                    "expected_icx_staked_from_staking_contract": "50000000000000000000",
                    "total_supply_sicx": "50000000000000000000",
                    "unit_test": [
                        {
                            "getTotalStake": "50000000000000000000",
                        }]
                }
            },
            {
                "description": "user 2 deposits 30 ICX as collateral and mints sicx to user1 wallet address.",
                "actions": {
                    "mint_to": "user1",
                    "prev_sicx_in_user": "50000000000000000000",
                    "prev_total_supply_sicx": "50000000000000000000",
                    "prev_icx_staked_from_staking_contract": "50000000000000000000",
                    "name": "stakeICX",
                    "deposited_icx": "30000000000000000000",
                    "expected_sicx_in_user": "80000000000000000000",
                    "expected_icx_staked_from_staking_contract": "80000000000000000000",
                    "total_supply_sicx": "80000000000000000000",
                    "unit_test": [
                        {
                            "getTotalStake": "80000000000000000000",
                        }]
                }
            },
            {
                "description": "user 2 deposits 30 ICX as collateral and mints sicx to own wallet address.",
                "actions": {
                    "mint_to": "user2",
                    "prev_sicx_in_user": "0",
                    "prev_total_supply_sicx": "80000000000000000000",
                    "prev_icx_staked_from_staking_contract": "80000000000000000000",
                    "name": "stakeICX",
                    "deposited_icx": "30000000000000000000",
                    "expected_sicx_in_user": "30000000000000000000",
                    "expected_icx_staked_from_staking_contract": "110000000000000000000",
                    "total_supply_sicx": "110000000000000000000",
                    "unit_test": [
                        {
                            "getTotalStake": "110000000000000000000",
                        }]
                }
            }

        ]
    }

    for case in test_cases['stories']:
        print(case['description'])
        if case['actions']['mint_to'] == "user1":
            wallet_address = user1.get_address()
            params = {"_to": wallet_address}
        else:
            wallet_address = user2.get_address()
            params = {"_to": wallet_address}

        set_div_per = CallTransactionBuilder().from_(user2.get_address()).to(staking_address).nid(NID).nonce(
            100).method(case['actions']['name']).params(params).value(int(case['actions']['deposited_icx'])).build()
        estimate_step = icon_service.estimate_step(set_div_per)
        step_limit = estimate_step + 10000000
        signed_transaction = SignedTransaction(set_div_per, user2, step_limit)

        tx_hash = icon_service.send_transaction(signed_transaction)

        @retry(JSONRPCException, tries=10, delay=1, back_off=2)
        def get_tx_result(_tx_hash):
            tx_result = icon_service.get_transaction_result(_tx_hash)
            return tx_result

        ab = get_tx_result(tx_hash)
        if ab['status'] == 1:
            method = ['balanceOf', 'getStake', 'totalSupply']
            for each in method:
                if each == 'balanceOf':
                    score_address = token_address
                    params = {"_owner": wallet_address}
                elif each == 'getStake':
                    score_address = GOVERNANCE_ADDRESS
                    params = {"address": staking_address}
                else:
                    params = {}
                    score_address = token_address
                _call = CallBuilder().from_(user2.get_address()).to(score_address).method(each).params(
                    params).build()

                _result = icon_service.call(_call)
                if each == 'balanceOf':
                    to_check = int(_result, 16)
                    output_json = int(case['actions']['expected_sicx_in_user'])
                    to_print = f'{wallet_address} total sicx is {int(_result, 16)}. Passed '
                elif each == 'getStake':
                    to_check = int(_result['stake'], 16)
                    output_json = int(case['actions']['expected_icx_staked_from_staking_contract'])
                    to_print = f'total ICX staked from contract is  {int(_result["stake"], 16)}. Passed '
                else:
                    to_check = int(_result, 16)
                    output_json = int(case['actions']['total_supply_sicx'])
                    to_print = f'total supply of sICX is  {int(_result, 16)}. Passed '
                assert to_check == output_json, f'{_result}, Failed'
                print(to_print)
            #             else:
            #                    print(f'{_result} Failed')

            for x in case['actions']['unit_test']:
                _call = CallBuilder().from_(user2.get_address()).to(staking_address).method('getTotalStake').build()
                _result = icon_service.call(_call)

                assert int(_result, 16) == int(x['getTotalStake']), f'{_result} Failed'
                print(f'Total stake is {int(_result, 16)}.Passed')
    #             else:
    #                 print(f'{_result} Failed')


# ## delegation test

# In[96]:

def test_delegations():
    test_cases = {

        "stories": [{
            "description": "User1 delegates 100% of it's votes to hx4917005bf4b8188b9591da520fc1c6dab8fe717f",
            "actions": {
                "name": "delegate",
                "params": {'_user_delegations': [{'_address': 'hx4917005bf4b8188b9591da520fc1c6dab8fe717f',
                                                  '_votes_in_per': '100000000000000000000'}]},
                "user": "user1",
                "within_top_preps": "true",
                "unit_test": [
                    {
                        "fn_name": "getAddressDelegations",
                        "output": {'hx4917005bf4b8188b9591da520fc1c6dab8fe717f': 80000000000000000000}
                    }]
            }
        },
            {
                "description": "User2 delegates 50% of it's votes to hxfd114a60eefa8e2c3de2d00dc5e41b1a0c7e8931 and 50% of its votes to hxf21dc87ce2c6273d7670135333f77a770c39fae0",
                "actions": {
                    "name": "delegate",
                    "params": {'_user_delegations': [{'_address': 'hxfd114a60eefa8e2c3de2d00dc5e41b1a0c7e8931',
                                                      '_votes_in_per': '50000000000000000000'},
                                                     {'_address': 'hxf21dc87ce2c6273d7670135333f77a770c39fae0',
                                                      '_votes_in_per': '50000000000000000000'}]},
                    "user": "user2",
                    "within_top_preps": "true",
                    "unit_test": [
                        {
                            "fn_name": "getAddressDelegations",
                            "output": {'hxfd114a60eefa8e2c3de2d00dc5e41b1a0c7e8931': 15000000000000000000,
                                       'hxf21dc87ce2c6273d7670135333f77a770c39fae0': 15000000000000000000}
                        }]
                }
            },
            {
                "description": "User1 delegates 100% of it's votes to hx8ac43d292fcc468f53e8377a8c01b1e82216c5a0(out of top preps)",
                "actions": {
                    "name": "delegate",
                    "params": {'_user_delegations': [{'_address': 'hx8ac43d292fcc468f53e8377a8c01b1e82216c5a0',
                                                      '_votes_in_per': '100000000000000000000'}]},
                    "user": "user1",
                    "within_top_preps": "false",
                    "unit_test": [
                        {
                            "fn_name": "getAddressDelegations",
                            "output": {'hx8ac43d292fcc468f53e8377a8c01b1e82216c5a0': 80000000000000000000}
                        }]
                }
            }
            ,
            {
                "description": "User1 delegates 100% of it's votes to hxca1e081e686ec4975d14e0fb8f966c3f068298be",
                "actions": {
                    "name": "delegate",
                    "params": {'_user_delegations': [{'_address': 'hxca1e081e686ec4975d14e0fb8f966c3f068298be',
                                                      '_votes_in_per': '100000000000000000000'}]},
                    "user": "user1",
                    "within_top_preps": "true",
                    "unit_test": [
                        {
                            "fn_name": "getAddressDelegations",
                            "output": {'hxca1e081e686ec4975d14e0fb8f966c3f068298be': 80000000000000000000}
                        }]
                }
            }

        ]
    }

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
        print(case['description'])
        set_div_per = CallTransactionBuilder().from_(wallet_address).to(staking_address).nid(NID).nonce(100).method(
            "delegate").params(case['actions']['params']).build()
        estimate_step = icon_service.estimate_step(set_div_per)
        step_limit = estimate_step + 10000000
        signed_transaction = SignedTransaction(set_div_per, user, step_limit)

        tx_hash = icon_service.send_transaction(signed_transaction)

        @retry(JSONRPCException, tries=10, delay=1, back_off=2)
        def get_tx_result(_tx_hash):
            tx_result = icon_service.get_transaction_result(_tx_hash)
            return tx_result

        ab = get_tx_result(tx_hash)
        if ab['status'] == 1:
            _call = CallBuilder().from_(wallet_address).to(staking_address).method('getAddressDelegations').params(
                {'_address': wallet_address}).build()

            _result = icon_service.call(_call)
            dict1 = {}
            for key, value in _result.items():
                dict1[key] = int(value, 16)
            assert dict(dict1) == dict(
                case['actions']['unit_test'][0]['output']), 'Test Case not passed for delegations'
    #             print('Test case passed for delegations')
    # test of delegations in network
    #         _call = CallBuilder()\
    #                         .from_(wallet_address)\
    #                         .to(GOVERNANCE_ADDRESS)\
    #                         .method('getDelegation')\
    #                         .params({'address':staking_address})\
    #                         .build()

    #         _result = icon_service.call(_call)
    #         delegation = _result['delegations']
    #         for each in delegation:
    #             if case['actions']['within_top_preps'] == 'false':
    #                 if each['address'] not in address_list:
    #                     print("Evenly distributed")
    #             if each['address'] in address_list:
    #                 if int(each['value'],16) == (case['actions']['unit_test'][0]['output'])[each['address']]:
    #                     print('Delegations in network passed')
    #                 else:
    #                     print('failed')


# ## transfer test

# In[97]:

def test_transfer():
    test_cases = {
        "stories": [
            {
                "description": "User1 transfers 10 sICX to user2",
                "actions": {
                    "name": "transfer",
                    "sender": "user1",
                    "receiver": "user2",
                    "prev_sender_sicx": "80000000000000000000",
                    "prev_receiver_sicx": "30000000000000000000",
                    "total_sicx_transferred": "10000000000000000000",
                    "curr_sender_sicx": "70000000000000000000",
                    "curr_receiver_sicx": "40000000000000000000",
                    "delegation_sender": {"hxca1e081e686ec4975d14e0fb8f966c3f068298be": 70000000000000000000},
                    "delegation_receiver": {"hxfd114a60eefa8e2c3de2d00dc5e41b1a0c7e8931": 20000000000000000000,
                                            "hxf21dc87ce2c6273d7670135333f77a770c39fae0": 20000000000000000000}

                }
            },
            {
                "description": "User2 transfers 20 sICX to some random address",
                "actions": {
                    "name": "transfer",
                    "sender": "user2",
                    "receiver": "hx72bff0f887ef183bde1391dc61375f096e75c74a",
                    "prev_sender_sicx": "40000000000000000000",
                    "prev_receiver_sicx": "0",
                    "total_sicx_transferred": "20000000000000000000",
                    "curr_sender_sicx": "20000000000000000000",
                    "curr_receiver_sicx": "20000000000000000000",
                    "delegation_sender": {"hxfd114a60eefa8e2c3de2d00dc5e41b1a0c7e8931": 10000000000000000000,
                                          "hxf21dc87ce2c6273d7670135333f77a770c39fae0": 10000000000000000000},
                    "delegation_receiver": "evenly_distribute"

                }
            }

        ]
    }

    for case in test_cases['stories']:
        dict1 = {}
        dict2 = {}
        print(case['description'])
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
        set_div_per = CallTransactionBuilder().from_(wallet_address).to(token_address).nid(NID).nonce(100).method(
            "transfer").params(params).build()
        estimate_step = icon_service.estimate_step(set_div_per)
        step_limit = estimate_step + 10000000
        signed_transaction = SignedTransaction(set_div_per, deployer_wallet, step_limit)

        tx_hash = icon_service.send_transaction(signed_transaction)

        @retry(JSONRPCException, tries=10, delay=1, back_off=2)
        def get_tx_result(_tx_hash):
            tx_result = icon_service.get_transaction_result(_tx_hash)
            return tx_result

        ab = get_tx_result(tx_hash)
        if ab['status'] == 1:
            _call = CallBuilder().from_(user2.get_address()).to(token_address).method('balanceOf').params(
                {"_owner": receiver_address}).build()

            _result = icon_service.call(_call)
            assert (int(_result, 16)) == int(
                case['actions']['curr_receiver_sicx']), 'The receiver did not receive the sICX from sender. Failed'

            _call = CallBuilder().from_(user2.get_address()).to(token_address).method('balanceOf').params(
                {"_owner": wallet_address}).build()

            _result = icon_service.call(_call)
            assert (int(_result, 16)) == int(
                case['actions']['curr_sender_sicx']), 'The sender failed to send the sICX to receiver. Failed'

            _call = CallBuilder().from_(user2.get_address()).to(staking_address).method(
                'getAddressDelegations').params({"_address": wallet_address}).build()

            _result = icon_service.call(_call)
            for key, value in _result.items():
                dict1[key] = int(value, 16)
            assert dict1 == case['actions']["delegation_sender"], 'Delegation is changed for sender. Test Failed'

            _call = CallBuilder().from_(user2.get_address()).to(staking_address).method(
                'getAddressDelegations').params({"_address": receiver_address}).build()

            _result = icon_service.call(_call)
            for key, value in _result.items():
                dict2[key] = int(value, 16)
            if case['actions']["delegation_receiver"] != "evenly_distribute":
                assert dict2 == case['actions'][
                    "delegation_receiver"], 'Delegation is changed for receiver. Test Failed'
            else:
                _call = CallBuilder().from_(user2.get_address()).to(staking_address).method(
                    'getAddressDelegations').params({"_address": receiver_address}).build()

                _result = icon_service.call(_call)

                _call2 = CallBuilder().from_(user2.get_address()).to(staking_address).method('getTopPreps').build()

                _result2 = icon_service.call(_call2)
                lis1 = []
                for x in _result.keys():
                    lis1.append(x)
                assert lis1 == _result2, 'delegations is not set to top preps for the random address'


# ## unstake test

# In[98]:

def test_top_preps():
    print('Testing top preps')
    _call = CallBuilder() \
        .from_(user2.get_address()) \
        .to(staking_address) \
        .method('getTopPreps') \
        .build()

    _result1 = icon_service.call(_call)

    _call = CallBuilder() \
        .from_(user2.get_address()) \
        .to(GOVERNANCE_ADDRESS) \
        .method('getPReps') \
        .params({'startRanking': 1, 'endRanking': 4}) \
        .build()

    _result2 = icon_service.call(_call)
    top_prep_in_network = []
    preps = (_result2['preps'])
    for prep in preps:
        top_prep_in_network.append(prep['address'])
    assert top_prep_in_network == _result1, 'Top preps not set properly'

def test_unstake():
    test_cases = {
        "stories": [
            {
                "description": "User1 request for unstake of 20sICX",
                "actions": {
                    "name": "transfer",
                    "sender": "user1",
                    "prev_total_stake": "110000000000000000000",
                    "curr_total_stake": "90000000000000000000",
                    "total_sicx_transferred": "20000000000000000000",
                    "unit_test": [
                        {
                            "fn_name": "getUnstakingAmount",
                            "output": "20000000000000000000"
                        }
                    ]

                }
            },
            {
                "description": "User2 request for unstake of 10sICX",
                "actions": {
                    "name": "transfer",
                    "sender": "user2",
                    "prev_total_stake": "90000000000000000000",
                    "curr_total_stake": "80000000000000000000",
                    "total_sicx_transferred": "10000000000000000000",
                    "unit_test": [
                        {
                            "fn_name": "getUnstakingAmount",
                            "output": "30000000000000000000"
                        }
                    ]

                }
            }

        ]
    }
    total_unstaking_amount = 0
    total_unstake_json = 0
    for case in test_cases['stories']:
        print(case['description'])
        if case['actions']['sender'] == 'user1':
            wallet_address = user1.get_address()
            deployer_wallet = user1
        else:
            wallet_address = user2.get_address()
            deployer_wallet = user2
        #     data = "{\"method\": \"unstake\",\"user\":\"hx436106433144e736a67710505fc87ea9becb141d\"}".encode("utf-8")
        data = "{\"method\": \"unstake\"}".encode("utf-8")
        params = {'_to': staking_address, "_value": int(case['actions']['total_sicx_transferred']), "_data": data}
        set_div_per = CallTransactionBuilder().from_(wallet_address).to(token_address).nid(NID).nonce(100).method(
            "transfer").params(params).build()
        estimate_step = icon_service.estimate_step(set_div_per)
        step_limit = estimate_step + 10000000
        signed_transaction = SignedTransaction(set_div_per, deployer_wallet, step_limit)

        tx_hash = icon_service.send_transaction(signed_transaction)

        @retry(JSONRPCException, tries=10, delay=1, back_off=2)
        def get_tx_result(_tx_hash):
            tx_result = icon_service.get_transaction_result(_tx_hash)
            return tx_result

        ab = get_tx_result(tx_hash)
        if ab['status'] == 1:
            _call = CallBuilder().from_(wallet_address).to(staking_address).method('getUnstakingAmount').build()

            _result = icon_service.call(_call)
            total_unstaking_amount = int(_result, 16)
            total_unstake_json = int(case['actions']['unit_test'][0]['output'])

            _call = CallBuilder().from_(wallet_address).to(GOVERNANCE_ADDRESS).method('getStake').params(
                {"address": staking_address}).build()

            _result = icon_service.call(_call)
            unstake_amount = 0
            for x in _result['unstakes']:
                unstake_amount += int(x['unstake'], 16)
            assert unstake_amount == int(
                case['actions']['unit_test'][0]['output']), 'Unstake request is not passed to the network. Failed'
            assert int(_result['stake'], 16) == int(
                case['actions']['curr_total_stake']), 'Total stake in the network is not decreased. Failed'
        else:
            print(f'Failed... {ab}')

    assert total_unstaking_amount == total_unstake_json, 'getUnstakingAmount function test failed'
    print('unstaking completed')


# ## user2 deposits 20 ICX again

# In[ ]:

def test_payout():
    params = {'_to': user2.get_address()}

    set_div_per = CallTransactionBuilder().from_(user2.get_address()).to(staking_address).nid(NID).nonce(
        100).method("stakeICX").params(params).value(20000000000000000000).build()
    estimate_step = icon_service.estimate_step(set_div_per)
    step_limit = estimate_step + 10000000
    signed_transaction = SignedTransaction(set_div_per, user2, step_limit)

    tx_hash = icon_service.send_transaction(signed_transaction)

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(_tx_hash):
        tx_result = icon_service.get_transaction_result(_tx_hash)
        return tx_result

    ab = get_tx_result(tx_hash)
    if ab['status'] == 1:
        _call = CallBuilder().from_(user1.get_address()).to(staking_address).method('getUnstakingAmount').build()

        _result = icon_service.call(_call)
        total_unstaking_amount = int(_result, 16)
        assert total_unstaking_amount == 10000000000000000000, 'Failed'
        print(
            "20 icx is deposited by user2 and as user1 has unstake request in top of the list. User1 will receive "
            "20 icx from the contract.")


def test_partial_payout():
    params = {'_to': user2.get_address()}

    set_div_per = CallTransactionBuilder() \
        .from_(user2.get_address()) \
        .to(staking_address) \
        .nid(NID) \
        .nonce(100) \
        .method("stakeICX") \
        .params(params) \
        .value(3000000000000000000) \
        .build()
    estimate_step = icon_service.estimate_step(set_div_per)
    step_limit = estimate_step + 10000000
    signed_transaction = SignedTransaction(set_div_per, user2, step_limit)

    tx_hash = icon_service.send_transaction(signed_transaction)

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(_tx_hash):
        tx_result = icon_service.get_transaction_result(_tx_hash)
        return tx_result

    ab = get_tx_result(tx_hash)
    if ab['status'] == 1:
        _call = CallBuilder() \
            .from_(user2.get_address()) \
            .to(staking_address) \
            .method('getUnstakingAmount') \
            .build()

        _result = icon_service.call(_call)
        total_unstaking_amount = int(_result, 16)
        print(total_unstaking_amount)
        assert total_unstaking_amount == 7000000000000000000, 'Failed'
        print(
            "3 icx is deposited partially by user2 and as user2 has unstake request in top of the list. User1 will receive 3 icx from the contract.")
        _call = CallBuilder() \
            .from_(user2.get_address()) \
            .to(staking_address) \
            .method('getUserUnstakeInfo') \
            .params({'_address': user2.get_address()}) \
            .build()

        _result = icon_service.call(_call)
        for x in _result:
            print(int(x['amount'], 16))
            assert int(x['amount'], 16) == 7000000000000000000


def test_complete_payout():
    params = {'_to': user2.get_address()}

    set_div_per = CallTransactionBuilder() \
        .from_(user2.get_address()) \
        .to(staking_address) \
        .nid(NID) \
        .nonce(100) \
        .method("stakeICX") \
        .params(params) \
        .value(30000000000000000000) \
        .build()
    estimate_step = icon_service.estimate_step(set_div_per)
    step_limit = estimate_step + 10000000
    signed_transaction = SignedTransaction(set_div_per, user2, step_limit)

    tx_hash = icon_service.send_transaction(signed_transaction)

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(_tx_hash):
        tx_result = icon_service.get_transaction_result(_tx_hash)
        return tx_result

    ab = get_tx_result(tx_hash)
    if ab['status'] == 1:
        _call = CallBuilder() \
            .from_(user2.get_address()) \
            .to(staking_address) \
            .method('getUnstakingAmount') \
            .build()

        _result = icon_service.call(_call)
        total_unstaking_amount = int(_result, 16)
        print(total_unstaking_amount)
        assert total_unstaking_amount == 0, 'Failed'
        print("Left 7 icx is transferred to user1")
        _call = CallBuilder() \
            .from_(user2.get_address()) \
            .to(staking_address) \
            .method('getUserUnstakeInfo') \
            .params({'_address': user2.get_address()}) \
            .build()

        _result = icon_service.call(_call)
        assert _result == [], 'Failed'


if __name__ == '__main__':
    icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io", 3))
    # NID = 80
    NID = 3

    # In[92]:

    user1 = KeyWallet.load("../keystores/keystore_test1.json", "test1_Account")
    with open("../keystores/balanced_test.pwd", "r") as f:
        key_data = f.read()
    user2 = KeyWallet.load("../keystores/balanced_test.json", key_data)

    # print(icon_service.get_balance(user1.get_address()) / 10 ** 18)
    # print(icon_service.get_balance(user2.get_address()) / 10 ** 18)
    # print(user2.get_address())

    # ## Deployment of sicx and staking contracts

    # In[93]:

    GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
    contracts = {'staking': {'zip': 'core_contracts/staking.zip',
                             'SCORE': 'cxd8e05c1280bc2c32bf53ff61f3bb2e2ecc7d6df5'},
                 'sicx': {'zip': 'token_contracts/sicx.zip',
                          'SCORE': 'cxcff8bf80ab213fa9bbb350636a4d68f5cb4fd9c1'}
                 }
    print('Deploying staking Contract')
    deploy = list(['staking', 'sicx'])
    for directory in {"../../core_contracts", "../../token_contracts"}:
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


    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(_tx_hash):
        tx_result = icon_service.get_transaction_result(_tx_hash)
        return tx_result

    def staking_on():
        set_div_per = CallTransactionBuilder() \
            .from_(user2.get_address()) \
            .to(staking_address) \
            .nid(NID) \
            .nonce(100) \
            .method("toggleStakingOn") \
            .build()
        estimate_step = icon_service.estimate_step(set_div_per)
        step_limit = estimate_step + 10000000
        signed_transaction = SignedTransaction(set_div_per, user2, step_limit)

        tx_hash = icon_service.send_transaction(signed_transaction)


    ab = get_tx_result(tx_hash)
    assert ab['status'] == 1, 'Staking contract not deployed'
    print('staking contract Deployed')
    # if ab['status'] == 1:
    #     print('staking contract Deployed')

    staking_address = ab['scoreAddress']
    # deployment of sICX contract
    print('Deploying sIcx Contract')
    zip_file = contracts['sicx']['zip']
    deploy_transaction = DeployTransactionBuilder().from_(user2.get_address()).to(GOVERNANCE_ADDRESS).nid(
        NID).nonce(100).content_type("application/zip").params({"_admin": staking_address}).content(
        gen_deploy_data_content(zip_file)).build()

    estimate_step = icon_service.estimate_step(deploy_transaction)
    step_limit = estimate_step + 40000000
    signed_transaction = SignedTransaction(deploy_transaction, user2, step_limit)
    tx_hash = icon_service.send_transaction(signed_transaction)


    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(_tx_hash):
        tx_result = icon_service.get_transaction_result(_tx_hash)
        return tx_result


    ab = get_tx_result(tx_hash)
    # print(ab)
    # if ab['status'] == 1:
    #     print('sICX contract Deployed')
    assert ab['status'] == 1, 'sICX contract not deployed'
    print('sICX contract Deployed')
    token_address = ab['scoreAddress']
    staking_on()
    test_top_preps()
    test_rate()
    test_stake_icx()
    test_delegations()
    test_transfer()
    test_unstake()
    test_payout()
    test_partial_payout()
    test_complete_payout()