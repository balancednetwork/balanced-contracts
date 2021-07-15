ICX = 10 ** 18
BAD_DEBT_STORIES = {
    "stories": [{
        "description": "User 1 retires 10 bnUSD bad debts",
        "actions": {
            "method": "retireBadDebt",
            "args": {
                "_symbol": "bnUSD",
                "_value": 10 * ICX
            }
        }
    },
        {
            "description": "User 1 retires 130 bnUSD bad debts",
            "actions": {
                "method": "retireBadDebt",
                "args": {
                    "_symbol": "bnUSD",
                    "_value": 130 * ICX
                }
            }
        }
    ]
}
