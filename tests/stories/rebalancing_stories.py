ICX = 10 ** 18
REBALANCING_STORIES = {
    "stories": [
        {
            "description": "In this condition rebalancing doesn't happen as price of dex is not less than 0.5% of "
                           "oracle price.",
            "actions": {
                "method": "transfer",
                "amount": 200 * ICX,
                "rebalancing_status": 0,
            }
        },
        {
            "description": "In this condition rebalancing doens't happen as price of dex is not less than 0.5% "
                           "of oracle price although sicx to retire is more than 1000 sicx.",
            "actions": {
                "method": "transfer",
                "amount": 1600 * ICX,
                "rebalancing_status": 0,
            }
        },
        {
            "description": "In this condition rebalancing happens as dex price changes with more than 0.5% of "
                           "oracle price.",
            "actions": {
                "method": "transfer",
                "amount": 400000 * ICX,
                "rebalancing_status": 1,
            }
        },
        {
            "description": "In this condition too rebalancing happens as dex price changes with more than 0.5% of "
                           "oracle price.",
            "actions": {
                "method": "transfer",
                "amount": 10000 * ICX,
                "rebalancing_status": 1,
            }
        }
    ]
}

REVERSE_REBALANCING_STORIES = {
    "stories": [
        {
            "description": "In this condition rebalancing doesn't happen as price of dex is not more than 0.5% of "
                           "oracle price.",
            "actions": {
                "method": "transfer",
                "amount": 200 * ICX,
                "rebalancing_status": 0,

            }
        },
        {
            "description": "In this condition also rebalancing doesn't happen as price of dex is not more than 0.5% "
                           "of oracle price.",
            "actions": {
                "method": "transfer",
                "amount": 1600 * ICX,
                "rebalancing_status": 0,
            }
        },
        {
            "description": "In this condition rebalancing happens as dex price increases with more than 0.5% of "
                           "oracle price.",
            "actions": {
                "method": "transfer",
                "amount": 200000 * ICX,
                "rebalancing_status": 1,
            }
        }
    ]
}
