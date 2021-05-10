import sys
import time

sys.path.append("./")
import json
from utils import deploy_utils
from utils.deploy_utils import BalancedIconService, contracts, ICX
from utils.deploy_utils import btest_wallet, staking_wallet, user1, user2

deploy_utils_obj = BalancedIconService("http://18.144.108.38:9000", "custom", 3)


filename = './scenarios/tests_py/balanced-rewards.json'


def read_file_data(filename):
    with open(filename, encoding="utf8") as data_file:
        json_data = json.load(data_file)
    return json_data


test_cases = read_file_data(filename)

print("==============================================="
      " ......Testing Rewards contract......."
      "=================================================")

deploy_utils_obj.deploy_and_launch_balanced()


def test_getBalnHolding():
    for i in range(10):
        deploy_utils_obj.fast_send_tx('rewards', 0, 'distribute', {}, btest_wallet)

    borrowerCount = int(deploy_utils_obj.call_tx('loans', 'borrowerCount', {}, False), 0)
    addresses = []
    daily_value = {}
    for i in range(1, borrowerCount + 1):
        position = deploy_utils_obj.call_tx('loans', 'getPositionByIndex', {'_index': i, '_day': -1}, False)
        addresses.append(position['address'])

    holders = deploy_utils_obj.call_tx('rewards', 'getBalnHoldings', {'_holders': addresses}, False)

    total_balances = 0
    baln_balances = {}
    for contract in ['rewards', 'reserve', 'bwt', 'dex', 'daofund']:
        result = int(deploy_utils_obj.call_tx('baln', 'balanceOf', {'_owner': contracts[contract]['SCORE']}, False), 0)
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

    res = deploy_utils_obj.call_tx('rewards', 'distStatus', {}, False)
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
    res = deploy_utils_obj.call_tx('rewards', 'getDataSourceNames', {}, False)
    assert res == ['Loans', 'sICX/ICX'], "Data source name error"
    print('Test case passed')


def test_getRecipients():
    print('Testing getRecipients method')
    res = deploy_utils_obj.call_tx('rewards', 'getRecipients', {}, False)
    assert res == ['Worker Tokens', 'Reserve Fund', 'DAOfund', 'Loans', 'sICX/ICX'], "Recipients name error"
    print('Test case passed')


def test_getRecipientsSplit():
    print('Testing getRecipientsSplit method')
    res = deploy_utils_obj.call_tx('rewards', 'getRecipientsSplit', {}, False)
    assert res == {'Worker Tokens': '0x2c68af0bb140000',
                   'Reserve Fund': '0xb1a2bc2ec50000',
                   'DAOfund': '0x58d15e176280000',
                   'Loans': '0x3782dace9d90000',
                   'sICX/ICX': '0x16345785d8a0000'}, "Recipients name error"

    print('Test case passed')


def test_getDataSources():
    print('Testing getDataSources method')
    res = deploy_utils_obj.call_tx('rewards', 'getDataSources', {}, False)
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

        res = deploy_utils_obj.call_tx('rewards', 'getSourceData', {'_name': _name}, False)
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
        deploy_utils_obj.send_tx('rewards', 0, 'claimRewards', {}, case['claiming_wallet'])
        res = deploy_utils_obj.call_tx('rewards', 'getBalnHolding', {'_holder': case['claiming_wallet'].get_address()}, False)
        assert int(res, 0) == 0, 'Rewards claiming issue'
        print('Test case passed while claiming rewards')


test_getSourceData()
test_getRecipients()
test_getDataSources()
test_getRecipientsSplit()
test_getDataSourceNames()

# Test case 1 with one borrower
print("Test case with only one user")
deploy_utils_obj.send_tx('loans', 500 * ICX, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 50 * ICX}, btest_wallet)
time.sleep(40)
test_getBalnHolding()

# Test case 2 with two borrowers
print("Test case with multiple users")
deploy_utils_obj.send_tx('loans', 500 * ICX, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 50 * ICX}, user1)
time.sleep(20)
test_getBalnHolding()

# claim rewards
test_claimRewards()
