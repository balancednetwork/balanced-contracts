stories = {

        "stories": [
            {
                "description": "User1 delegates 100% of it's votes to hx000e0415037ae871184b2c7154e5924ef2bc075e",
                "actions": {
                    "name": "delegate",
                    "params": {"_user_delegations": [{"_address": "hx000e0415037ae871184b2c7154e5924ef2bc075e",
                                                      "_votes_in_per": "100000000000000000000"}]},
                    "user": "user1",
                    "within_top_preps": "true",
                    "unit_test": [
                        {
                            "fn_name": "getAddressDelegations",
                            "output": {"hx000e0415037ae871184b2c7154e5924ef2bc075e": 0}
                        }]
                }
            }]
    }