from .test_staking_integrate_base import StakingTestBase
import os.path
import json

GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
to_stake_icx = 10000000000000000000


class BalancedTestStakingRewards(StakingTestBase):
    def test_rewards(self):
        _result = self.call_tx(self.contracts['staking'], 'getTotalStake')
        previous_stake = int(_result, 16)
        _result = self.call_tx(self.contracts['sicx'], 'totalSupply')
        total_supply = int(_result, 16)
        ab = self.send_tx(self.staking_wallet, self.contracts['staking'], to_stake_icx, 'stakeICX')
        if ab['status'] == 1:
            _result = self.call_tx(self.contracts['staking'], 'getTotalStake')
            current_stake = int(_result, 16)
            _result = self.call_tx(self.contracts['staking'], 'getLifetimeReward')
            lifetime_reward = int(_result, 16)
            daily_reward = current_stake - previous_stake - to_stake_icx
            self.assertEqual(lifetime_reward, daily_reward, "LifetimeRewards not set")
            rate = (previous_stake + daily_reward) * 1000000000000000000 // total_supply
            _result = self.call_tx(self.contracts['staking'], 'getTodayRate')
            current_rate = int(_result, 16)
            self.assertEqual(current_rate, rate, "Failed to set the rate")
            self.assertEqual(current_stake, previous_stake + to_stake_icx + daily_reward, ' Failed to stake ICX')
            _result = self.call_tx(GOVERNANCE_ADDRESS, 'getStake', {'address': self.contracts['staking']})
            self.assertEqual(current_stake, int(_result['stake'], 16), "stake in network failed")

    def test_icx_stake(self):
        params = {'_to': self.btest_wallet.get_address()}
        ab = self.send_tx(self.btest_wallet, self.contracts['staking'], 30000000000000000000, "stakeICX", params)
        if ab['status'] == 1:
            _result = self.call_tx(self.contracts['staking'], "getAddressDelegations",
                                   {'_address': self.btest_wallet.get_address()})
            dict1 = {}
            for key, value in _result.items():
                dict1[key] = int(value, 16)

            self.assertEqual(dict1, {"hx9eec61296a7010c867ce24c20e69588e2832bc52": 110000000000000000000}, 'Failed in ' \
                                                                                                           'stake_icx_after_delegation')
