import sys
import time

sys.path.append("./")
import json
from utils import deploy_utils
from utils.deploy_utils import BalancedIconService, contracts, ICX
from utils.deploy_utils import btest_wallet, staking_wallet, user1, user2

deploy_utils_obj = BalancedIconService("http://18.144.108.38:9000", "custom", 3)


print("==============================================="
      " ......Testing reserveFund score......."
      "=================================================")


deploy_utils_obj.send_tx('loans', 500 * ICX, 'depositAndBorrow', {'_asset': 'bnUSD', '_amount': 50 * ICX}, btest_wallet)


# Note: After depositing collateral and taking loan we need to wait 15 minutes to change the day
# and complete rewards distribution and run the below tests.

# Testing getBAlances method
def test_getBalances():
    for i in range(10):
        deploy_utils_obj.fast_send_tx('rewards', 0, 'distribute', {}, btest_wallet)

    total_balances = 0
    for contract in ['rewards', 'reserve', 'bwt', 'dex', 'daofund']:
        result = int(deploy_utils_obj.call_tx('baln', 'balanceOf', {'_owner': contracts[contract]['SCORE']}, False), 0)
        total_balances += result

    print(f'Total BALN: {total_balances / 10 ** 18}')

    res = deploy_utils_obj.call_tx('rewards', 'distStatus', {}, False)
    day = int(res['platform_day'], 0) - 1

    res = deploy_utils_obj.call_tx('reserve', 'getBalances', {}, False)
    assert int(res['BALN'], 0) / 10 ** 18 == 5000 * day, "Reserve not receiving proper rewards"
    print('Test case success')


# Testing redeem
def test_redeem():
    res = deploy_utils_obj.send_tx('reserve', 0, 'redeem', {'_to': user1.get_address(), '_amount': 10 * ICX, '_sicx_rate': 2}, btest_wallet)
    assert res['failure'][
               'message'] == 'BalancedReserveFund: The redeem method can only be called by the Loans SCORE.', 'Redeem methos can only be called from loans'
    print('Test case passed')


time.sleep(70)
test_getBalances()
test_redeem()
