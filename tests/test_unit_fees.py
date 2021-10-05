from iconservice import *
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from core_contracts.fees.fees import FeeHandler
import json


class TestGovernanceUnit(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_score = Address.from_string(f"cx{'1234' * 10}")
        self.fee_handler = self.get_score_instance(FeeHandler, self.test_account1)
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1231' * 10}")
        self.test_account5 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21,
            self.test_account5: 10 ** 21
        }
        self.initialize_accounts(account_info)
        self.fee_handler._governance.set(self.test_account1)


    def test_setgetdeleteRoute(self):

        # Initial settings.
        self.set_msg(self.test_account1)
        fromToken = Address.from_string("cxf61cd5a45dc9f91c15aa65831a30a90d59a09619")
        toToken = Address.from_string("cx88fd7df7ddff82f7cc735c871dc519838cb235bb")
        path = '["cx2609b924e33ef00b648a409245c7ea394c467824", "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"]'

        # Test db before setRoute.
        self.assertFalse(self.fee_handler.getRoute(fromToken, toToken))
        self.assertFalse(self.fee_handler._routes[fromToken][toToken])

        # Set route and test result.
        self.fee_handler.setRoute(fromToken, toToken, path)
        route = self.fee_handler.getRoute(fromToken, toToken)
        expected_route = {
            "fromToken": fromToken,
            "toToken": toToken,
            "path": [
                "cx2609b924e33ef00b648a409245c7ea394c467824",
                "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"
            ]
        }
        self.assertDictEqual(route, expected_route)

        # Delete route and test result.
        self.fee_handler.deleteRoute(fromToken, toToken)
        self.assertFalse(self.fee_handler.getRoute(fromToken, toToken))
        self.assertFalse(self.fee_handler._routes[fromToken][toToken])


    def test_setFeeProcessingInterval(self):
        
        # Initial settings.
        self.set_msg(self.test_account1)
        block_interval = 100

        # Test setter and getter.
        self.assertFalse(self.fee_handler._fee_processing_interval.get())
        self.fee_handler.setFeeProcessingInterval(block_interval)
        self.assertEqual(self.fee_handler.getFeeProcessingInterval(), block_interval)

    def test_createDataFieldRouter(self):
        path = ["cx88fd7df7ddff82f7cc735c871dc519838cb235bb", "cx2609b924e33ef00b648a409245c7ea394c467824"]
        result = self.fee_handler._createDataFieldRouter(self.test_account3, path)
        expected_result = json.dumps(
            {
            'method': "_swap",
            'params': {
                'path': path,
                'receiver': str(self.test_account3)
            }
        }
        ).encode()
        self.assertEqual(result, expected_result)
        
    def test_createDataFieldDex(self):
        result = self.fee_handler._createDataFieldDex(self.test_account4)
        expected_result = json.dumps(
            {
            'method': "_swap",
            'params': {
                'receiver': str(self.test_account4)
            }   
        }
        ).encode()
        self.assertEqual(result, expected_result)

    def test_timeForFeeProcessing(self):
        
        # Initial settings.
        self.set_block(199)
        token = Address.from_string("cx88fd7df7ddff82f7cc735c871dc519838cb235bb")
        self.fee_handler._fee_processing_interval.set(100)

        # Test if true is returned when no fee processing has occured yet.
        self.assertTrue(self.fee_handler._timeForFeeProcessing(token))

        # Test if false is returned when 199 blocks has passed and last processing
        # event was at block 100.
        self.fee_handler._last_fee_processing_block[token] = 100
        self.assertFalse(self.fee_handler._timeForFeeProcessing(token))

        # Test if True is returned when 200 blocks has passed and last processing
        # event was at block 100.
        self.set_block(200)
        self.assertTrue(self.fee_handler._timeForFeeProcessing(token))

    #def test_tokenFallback(self):
#
    #    # Mock parameters for tokenFallback function.
    #    token_sender = self.test_account3
    #    value = 1000
    #    data = b"None"
#
    #    # Settings.
    #    self.set_tx(_hash=b"mock_hash")
    #    self.set_block(100)
    #    self.set_msg(sender=self.test_account4)
    #    self.fee_handler._last_fee_processing_block[token_sender] = 50
    #    self.fee_handler._fee_processing_interval.set(100)
    #    #self.fee_handler._last_txhash.set("mock_hash")
#
    #    for i in range(10):
    #        print("")
    #    print(self.fee_handler.tx.hash == self.fee_handler._last_txhash.get())
#
    #    # First incomming token transfer to fee contract in this tx.
    #    self.fee_handler.tokenFallback(token_sender, value, data)
    #    print(self.fee_handler._last_txhash.get())
