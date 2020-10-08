from iconservice import Address
from iconservice.base.exception import DatabaseException
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from loans import Loans

class TestLoans(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score_address = Address.from_string(f"cx{'1234'*10}")
        self.loans = self.get_score_instance(Loans, self.test_account1,
                                              on_install_params={'score_address': self.mock_score_address})

        self.test_account3 = Address.from_string(f"hx{'12345'*8}")
        self.test_account4 = Address.from_string(f"hx{'1234'*10}")
        account_info = {
                        self.test_account3: 10 ** 21,
                        self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)

    def test_set_value(self):
        str_value = 'string_value'
        self.loans.setValue(str_value)
        # assert event log called with specified arguments
        self.loans.SetValue.assert_called_with(str_value)

        self.assertEqual(self.loans.getValue(), str_value)

    def test_get_value_and_set_value(self):
        # at first, value is empty string
        self.assertEqual(self.loans.getValue(), '')

        str_value = 'strValue'
        self.loans.setValue(str_value)

        self.assertEqual(self.loans.getValue(), str_value)

    # try writing value inside readonly method
    def test_write_on_readonly(self):
        self.assertRaises(DatabaseException, self.loans.write_on_readonly)

    # internal call
    def test_internal_call(self):
        self.patch_internal_method(self.mock_score_address, 'getValue', lambda: 150) # Patch the getValue function of SCORE at self.mock_score_address address with a function that takes no argument and returns 150
        value = self.loans.getSCOREValue()
        self.assertEqual(value, 150)
        self.assert_internal_call(self.mock_score_address, 'getValue') # assert getValue in self.mock_score_address is called.

        self.loans.setSCOREValue('asdf')
        self.assert_internal_call(self.mock_score_address, 'setValue', 'asdf') # assert setValue in self.mock_score_address is called with 'asdf'

    # internal call
    def test_internal_call2(self):
        # To determine whether a method is called properly with specified arguments, calling register_interface_score method is enough
        self.register_interface_score(self.mock_score_address)
        self.loans.setSCOREValue('asdf')
        self.assert_internal_call(self.mock_score_address, 'setValue', 'asdf')

    def test_msg(self):
        self.set_msg(Address.from_string(f"hx{'1234'*10}"), 3)
        self.loans.t_msg() # On the upper line, set the msg property to pass the assert statement so that no exception is raised.

        self.set_msg(Address.from_string(f"hx{'12'*20}"), 3)
        self.assertRaises(AssertionError, self.loans.t_msg) # On the upper line, set the msg property not to pass the assert statement, and raise an exception.

    def test_tx(self):
        self.set_tx(Address.from_string(f"hx{'1234'*10}"))
        self.loans.t_tx() # On the upper line, set the tx property to pass the assert statement so that no exception is raised.

        self.set_tx(Address.from_string(f"hx{'12'*20}"))
        self.assertRaises(AssertionError, self.loans.t_tx) # On the upper line, set the tx property not to pass the assert statement, and raise an exception.

    def test_block(self):
        self.set_block(3, 30)
        self.loans.t_block() # On the upper line, set the block property to pass the assert statement so that no exception is raised.

        self.set_block(3)
        self.assertRaises(AssertionError, self.loans.t_block) # On the upper line, set the block property not to pass the assert statement, and raise an exception.

    def test_update(self):
        self.loans = self.update_score(self.loans.address, Loans, on_update_params={"value": "updated_value"})
        self.assertEqual(self.loans.value.get(), "updated_value") # In the on_update method of Loans, set the value of the value to "updated_value".

    def test_get_balance(self):
        balance = self.get_balance(self.test_account3)
        self.assertEqual(balance, 10**21)

    def test_transfer(self):
        # before calling transfer method, check balance of test_account3 and test_account4
        amount = 10**21
        balance_3 = self.get_balance(self.test_account3)
        self.assertEqual(balance_3, amount)
        balance_4 = self.get_balance(self.test_account4)
        self.assertEqual(balance_4, amount)

        self.transfer(self.test_account3, self.test_account4, amount)
        # after calling transfer method, check balance of test_account3 and test_account4
        balance_3 = self.get_balance(self.test_account3)
        self.assertEqual(balance_3, 0)
        balance_4 = self.get_balance(self.test_account4)
        self.assertEqual(balance_4, amount*2)
