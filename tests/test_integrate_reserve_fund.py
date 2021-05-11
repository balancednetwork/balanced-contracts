from .test_integrate_base import BalancedTestBase
from .stories.loan_retireAssets import RETURN_ASSETS_STORIES


class BalancedTestLiquidation(BalancedTestBase):

    def setUp(self):
        super().setUp()

    def test_retire(self):
        self.send_icx(self.btest_wallet, self.user1.get_address(), 2500 * 10**18)
        self.send_icx(self.btest_wallet, self.user2.get_address(), 2500 * 10**18)

