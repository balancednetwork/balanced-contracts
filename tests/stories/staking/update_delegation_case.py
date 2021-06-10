stories = {

    "stories": [
     {
      "description": "User2 delegates 100% of it's votes to hxe064ff8825a522d933f2922b846dfae3c5ecd02f ",
      "actions": {
          "name": "delegate",
          "params":{'_user_delegations':[{'_address':'hxe064ff8825a522d933f2922b846dfae3c5ecd02f',  '_votes_in_per' : '100000000000000000000'}
              ]},
        "user":"user2",
          "within_top_preps":"true",
          "unit_test":[
               {
              "fn_name":"getAddressDelegations",
               "output":{'hxe064ff8825a522d933f2922b846dfae3c5ecd02f': 30000000000000000000}
               }]
      }
    }
        ,
        {
      "description": "User1 delegates 100% of it's votes to hx8ac43d292fcc468f53e8377a8c01b1e82216c5a0(out of top "
                     "preps)",
      "actions": {
          "name": "delegate",
          "params":{'_user_delegations':[{'_address':'hx8ac43d292fcc468f53e8377a8c01b1e82216c5a3',  '_votes_in_per' : '100000000000000000000'}]},
          "user":"user1",
          "within_top_preps":"false",
          "unit_test":[
               {
              "fn_name":"getAddressDelegations",
               "output":{'hx8ac43d292fcc468f53e8377a8c01b1e82216c5a3': 160000000000000000000}
               }]
      }
    }
        ,
        {
        "description": "User1 delegates 100% of it's votes to hx14219ac1b4cca98a29ec7d057afb6651a0eae461",
                       "actions": {
    "name": "delegate",
    "params": {'_user_delegations': [
        {'_address': 'hx14219ac1b4cca98a29ec7d057afb6651a0eae461', '_votes_in_per': '100000000000000000000'}]},
    "user": "user1",
    "within_top_preps": "true",
    "unit_test": [
        {
            "fn_name": "getAddressDelegations",
            "output": {'hx14219ac1b4cca98a29ec7d057afb6651a0eae461': 160000000000000000000}
        }]
}
}

  ]
}