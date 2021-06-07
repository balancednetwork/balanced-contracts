from datetime import time

from .test_integrate_base_rebalancing import BalancedTestBaseRebalancing
from iconservice import *


class BalancedTestLiquidation(BalancedTestBaseRebalancing):

    def setUp(self):
        super().setUp()

    def test_rebalance(self):

        print("############################################################################################")
        # self.call_tx(self.contracts['rebalancing'], 'name', {})
        # self.send_icx(self.btest_wallet, self.user1.get_address(), 1000 *10**18)
        # self.send_icx(self.btest_wallet, self.user2.get_address(), 1000 *10**18)
        #
        self.send_tx(self._test1, self.contracts['loans'], 750000 * 10**18, 'depositAndBorrow',
                     {'_asset': 'bnUSD', '_amount': 300000 * 10 ** 18})


        # self.send_tx(self.user1, self.contracts['loans'], 750 * 10 ** 18, 'depositAndBorrow',
        #              {'_asset': 'bnUSD', '_amount': 300 * 10 ** 18})
        # self.send_tx(self.user2, self.contracts['loans'], 750 * 10 ** 18, 'depositAndBorrow',
        #              {'_asset': 'bnUSD', '_amount': 300 * 10 ** 18})
        # self.call_tx(self.contracts['loans'], 'getAccountPositions',
        #              {'_owner': self._test1.get_address()})

        self.send_tx(self.btest_wallet, self.contracts['staking'], 1000 *10**18, 'stakeICX',
                     {"_to": self.contracts['rebalancing']})

        self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner":self.contracts['rebalancing']})

        self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner":self.contracts['rebalancing']})

        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setSicx',
                     {"_address": self.contracts['sicx']})
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setbnUSD',
                     {"_address": self.contracts['bnUSD']})
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setLoans',
                     {"_address": self.contracts['loans']})
        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'setDex',
                     {"_address": self.contracts['dex']})

        self.call_tx(self.contracts['dex'], 'getPriceByName', {"_name": "sICX/bnUSD"})

        dat = "{\"method\": \"_swap\", \"params\": {\"toToken\": \""+self.contracts['sicx']+"\"}}"
        data = dat.encode("utf-8")
        self.send_tx(self._test1, self.contracts['bnUSD'], 0, 'transfer',
                     {'_to': self.contracts['dex'], '_value': 200000 * 10 ** 18, "_data": data})

        self.send_tx(self.btest_wallet, self.contracts['rebalancing'], 0, 'rebalance', {})

        # self.call_tx(self.contracts['loans'], 'getMaxRetireAmount', {"_symbol": "bnUSD"})
        self.call_tx(self.contracts['sicx'], 'balanceOf', {"_owner": self.contracts['rebalancing']})
        self.call_tx(self.contracts['bnUSD'], 'balanceOf', {"_owner": self.contracts['rebalancing']})

        self.call_tx(self.contracts['dex'], 'getPriceByName', {"_name": "sICX/bnUSD"})
