from iconservice import Address
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from util.contract_addresses import ContractAddresses
from iconservice.base.exception import IconScoreException


class TestDividendsUnit(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score = Address.from_string(f"cx{'1234' * 10}")
        self.score = self.get_score_instance(ContractAddresses, self.test_account1)

        self.governance_address = Address.from_string(f"cx{'1234' * 10}")
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)

    def _set_governance(self):
        self.set_msg(self.test_account1)
        self.score.changeGovernance(self.governance_address)
        self.set_msg(None)

    def test_changeGovernance(self):
        with self.assertRaises(IconScoreException) as err:
            self.score.changeGovernance(Address.from_string(f"cx{'1234' * 10}"))
        self.assertEqual("Unauthorized: Owner only.", err.exception.message)

        self.set_msg(self.test_account1)
        with self.assertRaises(IconScoreException) as err:
            self.score.changeGovernance("12")
        self.assertEqual("All addresses should be contract addresses.", err.exception.message)

        self.set_msg(self.test_account1)
        with self.assertRaises(IconScoreException) as err:
            self.score.changeGovernance(self.test_account3)
        self.assertEqual("All addresses should be contract addresses.", err.exception.message)

        self._set_governance()
        self.assertEqual(self.governance_address, self.score.contract_address_collection["governance"])
        self.assertEqual("governance", self.score.contract_address_array[0])

    def test_set_contract_addresses(self):
        self._set_governance()

        with self.assertRaises(IconScoreException) as err:
            self.score.set_contract_addresses([{"name": "a", "address": 12}])
        self.assertEqual("Unauthorized: Governance only.", err.exception.message)

        self.set_msg(self.governance_address)
        with self.assertRaises(IconScoreException) as err:
            self.score.set_contract_addresses([{"name": "a", "address": "12"}])
        self.assertEqual("All addresses should be contract addresses.", err.exception.message)

        self.set_msg(self.governance_address)
        with self.assertRaises(IconScoreException) as err:
            self.score.set_contract_addresses([{"name": "a", "address": self.test_account4}])
        self.assertEqual("All addresses should be contract addresses.", err.exception.message)

        self.score.set_contract_addresses([{"name": "a", "address": Address.from_string(f"cx{'2487' * 10}")},
                                           {"name": "b", "address": Address.from_string(f"cx{'8421' * 10}")}])

        self.assertEqual(self.governance_address, self.score.contract_address_collection["governance"])
        self.assertEqual(Address.from_string(f"cx{'2487' * 10}"), self.score.contract_address_collection["a"])
        self.assertEqual(Address.from_string(f"cx{'8421' * 10}"), self.score.contract_address_collection["b"])
        self.assertEqual("governance", self.score.contract_address_array[0])
        self.assertEqual("a", self.score.contract_address_array[1])
        self.assertEqual("b", self.score.contract_address_array[2])

    def test_set_address(self):
        self.set_msg(self.governance_address)

        with self.assertRaises(IconScoreException) as err:
            self.score._set_address([{"name": "a", "address": "12"}])
        self.assertEqual("All addresses should be contract addresses.", err.exception.message)

        self.set_msg(self.governance_address)
        with self.assertRaises(IconScoreException) as err:
            self.score._set_address([{"name": "a", "address": self.test_account4}])
        self.assertEqual("All addresses should be contract addresses.", err.exception.message)

        # add new addresses
        self.score._set_address([{"name": "a", "address": Address.from_string(f"cx{'2487' * 10}")},
                                 {"name": "b", "address": Address.from_string(f"cx{'8421' * 10}")}])
        self.assertEqual(Address.from_string(f"cx{'2487' * 10}"), self.score.contract_address_collection["a"])
        self.assertEqual(Address.from_string(f"cx{'8421' * 10}"), self.score.contract_address_collection["b"])
        self.assertEqual("a", self.score.contract_address_array[0])
        self.assertEqual("b", self.score.contract_address_array[1])

        # update with existing address
        self.score._set_address([{"name": "a", "address": Address.from_string(f"cx{'2487' * 10}")}])
        self.assertEqual(Address.from_string(f"cx{'2487' * 10}"), self.score.contract_address_collection["a"])
        self.assertEqual(2, len(self.score.contract_address_array))

        # update with new address
        self.score._set_address([{"name": "a", "address": Address.from_string(f"cx{'2488' * 10}")}])
        self.assertEqual(Address.from_string(f"cx{'2488' * 10}"), self.score.contract_address_collection["a"])
        self.assertEqual(2, len(self.score.contract_address_array))

    def test_get_contract_address(self):
        self._set_governance()
        self.assertEqual(self.governance_address, self.score.get_contract_address("governance"))

        self.set_msg(self.governance_address)
        self.score._set_address([{"name": "a", "address": Address.from_string(f"cx{'2488' * 10}")}])
        self.assertEqual(Address.from_string(f"cx{'2488' * 10}"), self.score.get_contract_address("a"))

    def test_get_all_contract_addresses(self):
        self._set_governance()
        self.set_msg(self.governance_address)
        self.score._set_address([{"name": "a", "address": Address.from_string(f"cx{'2488' * 10}")}])
        self.assertDictEqual(
            {'a': Address.from_string(f"cx{'2488' * 10}"),
             'governance': self.governance_address}
            , self.score.get_all_contract_addresses())
