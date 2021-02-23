# from core_contracts.loans.loans.loans import Loans
# from core_contracts.dex.dex import DEX
# from core_contracts.dummy_oracle.dummy_oracle import DummyOracle
# from core_contracts.dividends.dividends import Dividends
# from core_contracts.rewards.rewards import Rewards
# from core_contracts.governance.governance import Governance
# from core_contracts.staking.staking import Staking
# from core_contracts.reserve.reserve_fund import ReserveFund
# from token_contracts.bal.balance import BalanceToken
# from token_contracts.bwt.worker_token import WorkerToken
# from token_contracts.icd.icd import ICONDollar
# from token_contracts.sicx.sicx import StakedICX
#
# from tbears.libs.scoretest.score_test_case import ScoreTestCase
# from iconservice import Address, AddressPrefix, IconScoreException
#
#
# class TestRewards(ScoreTestCase):
#     def setUp(self):
#         super().setUp()
#
#         params = {}
#         # USDbParams = {'_initialSupply': 500000000, '_decimals': 18}
#         # oTokenParams = {"_name": "BridgeUSDInterestToken", "_symbol": "oUSDb"}
#         self.loan = self.get_score_instance(Loans, self.test_account1, params)
#         self.dex = self.get_score_instance(DEX, self.test_account1, params)
#         self.reward = self.get_score_instance(Rewards, self.test_account1, params)
#         self.gov = self.get_score_instance(Governance, self.test_account1, params)
#         # self.stk = self.get_score_instance(Staking, self.test_account1, params)
#         self.reserve = self.get_score_instance(ReserveFund, self.test_account1, params)
#         self.dummy= self.get_score_instance(DummyOracle, self.test_account1, params)
#         self.div = self.get_score_instance(Dividends, self.test_account1, params)
#
#         self.bal = self.get_score_instance(BalanceToken, self.test_account1, params)
#         self.sicx = self.get_score_instance(StakedICX, self.test_account1, params)
#         self.bwt = self.get_score_instance(WorkerToken, self.test_account1, params)
#         self.icd = self.get_score_instance(ICONDollar, self.test_account1, params)
#
#         self.set_msg(self.test_account1, 0)
#         # set functions from rewards score
#         self.reward.setGovernance(self.gov.address)
#         # self.reward.setBaln(self.bal.address)
#         # self.reward.setBwt(self.bwt.address)
#         # self.reward.setReserve(self.reserve.address)
#         # self.reward.setBatchSize(50)
#
#         # self.reward.setTimeOffset(10)
#
#     def test_name(self):
#         name = "Rewards"
#         name2 = self.reward.name()
#         self.assertEqual(name, name2)
#         print("ok")
#
#     def test_getDataSourceNames(self):
#         lis = self.reward.getDataSourceNames()
#         print(lis)
#
#     # def test_getGovernance(self):
#     #     add = self.reward.getGovernance()
#     #     self.assertEqual(add, self.gov.address)
#     #
#     # def test_getBalnAddress(self):
#     #     add = self.reward.getBaln()
#     #     self.assertEqual(add, self.bal.address)
#     #
#     # def test_getBwtAddress(self):
#     #     add = self.reward.getBwt()
#     #     self.assertEqual(add, self.bwt.address)
#     #
#     # def test_getReserveAddress(self):
#     #     add = self.reward.getReserve()
#     #     self.assertEqual(add, self.reserve.address)
#     #
#     # def test_batch(self):
#     #     size = self.reward.getBatchSize()
#     #     print(size)
#
#     def test_getRecipients(self):
#         names = self.reward.getRecipients()
#         print(names)
#
#     def test_getRecipientsSplit(self):
#         recipient = self.reward.getRecipientsSplit()
#         print(recipient)