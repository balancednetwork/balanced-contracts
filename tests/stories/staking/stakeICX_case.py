stories = {
        "title": "Staking: stakeICX",
        "description": "Test cases for the stakeICX function.",
        "stories": [
            {
                "description": "User 1 deposits 50 ICX as collateral and mints sicx to own wallet address.",
                "actions": {
                    "mint_to": "user1",
                    "prev_sicx_in_user": "0",
                    "prev_total_supply_sicx": "0",
                    "prev_icx_staked_from_staking_contract": "0",
                    "name": "stakeICX",
                    "deposited_icx": "50000000000000000000",
                    "expected_sicx_in_user": "50000000000000000000",
                    "expected_icx_staked_from_staking_contract": "50000000000000000000",
                    "total_supply_sicx": "50000000000000000000",
                    "unit_test": [
                        {
                            "getTotalStake": "50000000000000000000"
                        }]
                }
            },
            {
                "description": "user 2 deposits 30 ICX as collateral and mints sicx to user1 wallet address.",
                "actions": {
                    "mint_to": "user1",
                    "prev_sicx_in_user": "50000000000000000000",
                    "prev_total_supply_sicx": "50000000000000000000",
                    "prev_icx_staked_from_staking_contract": "50000000000000000000",
                    "name": "stakeICX",
                    "deposited_icx": "30000000000000000000",
                    "expected_sicx_in_user": "80000000000000000000",
                    "expected_icx_staked_from_staking_contract": "80000000000000000000",
                    "total_supply_sicx": "80000000000000000000",
                    "unit_test": [
                        {
                            "getTotalStake": "80000000000000000000"
                        }]
                }
            },
            {
                "description": "user 2 deposits 30 ICX as collateral and mints sicx to own wallet address.",
                "actions": {
                    "mint_to": "user2",
                    "prev_sicx_in_user": "0",
                    "prev_total_supply_sicx": "80000000000000000000",
                    "prev_icx_staked_from_staking_contract": "80000000000000000000",
                    "name": "stakeICX",
                    "deposited_icx": "30000000000000000000",
                    "expected_sicx_in_user": "30000000000000000000",
                    "expected_icx_staked_from_staking_contract": "110000000000000000000",
                    "total_supply_sicx": "110000000000000000000",
                    "unit_test": [
                        {
                            "getTotalStake": "110000000000000000000"
                        }]
                }
            }

        ]
    }