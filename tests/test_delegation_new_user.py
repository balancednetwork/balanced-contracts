from .test_staking_integrate_base import StakingTestBase
from .stories.staking.new_user_delegations import stories as new_user_delegation_story

GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"


class BalancedTestStaking(StakingTestBase):
    def setUp(self):
        super().setUp()

    def test_delegation_by_new_user(self):
        test_cases = new_user_delegation_story
        for case in test_cases['stories']:
            address_list = []
            add = case['actions']['params']['_user_delegations']
            for x in add:
                address_list.append(x['_address'])
            wallet_address = self.btest_wallet.get_address()
            user = self.btest_wallet
            ab = self.send_tx(user, self.contracts['staking'], 0, 'delegate', case['actions']['params'])
            if ab['status'] == 1:
                _result = self.call_tx(self.contracts['staking'], 'getPrepList')

                for x in case['actions']['unit_test'][0]['output'].keys():
                    if x not in _result:
                        print('prepList not updated')
                        raise e
                _result = self.call_tx(self.contracts['staking'], 'getAddressDelegations', {'_address': wallet_address})
                dict1 = {}
                for key, value in _result.items():
                    dict1[key] = int(value, 16)
                self.assertEqual(dict(dict1), dict(
                    case['actions']['unit_test'][0]['output']), 'Test Case not passed for delegations')
