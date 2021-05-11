ICX = 10**18
RETURN_ASSETS_STORIES = {
    "stories": [
        {
            "description": "User2 tries to retire 10 bnusd",
            "actions": {
                "sender": "user2",
                "first_meth": "transfer",
                "second_meth": "returnAsset",
                "deposited_icx": "0",
                "first_params": {"_to": "user2.get_address()", "_value": 20 * ICX},
                "second_params": {"_symbol": "bnUSD", "_value": 5 * ICX},
                "expected_status_result": "1"
            }
        }
    ]
}
