from .test_staking_integrate_base import StakingTestBase

GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
to_stake_icx = 10000000000000000000


class BalancedTestStakingRewards(StakingTestBase):
    def test_rewards(self):
        _result = self.call_tx(self.contracts['staking'], 'getTotalStake')
        previous_stake = int(_result, 16)
        _result = self.call_tx(self.contracts['sicx'], 'totalSupply')
        total_supply = int(_result, 16)
        print(self.get_balance(self.contracts["staking"]))
        _result = self.call_tx(self.contracts['staking'], 'getLifetimeReward')
        lifetime_reward = int(_result, 16)
        print(lifetime_reward)
        _result = self.call_tx(self.contracts['staking'], 'getUnstakingAmount')
        print(int(_result, 16))
        _result = self.call_tx(self.contracts['staking'], "claimableICX",
                               {"_address": self.staking_wallet.get_address()})
        print(int(_result, 16))  # 4 icx
        print(self.get_balance(self.contracts["staking"]))
        ab = self.send_tx(self.staking_wallet, self.contracts['staking'], to_stake_icx, 'stakeICX')
        if ab['status'] == 1:
            _result = self.call_tx(self.contracts['staking'], 'getTotalStake')
            current_stake = int(_result, 16)
            print(current_stake)
            print(previous_stake)
            _result = self.call_tx(self.contracts['staking'], 'getUnstakingAmount')
            print(int(_result, 16))
            _result = self.call_tx(self.contracts['staking'], 'getLifetimeReward')
            lifetime_reward = int(_result, 16)
            print(self.get_balance(self.contracts["staking"]))
            _result = self.call_tx(self.contracts['staking'], "claimableICX",
                                   {"_address": self.staking_wallet.get_address()})
            print(int(_result, 16))  # 4 icx
            daily_reward = current_stake - previous_stake - to_stake_icx
            self.assertEqual(lifetime_reward, daily_reward, "LifetimeRewards not set")
            rate = (previous_stake + daily_reward) * 1000000000000000000 // total_supply
            _result = self.call_tx(self.contracts['staking'], 'getTodayRate')
            current_rate = int(_result, 16)
            self.assertEqual(current_rate, rate, "Failed to set the rate")
            self.assertEqual(current_stake, previous_stake + to_stake_icx + daily_reward, ' Failed to stake ICX')
            _result = self.call_tx(GOVERNANCE_ADDRESS, 'getStake', {'address': self.contracts['staking']})
            self.assertEqual(current_stake, int(_result['stake'], 16), "stake in network failed")
            _result = self.call_tx(self.contracts['staking'], "claimableICX",
                                   {"_address": self.staking_wallet.get_address()})
            self.assertEqual(int(_result, 16), 5 * 10 ** 18, "Failed in storing claimable ICX data in db")
            prev_icx = self.get_balance(self.staking_wallet.get_address())

            tx_result = self.send_tx(self.staking_wallet, self.contracts["staking"], 0, "claimUnstakedICX",
                                     {"_to": self.staking_wallet.get_address()})
            step_price = tx_result['stepPrice']
            step_used = tx_result['stepUsed']
            txfee = (step_price * step_used)
            self.assertEqual(self.get_balance(self.staking_wallet.get_address()), prev_icx + 5 * 10 ** 18 - txfee,
                             'Failed in sending '
                             'ICX')
            ab = self.send_tx(self.btest_wallet, self.contracts['staking'], to_stake_icx, 'stakeICX')
            _result = self.call_tx(self.contracts['staking'], 'getTotalStake')
            self.assertEqual(current_stake + to_stake_icx, int(_result, 16))
            data = "{\"method\": \"unstake\"}".encode("utf-8")
            params = {'_to': self.contracts['staking'], "_value": 5 * 10 ** 18,
                      "_data": data}
            self.send_tx(self.btest_wallet, self.contracts['sicx'], 0, "transfer", params)
            prev_icx = self.get_balance(self.btest_wallet.get_address())
            _result = self.call_tx(self.contracts['staking'], 'getUnstakingAmount')
            calc = 5 * current_rate
            self.assertEqual(int(_result, 16), calc, "failed in unstaking")
            self.assertEqual(self.get_balance(self.contracts["staking"]), 0, "failed in sending ICX")
            _result = self.call_tx(self.contracts['staking'], "claimableICX",
                                   {"_address": self.staking_wallet.get_address()})
            self.assertEqual(int(_result, 16), 0, "failed in storing ICX")
            _result = self.call_tx(self.contracts['staking'], "claimableICX",
                                   {"_address": self.btest_wallet.get_address()})
            self.assertEqual(int(_result, 16), 0, "failed in storing ICX")
            ab = self.send_tx(self.staking_wallet, self.contracts['staking'], 1 * 10 ** 18, 'stakeICX')
            _result = self.call_tx(self.contracts['staking'], "claimableICX",
                                   {"_address": self.staking_wallet.get_address()})
            self.assertEqual(int(_result, 16), 0, "failed in storing ICX")
            _result = self.call_tx(self.contracts['staking'], "claimableICX",
                                   {"_address": self.btest_wallet.get_address()})
            self.assertEqual(int(_result, 16), 1 * 10 ** 18, "failed in storing ICX")
            ab = self.send_tx(self.staking_wallet, self.contracts['staking'], 1 * 10 ** 18, 'stakeICX')
            _result = self.call_tx(self.contracts['staking'], "claimableICX",
                                   {"_address": self.staking_wallet.get_address()})
            self.assertEqual(int(_result, 16), 0, "failed in storing ICX")
            _result = self.call_tx(self.contracts['staking'], "claimableICX",
                                   {"_address": self.btest_wallet.get_address()})
            self.assertEqual(int(_result, 16), 2 * 10 ** 18, "failed in storing ICX")
            tx_result = self.send_tx(self.staking_wallet, self.contracts["staking"], 0, "claimUnstakedICX",
                                     {"_to": self.btest_wallet.get_address()})
            self.assertEqual(self.get_balance(self.btest_wallet.get_address()), prev_icx + 2 * 10 ** 18,
                             'Failed in sending '
                             'ICX')

    def test_icx_stake(self):
        params = {'_to': self.btest_wallet.get_address()}
        ab = self.send_tx(self.btest_wallet, self.contracts['staking'], 1000000000000000000, "stakeICX", params)
        if ab['status'] == 1:
            _result = self.call_tx(self.contracts['staking'], "getAddressDelegations",
                                   {'_address': self.btest_wallet.get_address()})
            dict1 = {}
            for key, value in _result.items():
                dict1[key] = int(value, 16)

            self.assertEqual(dict1, {"hx243d2388c934fe123a2a2abffe9d48f4c7520c25": 89000000000000000000}, 'Failed in ' \
                                                                                                          'stake_icx_after_delegation')
            _result = self.call_tx(self.contracts['staking'], 'getTotalStake')
            current_stake = int(_result, 16)
            print(current_stake)
            _result = self.call_tx(self.contracts['staking'], 'getUnstakingAmount')
            print(int(_result, 16))
