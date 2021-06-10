stories  = {
        "stories": [
            {
                "description": "User1 request for unstake of 20sICX",
                "actions": {
                    "name": "transfer",
                    "sender": "user1",
                    "prev_total_stake": "210000000000000000000",
                    "curr_total_stake": "190000000000000000000",
                    "curr_sender_sicx": "130000000000000000000",
                    "total_sicx_transferred": "20000000000000000000",
                    "unit_test": [
                        {
                            "fn_name": "getUnstakingAmount",
                            "output": "20000000000000000000"
                        }
                    ]

                }
            },
            {
                "description": "User2 request for unstake of 10sICX",
                "actions": {
                    "name": "transfer",
                    "sender": "user2",
                    "prev_total_stake": "190000000000000000000",
                    "curr_sender_sicx": "10000000000000000000",
                    "curr_total_stake": "180000000000000000000",
                    "total_sicx_transferred": "10000000000000000000",
                    "unit_test": [
                        {
                            "fn_name": "getUnstakingAmount",
                            "output": "30000000000000000000"
                        }
                    ]

                }
            }

        ]
    }