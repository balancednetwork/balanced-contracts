ICX = 10 ** 18
REBALANCING_STORIES = {
    "stories": [
        {
            "description": "In this condition rebalancing doesn't happen as price of dex is not less than 0.5% of "
                           "oracle price",
            "actions": {
                "initial_sicx_in_rebalancer": 1000 * ICX,
                "method": "transfer",
                "amount": 200 * ICX,
                "final_sicx_in_rebalancer": 1000 * ICX,
                # "sicx_to_retire": 119.29717293045304

            }
        },
        {
            "description": "In this condition 2 rebalancing doens't happen",
            "actions": {
                "initial_sicx_in_rebalancer": 1000 * ICX,
                "method": "transfer",
                "amount": 1600 * ICX,
                "final_sicx_in_rebalancer": 1000 * ICX,
                # "sicx_to_retire": 119.29717293045304

            }
        },
        {
            "description": "In this condition 3 rebalancing happens",
            "actions": {
                "initial_sicx_in_rebalancer": 1000 * ICX,
                "method": "transfer",
                "amount": 3000 * ICX,
                "final_sicx_in_rebalancer": 1000 * ICX,
                # "sicx_to_retire": 119.29717293045304

            }
        }
        # {
        #     "description": "Here re-balancing happens and the icx transferred from re-balancing is swapped "
        #                    "to bnUSD and retired",
        #     "actions": {
        #         "initial_sicx_in_rebalancer": 1000 * ICX,
        #         "method": "transfer",
        #         "amount": 200000 * ICX,
        #         "final_sicx_in_rebalancer": 1447011182227727316505,
        #         # "sicx_to_retire": 97806.93532549939
        #     }
        # }
    ]
}
