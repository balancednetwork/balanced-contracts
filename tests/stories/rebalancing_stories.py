ICX = 10 ** 18
REBALANCING_STORIES = {
    "stories": [
        {
            "description": "In this condition rebalancing doesn't happen as price of dex is not less than 0.5% of "
                           "oracle price.",
            "actions": {
                "method": "transfer",
                "amount": 200 * ICX,
                "rebalancing_status": False,
            }
        },
        {
            "description": "In this condition rebalancing doens't happen as price of dex is not less than 0.5% "
                           "of oracle price although sicx to retire is more than 1000 sicx.",
            "actions": {
                "method": "transfer",
                "amount": 1600 * ICX,
                "rebalancing_status": False,
            }
        },
        {
            "description": "In this condition rebalancing happens as dex price changes with more than 0.5% of "
                           "oracle price.",
            "actions": {
                "method": "transfer",
                "amount": 400000 * ICX,
                "rebalancing_status": True,
            }
        },
{
            "description": "In this condition too rebalancing happens as dex price changes with more than 0.5% of "
                           "oracle price.",
            "actions": {
                "method": "transfer",
                "amount": 100 * ICX,
                "rebalancing_status": 1,
            }
        }
    ]
}

REBALANCING_DOWN_STORIES = {
    "stories": [
        {
            "description": "In this condition rebalancing doesn't happen as price of dex is not more than 0.5% of "
                           "oracle price.",
            "actions": {
                "initial_sicx_in_rebalancer": 1000 * ICX,
                "initial_bnUSD_in_rebalancer": 1000 * ICX,
                "method": "transfer",
                "amount": 200 * ICX,
                "rebalancing_status": 0,
                "final_sicx_in_rebalancer": 1000 * ICX,
                "final_bnUSD_in_rebalancer": 1000 * ICX

            }
        },
        {
            "description": "In this condition rebalancing happen as price of dex is more than than 0.5% "
                           "of oracle price.",
            "actions": {
                "initial_sicx_in_rebalancer": 1000 * ICX,
                "initial_bnUSD_in_rebalancer": 1000 * ICX,
                "method": "transfer",
                "amount": 1600 * ICX,
                "rebalancing_status": 1,
                "final_sicx_in_rebalancer": 1000 * ICX,
                "final_bnUSD_in_rebalancer": 1000 * ICX
            }
        },
        {
            "description": "In this condition rebalancing happens as dex price increases with more than 0.5% of "
                           "oracle price.",
            "actions": {
                "initial_sicx_in_rebalancer": 1000 * ICX,
                "initial_bnUSD_in_rebalancer": 1000 * ICX,
                "method": "transfer",
                "amount": 1000 * ICX,
                "rebalancing_status": 1,
                "final_sicx_in_rebalancer": 1000 * ICX,
                "final_bnUSD_in_rebalancer": 1000 * ICX
            }
        }
    ]
}