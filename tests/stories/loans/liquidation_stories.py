ICX = 10**18
LIQUIDATION_STORIES = {
            "stories": [{
                "description": "liquidating btest_wallet account by depositing 782 icx collateral and minting 2000 "
                               "bnusd loan",
                "actions": {
                    "deposited_icx": 782769 * ICX // 1000,
                    "test_icx": 600,
                    "test_bnUSD": 2000 * ICX,
                    "expected_initial_position": "No Debt",
                    "expected_position": "Liquidate",
                    "expected_result": "Zero"
                }
            },
                {
                    "description": "liquidating btest_wallet account by depositing 782 icx collateral and minting "
                                   "1500 bnusd loan",
                    "actions": {
                        "deposited_icx": 782769 * ICX // 1000,
                        "test_icx": 600,
                        "test_bnUSD": 1500 * ICX,
                        "expected_initial_position": "No Debt",
                        "expected_position": "Liquidate",
                        "expected_result": "Zero"
                    }
                }
            ]
        }
