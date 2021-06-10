from .test_staking_integrate_base import StakingTestBase
from .stories.staking.update_stakeICX_case import stories as stake_story
from .stories.staking.update_delegation_case import stories as delegation_story
from .stories.staking.update_sicx_transfer import stories as transfer_story
from .stories.staking.update_unstake_case import stories as unstake_story

import json
import os.path
DIR_PATH = os.path.abspath(os.path.dirname(__file__))
path = os.path.abspath(os.path.join(DIR_PATH, "../update_staking_data.json"))
f = open('/home/suyog/Documents/ibriz/score/balanced/balanced-contracts/update_staking_data.json', 'r')
data = json.load(f)

GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"


# fname = os.path.join(os.path.abspath(os.path.dirname(__file__)), "staking_address.json")
#
# if os.path.isfile(fname):
#     os.remove(fname)

DIR_PATH = os.path.abspath(os.path.dirname(__file__))

class BalancedTestStaking(StakingTestBase):
    CORE_CONTRACTS_PATH = os.path.abspath(os.path.join(DIR_PATH, "../core_contracts"))

    def test_stake_icx(self):
        self.update()
        network_delegations = {}
        test_cases = stake_story
        for case in test_cases['stories']:
            if case['actions']['mint_to'] == "user1":
                wallet_address = self.btest_wallet.get_address()
                params = {"_to": wallet_address}
                deployer_wallet = self.btest_wallet
            else:
                wallet_address = self.staking_wallet.get_address()
                params = {"_to": wallet_address}
                deployer_wallet = self.staking_wallet
            self.send_tx(deployer_wallet, self.contracts['staking'], int(case['actions']['deposited_icx']),
                         case['actions']['name'], params)
            method = ['balanceOf', 'getStake', 'totalSupply', 'getAddressDelegations']
            for each in method:
                if each == 'balanceOf':
                    score_address = self.contracts['sicx']
                    params = {"_owner": wallet_address}
                elif each == 'getStake':
                    score_address = GOVERNANCE_ADDRESS
                    params = {"address": self.contracts['staking']}
                elif each == 'getAddressDelegations':
                    score_address = self.contracts['staking']
                    params = {"_address": wallet_address}
                else:
                    params = {}
                    score_address = self.contracts['sicx']
                _result = self.call_tx(score_address, each, params)
                if each == 'balanceOf':
                    to_check = int(_result, 16)
                    output_json = int(case['actions']['expected_sicx_in_user'])
                    # to_print = f'{wallet_address} total sicx is {int(_result, 16)}. Passed '

                elif each == 'getStake':
                    to_check = int(_result['stake'], 16)
                    output_json = int(case['actions']['expected_icx_staked_from_staking_contract'])
                    # to_print = f'total ICX staked from contract is  {int(_result["stake"], 16)}. Passed '
                elif each == 'getAddressDelegations':
                    result = {}
                    dict1 = {}
                    for key, value in _result.items():
                        dict1[key] = int(value, 16)
                    if case['actions']['mint_to'] == 'user1':
                        result = {
                            "hx243d2388c934fe123a2a2abffe9d48f4c7520c25": int(case["actions"]["expected_sicx_in_user"])}
                    else:
                        result = {"hxe064ff8825a522d933f2922b846dfae3c5ecd02f": (
                                    int(case["actions"]["expected_sicx_in_user"]) // 2),
                                  "hx4491a4dfc2e71474d938ce77d37be0a8654efe73": (
                                              int(case["actions"]["expected_sicx_in_user"]) // 2)
                                  }
                    to_check = result
                    output_json = dict1
                    # to_print = f'total ICX delegated evenly  {to_check}. Passed '

                else:
                    to_check = int(_result, 16)
                    output_json = int(case['actions']['total_supply_sicx'])
                    # to_print = f'total supply of sICX is  {int(_result, 16)}. Passed '

                self.assertEqual(to_check, output_json, f'{_result}, Failed in staking')
            for x in case['actions']['unit_test']:
                _result = self.call_tx(self.contracts['staking'], 'getTotalStake')
                self.assertEqual(int(_result, 16), int(x['getTotalStake']), f'{_result} Failed in staking')
            # _result = self.call_tx(GOVERNANCE_ADDRESS, 'getDelegation', {'address': self.contracts['staking']})
            # delegation = {}
            # for each in _result['delegations']:
            #     key = each['address']
            #     value = each['value']
            #     delegation[key] = int(value, 16)
            # self.assertEqual(delegation, network_delegations, 'Delegations in network failed')
            wallet_list = [self.btest_wallet, self.staking_wallet, "random"]
            prep_delegations_dict = {}
            for i in wallet_list:
                if i == "random":
                    _result = self.call_tx(self.contracts['staking'], 'getAddressDelegations',
                                           {'_address': "hx72bff0f887ef183bde1391dc61375f096e75c74a"})
                    for key, value in _result.items():
                        if key not in prep_delegations_dict.keys():
                            prep_delegations_dict[key] = int(value, 16)
                        else:
                            prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)
                else:
                    _result = self.call_tx(self.contracts['staking'], 'getAddressDelegations',
                                           {'_address': i.get_address()})
                    for key, value in _result.items():
                        if key not in prep_delegations_dict.keys():
                            prep_delegations_dict[key] = int(value, 16)
                        else:
                            prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)
            _result = self.call_tx(self.contracts['staking'], 'getPrepDelegations')
            prep_delegation = {}
            for key, value in _result.items():
                prep_delegation[key] = int(value, 16)
            del prep_delegation['hx8ac43d292fcc468f53e8377a8c01b1e82216c5a0']
            self.assertEqual(prep_delegation, prep_delegations_dict, "Failed")

    def test_the_delegations(self):
        network_delegations = {}
        previous_network_delegations = {}
        test_cases = delegation_story
        for case in test_cases['stories']:
            address_list = []
            add = case['actions']['params']['_user_delegations']
            for x in add:
                address_list.append(x['_address'])
            if case['actions']['user'] == "user1":
                wallet_address = self.btest_wallet.get_address()
                user = self.btest_wallet

            else:
                wallet_address = self.staking_wallet.get_address()
                user = self.staking_wallet
            _result = self.call_tx(GOVERNANCE_ADDRESS, "getDelegation", {'address': self.contracts['staking']})
            delegation = _result['delegations']
            for each in delegation:
                previous_network_delegations[each['address']] = int(each['value'], 16)
            self.send_tx(user, self.contracts['staking'], 0, "delegate", case['actions']['params'])
            _result = self.call_tx(self.contracts['staking'], "getPrepList")
            for x in case['actions']['unit_test'][0]['output'].keys():
                assert x in _result, 'prepList not updated'
            _result = self.call_tx(self.contracts['staking'], "getAddressDelegations", {'_address': wallet_address})
            dict1 = {}
            for key, value in _result.items():
                dict1[key] = int(value, 16)
            self.assertEqual(dict(dict1), dict(
                case['actions']['unit_test'][0]['output']), 'Test Case not passed for delegations')
            _result = self.call_tx(GOVERNANCE_ADDRESS, "getDelegation", {'address': self.contracts['staking']})
            delegation = _result['delegations']
            for each in delegation:
                network_delegations[each['address']] = int(each['value'], 16)

            output = case['actions']['unit_test'][0]['output']
            within_top_preps = case['actions']['within_top_preps']
            if within_top_preps != 'false':
                for key, value in output.items():
                    assert network_delegations[key] != previous_network_delegations[key], 'Failed to delegate'

            wallet_list = [self.btest_wallet, self.staking_wallet, "random"]
            prep_delegations_dict = {}
            for i in wallet_list:
                if i == "random":
                    _result = self.call_tx(self.contracts['staking'], 'getAddressDelegations',
                                           {'_address': "hx72bff0f887ef183bde1391dc61375f096e75c74a"})
                    for key, value in _result.items():
                        if key not in prep_delegations_dict.keys():
                            prep_delegations_dict[key] = int(value, 16)
                        else:
                            prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)
                else:
                    _result = self.call_tx(self.contracts['staking'], 'getAddressDelegations',
                                           {'_address': i.get_address()})
                    for key, value in _result.items():
                        if key not in prep_delegations_dict.keys():
                            prep_delegations_dict[key] = int(value, 16)
                        else:
                            prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)
            _result = self.call_tx(self.contracts['staking'], "getPrepDelegations")
            prep_delegation = {}
            for key, value in _result.items():
                prep_delegation[key] = int(value, 16)
                if key not in prep_delegations_dict.keys():
                    prep_delegations_dict[key] = 0
            self.assertEqual(prep_delegation, prep_delegations_dict, "Failed")

    def test_transfer(self):
        test_cases = transfer_story
        for case in test_cases['stories']:
            dict1 = {}
            dict2 = {}
            if case['actions']['sender'] == 'user1':
                wallet_address = self.btest_wallet.get_address()
                deployer_wallet = self.btest_wallet
            else:
                wallet_address = self.staking_wallet.get_address()
                deployer_wallet = self.staking_wallet
            if case['actions']['receiver'] == 'user2':
                receiver_address = self.staking_wallet.get_address()
            else:
                receiver_address = case['actions']['receiver']
            params = {'_to': receiver_address, "_value": case['actions']['total_sicx_transferred'], "_data": ''}
            self.send_tx(deployer_wallet, self.contracts['sicx'], 0, "transfer", params)
            _result = self.call_tx(self.contracts['sicx'], "balanceOf", {"_owner": receiver_address})
            self.assertEqual(int(_result, 16), int(
                case['actions']['curr_receiver_sicx']), 'The receiver did not receive the sICX from sender. Failed')

            _result = self.call_tx(self.contracts['sicx'], "balanceOf", {"_owner": wallet_address})
            self.assertEqual(int(_result, 16), int(
                case['actions']['curr_sender_sicx']), 'The sender failed to send the sICX to receiver. Failed')

            _result = self.call_tx(self.contracts['staking'], 'getAddressDelegations', {"_address": wallet_address})
            for key, value in _result.items():
                dict1[key] = int(value, 16)
            self.assertEqual(dict1, case['actions']["delegation_sender"],
                             'Delegation is changed for sender. Test Failed')
            _result = self.call_tx(self.contracts['staking'], "getAddressDelegations",
                                   {"_address": receiver_address})
            for key, value in _result.items():
                dict2[key] = int(value, 16)
            if case['actions']["delegation_receiver"] != "evenly_distribute":
                self.assertEqual(dict2, case['actions'][
                    "delegation_receiver"], 'Delegation is changed for receiver. Test Failed')
            else:
                _result = self.call_tx(self.contracts['staking'], "getAddressDelegations",
                                       {"_address": receiver_address})

                _result2 = self.call_tx(self.contracts['staking'], "getTopPreps")
                lis1 = []
                for x in _result.keys():
                    lis1.append(x)
                self.assertEqual(lis1, _result2, 'delegations is not set to top preps for the random address')

            _result2 = self.call_tx(self.contracts['staking'], "getTotalStake")

            self.assertEqual(int(_result2, 16), 210000000000000000000, "Failed to stake")

            wallet_list = [self.btest_wallet, self.staking_wallet, 'user3',"user4"]
            prep_delegations_dict = {}
            for i in wallet_list:
                if i == "user3":
                    params = "hx72bff0f887ef183bde1391dc61375f096e75c74b"
                elif i == "user4":
                    params = "hx72bff0f887ef183bde1391dc61375f096e75c74a"
                else:
                    params = i.get_address()
                _result = self.call_tx(self.contracts['staking'], "getAddressDelegations", {'_address': params})
                for key, value in _result.items():
                    if key not in prep_delegations_dict.keys():
                        prep_delegations_dict[key] = int(value, 16)
                    else:
                        prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)

            _result = self.call_tx(self.contracts['staking'], "getPrepDelegations")
            prep_delegation = {}
            for key, value in _result.items():
                prep_delegation[key] = int(value, 16)
                if key not in prep_delegations_dict.keys():
                    prep_delegations_dict[key] = 0
            self.assertEqual(prep_delegation, prep_delegations_dict, "Failed")
            top_prep_list = self.call_tx(self.contracts['staking'], "getTopPreps")
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
                prep_delegations_dict[key] += evenly_distributed_value // 100
            _result = self.call_tx(GOVERNANCE_ADDRESS, "getDelegation", {'address': self.contracts['staking']})
            delegation = _result['delegations']
            network_delegations = {}
            for each in delegation:
                network_delegations[each['address']] = int(each['value'], 16)
            self.assertEqual(prep_delegations_dict, network_delegations, 'Failed to delegate in Network')

    def update(self):
        external_contracts = ["staking"]

        txs = []
        for contract in external_contracts:
            deploy_tx = self.build_deploy_tx(
                from_=self.staking_wallet,
                to=self.contracts.get(contract, self.contracts["staking"]),
                content=os.path.abspath(os.path.join(self.CORE_CONTRACTS_PATH, contract))
            )
            txs.append(deploy_tx)
        results = self.process_transaction_bulk(
            requests=txs,
            network=self.icon_service,
            block_confirm_interval=self.BLOCK_INTERVAL
        )

    def test_unstake(self):
        test_cases = unstake_story
        count = 0
        for case in test_cases['stories']:
            count += 1
            if case['actions']['sender'] == 'user1':
                wallet_address = self.btest_wallet.get_address()
                deployer_wallet = self.btest_wallet
            else:
                wallet_address = self.staking_wallet.get_address()
                deployer_wallet = self.staking_wallet
            #     data = "{\"method\": \"unstake\",\"user\":\"hx436106433144e736a67710505fc87ea9becb141d\"}".encode("utf-8")
            data = "{\"method\": \"unstake\"}".encode("utf-8")
            params = {'_to': self.contracts['staking'], "_value": int(case['actions']['total_sicx_transferred']),
                      "_data": data}
            self.send_tx(deployer_wallet, self.contracts['sicx'], 0, "transfer", params)
            _result = self.call_tx(self.contracts['staking'], "getUnstakingAmount")
            total_unstaking_amount = int(_result, 16)
            total_unstake_json = int(case['actions']['unit_test'][0]['output'])
            self.assertEqual(total_unstaking_amount, total_unstake_json, 'getUnstakingAmount function test failed')
            _result = self.call_tx(GOVERNANCE_ADDRESS, "getStake", {"address": self.contracts['staking']})
            unstake_amount = 0
            for x in _result['unstakes']:
                unstake_amount += int(x['unstake'], 16)
            self.assertEqual(unstake_amount, int(
                case['actions']['unit_test'][0]['output']), 'Unstake request is not passed to the network. Failed')
            self.assertEqual(int(_result['stake'], 16), int(
                case['actions']['curr_total_stake']), 'Total stake in the network is not decreased. Failed')
            _result = self.call_tx(self.contracts['sicx'], "balanceOf", {"_owner": wallet_address})
            self.assertEqual(int(_result, 16), int(case['actions']['curr_sender_sicx']), "sICX not burned")
            _result = self.call_tx(self.contracts['sicx'], "totalSupply")
            self.assertEqual(int(_result, 16), int(case['actions']['curr_total_stake']),
                             "total supply not decreased")
            wallet_list = [self.btest_wallet, self.staking_wallet, 'user3','user4']
            prep_delegations_dict = {}
            for i in wallet_list:
                if i == "user3":
                    params = "hx72bff0f887ef183bde1391dc61375f096e75c74a"
                elif i == "user4":
                    params = "hx72bff0f887ef183bde1391dc61375f096e75c74a"
                else:
                    params = i.get_address()
                _result = self.call_tx(self.contracts['staking'], "getAddressDelegations", {'_address': params})
                for key, value in _result.items():
                    if key not in prep_delegations_dict.keys():
                        prep_delegations_dict[key] = int(value, 16)
                    else:
                        prep_delegations_dict[key] = prep_delegations_dict[key] + int(value, 16)

            _result = self.call_tx(self.contracts['staking'], "getPrepDelegations")
            prep_delegation = {}
            for key, value in _result.items():
                prep_delegation[key] = int(value, 16)
                if key not in prep_delegations_dict.keys():
                    prep_delegations_dict[key] = 0
            self.assertEqual(prep_delegation, prep_delegations_dict, "Failed in unstake of sicx")
            top_prep_list = self.call_tx(self.contracts['staking'], "getTopPreps")
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
                prep_delegations_dict[key] += evenly_distributed_value // 100

            _result = self.call_tx(GOVERNANCE_ADDRESS, "getDelegation", {'address': self.contracts['staking']})
            delegation = _result['delegations']
            network_delegations = {}
            for each in delegation:
                network_delegations[each['address']] = int(each['value'], 16)
            self.assertEqual(prep_delegations_dict, network_delegations, 'Failed to delegate in Network')
            linked_list = self.call_tx(self.contracts['staking'], "getUnstakeInfo")
            if count == 2:
                linked_list.pop(0)
            for each in linked_list:
                self.assertEqual(int(each[1], 16), int(case['actions']['total_sicx_transferred']),
                                 "Linked list failed")
                self.assertEqual(each[2], wallet_address, "Linked list failed")

    def test_withdraw(self):
        params = {'_to': self.staking_wallet.get_address()}
        self.send_tx(self.staking_wallet, self.contracts['staking'], 20000000000000000000, "stakeICX", params)
        _result = self.call_tx(self.contracts['staking'], "getUnstakingAmount")
        total_unstaking_amount = int(_result, 16)
        self.assertEqual(total_unstaking_amount, 10000000000000000000, 'Failed')
        _result = self.call_tx(self.contracts['staking'], "getTotalStake")
        total_stake = int(_result,16)
        self.assertEqual(total_stake,200000000000000000000,"Failed in staking")
        user2_delegations = self.call_tx(self.contracts["staking"],"getAddressDelegations",{"_address":self.staking_wallet.get_address()})
        val = 0
        for key,value in user2_delegations.items():
            val += int(value,16)
        self.assertEqual(val,30000000000000000000,"failed")

    def test_withdraw_few(self):
        params = {'_to': self.staking_wallet.get_address()}
        self.send_tx(self.staking_wallet, self.contracts['staking'], 3000000000000000000, "stakeICX", params)
        _result = self.call_tx(self.contracts['staking'], "getUnstakingAmount")
        total_unstaking_amount = int(_result, 16)
        self.assertEqual(total_unstaking_amount, 7000000000000000000, 'Failed')
        # print(
        #     "3 icx is deposited partially by user2 and as user2 has unstake request in top of the list. User1 will receive 3 icx from the contract.")
        _result = self.call_tx(self.contracts['staking'], "getUserUnstakeInfo",
                               {'_address': self.staking_wallet.get_address()})
        for x in _result:
            self.assertEqual(int(x['amount'], 16), 7000000000000000000, 'Failed in payout')

    def test_withdraw_full(self):
        params = {'_to': self.staking_wallet.get_address()}
        self.send_tx(self.staking_wallet, self.contracts['staking'], 7000000000000000000, "stakeICX", params)
        _result = self.call_tx(self.contracts['staking'], "getUnstakingAmount")
        total_unstaking_amount = int(_result, 16)
        self.assertEqual(total_unstaking_amount, 0, 'Failed')
        # print("Left 7 icx is transferred to user1")
        _result = self.call_tx(self.contracts['staking'], "getUserUnstakeInfo",
                               {'_address': self.staking_wallet.get_address()})
        self.assertEqual(_result, [], 'Failed')
        data = "{\"method\": \"unstake\"}".encode("utf-8")
        params = {'_to': self.contracts['staking'], "_value": 40 * 10 ** 18,
                  "_data": data}
        self.send_tx(self.staking_wallet, self.contracts['sicx'], 0, "transfer", params)
        signed_transaction = self.build_tx(self.btest_wallet, self.contracts['sicx'], 0, "burnFrom",
                                           {"_account": self.staking_wallet.get_address()
                                               , "_amount": 10 * 10 ** 18})
        tx_result = self.process_transaction(signed_transaction, self.icon_service, self.BLOCK_INTERVAL)
        self.assertEqual(tx_result['failure']['message'], str(self.btest_wallet.get_address()),
                         'BurnFrom called without admin')
        # self.send_tx(self.btest_wallet,self.contracts['sicx'],0,"burnFrom",{"_account":self.staking_wallet.get_address()
        #                                                                       ,"_amount":10*10**18})
        signed_transaction = self.build_tx(self.btest_wallet, self.contracts['sicx'], 0, "mintTo",
                                           {"_account": self.staking_wallet.get_address()
                                               , "_amount": 10 * 10 ** 18})
        tx_result = self.process_transaction(signed_transaction, self.icon_service, self.BLOCK_INTERVAL)
        self.assertEqual(tx_result['failure']['message'], str(self.btest_wallet.get_address()),
                         'mintTo called without admin')
        data = "{\"method\": \"unstake\"}".encode("utf-8")
        params = {'_to': self.contracts['staking'], "_value": 10 * 10 ** 18,
                  "_data": data}
        signed_transaction = self.build_tx(self.staking_wallet, self.contracts['sicx'], 0, "transfer",
                                           params)
        tx_result = self.process_transaction(signed_transaction, self.icon_service, self.BLOCK_INTERVAL)
        self.assertEqual(tx_result['failure']['message'], "Insufficient balance.","Failed")

    def test_zstake_icx_after_delegation(self):
        params = {'_to': self.btest_wallet.get_address()}
        self.send_tx(self.btest_wallet, self.contracts['staking'], 30000000000000000000, "stakeICX", params)
        _result = self.call_tx(self.contracts['staking'], "getAddressDelegations",
                               {'_address': self.btest_wallet.get_address()})
        dict1 = {}
        for key, value in _result.items():
            dict1[key] = int(value, 16)
        self.assertEqual(dict1, {"hx14219ac1b4cca98a29ec7d057afb6651a0eae461": 160000000000000000000}, 'Failed in ' \
                                                                                                      'stake_icx_after_delegation ')

    def test_zzstake_by_new_user(self):
        self.send_tx(self.btest_wallet, self.contracts['staking'], 10000000000000000000, "stakeICX")
        _result = self.call_tx(GOVERNANCE_ADDRESS, 'getDelegation', {'address': self.contracts['staking']})
        old_delegation = _result['delegations']
        prep_delegations = self.call_tx(self.contracts["staking"],"getPrepDelegations")
        top_prep_list = self.call_tx(self.contracts["staking"],"getTopPreps")
        self.send_tx(self._test1, self.contracts['staking'], 100000000000000000000, "stakeICX")
        _result = self.call_tx(self.contracts['staking'], "getAddressDelegations",
                               {'_address': self._test1.get_address()})
        val = 0
        for key,value in _result.items():
            val += int(value,16)
        prep_delegations_check = {}
        for key,value in prep_delegations.items():
            if key in top_prep_list:
                prep_delegations_check[key] = int(prep_delegations[key],16) + 1000000000000000000
            else:
                prep_delegations_check[key] = int(prep_delegations[key],16)
        updated_prep_delegations = self.call_tx(self.contracts["staking"],"getPrepDelegations")
        prep_del ={}
        for key,value in updated_prep_delegations.items():
            prep_del[key] = int(value,16)
        total_stake = self.call_tx(self.contracts["staking"],"getTotalStake")
        total_stake = int(total_stake,16)
        self.assertEqual(val,100000000000000000000,"Failed in address delegations")
        self.assertEqual(len(_result),100,"Failed")
        self.assertEqual(total_stake,310000000000000000000,"Failed")
        self.assertEqual(prep_del,prep_delegations_check,"failed in prep delegations")
        _result = self.call_tx(GOVERNANCE_ADDRESS, 'getDelegation', {'address': self.contracts['staking']})
        updated_delegation = _result['delegations']
        new_delegation ={}
        check_delegation = {}
        for each in old_delegation:
            new_delegation[each['address']] = int(each['value'], 16) + 1000000000000000000
        for each in updated_delegation:
            check_delegation[each['address']] = int(each['value'], 16)
        self.assertEqual(new_delegation,check_delegation,"failed in delegation in network")
        params = {"_user_delegations": [{"_address": "hx14219ac1b4cca98a29ec7d057afb6651a0eae461",
                                                      "_votes_in_per": "100000000000000000000"}]}
        self.send_tx(self._test1, self.contracts['staking'], 0, "delegate", params)
        _result = self.call_tx(self.contracts['staking'], "getAddressDelegations",
                               {'_address': self._test1.get_address()})
        val = 0
        for key, value in _result.items():
            val += int(value, 16)
        self.assertEqual(val, 100000000000000000000, "Failed in address delegations")
        self.assertEqual(len(_result), 1, "Failed")
        self.assertEqual(total_stake,310000000000000000000,"Failed")
        for key,value in check_delegation.items():
            if key == "hx14219ac1b4cca98a29ec7d057afb6651a0eae461":
                check_delegation[key] = check_delegation[key] + 100000000000000000000 - 1000000000000000000
            else:
                check_delegation[key] = check_delegation[key] - 1000000000000000000
        _result = self.call_tx(GOVERNANCE_ADDRESS, 'getDelegation', {'address': self.contracts['staking']})
        updated_delegation = _result['delegations']
        new_delegation={}
        for each in updated_delegation:
            new_delegation[each['address']] = int(each['value'], 16)
        self.assertEqual(new_delegation,check_delegation,"failed after delegation")