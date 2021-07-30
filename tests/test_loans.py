from unittest import mock
import time

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
DIVIDENDS_ADDR = Address.from_string(f"cx{'8127' * 10}")
REWARDS_ADDR = Address.from_string(f"cx{'8471' * 10}")
RESERVE_ADDR = Address.from_string(f"cx{'8624' * 10}")
DEPLOY_TIME = None


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

        class MockDividends:
            def distribute(self):
                return True

        class MockAsset:
            def __init__(self, token_id):
                self.token_id = token_id
                if token_id not in outer_cls.balance:
                    outer_cls.balance[token_id] = {}

            def burnFrom(self, _account, _amount):
                outer_cls.balance[self.token_id][_account] = outer_cls.balance[self.token_id].get(_account, 0) - _amount

            def transfer(self, _to, _amount):
                outer_cls.balance[self.token_id][_to] = outer_cls.balance[self.token_id].get(_to, 0) + _amount

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
                self.balance[self.token_id][_from] = self.balance[self.token_id].get(_from, 0) + _amount

            def mintTo(self, _from, _amount, _data):
                outer_cls.call_array.append(("mintTo", (_from, _amount, _data)))
                outer_cls.balance[self.token_id][_from] = outer_cls.balance[self.token_id].get(_from, 0) + _amount

            def balanceOf(self, _address):
                return outer_cls.balance[self.token_id].get(_address, 0)

        class MockStaking:
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

        class MockRewards:

            def distribute(self):
                return True

        class MockReserve:
            def redeem(self, _to: Address, _amount: int, _sicx_rate: int):
                outer_cls.addresses[SICX_ADDR].mintTo(_to, _amount, None)
                outer_cls.test_score._sICX_received.set(_amount)
                return _amount

        self.addresses = {
            STAKING_ADDR: MockStaking(),
            TOKEN_ADDR1: MockAsset("TOKEN1"),
            TOKEN_ADDR2: MockAsset("TOKEN2"),
            TOKEN_ADDR3: MockAsset("TOKEN3"),
            TOKEN_ADDR4: MockAsset("TOKEN4"),
            TOKEN_ADDR5: MockAsset("TOKEN5"),
            SICX_ADDR: MockAsset('sICX'),
            BNUSD_ADDR: MockAsset("bnUSD"),
            DIVIDENDS_ADDR: MockDividends(),
            REWARDS_ADDR: MockRewards(),
            RESERVE_ADDR: MockReserve()
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
        global DEPLOY_TIME
        DEPLOY_TIME = int(str(time.time()).replace(".", ""))

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
            self.score.addAsset(BNUSD_ADDR, True, False)
        self.set_msg(None)

    def _set_rewards(self):
        self.set_msg(self.owner)
        self.score.setRewards(REWARDS_ADDR)
        self.set_msg(None)

    def _set_dividends(self):
        self.set_msg(self.owner)
        self.score.setDividends(DIVIDENDS_ADDR)
        self.set_msg(None)

    def _set_reserve(self):
        self.set_msg(self.owner)
        self.score.setReserve(RESERVE_ADDR)
        self.set_msg(None)

    def _configure_loans(self):
        self._turn_loans_on()
        self._add_asset()
        self._add_sicx_asset()
        self._add_bnusd_asset()
        self._set_staking()
        self._set_dividends()
        self._set_rewards()
        self._set_reserve()

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

    def test_turnLoansOn(self):
        with self.assertRaises(SenderNotGovernance):
            self.score.turnLoansOn()

        self.set_msg(self.admin)
        with mock.patch.object(self.score, "getDay", return_value=12):
            self.score.turnLoansOn()
        self.assertTrue(self.score._loans_on.get())
        self.assertEqual(12, self.score._current_day.get())
        self.assertEqual(1, len(self.score._positions._snapshot_db._indexes))
        self.assertEqual(12, self.score._positions._snapshot_db._indexes[0])
        result = self.score._positions._snapshot_db._get_snapshot(12, 0).snap_day.get()
        raise  # todo whats this

    def test_toggleLoansOn(self):
        with self.assertRaises(SenderNotGovernance):
            self.score.toggleLoansOn()

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

    def test_delegate(self):
        with self.assertRaises(SenderNotGovernance):
            self.score.delegate([])
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
        result = self.score.positionCount()
        self.assertEqual(0, result)

        # [SETUP] SET UP COLLATERAL FOR LOAN
        self._configure_loans()
        with mock.patch.object(self.score, "create_interface_score",
                               wraps=MockClass(self.score).create_interface_score):
            self._deposit(self.test_account1, 10 ** 18)
            result = self.score.positionCount()
            self.assertEqual(1, result)
            self._deposit(self.test_account1, 10 ** 18)
            result = self.score.positionCount()
            self.assertEqual(1, result)

            self._deposit(self.test_account2, 10 ** 21)
            result = self.score.positionCount()
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

    def test_addAsset(self):
        token_address = Address.from_string(f"cx{'5135' * 10}")
        with self.assertRaises(SenderNotAuthorized):
            self.score.addAsset(token_address, True, False)

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

    def test_toggleAssetActive(self):
        self._add_asset()
        self.set_msg(self.test_account1)
        with self.assertRaises(SenderNotAuthorized):
            self.score.toggleAssetActive("TOKEN1")

        is_active = self.score._assets["TOKEN1"].is_active()
        self.set_msg(self.owner)
        self.score.toggleAssetActive("TOKEN1")
        self.assertNotEqual(is_active, self.score._assets["TOKEN1"].is_active())

    def test_precomute(self):
        rewards_addr = Address.from_string(f'cx{"2658" * 10}')
        raise  # todo

    def test_getTotalValue(self):
        self._configure_loans()
        patched_cls = MockClass(self.score)
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self._deposit(self.test_account1, 12)
            self.score.getTotalValue('', 1)

    def test_getBnusdValue(self):
        self.score.getBnusdValue()

    def test_getDataCount(self):
        self.score.getDataCount()

    def test_getDataBatch(self):
        self.score.getDataBatch()

    def test_checkForNewDay_loans_off(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.checkForNewDay()
        self.assertEqual("BalancedLoans: Balanced Loans SCORE is not active.", err.exception.message)

    def test_checkForNewDay(self):
        self.score.checkForNewDay()
        raise

    def test_checkDistributions_loans_off(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.checkDistributions()
        self.assertEqual("BalancedLoans: Balanced Loans SCORE is not active.", err.exception.message)

    def test_checkDistributions(self):
        self._turn_loans_on()
        self.score.checkDistributions()
        raise

    def test_tokenFallback_loans_off(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.tokenFallback()
        self.assertEqual("BalancedLoans: Balanced Loans SCORE is not active.", err.exception.message)

    def test_tokenFallback_mismatch_value(self):
        self._configure_loans()
        with self.assertRaises(IconScoreException) as err:
            self.score.tokenFallback(self.test_account1, -1, None)
        self.assertEqual("BalancedLoans: Amount sent must be greater than zero.", err.exception.message)

    def test_tokenFallback_mistmatch_sender(self):
        self._configure_loans()
        with self.assertRaises(IconScoreException) as err:
            self.score.tokenFallback(self.test_account1, 12, None)
        self.assertEqual("BalancedLoans: The Balanced Loans contract does not accept that token type.",
                         err.exception.message)

    def test_tokenFallback_invalid_data(self):
        self._configure_loans()
        self.set_msg(SICX_ADDR)
        with self.assertRaises(IconScoreException) as err:
            self.score.tokenFallback(self.test_account1, 12, None)
        self.assertEqual(
            "BalancedLoans: Invalid data: None, returning tokens. Exception: 'NoneType' object has no attribute 'decode'",
            err.exception.message)

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
        self.assertEqual("BalancedLoans: Balanced Loans SCORE is not active.", err.exception.message)

    def test_depositAndBorrow_unsupported_asset(self):
        self._turn_loans_on()
        self.set_msg(self.test_account1, 12)
        with self.assertRaises(IconScoreException) as err:
            self.score.depositAndBorrow(_asset="TOKEN1")
        self.assertEqual("BalancedLoansAssets: sICX is not a supported asset.", err.exception.message)

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
        self.assertEqual("BalancedLoans: Loans of collateral assets are not allowed.", err.exception.message)

    def test_borrow_below_minimum(self):
        self._configure_loans()

        patch_fxn = MockClass(token_total_supply=100,
                              token_price_loop=10,
                              sicx_price_loop=20,
                              bnusd_price_loop=10, ).create_interface_score
        with self.assertRaises(IconScoreException) as err:
            with mock.patch.object(self.score, "create_interface_score", wraps=patch_fxn):
                self._borrow(self.test_account1, 12, "TOKEN2")
        self.assertEqual("BalancedLoans: The initial loan of any asset must have a minimum value of 10.0 dollars.",
                         err.exception.message)

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
        self.assertEqual(expected_message, err.exception.message)

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
            self._borrow(self.test_account3, 10 * 10 ** 18)

            result = self.score.getDebts([str(self.test_account3)], 0)
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

    def test_getPositionAddress_invalid_key(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.getPositionAddress(0)
        self.assertEqual("BalancedLoansPositions: That is not a valid key.", err.exception.message)

    def test_getPositionAddress(self):
        self._configure_loans()
        patched_cls = MockClass(self.score)
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self._deposit(self.test_account1, 12)
            self._deposit(self.test_account2, 12)
            result = self.score.getPositionAddress(1)
            self.assertEqual(self.test_account1, result)
            result = self.score.getPositionAddress(2)
            self.assertEqual(self.test_account2, result)

    def test_getTotalCollateral(self):
        result = self.score.getTotalCollateral()
        self.assertEqual(0, result)

        self._configure_loans()
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

    def test_retireBadDebt_loans_off(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.retireBadDebt("TOKEN1", 1)
        self.assertEqual("BalancedLoans: Balanced Loans SCORE is not active.", err.exception.message)

    def test_retireBadDebt(self):
        self._configure_loans()
        patched_cls = MockClass(self.score,
                                token_total_supply=100 * 10 ** 18,
                                token_price_loop=100 * 10 ** 18,
                                sicx_price_loop=100 * 10 ** 18,
                                bnusd_price_loop=100 * 10 ** 18,
                                token_peg=100 * 10 ** 18)
        patched_cls.addresses[BNUSD_ADDR].mintTo(self.test_account2, 10 * 10 ** 21, None)
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            # no bad debt
            self.set_msg(self.test_account2)
            with self.assertRaises(IconScoreException) as err:
                self.score.retireBadDebt("bnUSD", 10 * 10 ** 21)
            self.assertEqual("BalancedLoans: No bad debt for bnUSD.", err.exception.message)

            # LIQUIDATION START
            self.set_block(1, DEPLOY_TIME + 1)
            self._deposit(self.test_account1, 60 * 10 ** 18)
            self._borrow(self.test_account1, 11 * 10 ** 18, "bnUSD")

        sicx_price_loop = 100 * 10 ** 18
        bnusd_price_loop = 10000 * 10 ** 18
        patched_cls_1 = MockClass(self.score,
                                  token_total_supply=100 * 10 ** 18,
                                  token_price_loop=100 * 10 ** 18,
                                  sicx_price_loop=sicx_price_loop,
                                  bnusd_price_loop=bnusd_price_loop,
                                  token_peg=100 * 10 ** 18)
        patched_cls_1.balance = patched_cls.balance
        del patched_cls
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls_1.create_interface_score):
            self.score.liquidate(self.test_account1)
            # LIQUIDATION END

            with self.assertRaises(IconScoreException) as err:
                self.score.retireBadDebt("bnUSD", -1)
            self.assertEqual("BalancedLoans: Amount retired must be greater than zero.", err.exception.message)

            with self.assertRaises(IconScoreException) as err:
                self.score.retireBadDebt("bnUSD", 10 * 10 ** 41)
            self.assertEqual("BalancedLoans: Insufficient balance.", err.exception.message)

            self.set_msg(self.test_account2)
            bnuds_score = patched_cls_1.addresses[BNUSD_ADDR]
            bnusd_asset = self.score._assets["bnUSD"]
            # pay amount <= liquidation
            bad_debt_before = bnusd_asset.bad_debt.get()
            liquidation_pool_before = bnusd_asset.liquidation_pool.get()

            # liquid = bnUSD_pay * (sicx_price_loop / bnusd_price_loop)
            retire_amount = 10 ** 12
            user_balance = bnuds_score.balanceOf(self.test_account2)
            self.score.retireBadDebt("bnUSD", retire_amount)
            self.assertEqual(bad_debt_before - retire_amount, bnusd_asset.bad_debt.get())
            self.assertEqual(liquidation_pool_before - retire_amount*(sicx_price_loop//bnusd_price_loop),
                             bnusd_asset.liquidation_pool.get())
            self.assertEqual(user_balance - retire_amount, bnuds_score.balanceOf(self.test_account2))

            print("bad debt", self.score._assets["bnUSD"].bad_debt.get())
            print("liquid", self.score._assets["bnUSD"].liquidation_pool.get())
            # pay amount > liquidation
            user_balance = bnuds_score.balanceOf(self.test_account2)
            self.score.retireBadDebt("bnUSD", 10 ** 19)
            self.assertEqual(user_balance - 10 ** 19, bnuds_score.balanceOf(self.test_account2))

            print("bad debt", self.score._assets["bnUSD"].bad_debt.get())
            print("liquid", self.score._assets["bnUSD"].liquidation_pool.get())
            # check if bnusd deducted from user

        raise

    def test_returnAsset(self):
        raise

    def test_retireRedeem(self):
        raise

    def test_bd_redeem(self):
        raise

    def test__originate_loan(self):
        self.score._originate_loan()
        raise

    def test_withdrawCollateral_loans_off(self):
        with self.assertRaises(IconScoreException)as err:
            self.score.withdrawCollateral()
        self.assertEqual("BalancedLoans: Balanced Loans SCORE is not active.", err.exception.message)

    def test_withdrawCollateral_non_positive(self):
        self._configure_loans()
        patched_cls = MockClass(self.score)
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self._deposit(self.test_account3, 12)
            with self.assertRaises(IconScoreException) as err:
                self.score.withdrawCollateral(0)
            self.assertEqual("BalancedLoans: Withdraw amount must be more than zero.", err.exception.message)

    def test_withdrawCollateral_no_position(self):
        self._configure_loans()

        patched_cls = MockClass(self.score)
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.set_msg(self.test_account1)
            with self.assertRaises(IconScoreException) as err:
                self.score.withdrawCollateral(12)
            self.assertEqual("BalancedLoans: This address does not have a position on Balanced.", err.exception.message)

    def test_withdrawCollateral_not_enough_collateral(self):
        self._configure_loans()

        patched_cls = MockClass(self.score)
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self._deposit(self.test_account1, 1)
            self.set_msg(self.test_account1)
            with self.assertRaises(IconScoreException) as err:
                self.score.withdrawCollateral(12)
            self.assertEqual("BalancedLoans: Position holds less collateral than the requested withdrawal.",
                             err.exception.message)

    def test_withdrawCollateral(self):
        self._configure_loans()

        patched_cls = MockClass(self.score)
        sicx_score = patched_cls.addresses[SICX_ADDR]
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self._deposit(self.test_account1, 12)

            self.set_msg(self.test_account1)
            self.score.withdrawCollateral(2)
            self.assertEqual(2, sicx_score.balanceOf(self.test_account1))
            response = self.score.getAccountPositions(self.test_account1)
            self.assertEqual(10, response["assets"]["sICX"])

            self.score.withdrawCollateral(3)
            self.assertEqual(5, sicx_score.balanceOf(self.test_account1))
            response = self.score.getAccountPositions(self.test_account1)
            self.assertEqual(7, response["assets"]["sICX"])

    def test_liquidate_no_position(self):
        self._configure_loans()
        with self.assertRaises(IconScoreException) as err:
            self.score.liquidate(self.test_account1)
        self.assertEqual("BalancedLoans: This address does not have a position on Balanced.", err.exception.message)

    def test_liquidate(self):
        self._configure_loans()
        patched_cls = MockClass(self.score,
                                token_total_supply=100 * 10 ** 18,
                                token_price_loop=100 * 10 ** 18,
                                sicx_price_loop=100 * 10 ** 18,
                                bnusd_price_loop=100 * 10 ** 18,
                                token_peg=100 * 10 ** 18)
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            self.set_block(1, DEPLOY_TIME + 1)
            self._deposit(self.test_account3, 1000 * 10 ** 18)
            result = self.score.getAccountPositions(self.test_account3)
            self.assertEqual("No Debt", result["standing"])

            self._borrow(self.test_account3, 10 * 10 ** 18, "bnUSD")
            result = self.score.getAccountPositions(self.test_account3)
            self.assertEqual("Not Mining", result["standing"])

            self._borrow(self.test_account3, 50 * 10 ** 18, "bnUSD")
            result = self.score.getAccountPositions(self.test_account3)
            self.assertEqual("Mining", result["standing"])

            self._borrow(self.test_account3, 150 * 10 ** 18, "bnUSD")
            result = self.score.getAccountPositions(self.test_account3)
            self.assertEqual("Not Mining", result["standing"])

            self._deposit(self.test_account3, 100 * 10 ** 18)
            self._borrow(self.test_account3, 600 * 10 ** 17, "bnUSD")
            result = self.score.getAccountPositions(self.test_account3)
            self.assertEqual("Not Mining", result["standing"])

        patched_cls_new = MockClass(self.score,
                                    token_total_supply=100 * 10 ** 18,
                                    token_price_loop=100 * 10 ** 18,
                                    sicx_price_loop=100 * 10 ** 18,
                                    bnusd_price_loop=200 * 10 ** 18,
                                    token_peg=100 * 10 ** 18)
        patched_cls_new.balance = patched_cls.balance
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls_new.create_interface_score):
            result = self.score.getAccountPositions(self.test_account3)
            self.assertEqual("Locked", result["standing"])

        patched_cls_new = MockClass(self.score,
                                    token_total_supply=100 * 10 ** 18,
                                    token_price_loop=100 * 10 ** 18,
                                    sicx_price_loop=100 * 10 ** 18,
                                    bnusd_price_loop=10000 * 10 ** 18,
                                    token_peg=100 * 10 ** 18)
        patched_cls_new.balance = patched_cls.balance

        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls_new.create_interface_score):
            result = self.score.getAccountPositions(self.test_account3)
            self.assertEqual("Liquidate", result["standing"])

            self.score.liquidate(self.test_account3)
            result = self.score.getAccountPositions(self.test_account3)
            self.assertEqual("Zero", result["standing"])

    def test_check_dead_markets(self):
        raise

    def test_send_token(self):
        self._configure_loans()
        patched_cls = MockClass(self.score)
        token1_score = patched_cls.addresses[TOKEN_ADDR1]
        with mock.patch.object(self.score, "create_interface_score", wraps=patched_cls.create_interface_score):
            for i in [self.test_account1, self.test_account2]:
                blc = token1_score.balanceOf(i)
                self.assertEqual(0, blc)

                self.score._send_token("TOKEN1", i, 12, "hi")
                blc = token1_score.balanceOf(i)
                self.assertEqual(12, blc)

                self.score._send_token("TOKEN1", i, 12, "hi")
                blc = token1_score.balanceOf(i)
                self.assertEqual(24, blc)

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
        self.assertEqual("BalancedLoans: Address provided is an EOA address. A contract address is required.",
                         err.exception.message)

    def test_setRebalance(self):
        self.set_msg(self.owner)
        self.score.setRebalance(REBALANCE_ADDR)
        self.assertEqual(REBALANCE_ADDR, self.score._rebalance.get())

    def test_setDex_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setDex()

    def test_setDex(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setDex(self.test_account1)
        self.assertEqual("BalancedLoans: Address provided is an EOA address. A contract address is required.",
                         err.exception.message)

    def test_setAdmin_not_auth(self):
        with self.assertRaises(SenderNotGovernance):
            self.score.setAdmin()

    def test_setAdmin(self):
        self.set_msg(self.admin)
        self.score.setAdmin(SICX_ADDR)
        self.assertEqual(SICX_ADDR, self.score._admin.get())

    def test_setDividends_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setDividends()

    def test_setDividends_not_contract(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setDividends(self.test_account1)
        self.assertEqual("BalancedLoans: Address provided is an EOA address. A contract address is required.",
                         err.exception.message)

    def test_setDividends(self):
        self.set_msg(self.owner)
        self.score.setDividends(SICX_ADDR)
        self.assertEqual(SICX_ADDR, self.score._dividends.get())

    def test_setReserve_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setReserve()

    def test_setReserve_not_contract(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setReserve(self.admin)
        self.assertEqual("BalancedLoans: Address provided is an EOA address. A contract address is required.",
                         err.exception.message)

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
        self.assertEqual("BalancedLoans: Address provided is an EOA address. A contract address is required.",
                         err.exception.message)

    def test_setStaking(self):
        self.set_msg(self.owner)
        self.score.setStaking(SICX_ADDR)
        self.assertEqual(SICX_ADDR, self.score._staking.get())

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

    def test_setLiquidationRatio_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setLiquidationRatio(1)

    def test_setLiquidationRatio(self):
        self.set_msg(self.owner)
        self.score.setLiquidationRatio(1)
        self.assertEqual(1, self.score._liquidation_ratio.get())

    def test_setOriginationFee_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setOriginationFee(1)

    def test_setOriginationFee(self):
        self.set_msg(self.owner)
        self.score.setOriginationFee(1)
        self.assertEqual(1, self.score._origination_fee.get())

    def test_setRedemptionFee_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setRedemptionFee()

    def test_setRedemptionFee(self):
        self.set_msg(self.owner)
        self.score.setRedemptionFee(1)
        self.assertEqual(1, self.score._redemption_fee.get())

    def test_setLiquidationReward_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setLiquidationReward(1)

    def test_setLiquidationReward(self):
        self.set_msg(self.owner)
        self.score.setLiquidationReward(1)
        self.assertEqual(1, self.score._liquidation_reward.get())

    def test_setNewLoanMinimum_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setNewLoanMinimum(1)

    def test_setNewLoanMinimum(self):
        self.set_msg(self.owner)
        self.score.setNewLoanMinimum(1)
        self.assertEqual(1, self.score._new_loan_minimum.get())

    def test_setMinMiningDebt_not_auth(self):
        with self.assertRaises(SenderNotAuthorized):
            self.score.setMinMiningDebt(1)

    def test_setMinMiningDebt(self):
        self.set_msg(self.owner)
        self.score.setMinMiningDebt(1)
        self.assertEqual(1, self.score._min_mining_debt.get())

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
        self.assertEqual("Input parameter must be in the range 0 to 10000 points.", err.exception.message)

    def test_setMaxRetirePercent_exceed(self):
        self.set_msg(self.owner)
        with self.assertRaises(IconScoreException) as err:
            self.score.setMaxRetirePercent(100000)
        self.assertEqual("Input parameter must be in the range 0 to 10000 points.", err.exception.message)

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
        raise
