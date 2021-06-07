ICX = 10**18
LIQUIDATION_STORIES = {
            "stories": [{
                "description": "liquidating btest_wallet account by depositing 782 icx collateral and minting 2000 "
                               "bnusd loan",
                "actions": {
                    "deposited_icx": 782769 * ICX // 1000,
                    "expected_initial_position": "Not Mining",
                    "oracle": {
                        "rate": 5 * ICX,
                        "last_update_base": 1802202277702605,
                        "last_update_quote": 1802202290000000
                    },
                    "expected_position": "Liquidate",
                    "expected_result": "Zero"
                }
            }
                # {
                #     "description": "liquidating btest_wallet account by depositing 782 icx collateral and minting "
                #                    "1500 bnusd loan",
                #     "actions": {
                #         "deposited_icx": 782769 * ICX // 1000,
                #         "expected_initial_position": "No Debt",
                #         "expected_position": "Liquidate",
                #         "expected_result": "Zero"
                #     }
                # }
            ]
        }
