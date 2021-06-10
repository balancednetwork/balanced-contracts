import json
import os
DIR_PATH = os.path.abspath(os.path.dirname(__file__))
path = os.path.abspath(os.path.join(DIR_PATH, "../../../update_staking_data.json"))
f = open(path,'r')
data = json.load(f)
stories = {
        "title": "Staking: stakeICX",
        "description": "Test cases for the stakeICX function.",
        "stories": [
            {
                "description": "User 1 deposits 50 ICX as collateral and mints sicx to own wallet address.",
                "actions": {
                    "mint_to": "user1",
                    "prev_sicx_in_user": str(data["user1_sicx"]),
                    "prev_total_supply_sicx": str(data["total_sicx_supply"]),
                    "prev_icx_staked_from_staking_contract": str(data["total_stake"]),
                    "name": "stakeICX",
                    "deposited_icx": "50000000000000000000",
                    "expected_sicx_in_user": str(data["user1_sicx"] + 50000000000000000000),
                    "expected_icx_staked_from_staking_contract": str(data["total_stake"] + 50000000000000000000),
                    "total_supply_sicx": str(data["total_sicx_supply"] + 50000000000000000000),
                    "unit_test": [
                        {
                            "getTotalStake": str(data["total_stake"] + 50000000000000000000)
                        }]
                }
            },
            {
                "description": "user 2 deposits 30 ICX as collateral and mints sicx to user1 wallet address.",
                "actions": {
                    "mint_to": "user1",
                    "prev_sicx_in_user": str(data["user1_sicx"] + 50000000000000000000),
                    "prev_total_supply_sicx": str(data["total_sicx_supply"] + 50000000000000000000),
                    "prev_icx_staked_from_staking_contract": str(data["total_stake"] + 50000000000000000000),
                    "name": "stakeICX",
                    "deposited_icx": "30000000000000000000",
                    "expected_sicx_in_user": str(data["user1_sicx"] + 50000000000000000000 + 30000000000000000000),
                    "expected_icx_staked_from_staking_contract": str(data["total_stake"] + 50000000000000000000+30000000000000000000),
                    "total_supply_sicx":  str(data["total_sicx_supply"] + 50000000000000000000 + 30000000000000000000),
                    "unit_test": [
                        {
                            "getTotalStake": str(data["total_stake"] + 50000000000000000000+30000000000000000000)
                        }]
                }
            },
            {
                "description": "user 2 deposits 30 ICX as collateral and mints sicx to own wallet address.",
                "actions": {
                    "mint_to": "user2",
                    "prev_sicx_in_user": "0",
                    "prev_total_supply_sicx": str(data["total_sicx_supply"] + 50000000000000000000 + 30000000000000000000),
                    "prev_icx_staked_from_staking_contract":  str(data["total_stake"] + 50000000000000000000+30000000000000000000),
                    "name": "stakeICX",
                    "deposited_icx": "30000000000000000000",
                    "expected_sicx_in_user": "30000000000000000000",
                    "expected_icx_staked_from_staking_contract": str(data["total_stake"] + 50000000000000000000+30000000000000000000+
                                                                     30000000000000000000),
                    "total_supply_sicx": str(data["total_sicx_supply"] + 50000000000000000000 + 30000000000000000000
                                             +30000000000000000000),
                    "unit_test": [
                        {
                            "getTotalStake": str(data["total_stake"] + 50000000000000000000+30000000000000000000+
                                                                     30000000000000000000)
                        }]
                }
            }

        ]
    }