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

    def test_overall_snapshot(self):
        mock_class = MockClass()
        self.set_block(1, 1 * 24 * 60 * 60 * 10 ** 6)

        # test the initial snapshot

        self.assertEqual(self.rewards.getRecipientsSplit(), {'Worker Tokens': 0, 'Reserve Fund': 0, 'DAOfund': 0})
        recipients_list = self.rewards.getRecipients()
        recipient_split = {}
        recipient_split_at_60 = {}
        for recipient in recipients_list:
            recipient_split[recipient] = self.rewards.recipientAt(recipient, 0)
            recipient_split_at_60[recipient] = self.rewards.recipientAt(recipient, 60)
        self.assertEqual(recipient_split, {'Worker Tokens': 0, 'Reserve Fund': 0, 'DAOfund': 0})
        self.assertEqual(recipient_split_at_60, {'Worker Tokens': 0, 'Reserve Fund': 0, 'DAOfund': 0})

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
        self.assertEqual(self.rewards.getRecipientsSplit(), check_split)
        recipients_list = self.rewards.getRecipients()
        recipient_split = {}
        recipient_split_at_60 = {}
        recipient_split_at_1 = {}
        for recipient in recipients_list:
            recipient_split[recipient] = self.rewards.recipientAt(recipient, 0)
            recipient_split_at_60[recipient] = self.rewards.recipientAt(recipient, 60)
            recipient_split_at_1[recipient] = self.rewards.recipientAt(recipient, 1)
        self.assertEqual(recipient_split, {'Worker Tokens': 0, 'Reserve Fund': 0, 'DAOfund': 0})
        self.assertEqual(recipient_split_at_60, check_split)
        self.assertEqual(recipient_split_at_1, check_split)
        # print(self.rewards.recipientAt("Worker Tokens", 9))
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
            # print(self.rewards.getRecipientsSplit())
            # print(self.rewards.recipientAt("Worker Tokens", 9))
            self.rewards.updateBalTokenDistPercentage(recipient_list)
            recipients_list = self.rewards.getRecipients()
            check_split2 = {}
            for x in recipient_list:
                name = x['recipient_name']
                per = x['dist_percent']
                check_split2[name] = per
            recipient_split = {}
            recipient_split_at_60 = {}
            recipient_split_at_1 = {}
            for recipient in recipients_list:
                recipient_split[recipient] = self.rewards.recipientAt(recipient, 0)
                recipient_split_at_60[recipient] = self.rewards.recipientAt(recipient, 60)
                recipient_split_at_1[recipient] = self.rewards.recipientAt(recipient, 1)

            self.assertEqual(recipient_split,
                             {'Worker Tokens': 0, 'Reserve Fund': 0, 'DAOfund': 0, 'Loans': 0, 'sICX/ICX': 0,
                              'sICX/bnUSD': 0})
            self.assertEqual(recipient_split_at_60, check_split2)
            check_split["Loans"] = 0
            check_split["sICX/ICX"] = 0
            check_split["sICX/bnUSD"] = 0
            self.assertEqual(recipient_split_at_1, check_split)
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
            self.assertEqual(e.message, "BalancedRewards: Recipient lists lengths mismatched!")

        # providing incorrect name as a recipients
        try:
            incorrect_recipient = [{'recipient_name': 'Reserve Fund2', 'dist_percent': 70 * 10 ** 16},
                              {'recipient_name': 'DAOfund2', 'dist_percent': 10 * 10 ** 16},
                              {'recipient_name': 'Worker Tokens2', 'dist_percent': 20 * 10 ** 16}]
            self.rewards.updateBalTokenDistPercentage(incorrect_recipient)
        except IconScoreException as e:
            self.assertEqual(e.message, "BalancedRewards: Recipient Reserve Fund2 does not exist.")

        # providing distribution percentage more than 100
        try:
            test_percentage = [{'recipient_name': 'Reserve Fund', 'dist_percent': 70 * 10 ** 16},
                              {'recipient_name': 'DAOfund', 'dist_percent': 10 * 10 ** 16},
                              {'recipient_name': 'Worker Tokens', 'dist_percent': 30 * 10 ** 16}]
            self.rewards.updateBalTokenDistPercentage(test_percentage)
        except IconScoreException as e:
            self.assertEqual(e.message, "BalancedRewards: Total percentage does not sum up to 100.")

        # test the actual function with correct data
        recipient_list.pop()
        self.rewards.updateBalTokenDistPercentage(recipient_list)
        day = self.rewards._get_day()
        self.assertEqual(self.rewards._recipient_split['DAOfund'], 10 * 10 ** 16)
        self.assertEqual(self.rewards._recipient_split['Reserve Fund'], 70 * 10 ** 16)
        self.assertEqual(self.rewards._recipient_split['Worker Tokens'], 20 * 10 ** 16)
        self.assertEqual(self.rewards._data_source_db["DAOfund"].get_data()['day'], day)
        self.assertEqual(self.rewards._data_source_db["Reserve Fund"].get_data()['day'], day)
        self.assertEqual(self.rewards._data_source_db["Worker Tokens"].get_data()['day'], day)

    def test_addNewDataSource(self):
        self.set_msg(self.mock_score)
        day = self.rewards._get_day()
        # test if the data source address is a contract or not

        try:
            self.rewards.addNewDataSource("sICX", Address.from_string(f"hx{'02345' * 8}"))
        except IconScoreException as e:
            self.assertEqual(e.message, "BalancedRewards: Data source must be a contract.")

        self.rewards.addNewDataSource("Loans", Address.from_string(f"cx{'02345' * 8}"))
        recipient_list = self.rewards.getRecipients()
        self.assertEqual(recipient_list[3], "Loans")
        self.assertEqual(self.rewards._recipient_split["Loans"], 0)
        self.assertEqual(self.rewards._data_source_db["Loans"].name.get(), "Loans")
        self.assertEqual(self.rewards._data_source_db["Loans"].day.get(), day)
        self.assertEqual(self.rewards._data_source_db["Loans"].contract_address.get(), Address.from_string(f"cx{'02345' * 8}"))

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
            self.assertEqual(self.rewards._baln_holdings[str(self.test_account3)], 0)