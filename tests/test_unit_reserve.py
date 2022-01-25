from unittest import mock
from iconservice import Address, IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from core_contracts.reserve.reserve_fund import ReserveFund


class MockClass:
    def __init__(self, getCollateralTokens=None, symbol=None):
        self._getCollateralTokens = getCollateralTokens
        self._symbol = symbol

    def patch_internal(self, address, score):
        return self

    def getCollateralTokens(self):
        return self._getCollateralTokens

    def symbol(self):
        return self._symbol

    def transfer(self, _to, _amount):
        pass


class TestReserveUnit(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.mock_score = Address.from_string(f"cx{'1234' * 10}")
        self.reserve = self.get_score_instance(ReserveFund, self.test_account1,
                                               on_install_params={"_governance": self.mock_score})
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)

        self.baln = Address.from_string(f"cx{'12345' * 8}")
        self.sicx = Address.from_string(f"cx{'15785' * 8}")
        self.reserve._baln_token.set(self.baln)
        self.reserve._sicx_token.set(self.sicx)
        self.reserve._sicx.set(100*10**18)
        self.reserve._baln.set(100*10**18)

    def test_disburse_and_claim(self):
        self.set_msg(self.mock_score)
        _recepient = Address.from_string('cx3784537845378453784537845378453784537845')

        _amount = [{'address': f"cx{'34567' * 8}", 'amount': 10 * 10 ** 18},
                   {'address': f"cx{'15785' * 8}", 'amount': 10 * 10 ** 18}]
        with self.assertRaises(IconScoreException) as err:
            self.reserve.disburse(_recepient, _amount)
        self.assertEqual('BalancedReserveFund: Unavailable assets in the reserve fund requested.', err.exception.message)

        _amount = [{'address': f"cx{'12345' * 8}", 'amount': 200 * 10 ** 18},
                   {'address': f"cx{'15785' * 8}", 'amount': 200 * 10 ** 18}]
        for disbursement in _amount:
            disbursement['address'] = Address.from_string(disbursement['address'])
        with self.assertRaises(IconScoreException) as err:
            self.reserve.disburse(_recepient, _amount)
        self.assertEqual('BalancedReserveFund: Insufficient balance of asset '
                         'cx1234512345123451234512345123451234512345 in the reserve fund.', err.exception.message)

        _amount = [{'address': f"cx{'12345' * 8}", 'amount': 10 * 10 ** 18},
                   {'address': f"cx{'15785' * 8}", 'amount': 10 * 10 ** 18}]
        for disbursement in _amount:
            disbursement['address'] = Address.from_string(disbursement['address'])
        self.reserve.disburse(_recepient, _amount)

        sicx_left = self.reserve._sicx.get()
        self.assertEqual(90000000000000000000, sicx_left)
        user_rewards = self.reserve._awards[_recepient][Address.from_string('cx1234512345123451234512345123451234512345')]
        self.assertEqual(10000000000000000000, user_rewards)

        # testing claim method
        mock_class = MockClass(getCollateralTokens={'sICX': 'cx1234512345123451234512345123451234512345'},
                               symbol='sICX')
        self.set_msg(_recepient)
        with mock.patch.object(self.reserve, "create_interface_score", mock_class.patch_internal):
            self.reserve.claim()

        after_claim = self.reserve._awards[_recepient][Address.from_string('cx1234512345123451234512345123451234512345')]
        self.assertEqual(0, after_claim)
