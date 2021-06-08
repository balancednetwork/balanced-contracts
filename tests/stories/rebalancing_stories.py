ICX = 10 ** 18
REBALANCING_STORIES = {
    "stories": [{
        "description": "In this condition rebalancing doens't happen",
        "actions": {
            "initial_sicx_in_rebalancer": 1000 * ICX,
            "method": "transfer",
            "amount" : 200 * ICX,
            "final_sicx_in_rebalancer": 1000 * ICX

        }
    },
        {
            "description": "Here re-balancing happens and the icx transferred from re-balancing is swapped "
                           "to bnUSD and retired",
            "actions": {
                "initial_sicx_in_rebalancer": 1000 * ICX,
                "method": "transfer",
                "amount" : 200000 * ICX,
                "final_sicx_in_rebalancer": 1447011182227727316505

            }
        }
    ]
}
