from math import sqrt
from unittest import mock

from iconservice import Address
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice.base.exception import IconScoreException

from core_contracts.loans.loans.loans import Loans
from core_contracts.loans.utils.consts import U_SECONDS_DAY
from core_contracts.loans.utils.checks import SenderNotGovernance, SenderNotAuthorized, SenderNotScoreOwnerError, \
    SenderNotRebalance

TOKEN_ADDR1 = Address.from_string(f"cx{'5135' * 10}")
TOKEN_ADDR2 = Address.from_string(f"cx{'5784' * 10}")
TOKEN_ADDR3 = Address.from_string(f"cx{'5964' * 10}")
TOKEN_ADDR4 = Address.from_string(f"cx{'7486' * 10}")
SICX_ADDR = Address.from_string(f"cx{'5128' * 10}")
STAKING_ADDR = Address.from_string(f"cx{'1234' * 10}")
BNUSD_ADDR = Address.from_string(f"cx{'5126' * 10}")


class MockClass:

    def __init__(self, test_score=None):
        outer_cls = self
        self.test_score = test_score
        self.call_array = []

        class MockAsset:
            def __init__(self, token_id):
                self.token_id = token_id

            def symbol(self):
                return str(self.token_id)

        class Staking:
            def __init__(self):
                self.icx_amt = None

            def delegate(self, _delegations):
                outer_cls.call_array.append(("delegations", _delegations))

            def icx(self, amt):
                outer_cls.call_array.append(("icx", amt))
                self.icx_amt = amt
                return self

            def stakeICX(self, _to):
                outer_cls.call_array.append(("stakeICX", _to))
                # stacke ICX internally calls
                outer_cls.test_score._sICX_received.set(self.icx_amt)
                return self

        self.addresses = {
            STAKING_ADDR: Staking(),
            TOKEN_ADDR1: MockAsset(1),
            TOKEN_ADDR2: MockAsset(2),
            TOKEN_ADDR3: MockAsset(3),
            TOKEN_ADDR4: MockAsset(4),
            SICX_ADDR: MockAsset('sICX'),
            BNUSD_ADDR: MockAsset("bnUSD")
        }

    def create_interface_score(self, address, score):
        score = self.addresses.get(address)
        if not score:
            raise NotImplemented()
        return score


class TestLoans(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score_address = Address.from_string(f"cx{'1234' * 10}")

        self.admin = Address.from_string(f"hx{'12345' * 8}")
        self.owner = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.admin: 10 ** 21,
            self.owner: 10 ** 21}
        self.initialize_accounts(account_info)
        self.score = self.get_score_instance(Loans, self.owner,
                                             on_install_params={'_governance': self.admin})

    def test_name(self):
        name = self.score.name()
        self.assertTrue("Balanced Loans", name)

    def test_turnLoansOn_not_governance(self):
        with self.assertRaises(SenderNotGovernance):
            self.score.turnLoansOn()

    def test_turnLoansOn(self):
        self.set_msg(self.admin)
        with mock.patch.object(self.score, "getDay", return_value=12):
            self.score.turnLoansOn()
        self.assertTrue(self.score._loans_on.get())
        self.assertEqual(12, self.score._current_day.get())
        self.assertEqual(1, len(self.score._positions._snapshot_db._indexes))
        self.assertEqual(12, self.score._positions._snapshot_db._indexes[0])
        result = self.score._positions._snapshot_db._get_snapshot(12, 0).snap_day.get()
        raise  # todo whats this
        print(result)

    def test_toggleLoansOn_not_governance(self):
        with self.assertRaises(SenderNotGovernance):
            self.score.toggleLoansOn()

    def test_toggleLoansOn(self):
        self.set_msg(self.admin)

        status = self.score._loans_on.get()
        self.score.toggleLoansOn()
        self.assertNotEqual(status, self.score._loans_on.get())

        self.score.toggleLoansOn()
        self.assertEqual(status, self.score._loans_on.get())

    def test_getLoansOn(self):
        self.assertFalse(self.score.getLoansOn())
        self._toggle_loans_on()
        self.assertTrue(self.score.getLoansOn())

    def test_getDay(self):
        self.set_block(12, 123456789123456789)
        result = self.score.getDay()
        expected = (123456789123456789 - self.score._time_offset.get()) // U_SECONDS_DAY
        self.assertEqual(expected, result)

    def test_delegate_not_governance(self):
        with self.assertRaises(SenderNotGovernance):
            self.score.delegate([])

    def test_delegate(self):
        self._set_staking()

        patched_cls = MockClass()

        self.set_msg(self.admin)
        delegate_params = ["apple", "banana"]
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.score.delegate(delegate_params)
        self.assertTupleEqual(("delegations", delegate_params), patched_cls.call_array[0])

    def test_getDistributionsDone(self):
        self.score._rewards_done.set(True)
        self.score._dividends_done.set(False)
        expected = {"Rewards": True, "Dividends": False}
        self.assertDictEqual(expected, self.score.getDistributionsDone())

    def test_getDebts(self):
        raise
        # TODO how to add debts

    def test_getMaxRetireAmount(self):
        raise

    def test_checkDeadMarkets(self):
        result = self.score.checkDeadMarkets()
        self.assertListEqual([], result)

        # todo test after creating a dead market
        raise

    def test_getNonzeroPositionCount(self):
        # todo ?
        self.score.getNonzeroPositionCount()

    def test_getPositionStanding(self):
        self.score.getPositionStanding()

    def test_getPositionAddress(self):
        self.score.getPositionAddress(0)

    def test_getAssetTokens(self):
        result = self.score.getAssetTokens()
        self.assertDictEqual({}, result)

        self._add_asset()
        result = self.score.getAssetTokens()
        expected = {'1': str(TOKEN_ADDR1),
                    '2': str(TOKEN_ADDR2),
                    '3': str(TOKEN_ADDR3),
                    '4': str(TOKEN_ADDR4)}
        self.assertDictEqual(expected, result)

    def test_getCollateralTokens(self):
        result = self.score.getCollateralTokens()
        self.assertDictEqual({}, result)

        self._add_asset()
        result = self.score.getCollateralTokens()
        expected = {'1': str(TOKEN_ADDR1), '3': str(TOKEN_ADDR3)}
        self.assertDictEqual(expected, result)

    def test_getTotalCollateral(self):
        result = self.score.getTotalCollateral()
        self.assertEqual(0, result)
        # todo: test collateraal
        raise

    def test_getAccountPositions(self):
        result = self.score.getAccountPositions()

    def test_getPositionByIndex(self):
        result = self.score.getPositionByIndex()
        print(result)

    def test_getAvailableAssets(self):
        result = self.score.getAvailableAssets()
        self.assertDictEqual({}, result)

        raise

    def test_assetCount(self):
        result = self.score.assetCount()
        self.assertEqual(0, result)
        self._add_asset()
        result = self.score.assetCount()
        self.assertEqual(4, result)

    def test_borrowerCount(self):
        result = self.score.borrowerCount()
        self.assertEqual(0, result)
        raise

    def test_hasDebt(self):
        result = self.score.hasDebt()

    def test_getSnapshot(self):
        result = self.score.getSnapshot()
        raise

    def test_addAsset_not_admin(self):
        token_address = Address.from_string(f"cx{'5135' * 10}")
        with self.assertRaises(SenderNotGovernance):
            self.score.addAsset(token_address, True, False)

    def _add_asset(self):
        self.set_msg(self.owner)
        patched_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.set_block(1, 12)
            self.score.addAsset(TOKEN_ADDR1, True, True)
            self.set_block(2, 13)
            self.score.addAsset(TOKEN_ADDR2, True, False)
            self.set_block(3, 14)
            self.score.addAsset(TOKEN_ADDR3, False, True)
            self.set_block(4, 15)
            self.score.addAsset(TOKEN_ADDR4, False, False)
        self.set_msg(None)

    def test_addAsset_not_admin(self):
        self._add_asset()

        self.assertEqual(4, len(self.score._assets.alist))

        asset1 = self.score._assets._get_asset(str(TOKEN_ADDR1))
        asset2 = self.score._assets._get_asset(str(TOKEN_ADDR2))
        asset3 = self.score._assets._get_asset(str(TOKEN_ADDR3))
        asset4 = self.score._assets._get_asset(str(TOKEN_ADDR4))

        self.assertEqual(TOKEN_ADDR1, asset1.asset_address.get())
        self.assertEqual(TOKEN_ADDR2, asset2.asset_address.get())
        self.assertEqual(TOKEN_ADDR3, asset3.asset_address.get())
        self.assertEqual(TOKEN_ADDR4, asset4.asset_address.get())

        self.assertEqual(12, asset1.added.get())
        self.assertEqual(13, asset2.added.get())
        self.assertEqual(14, asset3.added.get())
        self.assertEqual(15, asset4.added.get())

        patched_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.assertEqual("1", asset1.symbol())
            self.assertEqual("2", asset2.symbol())
            self.assertEqual("3", asset3.symbol())
            self.assertEqual("4", asset4.symbol())

        self.assertEqual(4, len(self.score._assets.slist))

        self.assertEqual(str(TOKEN_ADDR1), self.score._assets.symboldict["1"])
        self.assertEqual(str(TOKEN_ADDR2), self.score._assets.symboldict["2"])
        self.assertEqual(str(TOKEN_ADDR3), self.score._assets.symboldict["3"])
        self.assertEqual(str(TOKEN_ADDR4), self.score._assets.symboldict["4"])

        self.assertTrue(asset1._active.get())
        self.assertTrue(asset2._active.get())
        self.assertFalse(asset3._active.get())
        self.assertFalse(asset4._active.get())

        self.assertTrue(asset1._is_collateral.get())
        self.assertFalse(asset2._is_collateral.get())
        self.assertTrue(asset3._is_collateral.get())
        self.assertFalse(asset4._is_collateral.get())

    def test_toggleAssetActive_not_admin(self):
        self._add_asset()
        self.set_msg(self.test_account1)
        with self.assertRaises(SenderNotAuthorized):
            self.score.toggleAssetActive("1")

    def test_toggleAssetActive(self):
        self._add_asset()
        is_active = self.score._assets["1"].is_active()
        self.score.toggleAssetActive("1")
        self.assertNotEqual(is_active, self.score._assets["1"].is_active())

    def test_precomute(self):
        rewards_addr = Address.from_string(f'cx{"2658" * 10}')
        raise  # todo

    def test_getTotalValue(self):
        self.score.getTotalValue()

    def test_getBnusdValue(self):
        self.score.getBnusdValue()

    def test_getDataCount(self):
        self.score.getDataCount()

    def test_getDataBatch_loans_off(self):
        self.score.getDataBatch()

    def test_checkForNewDay_loans_off(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.checkForNewDay()
        self.assertIn("BalancedLoans: Balanced Loans SCORE is not active.", str(err.exception))

    def test_checkForNewDay(self):
        self.score.checkForNewDay()
        raise

    def test_checkDistributions_loans_off(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.checkDistributions()
        self.assertIn("BalancedLoans: Balanced Loans SCORE is not active.", str(err.exception))

    def test_checkDistributions(self):
        self._toggle_loans_on()
        self.score.checkDistributions()
        raise

    def test_tokenFallback_loans_off(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.tokenFallback()
        self.assertIn("BalancedLoans: Balanced Loans SCORE is not active.", str(err.exception))

    def test_tokenFallback(self):
        self.score.tokenFallback()
        raise

    def test_depositAndBorrow_loans_off(self):
        self.set_msg(self.test_account1, 12)
        with self.assertRaises(IconScoreException) as err:
            self.score.depositAndBorrow()
        self.assertIn("BalancedLoans: Balanced Loans SCORE is not active.", str(err.exception))

    def _toggle_loans_on(self):
        self.set_msg(self.admin)
        self.score.toggleLoansOn()
        self.set_msg(None)

    def test_depositAndBorrow_unsupported_asset(self):
        self._toggle_loans_on()
        self.set_msg(self.test_account1, 12)
        with self.assertRaises(IconScoreException) as err:
            self.score.depositAndBorrow(_asset="1")
        self.assertIn("BalancedLoansAssets: sICX is not a supported asset.", str(err.exception))

    def _add_sicx_asset(self):
        self.set_msg(self.owner)
        patched_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.set_block(1, 12)
            self.score.addAsset(SICX_ADDR, True, True)
        self.set_msg(None)

    def _set_staking(self):
        self.set_msg(self.owner)
        self.score.setStaking(STAKING_ADDR)
        self.set_msg(None)

    def _add_bnusd_asset(self):
        self.set_msg(self.owner)
        patched_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.set_block(1, 12)
            self.score.addAsset(BNUSD_ADDR, True, True)
        self.set_msg(None)

    def _configure_laons(self):
        self._toggle_loans_on()
        self._add_asset()
        self._add_sicx_asset()
        self._add_bnusd_asset()
        self._set_staking()

    def test_depositAndBorrow(self):
        self._configure_laons()

        self.set_msg(self.test_account1, 12)
        patched_fnx = MockClass(self.score).create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
            self.score.depositAndBorrow(_asset="1")
