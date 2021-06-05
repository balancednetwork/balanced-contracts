stories = {

        "stories": [
            {
                "description": "User1 delegates 100% of it's votes to  hx9eec61296a7010c867ce24c20e69588e2832bc52",
                "actions": {
                    "name": "delegate",
                    "params": {"_user_delegations": [{"_address": "hx9eec61296a7010c867ce24c20e69588e2832bc52",
                                                      "_votes_in_per": "100000000000000000000"}]},
                    "user": "user1",
                    "within_top_preps": "true",
                    "unit_test": [
                        {
                            "fn_name": "getAddressDelegations",
                            "output": {"hx9eec61296a7010c867ce24c20e69588e2832bc52": 80000000000000000000}
                        }]
                }
            },
            {
                "description": "User2 delegates 50% of it's votes to hx000e0415037ae871184b2c7154e5924ef2bc075e and "
                               "50% of its votes to hx9eec61296a7010c867ce24c20e69588e2832bc52",
                "actions": {
                    "name": "delegate",
                    "params": {"_user_delegations": [{"_address": "hx000e0415037ae871184b2c7154e5924ef2bc075e",
                                                      "_votes_in_per": "50000000000000000000"},
                                                     {"_address": "hx9eec61296a7010c867ce24c20e69588e2832bc52",
                                                      "_votes_in_per": "50000000000000000000"}]},
                    "user": "user2",
                    "within_top_preps": "true",
                    "unit_test": [
                        {
                            "fn_name": "getAddressDelegations",
                            "output": {"hx000e0415037ae871184b2c7154e5924ef2bc075e": 15000000000000000000,
                                       "hx9eec61296a7010c867ce24c20e69588e2832bc52": 15000000000000000000}
                        }]
                }
            },
            {
                "description": "User1 delegates 100% of it's votes to hx8ac43d292fcc468f53e8377a8c01b1e82216c5a0(out of top preps)",
                "actions": {
                    "name": "delegate",
                    "params": {"_user_delegations": [{"_address": "hx8ac43d292fcc468f53e8377a8c01b1e82216c5a0",
                                                      "_votes_in_per": "100000000000000000000"}]},
                    "user": "user1",
                    "within_top_preps": "false",
                    "unit_test": [
                        {
                            "fn_name": "getAddressDelegations",
                            "output": {"hx8ac43d292fcc468f53e8377a8c01b1e82216c5a0": 80000000000000000000}
                        }]
                }
            }
            ,
            {
                "description": "User1 delegates 100% of it's votes to hx9eec61296a7010c867ce24c20e69588e2832bc52",
                "actions": {
                    "name": "delegate",
                    "params": {"_user_delegations": [{"_address": "hx9eec61296a7010c867ce24c20e69588e2832bc52",
                                                      "_votes_in_per": "100000000000000000000"}]},
                    "user": "user1",
                    "within_top_preps": "true",
                    "unit_test": [
                        {
                            "fn_name": "getAddressDelegations",
                            "output": {"hx9eec61296a7010c867ce24c20e69588e2832bc52": 80000000000000000000}
                        }]
                }
            }

        ]
    }