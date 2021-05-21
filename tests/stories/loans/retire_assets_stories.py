ICX = 10 ** 18
RETURN_ASSETS_STORIES = {
    "stories": [
        {
            "description": "User2 tries to retire 50 bnusd",
            "actions": {
                "sender": "user2",
                "first_meth": "transfer",
                "second_meth": "returnAsset",
                "deposited_icx": "0",
                "first_params": {"_to": "user2", "_value": 50 * ICX},
                "second_params": {"_symbol": "bnUSD", "_value": 50 * ICX},
                "revertMessage": "BalancedLoans: Retired amount is greater than the current maximum allowed.",
                "expected_status_result": "0"
            }
        },
        {
            "description": "User1 tries to transfer 5000 bnusd",
            "actions": {
                "sender": "user2",
                "first_meth": "transfer",
                "second_meth": "returnAsset",
                "deposited_icx": "0",
                "first_params": {"_to": "user2", "_value": 5000 * ICX},
                "second_params": {"_symbol": "bnUSD", "_value": 50 * ICX},
                "revertMessage": "Insufficient balance.",
                "expected_status_result": "0"
            }
        },
        {
            "description": "User1 tries to transfer -50 bnusd",
            "actions": {
                "sender": "user2",
                "first_meth": "transfer",
                "second_meth": "returnAsset",
                "deposited_icx": "0",
                "first_params": {"_to": "user2", "_value": -50 * ICX},
                "second_params": {"_symbol": "bnUSD", "_value": 5 * ICX},
                "revertMessage": "Transferring value cannot be less than 0.",
                "expected_status_result": "0"
            }
        },
        {
            "description": "User2 tries to retire -5 bnusd",
            "actions": {
                "sender": "user2",
                "first_meth": "transfer",
                "second_meth": "returnAsset",
                "deposited_icx": "0",
                "first_params": {"_to": "user2", "_value": 20 * ICX},
                "second_params": {"_symbol": "bnUSD", "_value": -5 * ICX},
                "revertMessage": "BalancedLoans: Amount retired must be greater than zero.",
                "expected_status_result": "0"
            }
        },
        {
            "description": "User2 tries to retire 5 bnusd",
            "actions": {
                "sender": "user2",
                "first_meth": "transfer",
                "second_meth": "returnAsset",
                "deposited_icx": "0",
                "first_params": {"_to": "user2", "_value": 20 * ICX},
                "second_params": {"_symbol": "bnUSD", "_value": 5 * ICX},
                "expected_status_result": "1"
            }
        }
    ]
}
