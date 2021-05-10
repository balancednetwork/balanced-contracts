import sys

sys.path.append("./")
import json
from utils import deploy_utils
from utils.deploy_utils import BalancedIconService, contracts, ICX
from utils.deploy_utils import btest_wallet, staking_wallet

deploy_utils_obj = BalancedIconService("http://18.144.108.38:9000", "custom", 3)

filename = './scenarios/tests_py/loans-liquidation.json'


def read_file_data(filename):
    with open(filename, encoding="utf8") as data_file:
        json_data = json.load(data_file)
    return json_data


test_cases = read_file_data(filename)

print("==============================================="
      " ......Testing liquidate method......."
      "=================================================")

deploy_utils_obj.deploy_and_launch_balanced()


def test_liquidation():
    # Test Liquidation
    # 1. Deposit collateral to fresh wallet
    # 2. Once Call toggleTestMode to on test mode
    # 3. Check the account standing after depositing collateral - Should be 'No Debt', and
    #    holding '0x2a6f1a22364bbe8000' worth of sICX.
    # 3a. Mints bnUSD to the test address without checking collateralization ratio
    #     With the above collateral deposit it will put the position in a standing of Liquidation.
    # 4. Check the new standing of the account. Should have added '0xad78ebc5ac6200000' bnUSD and have standing of 'Liquidate'.
    #    if not 'Liquidate' then again call 'create_test_position' method
    # 5. Call liquidate method
    # 6. Check account position , if the account standing is 'Zero' ,the account is liquidated and test successfull

    cases = test_cases['stories']
    for case in cases:
        print(case['description'])

        _icx = int(case['actions']['deposited_icx']) * ICX // 1000
        _test_icx = int(case['actions']['test_icx'])
        _test_bnUSD = int(case['actions']['test_bnUSD']) * ICX

        deploy_utils_obj.send_tx('loans', _icx, 'depositAndBorrow', {'_asset': '', '_amount': 0}, btest_wallet, False)

        res = deploy_utils_obj.call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()}, False)
        assert res['standing'] == case['actions']['expected_initial_position'] and res['assets'][
            'sICX'] == '0x2a6f1a22364bbe8000', 'Test case failed for liquidation'
        deploy_utils_obj.send_tx('loans', _test_icx, 'create_test_position',
                {'_address': btest_wallet.get_address(), '_asset': 'bnUSD', '_amount': _test_bnUSD}, btest_wallet, False)

        #     res = call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()})
        #     assert res['standing'] != case['actions']['expected_position'], 'Test case failed for liquidation'
        #     print('.....Calling create_test_position 2nd time......')
        #     send_tx('loans', _test_icx, 'create_test_position', {'_address': btest_wallet.get_address(), '_asset': 'bnUSD', '_amount': _test_bnUSD}, btest_wallet)

        res = deploy_utils_obj.call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()}, False)
        assert res['standing'] == case['actions']['expected_position'], 'Test case failed for liquidation'
        deploy_utils_obj.send_tx('loans', 0, 'liquidate', {'_owner': btest_wallet.get_address()}, btest_wallet)

        res = deploy_utils_obj.call_tx('loans', 'getAccountPositions', {'_owner': btest_wallet.get_address()}, False)
        assert res['standing'] == case['actions']['expected_result']
        print("Test Successful")
        print('............................................')


test_liquidation()
