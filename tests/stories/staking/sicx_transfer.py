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
                    "delegation_sender": {"hx9eec61296a7010c867ce24c20e69588e2832bc52": 70000000000000000000},
                    "delegation_receiver": {"hx000e0415037ae871184b2c7154e5924ef2bc075e": 20000000000000000000,
                                            "hx9eec61296a7010c867ce24c20e69588e2832bc52": 20000000000000000000}

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
                    "delegation_sender": {"hx000e0415037ae871184b2c7154e5924ef2bc075e": 10000000000000000000,
                                          "hx9eec61296a7010c867ce24c20e69588e2832bc52": 10000000000000000000},
                    "delegation_receiver": "evenly_distribute"

                }
            }

        ]
    }