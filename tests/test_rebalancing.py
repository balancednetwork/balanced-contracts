from math import sqrt
from unittest import mock

from iconservice import Address
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice.base.exception import IconScoreException

from core_contracts.rebalancing.rebalancing import Rebalancing
from core_contracts.rebalancing.utils.checks import SenderNotGovernance, SenderNotAuthorized, SenderNotScoreOwnerError


class MockClass:

    def __init__(self, bnusd_address, dex_address, loans_address, sicx_address,
                 bnusd_lastPriceInLoop, sicx_lastPriceInLoop, dex_getPoolStats):
        self.bnusd_address = bnusd_address
        self.dex_address = dex_address
        self.sicx_address = sicx_address
        self.loans_address = loans_address
        self.call_stack = []
        outer_class = self

        class MockBNUDS:
            def lastPriceInLoop(self):
                return bnusd_lastPriceInLoop

        self.mock_bnusd = MockBNUDS()

        class MockDex:
            def getPoolStats(self, pool_address):
                return dex_getPoolStats

        self.mock_dex = MockDex()

        class MockLoans:
            def retireRedeem(self, _symbol: str, _sicx_from_lenders: int):
                outer_class.call_stack.append(f"retireRedeem( {_symbol} , {_sicx_from_lenders})")

        self.mock_loans = MockLoans()

        class MockSICX:

            def lastPriceInLoop(self):
                return sicx_lastPriceInLoop

            def transfer(self, _to: Address, _value: int, _data: bytes = None):
                outer_class.call_stack.append((_to, _value, _data))

        self.mock_sicx = MockSICX()

    def create_interface_score(self, address, score):
        if address == self.bnusd_address:
            return self.mock_bnusd
        elif address == self.dex_address:
            return self.mock_dex
        elif address == self.sicx_address:
            return self.mock_sicx
        elif address == self.loans_address:
            return self.mock_loans
        else:
            raise NotImplemented()


class TestRebalancing(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score_address = Address.from_string(f"cx{'1234' * 10}")

        self.admin = Address.from_string(f"hx{'12345' * 8}")
        self.owner = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.admin: 10 ** 21,
            self.owner: 10 ** 21}
        self.initialize_accounts(account_info)
        self.score = self.get_score_instance(Rebalancing, self.owner,
                                             on_install_params={'_governance': self.admin})

    def test_setBnusd_not_admin(self):
        with self.assertRaises(SenderNotAuthorized) as err:
            self.score.setBnusd(self.test_account1)

    def test_setBnusd_not_contract(self):
        self.set_msg(self.admin)
        with self.assertRaises(IconScoreException) as err:
            self.score.setBnusd(self.test_account1)
        self.assertIn("Rebalancing: Address provided is an EOA address. A contract address is required.",
                      str(err.exception))

    def test_setBnusd(self):
        self.set_msg(self.admin)
        address = Address.from_string(f"cx{'1010' * 10}")
        self.score.setBnusd(address)
        self.assertEqual(address, self.score._bnUSD.get())

    def test_setLoans_not_admin(self):
        with self.assertRaises(SenderNotAuthorized) as err:
            self.score.setLoans(self.test_account1)

    def test_setLoans_not_contract(self):
        self.set_msg(self.admin)
        with self.assertRaises(IconScoreException) as err:
            self.score.setLoans(self.test_account1)
        self.assertIn("Rebalancing: Address provided is an EOA address. A contract address is required.",
                      str(err.exception))

    def test_setLoans(self):
        self.set_msg(self.admin)
        address = Address.from_string(f"cx{'1010' * 10}")
        self.score.setLoans(address)
        self.assertEqual(address, self.score._loans.get())

    def test_setSicx_not_admin(self):
        with self.assertRaises(SenderNotAuthorized) as err:
            self.score.setSicx(self.test_account1)

    def test_setSicx(self):
        self.set_msg(self.admin)
        address = Address.from_string(f"cx{'1010' * 10}")
        self.score.setSicx(address)
        self.assertEqual(address, self.score._sicx.get())

    def test_setSicx_not_contract(self):
        self.set_msg(self.admin)
        with self.assertRaises(IconScoreException) as err:
            self.score.setSicx(self.test_account1)
        self.assertIn("Rebalancing: Address provided is an EOA address. A contract address is required.",
                      str(err.exception))

    def test_setGovernance_not_owner(self):
        with self.assertRaises(SenderNotScoreOwnerError) as err:
            self.score.setGovernance(self.test_account1)

    def test_setGovernance(self):
        self.set_msg(self.owner)
        address = Address.from_string(f"cx{'1010' * 10}")
        self.score.setGovernance(address)
        self.assertEqual(address, self.score._governance.get())

    def test_setGovernance_not_contract(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setGovernance(self.test_account1)
        self.assertIn("Rebalancing: Address provided is an EOA address. A contract address is required.",
                      str(err.exception))

    def test_setDex_not_admin(self):
        with self.assertRaises(SenderNotAuthorized) as err:
            self.score.setDex(self.test_account1)

    def test_setDex(self):
        self.set_msg(self.admin)
        address = Address.from_string(f"cx{'1010' * 10}")
        self.score.setDex(address)
        self.assertEqual(address, self.score._dex.get())

    def test_setDex_not_contract(self):
        self.set_msg(self.admin)
        with self.assertRaises(IconScoreException) as err:
            self.score.setDex(self.test_account1)
        self.assertIn("Rebalancing: Address provided is an EOA address. A contract address is required.",
                      str(err.exception))

    def test_sqrt(self):
        sq_root = ((i, int(sqrt(i))) for i in range(0, 11))
        for i in sq_root:
            self.assertEqual(i[1], self.score._sqrt(i[0]))

    def test_calculate_tokens_to_retire(self):
        result = self.score._calculate_tokens_to_retire(12 * 10 ** 18, 2 * 10 ** 18, 10 * 10 ** 18)
        self.assertEqual(13491933384829667540, result)

    def test_setPriceDiffThreshold_not_governance(self):
        # setup
        governance = Address.from_string(f"cx{'1010' * 10}")
        self.set_msg(self.owner)
        self.score.setGovernance(governance)
        # actual test
        with self.assertRaises(SenderNotGovernance):
            self.score.setPriceDiffThreshold(12)

    def test_setPriceDiffThreshold(self):
        # setup
        governance = self._setup_governance()
        # actual test
        self.set_msg(governance)
        self.score.setPriceDiffThreshold(12)
        self.assertEqual(12, self.score._price_threshold.get())

    def _setup_governance(self):
        governance = Address.from_string(f"cx{'1010' * 10}")
        self.set_msg(self.owner)
        self.score.setGovernance(governance)
        return governance

    def test_getPriceChangeThreshold(self):
        governance = self._setup_governance()

        self.set_msg(governance)
        self.score.setPriceDiffThreshold(12)
        self.assertEqual(12, self.score.getPriceChangeThreshold())

    def test_setSicxReceivable_not_governance(self):
        governance = self._setup_governance()
        with self.assertRaises(SenderNotGovernance):
            self.score.setSicxReceivable(12)

    def test_setSicxReceivable(self):
        governance = self._setup_governance()
        self.set_msg(governance)
        self.score.setSicxReceivable(12)
        self.assertEqual(12, self.score._sicx_receivable.get())

    def test_getSicxReceivable(self):
        governance = self._setup_governance()
        self.set_msg(governance)
        self.score.setSicxReceivable(12)
        self.assertEqual(12, self.score.getSicxReceivable())

    def test_getRebalancingStatus_true_case(self):
        bnusd_address = Address.from_string(f"cx{'7894' * 10}")
        dex_address = Address.from_string(f"cx{'7854' * 10}")
        sicx_address = Address.from_string(f"cx{'9458' * 10}")
        loans_address = Address.from_string(f"cx{'9845' * 10}")


        # setup
        self.set_msg(self.admin)
        self.score._price_threshold.set(1 * 10 ** 8)
        self.score.setDex(dex_address)
        self.score.setSicx(sicx_address)
        self.score.setBnusd(bnusd_address)

        bnusd_lastPriceInLoop = 1 * 10 ** 12
        sicx_lastPriceInLoop = 1 * 10 ** 12
        dex_getPoolStats = {"base": 0.1 * 10 ** 12, "quote": 20 * 10 ** 12}

        patched_interface_fxn = MockClass(bnusd_address=bnusd_address,
                                          dex_address=dex_address,
                                          loans_address=loans_address,
                                          sicx_address=sicx_address,
                                          bnusd_lastPriceInLoop=bnusd_lastPriceInLoop,
                                          sicx_lastPriceInLoop=sicx_lastPriceInLoop,
                                          dex_getPoolStats=dex_getPoolStats
                                          ).create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_interface_fxn):
            response = self.score.getRebalancingStatus()
            expected_list = [True, 1314213562373]
            self.assertListEqual(expected_list, response)

    def test_getRebalancingStatus_false_case(self):
        bnusd_address = Address.from_string(f"cx{'7894' * 10}")
        dex_address = Address.from_string(f"cx{'7854' * 10}")
        sicx_address = Address.from_string(f"cx{'9458' * 10}")
        loans_address = Address.from_string(f"cx{'9845' * 10}")


        # setup
        self.set_msg(self.admin)
        self.score._price_threshold.set(1 * 10 ** 18)
        self.score.setDex(dex_address)
        self.score.setSicx(sicx_address)
        self.score.setBnusd(bnusd_address)

        bnusd_lastPriceInLoop = 2 * 10 ** 18
        sicx_lastPriceInLoop = 1 * 10 ** 18
        dex_getPoolStats = {"base": 1 * 10 ** 18, "quote": 1 * 10 ** 18}

        patched_interface_fxn = MockClass(bnusd_address=bnusd_address,
                                          dex_address=dex_address,
                                          loans_address=loans_address,
                                          sicx_address=sicx_address,
                                          bnusd_lastPriceInLoop=bnusd_lastPriceInLoop,
                                          sicx_lastPriceInLoop=sicx_lastPriceInLoop,
                                          dex_getPoolStats=dex_getPoolStats
                                          ).create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_interface_fxn):
            response = self.score.getRebalancingStatus()
            expected_list = [False, 414213562373095048]
            self.assertListEqual(expected_list, response)

    def test_rebalance(self):
        bnusd_address = Address.from_string(f"cx{'7894' * 10}")
        dex_address = Address.from_string(f"cx{'7854' * 10}")
        sicx_address = Address.from_string(f"cx{'9458' * 10}")
        loans_address = Address.from_string(f"cx{'9845' * 10}")
        # setup
        self.set_msg(self.admin)
        self.score._price_threshold.set(1 * 10 ** 8)
        self.score.setDex(dex_address)
        self.score.setSicx(sicx_address)
        self.score.setBnusd(bnusd_address)
        self.score.setLoans(loans_address)
        governance = self._setup_governance()
        self.set_msg(governance)
        self.score.setSicxReceivable(12 * 10 ** 3)

        bnusd_lastPriceInLoop = 1 * 10 ** 12
        sicx_lastPriceInLoop = 1 * 10 ** 12
        dex_getPoolStats = {"base": 0.1 * 10 ** 12, "quote": 20 * 10 ** 12}

        patched_class = MockClass(bnusd_address=bnusd_address,
                                  dex_address=dex_address,
                                  loans_address=loans_address,
                                  sicx_address=sicx_address,
                                  bnusd_lastPriceInLoop=bnusd_lastPriceInLoop,
                                  sicx_lastPriceInLoop=sicx_lastPriceInLoop,
                                  dex_getPoolStats=dex_getPoolStats
                                  )
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_class.create_interface_score):
            self.score.rebalance()
            sicx_value = 12 * 10 ** 3
            expected = f"retireRedeem( bnUSD , {sicx_value})"
            self.assertEqual(expected, patched_class.call_stack[0])
