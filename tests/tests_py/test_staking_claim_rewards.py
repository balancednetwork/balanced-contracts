from iconsdk.exception import JSONRPCException
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
import sys
sys.path.append("..")
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.utils.convert_type import convert_hex_str_to_int
from repeater import retry
import json
icon_service = IconService(HTTPProvider("http://localhost:9000", 3))
# NID = 80
NID = 3

# In[92]:
with open('./tests_py/contracts.json', 'r') as outfile:
    data = json.load(outfile)
user1 = KeyWallet.load("./keystores/keystore_test1.json", "test1_Account")
with open("./keystores/balanced_test.pwd", "r") as f:
    key_data = f.read()
user2 = KeyWallet.load("./keystores/balanced_test.json", key_data)
GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"



@retry(JSONRPCException, tries=10, delay=1, back_off=2)
def get_tx_result(_tx_hash):
    tx_result = icon_service.get_transaction_result(_tx_hash)
    return tx_result


to_stake_icx = 10000000000000000000
def test_daily_rewards():
    _call = CallBuilder().from_(user2.get_address()).to(data['staking_address']).method('getTotalStake').build()

    _result = icon_service.call(_call)
    previous_stake = int(_result, 16)
    _call = CallBuilder().from_(user2.get_address()).to(data['token_address']).method('totalSupply').build()

    _result = icon_service.call(_call)
    total_supply = int(_result, 16)
    set_div_per = CallTransactionBuilder().from_(user2.get_address()).to(data['staking_address']).nid(NID).nonce(
        100).method('stakeICX').value(to_stake_icx).build()
    estimate_step = icon_service.estimate_step(set_div_per)
    step_limit = estimate_step + 10000000
    signed_transaction = SignedTransaction(set_div_per, user2, step_limit)

    tx_hash = icon_service.send_transaction(signed_transaction)
    ab = get_tx_result(tx_hash)
    if ab['status'] == 1:
        _call = CallBuilder().from_(user2.get_address()).to(data['staking_address']).method('getTotalStake').build()

        _result = icon_service.call(_call)
        current_stake = int(_result, 16)
        daily_reward = current_stake - previous_stake - to_stake_icx
        # assert lifetime_reward == daily_reward, "LifetimeRewards not set"

        rate = (previous_stake+daily_reward) * 1000000000000000000 // total_supply

        _call = CallBuilder().from_(user2.get_address()).to(data['staking_address']).method('getTodayRate').build()

        _result = icon_service.call(_call)
        current_rate = int(_result, 16)
        assert current_rate == rate, "Failed to set the rate"

        assert current_stake == previous_stake + to_stake_icx + daily_reward, ' Failed to stake ICX'

        _call = CallBuilder() \
            .from_(user2.get_address()) \
            .to(GOVERNANCE_ADDRESS) \
            .method('getStake') \
            .params({'address': data['staking_address']}) \
            .build()

        _result = icon_service.call(_call)

        assert current_stake == int(_result['stake'],16), "stake in network failed"


for i in range(0,3):
    test_daily_rewards()