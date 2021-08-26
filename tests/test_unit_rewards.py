from iconservice import Address
from iconservice.base.exception import IconScoreException
from unittest import mock
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from core_contracts.rewards.rewards import Rewards


class MockClass:
    def __init__(self):
        class MockBaln:
            def mint(self, amount: int):
                pass

            def transfer(self, _to: Address, _value: int, _data: bytes = None):
                pass

        self.mockbaln = MockBaln()
        pass

    def create_interface_score(self, address: Address, score):
        return self.mockbaln


class TestRewards(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score = Address.from_string(f"cx{'1234' * 10}")
        self.rewards = self.get_score_instance(Rewards, self.test_account1,
                                               on_install_params={"_governance": self.mock_score})
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)

    def test_updateBalTokenDistPercentage_verify_snapshot(self):
        mock_class = MockClass()
        self.set_block(1, 1 * 24 * 60 * 60 * 10 ** 6)
        # test the initial snapshot
        self.assertDictEqual({}, self.rewards.recipientAt(1))
        self.assertDictEqual({}, self.rewards.recipientAt(0))
        self.assertDictEqual({}, self.rewards.recipientAt(60))
        # update the recipent_split percentage

        test_list = [{'recipient_name': 'Reserve Fund', 'dist_percent': 70 * 10 ** 16},
                     {'recipient_name': 'DAOfund', 'dist_percent': 10 * 10 ** 16},
                     {'recipient_name': 'Worker Tokens', 'dist_percent': 20 * 10 ** 16}]
        self.set_msg(self.mock_score)
        self.rewards.updateBalTokenDistPercentage(test_list)
        check_split = {}
        for x in test_list:
            name = x['recipient_name']
            per = x['dist_percent']
            check_split[name] = per
        self.assertDictEqual(check_split, self.rewards.getRecipientsSplit())
        self.assertDictEqual({}, self.rewards.recipientAt(0))
        self.assertDictEqual(check_split, self.rewards.recipientAt(60))
        self.assertDictEqual(check_split, self.rewards.recipientAt(1))
        with mock.patch.object(self.rewards, "create_interface_score", wraps=mock_class.create_interface_score):
            self.set_block(1, 9 * 24 * 60 * 60 * 10 ** 6)
            # day is set to 9 and new recipents are added

            recipient_list = [{'recipient_name': 'Loans', 'dist_percent': 25 * 10 ** 16},
                              {'recipient_name': 'sICX/ICX', 'dist_percent': 10 * 10 ** 16},
                              {'recipient_name': 'Worker Tokens', 'dist_percent': 20 * 10 ** 16},
                              {'recipient_name': 'Reserve Fund', 'dist_percent': 5 * 10 ** 16},
                              {'recipient_name': 'DAOfund', 'dist_percent': 225 * 10 ** 15},
                              {'recipient_name': 'sICX/bnUSD', 'dist_percent': 175 * 10 ** 15}]
            for i, items_dict in enumerate(recipient_list):
                add = f"cx{str(i) * 40}"
                if items_dict["recipient_name"] != "Worker Tokens" or items_dict["recipient_name"] != "Reserve Fund" or \
                        items_dict["recipient_name"] != "DAOfund":
                    self.rewards.addNewDataSource(items_dict["recipient_name"], Address.from_string(add))
            self.rewards.updateBalTokenDistPercentage(recipient_list)
            check_split2 = {}
            for x in recipient_list:
                name = x['recipient_name']
                per = x['dist_percent']
                check_split2[name] = per
            self.assertDictEqual({}, self.rewards.recipientAt(0))
            self.assertDictEqual(check_split, self.rewards.recipientAt(8))
            self.assertDictEqual(check_split2, self.rewards.recipientAt(60))
            self.assertDictEqual(check_split2, self.rewards.recipientAt(9))
            self.assertDictEqual(check_split, self.rewards.recipientAt(1))

            self.assertDictEqual(check_split, self.rewards.recipientAt(8))
            self.rewards.distribute()
            self.set_block(1, 11 * 24 * 60 * 60 * 10 ** 6)
            self.rewards.distribute()

    def test_updateBalTokenDistPercentage(self):
        recipient_list = [{'recipient_name': 'Reserve Fund', 'dist_percent': 70 * 10 ** 16},
                          {'recipient_name': 'DAOfund', 'dist_percent': 10 * 10 ** 16},
                          {'recipient_name': 'Worker Tokens', 'dist_percent': 20 * 10 ** 16}]
        self.set_msg(self.mock_score)

        # mismatching the length of the recipients
        try:
            recipient_list.append({'recipient_name': 'Worker Tokens2', 'dist_percent': 20 * 10 ** 16})
            self.rewards.updateBalTokenDistPercentage(recipient_list)
        except IconScoreException as e:
            self.assertEqual("BalancedRewards: Recipient lists lengths mismatched!", e.message)
        # providing incorrect name as a recipients
        try:
            incorrect_recipient = [{'recipient_name': 'Reserve Fund2', 'dist_percent': 70 * 10 ** 16},
                              {'recipient_name': 'DAOfund2', 'dist_percent': 10 * 10 ** 16},
                              {'recipient_name': 'Worker Tokens2', 'dist_percent': 20 * 10 ** 16}]
            self.rewards.updateBalTokenDistPercentage(incorrect_recipient)
        except IconScoreException as e:
            self.assertEqual("BalancedRewards: Recipient Reserve Fund2 does not exist.", e.message)

        # providing distribution percentage more than 100

        try:
            test_percentage = [{'recipient_name': 'Reserve Fund', 'dist_percent': 70 * 10 ** 16},
                              {'recipient_name': 'DAOfund', 'dist_percent': 10 * 10 ** 16},
                              {'recipient_name': 'Worker Tokens', 'dist_percent': 30 * 10 ** 16}]
            self.rewards.updateBalTokenDistPercentage(test_percentage)
        except IconScoreException as e:
            self.assertEqual("BalancedRewards: Total percentage does not sum up to 100.", e.message)


        # test the actual function with correct data

        recipient_list.pop()
        self.rewards.updateBalTokenDistPercentage(recipient_list)
        day = self.rewards._get_day()
        expected = {}
        for recipient in recipient_list:
            expected[recipient["recipient_name"]] = recipient["dist_percent"]
        print(self.rewards.recipientAt(day))
        self.assertEqual(expected, self.rewards.recipientAt(day))
        # self.assertEqual(10 * 10 ** 16, self.rewards.recipientAt('DAOfund', day))
        # self.assertEqual(70 * 10 ** 16, self.rewards.recipientAt('Reserve Fund', day))
        # self.assertEqual(20 * 10 ** 16, self.rewards.recipientAt('Worker Tokens', day))
        self.assertEqual(day, self.rewards._data_source_db["DAOfund"].get_data()['day'])
        self.assertEqual(day, self.rewards._data_source_db["Reserve Fund"].get_data()['day'])
        self.assertEqual(day, self.rewards._data_source_db["Worker Tokens"].get_data()['day'])

    def test_addNewDataSource(self):
        self.set_msg(self.mock_score)
        day = self.rewards._get_day()
        # test if the data source address is a contract or not

        try:
            self.rewards.addNewDataSource("sICX", Address.from_string(f"hx{'02345' * 8}"))
        except IconScoreException as e:
            self.assertEqual("BalancedRewards: Data source must be a contract.", e.message)

        self.rewards.addNewDataSource("Loans", Address.from_string(f"cx{'02345' * 8}"))
        recipient_list = self.rewards.getRecipients()
        self.assertEqual("Loans", recipient_list[3])
        self.assertEqual(0, self.rewards._recipient_split["Loans"])
        self.assertEqual("Loans", self.rewards._data_source_db["Loans"].name.get())
        self.assertEqual(day, self.rewards._data_source_db["Loans"].day.get())
        self.assertEqual( Address.from_string(f"cx{'02345' * 8}"), self.rewards._data_source_db["Loans"].contract_address.get())

        # the recipents name is already present before adding data sources. Thus the execution
        # returns although the address is wallet address
        self.rewards.addNewDataSource("Loans", Address.from_string(f"hx{'02345' * 8}"))

    def test_claimRewards(self):
        # with no holdings
        self.rewards.claimRewards()

        # with some holdings
        self.rewards._baln_holdings[str(self.test_account3)] = 50 * 10**18
        self.set_msg(self.test_account3)
        mock_class = MockClass()
        with mock.patch.object(self.rewards, "create_interface_score", wraps=mock_class.create_interface_score):
            self.rewards.claimRewards()
            self.assertEqual(0, self.rewards._baln_holdings[str(self.test_account3)])

    def test_distribute(self):
        # this is the distribute function test done partially. Few cases need to be covered still.
        mock_class = MockClass()
        self.set_block(1, 1 * 24 * 60 * 60 * 10 ** 6)
        with mock.patch.object(self.rewards, "create_interface_score", wraps=mock_class.create_interface_score):
            # distributing with certain percentages
            self.assertEqual(self.rewards._total_dist.get(), 0)
            recipient_list = [{'recipient_name': 'Reserve Fund', 'dist_percent': 70 * 10 ** 16},
                              {'recipient_name': 'DAOfund', 'dist_percent': 10 * 10 ** 16},
                              {'recipient_name': 'Worker Tokens', 'dist_percent': 20 * 10 ** 16}]
            self.set_msg(self.mock_score)
            self.rewards.updateBalTokenDistPercentage(recipient_list)
            self.rewards.distribute()
            self.assertEqual(1, self.rewards._platform_day.get())
            self.assertEqual(0, self.rewards._total_dist.get())

            #Loans is added in recipient
            self.set_block(1, 20 * 24 * 60 * 60 * 10 ** 6)
            self.rewards.addNewDataSource("Loans2", Address.from_string(f"cx{'02345' * 8}"))
            recipient_list.pop()
            recipient_list.append({'recipient_name': 'Worker Tokens', 'dist_percent': 10 * 10 ** 16})
            recipient_list.append({'recipient_name': 'Loans2', 'dist_percent': 10 * 10 ** 16})
            self.rewards.updateBalTokenDistPercentage(recipient_list)
            self.rewards.distribute()
            self.assertEqual(10000000000000000000000, self.rewards._data_source_db['Loans2'].total_dist[1])