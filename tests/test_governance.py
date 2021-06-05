import time

from .test_governance_base import BalancedTestBaseRewards


# GOVERNANCE_ADDRESS = "cx0000000000000000000000000000000000000000"
# fname = os.path.join(os.path.abspath(os.path.dirname(__file__)), "score_address.json")
#
# if os.path.isfile(fname):
#     os.remove(fname)
#
# DIR_PATH = os.path.abspath(os.path.dirname(__file__))
# SCORE_ADDRESS = "scoreAddress"


class BalancedTestStaking(BalancedTestBaseRewards):
    def setUp(self):
        super().setUp()

    def test_set_addresses(self):
        _result = (self.call_tx(self.contracts['governance'], "getAddresses"))
        del self.contracts['governance']
        del self.contracts['system']
        self.assertEqual(_result, self.contracts, "failed")

    def test_set_admin(self):
        admin_test = {
            'dex': 'governance',
            'rewards': 'governance',
            'dividends': 'governance',
            'daofund': 'governance',
            'reserve': 'governance',
            'bnUSD': 'loans',
            'baln': 'rewards',
            'bwt': 'governance'}
        for key, value in admin_test.items():
            _result = (self.call_tx(self.contracts[key], "getAdmin"))
            self.assertEqual(_result, self.contracts[value], "failed")

    def test_assets(self):
        assest_list = ["sICX", "bnUSD", "BALN"]
        assest_dict = {}
        for token in assest_list:
            if token != "bnUSD":
                assest_dict[token] = self.contracts[token.lower()]
            else:
                assest_dict[token] = self.contracts[token]
        _result = (self.call_tx(self.contracts["loans"], "getAssetTokens"))
        self.assertEqual(_result, assest_dict, "Failed to set assest")

    def test_data_source(self):
        data_source_list = ['Loans', 'sICX/ICX', 'sICX/bnUSD']
        _result = (self.call_tx(self.contracts["rewards"], "getDataSourceNames"))
        self.assertEqual(data_source_list, _result, "Failed")
        _result = (self.call_tx(self.contracts["loans"], "getLoansOn"))
        self.assertEqual(_result, '0x1', "Loans score not active")
        _result = (self.call_tx(self.contracts["dex"], "getDexOn"))
        self.assertEqual(_result, '0x1', "Dex score not active")

    def test_toggle_active_assest(self):
        tx_result = self.send_tx(self.btest_wallet, self.contracts["governance"], 0, "toggleAssetActive",
                                 {"_symbol": "bnUSD"})
        event = tx_result["eventLogs"]
        data = event[0]['data']
        self.assertEqual('Active', data[0], 'Failed to active assest')

    def test_launch_day(self):
        _result = (self.call_tx(self.contracts["governance"], "getLaunchDay"))
        print(_result)
        self.assertEqual(_result, "0x78", "Failed to set day.")

    def test_launch_time(self):
        _result = (self.call_tx(self.contracts["governance"], "getLaunchTime"))
        print(_result)
        self.assertEqual(_result, "0x78", "Failed to set time.")

    def test_bnusd_market_creation(self):
        bnusd_dex = (self.call_tx(self.contracts["bnUSD"], "balanceOf", {"_owner": self.contracts['dex']}))
        sicx_dex = (self.call_tx(self.contracts["sicx"], "balanceOf", {"_owner": self.contracts['dex']}))
        self.assertEqual(int(bnusd_dex, 16), 50170938591129428969, "Failed in transfer bnusd to dex")
        self.assertEqual(int(sicx_dex, 16), 30000000000000000000, "Failed in transfer sicx to dex")
        recipent_dict = {'Loans': 25 * 10 ** 16,
                         'sICX/ICX': 10 * 10 ** 16,
                         'Worker Tokens': 20 * 10 ** 16,
                         'Reserve Fund': 5 * 10 ** 16,
                         'DAOfund': 225 * 10 ** 15,
                         'sICX/bnUSD': 175 * 10 ** 15}

        _result = (self.call_tx(self.contracts["rewards"], "getRecipientsSplit"))
        dict1 = {}
        for key, value in _result.items():
            dict1[key] = int(value, 16)
        self.assertEqual(dict1, recipent_dict, "failed")

    # def test_baln_market_creation(self):
    #     bnusd_dex = (self.call_tx(self.contracts["baln"], "balanceOf", {"_owner": self.contracts['dex']}))
    #     sicx_dex = (self.call_tx(self.contracts["sicx"], "balanceOf", {"_owner": self.contracts['dex']}))
    #     self.assertEqual(int(bnusd_dex, 16), 50170938591129428969, "Failed in transfer bnusd to dex")
    #     self.assertEqual(int(sicx_dex, 16), 30000000000000000000, "Failed in transfer sicx to dex")
    #     recipent_dict = {'Loans': 25 * 10 ** 16,
    #                      'sICX/ICX': 10 * 10 ** 16,
    #                      'Worker Tokens': 20 * 10 ** 16,
    #                      'Reserve Fund': 5 * 10 ** 16,
    #                      'DAOfund': 225 * 10 ** 15,
    #                      'sICX/bnUSD': 175 * 10 ** 15}
    #
    #     _result = (self.call_tx(self.contracts["rewards"], "getRecipientsSplit"))
    #     dict1 = {}
    #     for key, value in _result.items():
    #         dict1[key] = int(value, 16)
    #     self.assertEqual(dict1, recipent_dict, "failed")

    # def test_try(self):
    #     data = "{\"method\": \"_deposit\"}".encode("utf-8")
    #     bnusd_dex = (self.call_tx(self.contracts["baln"], "balanceOf", {"_owner": self.btest_wallet.get_address()}))
    #     #
    #     # self.send_tx(self.btest_wallet, self.contracts['loans'], 2000 * 10 ** 18, 'depositAndBorrow',
    #     #              {'_asset': 'bnUSD', '_amount': 100 * 10 ** 18})
    #     # time.sleep(15)
    #     # txs = []
    #     # for i in range(500):
    #     #     deploy_tx = self.build_tx(self.btest_wallet, self.contracts['rewards'], 0, 'distribute', {})
    #     #     txs.append(deploy_tx)
    #     # self.process_transaction_bulk_without_txresult(txs, self.icon_service)
    #     # self.send_tx(self.btest_wallet, self.contracts['rewards'], 0, 'claimRewards', {})
    #     # self.send_tx(self.btest_wallet, self.contracts["bnUSD"], 0, "transfer",
    #     #              {"_to": self.contracts["dex"], "_value": 20 * 10 ** 18,"_data":data})
    #     # self.send_tx(self.btest_wallet, self.contracts["baln"], 0, "transfer",
    #     #              {"_to": self.contracts["dex"], "_value": 20 * 10 ** 18,"_data":data})
    #     # self.send_tx(self.btest_wallet, self.contracts['governance'], 0, 'createBalnMarket',
    #     #              {"_bnUSD_amount": 10 * 10 ** 18, "_baln_amount": 1 * 10 ** 18})
    #     # self.send_tx(self.btest_wallet, self.contracts['dex'], 0, '_deposit',
    #     #              {"_bnUSD_amount": 10 * 10 ** 18, "_baln_amount": 1 * 10 ** 18})
    #     bnusd_dex = (self.call_tx(self.contracts["bnUSD"], "balanceOf", {"_owner": self.contracts['dex']}))
    #     baln_dex = (self.call_tx(self.contracts["baln"], "balanceOf", {"_owner": self.contracts['dex']}))
    #     print(int(baln_dex, 16))
    #     print(int(bnusd_dex, 16))
    #     self.assertEqual(int(bnusd_dex, 16), 50 * 10 ** 18, "Failed in transfer bnusd to dex")
    #     self.assertEqual(int(baln_dex, 16), 50 * 10 ** 18, "Failed in transfer sicx to dex")
