import sys

sys.path.append("./")
import json
from utils import deploy_utils
from utils.deploy_utils import BalancedIconService, contracts, ICX
from utils.deploy_utils import btest_wallet, staking_wallet, user1, user2

deploy_utils_obj = BalancedIconService("http://18.144.108.38:9000", "custom", 3)

filename = './scenarios/tests_py/loans-retireAssets.json'


def read_file_data(filename):
    with open(filename, encoding="utf8") as data_file:
        json_data = json.load(data_file)
    return json_data


test_cases = read_file_data(filename)


print("==============================================="
      " ......Testing retireAssets method......."
      "=================================================")

deploy_utils_obj.deploy_and_launch_balanced()


deploy_utils_obj.call_tx('loans', 'getAccountPositions', {'_owner': user1.get_address()}, False)
deploy_utils_obj.call_tx('loans', 'getAccountPositions', {'_owner': user2.get_address()}, False)


# add collateral to user1 account
deploy_utils_obj.send_tx('loans', 2000*ICX, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 500 * ICX}, user1)

# gives maximum retire amount
deploy_utils_obj.call_tx('loans', 'getMaxRetireAmount', {'_symbol': 'bnUSD'}, False)


def test_retireAssets():
    #  Now we try to retire maximum bnusd retirement allowed

    cases = test_cases['stories']
    for case in cases:
        print(case['description'])
        _to = contracts['bnUSD']['SCORE']
        meth1 = case['actions']['first_meth']
        meth2 = case['actions']['second_meth']
        val = int(case['actions']['deposited_icx'])
        data1 = case['actions']['first_params']
        first_params = {"_to": data1['_to'], "_value": data1['_value']}

        data2 = case['actions']['second_params']
        second_params = {'_symbol': data2['_symbol'], '_value': data2['_value']}

        deploy_utils_obj.send_tx('bnUSD', 0, meth1, first_params, user1, False)
        res = deploy_utils_obj.send_tx('loans', 0, meth2, second_params, user2, False)
        assert res['status'] == int(
            case['actions']['expected_status_result']), 'Retired amount is greater than the current maximum allowed'
        print('Test case passed')


test_retireAssets()
