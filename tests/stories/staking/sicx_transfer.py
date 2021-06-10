stories = {
        "stories": [
            {
                "description": "User1 transfers 10 sICX to user2",
                "actions": {
                    "name": "transfer",
                    "sender": "user1",
                    "receiver": "user2",
                    "prev_sender_sicx": "80000000000000000000",
                    "prev_receiver_sicx": "30000000000000000000",
                    "total_sicx_transferred": "10000000000000000000",
                    "curr_sender_sicx": "70000000000000000000",
                    "curr_receiver_sicx": "40000000000000000000",
                    "delegation_sender": {"hx243d2388c934fe123a2a2abffe9d48f4c7520c25": 70000000000000000000},
                    "delegation_receiver": {"hxe064ff8825a522d933f2922b846dfae3c5ecd02f": 20000000000000000000,
                                            "hx4491a4dfc2e71474d938ce77d37be0a8654efe73": 20000000000000000000}

                }
            },
            {
                "description": "User2 transfers 20 sICX to some random address",
                "actions": {
                    "name": "transfer",
                    "sender": "user2",
                    "receiver": "hx72bff0f887ef183bde1391dc61375f096e75c74a",
                    "prev_sender_sicx": "40000000000000000000",
                    "prev_receiver_sicx": "0",
                    "total_sicx_transferred": "20000000000000000000",
                    "curr_sender_sicx": "20000000000000000000",
                    "curr_receiver_sicx": "20000000000000000000",
                    "delegation_sender": {"hxe064ff8825a522d933f2922b846dfae3c5ecd02f": 10000000000000000000,
                                          "hx4491a4dfc2e71474d938ce77d37be0a8654efe73": 10000000000000000000},
                    "delegation_receiver": "evenly_distribute"

                }
            }

        ]
    }