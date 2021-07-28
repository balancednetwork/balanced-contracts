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
TOKEN_ADDR5 = Address.from_string(f"cx{'5749' * 10}")
SICX_ADDR = Address.from_string(f"cx{'5128' * 10}")
STAKING_ADDR = Address.from_string(f"cx{'1234' * 10}")
BNUSD_ADDR = Address.from_string(f"cx{'5126' * 10}")
REBALANCE_ADDR = Address.from_string(f"cx{'5148' * 10}")


class MockClass:

    def __init__(self, test_score=None,
                 token_total_supply=0,
                 token_price_loop=0,
                 sicx_price_loop=0,
                 bnusd_price_loop=0,
                 token_peg=0):
        outer_cls = self
        self.token_total_supply = token_total_supply
        self.test_score = test_score
        self.token_price_loop = token_price_loop
        self.sicx_price_loop = sicx_price_loop
        self.bnusd_price_loop = bnusd_price_loop
        self.token_peg = token_peg
        self.call_array = []
        self.balance = {}

        class MockAsset:
            def __init__(self, token_id):
                self.token_id = token_id
                if token_id not in outer_cls.balance:
                    outer_cls.balance[token_id] = {}

            def getPeg(self):
                return outer_cls.token_peg

            def symbol(self):
                return str(self.token_id)

            def totalSupply(self):
                return outer_cls.token_total_supply

            def lastPriceInLoop(self):
                return self.priceInLoop()

            def priceInLoop(self):
                if self.token_id == "sICX":
                    return outer_cls.sicx_price_loop
                elif self.token_id == "bnUSD":
                    return outer_cls.bnusd_price_loop
                return outer_cls.token_price_loop

            def mint(self, _from, _amount):
                outer_cls.call_array.append(("mint", (_from, _amount)))
                self.balance[_from] = self.balance.get(_from, 0) + _amount

            def mintTo(self, _from, _amount, _data):
                outer_cls.call_array.append(("mintTo", (_from, _amount, _data)))
                outer_cls.balance[_from] = outer_cls.balance.get(_from, 0) + _amount

            def balanceOf(self, _address):
                return outer_cls.balance[self.token_id].get(_address, 0)

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
                # stack ICX internally calls
                if "sICX" not in outer_cls.balance:
                    outer_cls.balance["sICX"] = {}
                outer_cls.balance["sICX"][_to] = outer_cls.balance["sICX"].get(_to, 0) + self.icx_amt
                outer_cls.test_score._sICX_received.set(self.icx_amt)

        self.addresses = {
            STAKING_ADDR: Staking(),
            TOKEN_ADDR1: MockAsset("TOKEN1"),
            TOKEN_ADDR2: MockAsset("TOKEN2"),
            TOKEN_ADDR3: MockAsset("TOKEN3"),
            TOKEN_ADDR4: MockAsset("TOKEN4"),
            TOKEN_ADDR5: MockAsset("TOKEN5"),
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
        self.test_account3 = Address.from_string(f"hx{'12341' * 8}")
        account_info = {
            self.admin: 10 ** 21,
            self.test_account3: 10 ** 40,
            self.owner: 10 ** 21}
        self.initialize_accounts(account_info)
        self.score = self.get_score_instance(Loans, self.owner,
                                             on_install_params={'_governance': self.admin})

    def _turn_loans_on(self):
        self.set_msg(self.admin)
        self.score.turnLoansOn()
        self.set_msg(None)

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

    def _configure_loans(self):
        self._turn_loans_on()
        self._add_asset()
        self._add_sicx_asset()
        self._add_bnusd_asset()
        self._set_staking()

    def _deposit(self, account, deposit_icx_amt=0):
        self.set_msg(account, deposit_icx_amt)
        self.score.depositAndBorrow()

    def _borrow(self, account, borrow_amt=0, _asset=''):
        self.set_msg(account)
        self.score.depositAndBorrow(_asset=_asset, _amount=borrow_amt)

    def _add_asset(self):
        self.set_msg(self.owner)
        patched_cls = MockClass()
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.set_block(1, 12)
            self.score.addAsset(TOKEN_ADDR1, True, True)
            self.set_block(2, 13)
            self.score.addAsset(TOKEN_ADDR2, True, False)
            self.score.addAsset(TOKEN_ADDR5, True, False)
            self.set_block(3, 14)
            self.score.addAsset(TOKEN_ADDR3, False, True)
            self.set_block(4, 15)
            self.score.addAsset(TOKEN_ADDR4, False, False)
        self.set_msg(None)

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
        self._turn_loans_on()
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
        delegate_params = ["param1", "param2"]
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.score.delegate(delegate_params)
        self.assertTupleEqual(("delegations", delegate_params), patched_cls.call_array[0])

    def test_getDistributionsDone(self):
        self.score._rewards_done.set(True)
        self.score._dividends_done.set(False)
        expected = {"Rewards": True, "Dividends": False}
        self.assertDictEqual(expected, self.score.getDistributionsDone())

    def test_getAssetTokens(self):
        result = self.score.getAssetTokens()
        self.assertDictEqual({}, result)

        self._add_asset()
        result = self.score.getAssetTokens()
        expected = {'TOKEN1': str(TOKEN_ADDR1),
                    'TOKEN2': str(TOKEN_ADDR2),
                    'TOKEN3': str(TOKEN_ADDR3),
                    'TOKEN4': str(TOKEN_ADDR4),
                    'TOKEN5': str(TOKEN_ADDR5),
                    }
        self.assertDictEqual(expected, result)

    def test_getCollateralTokens(self):
        result = self.score.getCollateralTokens()
        self.assertDictEqual({}, result)

        self._add_asset()
        result = self.score.getCollateralTokens()
        expected = {'TOKEN1': str(TOKEN_ADDR1), 'TOKEN3': str(TOKEN_ADDR3)}
        self.assertDictEqual(expected, result)

    def test_getAccountPositions(self):
        self._configure_loans()
        patched_fnx = MockClass(self.score).create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
            self._deposit(self.test_account1, 12)
            result = self.score.getAccountPositions(self.test_account1)
        expected_result = {'pos_id': 1, 'created': 12, 'address': str(self.test_account1),
                           'snap_id': 0, 'snaps_length': 1, 'last_snap': 0, 'first day': 0, 'assets': {'sICX': 12},
                           'total_debt': 0, 'collateral': 0, 'ratio': 0, 'standing': 'Zero'}
        self.assertDictEqual(expected_result, result)

    def test_getPositionByIndex(self):
        result = self.score.getPositionByIndex()

    def test_getAvailableAssets(self):
        result = self.score.getAvailableAssets()
        self.assertDictEqual({}, result)

        self._configure_loans()

        patched_fnx = MockClass(self.score,
                                token_total_supply=0,
                                token_price_loop=25,
                                sicx_price_loop=1 * 10 ** 2,
                                bnusd_price_loop=10 ** 2).create_interface_score

        with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
            # NO LOANS AND DEPOSIT
            result = self.score.getAvailableAssets()
            expected_result = {
                'TOKEN2': {'symbol': 'TOKEN2', 'address': 'cx5784578457845784578457845784578457845784', 'peg': 0,
                           'added': 13, 'is_collateral': False, 'active': True, 'borrowers': 0, 'total_supply': 0,
                           'total_burned': 0, 'bad_debt': 0, 'liquidation_pool': 0, 'dead_market': False},
                'TOKEN5': {'symbol': 'TOKEN5', 'address': 'cx5749574957495749574957495749574957495749', 'peg': 0,
                           'added': 13, 'is_collateral': False, 'active': True, 'borrowers': 0, 'total_supply': 0,
                           'total_burned': 0, 'bad_debt': 0, 'liquidation_pool': 0, 'dead_market': False}}
            self.assertDictEqual(expected_result, result)

            # SINGLE DEPOSIT
            self._deposit(self.test_account3, 12 * 10 ** 31)
            result = self.score.getAvailableAssets()
            expected_result = {
                'TOKEN2': {'symbol': 'TOKEN2', 'address': 'cx5784578457845784578457845784578457845784', 'peg': 0,
                           'added': 13, 'is_collateral': False, 'active': True, 'borrowers': 0, 'total_supply': 0,
                           'total_burned': 0, 'bad_debt': 0, 'liquidation_pool': 0, 'dead_market': False},
                'TOKEN5': {'symbol': 'TOKEN5', 'address': 'cx5749574957495749574957495749574957495749', 'peg': 0,
                           'added': 13, 'is_collateral': False, 'active': True, 'borrowers': 0, 'total_supply': 0,
                           'total_burned': 0, 'bad_debt': 0, 'liquidation_pool': 0, 'dead_market': False}}
            self.assertDictEqual(expected_result, result)

            # SINGLE BORROW
            self._borrow(self.test_account3, borrow_amt=120 * 10 ** 18, _asset='TOKEN2')
            result = self.score.getAvailableAssets()
            expected_result = {
                'TOKEN2': {'symbol': 'TOKEN2', 'address': 'cx5784578457845784578457845784578457845784', 'peg': 0,
                           'added': 13, 'is_collateral': False, 'active': True, 'borrowers': 1, 'total_supply': 0,
                           'total_burned': 0, 'bad_debt': 0, 'liquidation_pool': 0, 'dead_market': False},
                'TOKEN5': {'symbol': 'TOKEN5', 'address': 'cx5749574957495749574957495749574957495749', 'peg': 0,
                           'added': 13, 'is_collateral': False, 'active': True, 'borrowers': 0, 'total_supply': 0,
                           'total_burned': 0, 'bad_debt': 0, 'liquidation_pool': 0, 'dead_market': False}}
            self.assertDictEqual(expected_result, result)

    def test_assetCount(self):
        result = self.score.assetCount()
        self.assertEqual(0, result)
        self._add_asset()
        result = self.score.assetCount()
        self.assertEqual(5, result)

    def test_borrowerCount(self):
        result = self.score.borrowerCount()
        self.assertEqual(0, result)

        # [SETUP] SET UP COLLATERAL FOR LOAN
        self._configure_loans()
        with mock.patch.object(self.score, "create_interface_score",
                               wraps=MockClass(self.score).create_interface_score):
            self._deposit(self.test_account1, 10 ** 18)
            result = self.score.borrowerCount()
            self.assertEqual(1, result)
            self._deposit(self.test_account1, 10 ** 18)
            result = self.score.borrowerCount()
            self.assertEqual(1, result)

            self._deposit(self.test_account2, 10 ** 21)
            result = self.score.borrowerCount()
            self.assertEqual(2, result)

    def test_hasDebt(self):
        self._configure_loans()

        token_total_supply = 1 * 10 ** 30
        token_price_loop = 25
        sicx_price_loop = 1 * 10 ** 2
        bnusd_price_loop = 10 ** 2
        patched_fnx = MockClass(self.score, token_total_supply, token_price_loop, sicx_price_loop,
                                bnusd_price_loop).create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
            self._deposit(self.test_account3, 10 ** 21)
            result = self.score.hasDebt(self.test_account3)
            self.assertFalse(result)
            self._borrow(self.test_account3, 12 * 10 ** 19, "TOKEN2")
            result = self.score.hasDebt(self.test_account3)
            self.assertTrue(result)

    def test_getSnapshot(self):
        result = self.score.getSnapshot()
        raise

    def test_addAsset_not_admin(self):
        token_address = Address.from_string(f"cx{'5135' * 10}")
        with self.assertRaises(SenderNotGovernance):
            self.score.addAsset(token_address, True, False)

    def test_addAsset_not_admin(self):
        self._add_asset()

        self.assertEqual(5, len(self.score._assets.alist))

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
            self.assertEqual("TOKEN1", asset1.symbol())
            self.assertEqual("TOKEN2", asset2.symbol())
            self.assertEqual("TOKEN3", asset3.symbol())
            self.assertEqual("TOKEN4", asset4.symbol())

        self.assertEqual(5, len(self.score._assets.slist))

        self.assertEqual(str(TOKEN_ADDR1), self.score._assets.symboldict["TOKEN1"])
        self.assertEqual(str(TOKEN_ADDR2), self.score._assets.symboldict["TOKEN2"])
        self.assertEqual(str(TOKEN_ADDR3), self.score._assets.symboldict["TOKEN3"])
        self.assertEqual(str(TOKEN_ADDR4), self.score._assets.symboldict["TOKEN4"])

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
            self.score.toggleAssetActive("TOKEN1")

    def test_toggleAssetActive(self):
        self._add_asset()
        is_active = self.score._assets["TOKEN1"].is_active()
        self.set_msg(self.owner)
        self.score.toggleAssetActive("TOKEN1")
        self.assertNotEqual(is_active, self.score._assets["TOKEN1"].is_active())

    def test_precomute(self):
        rewards_addr = Address.from_string(f'cx{"2658" * 10}')
        raise  # todo

    def test_getTotalValue(self):
        self.score.getTotalValue()

    def test_getBnusdValue(self):
        self.score.getBnusdValue()

    def test_getDataCount(self):
        self.score.getDataCount()

    def test_getDataBatch(self):
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
        self._turn_loans_on()
        self.score.checkDistributions()
        raise

    def test_tokenFallback_loans_off(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.tokenFallback()
        self.assertIn("BalancedLoans: Balanced Loans SCORE is not active.", str(err.exception))

    def test_tokenFallback_mismatch_value(self):
        self._configure_loans()
        with self.assertRaises(IconScoreException) as err:
            self.score.tokenFallback(self.test_account1, -1, None)
        self.assertIn("BalancedLoans: Amount sent must be greater than zero.", str(err.exception))

    def test_tokenFallback_mistmatch_sender(self):
        self._configure_loans()
        with self.assertRaises(IconScoreException) as err:
            self.score.tokenFallback(self.test_account1, 12, None)
        self.assertIn("BalancedLoans: The Balanced Loans contract does not accept that token type.", str(err.exception))

    def test_tokenFallback_invalid_data(self):
        self._configure_loans()
        self.set_msg(SICX_ADDR)
        with self.assertRaises(IconScoreException) as err:
            self.score.tokenFallback(self.test_account1, 12, None)
        self.assertIn(
            "BalancedLoans: Invalid data: None, returning tokens. Exception: 'NoneType' object has no attribute 'decode'",
            str(err.exception))

    def test_tokenFallback(self):
        self._configure_loans()
        self.set_msg(SICX_ADDR)

        with mock.patch.object(self.score, "depositAndBorrow", return_value=None) as mck:
            self.score.tokenFallback(self.test_account1, 12, b'{"_asset":"","_amount":12}')
        mck.assert_called_once_with("", 12, self.test_account1, 12)

        with mock.patch.object(self.score, "retireRedeem", return_value=None) as mck:
            self.score.tokenFallback(self.test_account1, 13, b'{"_asset":"","_amount":""}')
        mck.assert_called_once_with("", 13)

    def test_depositAndBorrow_loans_off(self):
        self.set_msg(self.test_account1, 12)
        with self.assertRaises(IconScoreException) as err:
            self.score.depositAndBorrow()
        self.assertIn("BalancedLoans: Balanced Loans SCORE is not active.", str(err.exception))

    def test_depositAndBorrow_unsupported_asset(self):
        self._turn_loans_on()
        self.set_msg(self.test_account1, 12)
        with self.assertRaises(IconScoreException) as err:
            self.score.depositAndBorrow(_asset="TOKEN1")
        self.assertIn("BalancedLoansAssets: sICX is not a supported asset.", str(err.exception))

    def test_deposit(self):
        self._configure_loans()
        patched_fxn = MockClass(self.score).create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_fxn):
            self._deposit(self.test_account1, 12)
        self.assertEqual(12, self.score._positions.get_pos(self.test_account1)["sICX"])

    def test_borrow_collateral(self):
        self._configure_loans()
        with self.assertRaises(IconScoreException) as err:
            self._borrow(self.test_account1, 12, "TOKEN1")
        self.assertIn("BalancedLoans: Loans of collateral assets are not allowed.", str(err.exception))

    def test_borrow_below_minimum(self):
        self._configure_loans()

        patch_fxn = MockClass(token_total_supply=100,
                              token_price_loop=10,
                              sicx_price_loop=20,
                              bnusd_price_loop=10, ).create_interface_score
        with self.assertRaises(IconScoreException) as err:
            with mock.patch.object(self.score, "create_interface_score", wraps=patch_fxn):
                self._borrow(self.test_account1, 12, "TOKEN2")
        self.assertIn("BalancedLoans: The initial loan of any asset must have a minimum value of 10.0 dollars.",
                      str(err.exception))

    def test_borrow_not_enough_collateral(self):
        self._configure_loans()
        token_total_supply = 1 * 10 ** 30
        token_price_loop = 10000
        sicx_price_loop = 1
        bnusd_price_loop = 1
        patched_fnx = MockClass(self.score, token_total_supply, token_price_loop, sicx_price_loop,
                                bnusd_price_loop).create_interface_score
        with self.assertRaises(IconScoreException) as err:
            with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
                self._borrow(self.test_account1, 120 * 10 ** 18, "TOKEN2")
        expected_message = "BalancedLoans: 0.0 collateral is insufficient to originate a loan of 120.0 TOKEN2" \
                           " when max_debt_value = 0.0, new_debt_value = 1.212e-12, " \
                           "which includes a fee of 1.2 TOKEN2, given an existing loan value of 0.0."
        self.assertIn(expected_message, str(err.exception))

    def test_borrow(self):
        self._configure_loans()

        # [SETUP] PARAMETERS TO PATCH TO GET USER LOAN INFORMATION
        token_total_supply = 1 * 10 ** 30
        token_price_loop = 25
        sicx_price_loop = 1 * 10 ** 2
        bnusd_price_loop = 10 ** 2
        patched_fnx = MockClass(self.score, token_total_supply, token_price_loop, sicx_price_loop,
                                bnusd_price_loop).create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
            # [SETUP] INITIAL DEPOSIT AS COLLATERAL
            self._deposit(self.test_account1, 10 ** 21)
            self._deposit(self.test_account2, 10 ** 21)

            # [TEST] USER1'S 1ST LOAN
            self._borrow(self.test_account1, borrow_amt=120 * 10 ** 18, _asset='TOKEN2')
            result = self.score.getAccountPositions(self.test_account1)
            expected_result = {'pos_id': 1, 'created': 12, 'address': str(self.test_account1),
                               'snap_id': 0, 'snaps_length': 1, 'last_snap': 0, 'first day': 0,
                               'assets': {'TOKEN2': 121200000000000000000, 'sICX': 1000000000000000000000},
                               'total_debt': 3030, 'collateral': 100000, 'ratio': 33003300330033003300,
                               'standing': 'Not Mining'}
            self.assertDictEqual(expected_result, result)

            # [TEST] USERS1'S 2ND LOAN
            self._borrow(self.test_account1, borrow_amt=120 * 10 ** 18, _asset='TOKEN2')

            with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
                result = self.score.getAccountPositions(self.test_account1)
            expected_result = {'pos_id': 1, 'created': 12, 'address': str(self.test_account1),
                               'snap_id': 0, 'snaps_length': 1, 'last_snap': 0, 'first day': 0,
                               'assets': {'TOKEN2': 242400000000000000000, 'sICX': 1000000000000000000000},
                               'total_debt': 6060, 'collateral': 100000, 'ratio': 16501650165016501650,
                               'standing': 'Mining'}
            self.assertDictEqual(expected_result, result)

            # [TEST] USER2'S 1ST LOAN
            self._borrow(self.test_account2, borrow_amt=120 * 10 ** 18, _asset='TOKEN2')
            with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
                result = self.score.getAccountPositions(self.test_account2)
                expected_result = {'pos_id': 2, 'created': 12, 'address': str(self.test_account2), 'snap_id': 0,
                                   'snaps_length': 1, 'last_snap': 0, 'first day': 0,
                                   'assets': {'TOKEN2': 121200000000000000000, 'sICX': 1000000000000000000000},
                                   'total_debt': 3030, 'collateral': 100000, 'ratio': 33003300330033003300,
                                   'standing': 'Not Mining'}
                self.assertDictEqual(expected_result, result)

            # [TEST] USER1'S LOAN ON A NEW TOKEN
            self._borrow(self.test_account1, borrow_amt=120 * 10 ** 18, _asset='TOKEN5')
            with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
                result = self.score.getAccountPositions(self.test_account1)
            expected_result = {'pos_id': 1, 'created': 12, 'address': str(self.test_account1),
                               'snap_id': 0, 'snaps_length': 1, 'last_snap': 0, 'first day': 0,
                               'assets': {'TOKEN2': 242400000000000000000, 'TOKEN5': 121200000000000000000,
                                          'sICX': 1000000000000000000000}, 'total_debt': 9090, 'collateral': 100000,
                               'ratio': 11001100110011001100, 'standing': 'Mining'}

            self.assertDictEqual(expected_result, result)

    def test_getDebts(self):
        self._configure_loans()

        token_total_supply = 1 * 10 ** 30
        token_price_loop = 25
        sicx_price_loop = 1 * 10 ** 2
        bnusd_price_loop = 10 ** 2
        patched_fnx = MockClass(self.score, token_total_supply, token_price_loop, sicx_price_loop,
                                bnusd_price_loop).create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
            self._deposit(self.test_account3, 10 * 10 ** 18)
            day = self.score.getDay()
            print(day)
            self._borrow(self.test_account3, 10 * 10 ** 18)

            result = self.score.getDebts([str(self.test_account3)], 0)
            print(result)
            raise

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

    def test_getTotalCollateral(self):
        result = self.score.getTotalCollateral()
        self.assertEqual(0, result)

        self._configure_loans()
        print("configured")
        token_total_supply = 1 * 10 ** 30
        token_price_loop = 25
        sicx_price_loop = 1 * 10 ** 2
        bnusd_price_loop = 10 ** 2
        patched_fnx = MockClass(self.score, token_total_supply, token_price_loop, sicx_price_loop,
                                bnusd_price_loop).create_interface_score
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_fnx):
            self.set_msg(self.test_account3, 2 * 10 ** 17)
            self.score.depositAndBorrow()
            result = self.score.getTotalCollateral()
            self.assertEqual(20, result)

            self.set_msg(self.test_account1, 3 * 10 ** 17)
            self.score.depositAndBorrow()
            result = self.score.getTotalCollateral()
            self.assertEqual(50, result)

            self.set_msg(self.test_account3, 4 * 10 ** 17)
            self.score.depositAndBorrow()
            result = self.score.getTotalCollateral()
            self.assertEqual(90, result)

    def test_retireBadDebt(self):
        raise

    def test_returnAsset(self):
        raise

    def test_retireRedeem(self):
        raise

    def test_bd_redeem(self):
        raise

    def test__originate_loan(self):
        raise

    def test_withdrawCollateral(self):
        raise

    def test_liquidate(self):
        raise

    def test_check_dead_markets(self):
        raise

    def test_send_token(self):
        raise

    def test_setGovernance_not_auth(self):
        with self.assertRaises(SenderNotScoreOwnerError):
            self.score.setGovernance()

    def test_setGovernance(self):
        self.set_msg(self.owner)
        self.score.setGovernance(SICX_ADDR)
        self.assertEqual(SICX_ADDR, self.score._governance.get())

    def test_setRebalance_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setRebalance()

    def test_setRebalance_not_contract(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setRebalance(self.test_account1)
        self.assertIn("BalancedLoans: Address provided is an EOA address. A contract address is required.",
                      str(err.exception))

    def test_setRebalance(self):
        self.set_msg(self.owner)
        self.score.setRebalance(REBALANCE_ADDR)
        self.assertEqual(REBALANCE_ADDR, self.score._rebalance.get())

    def test_setDex(self):
        raise

    def test_setAdmin_not_auth(self):
        with self.assertRaises(SenderNotGovernance):
            self.score.setAdmin()

    def test_setAdmin(self):
        self.set_msg(self.admin)
        self.score.setAdmin(SICX_ADDR)
        self.assertEqual(SICX_ADDR, self.score._admin.get())

    def test_setDividends(self):
        raise

    def test_setReserve_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setReserve()

    def test_setReserve_not_contract(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setReserve(self.admin)
        self.assertIn("BalancedLoans: Address provided is an EOA address. A contract address is required.",
                      str(err.exception))

    def test_setReserve(self):
        self.set_msg(self.owner)
        self.score.setReserve(SICX_ADDR)
        self.assertEqual(SICX_ADDR, self.score._reserve.get())

    def test_setStaking_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setStaking()

    def test_setStaking_not_contract(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setStaking(self.test_account1)
        self.assertIn("BalancedLoans: Address provided is an EOA address. A contract address is required.",
                      str(err.exception))

    def test_setStaking(self):
        self.set_msg(self.owner)
        self.score.setStaking(SICX_ADDR)
        self.assertEqual(SICX_ADDR, self.scoore._staking.get())

    def test_setMiningRatio_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setMiningRatio()

    def test_setMiningRatio(self):
        self.set_msg(self.owner)
        self.score.setMiningRatio(1)
        self.assertEqual(1, self.score._mining_ratio.get())

    def test_setLockingRatio_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setLockingRatio(1)

    def test_setLockingRatio(self):
        self.set_msg(self.owner)
        self.score.setLockingRatio(1)
        self.assertEqual(1, self.score._locking_ratio.get())

    def test_setLiquidationRatio(self):
        raise

    def test_setOriginationFee_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setOriginationFee(1)

    def test_setOriginationFee(self):
        self.set_msg(self.owner)
        self.score.setOriginationFee(1)
        self.assertEqual(1, self.score._origination_fee.get())

    def test_setRedemptionFee(self):
        raise

    def test_setLiquidationReward(self):
        raise

    def test_setNewLoanMinimum(self):
        raise

    def test_setMinMiningDebt(self):
        raise

    def test_setTimeOffset_not_governance(self):
        with self.assertRaises(SenderNotGovernance):
            self.score.setTimeOffset(1)

    def test_setTimeOffset(self):
        self.set_msg(self.admin)
        self.score.setTimeOffset(1)
        self.assertEqual(1, self.score._time_offset.get())

    def test_setMaxRetirePercent_not_governance(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setMaxRetirePercent()

    def test_setMaxRetirePercent_negative(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setMaxRetirePercent(-1)
        self.assertIn("Input parameter must be in the range 0 to 10000 points.", str(err.exception))

    def test_setMaxRetirePercent_exceed(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setMaxRetirePercent(100000)
        self.assertIn("Input parameter must be in the range 0 to 10000 points.", str(err.exception))

    def test_setMaxRetirePercent(self):
        self.set_msg(self.owner)
        self.score.setMaxRetirePercent(1)
        self.assertEqual(1, self.score._max_retire_percent.get())

    def test_setRedeemBatchSize_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setRedeemBatchSize()

    def test_setRedeemBatchSize(self):
        self.set_msg(self.owner)
        self.score.setRedeemBatchSize(12)
        self.assertEqual(12, self.score._redeem_batch.get())

    def test_getParameters(self):
        result = self.score.getParameters()
        print(result)
        raise
