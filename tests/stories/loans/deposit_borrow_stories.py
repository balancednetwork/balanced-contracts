ICX = 10 ** 18
DEPOSIT_AND_BORROW_STORIES = {
    "stories": [
        {
            "description": "User 1 deposits 500 ICX as collateral and borrows 50 bnUSD loan",
            "actions": {
                "prev_sicx_bal_loan": 0,
                "prev_bnUSD_debt_bal_loan": 0,
                "sender": "user1",
                "name": "depositAndBorrow",
                "deposited_icx": 500 * ICX,
                "args": {
                    "_asset": "bnUSD",
                    "_amount": 50 *ICX
                },
                "expected": "1",
                "expected_sicx_baln_loan": 500 * ICX,
                "expected_bnUSD_debt_baln_loan": 50 * ICX
            }
        },
        {
            "description": "User 1 deposits 500 ICX as collateral and borrows 9 bnUSD loan",
            "actions": {
                "prev_sicx_bal_loan": 500 * ICX,
                "prev_bnUSD_debt_bal_loan": 50 * ICX,
                "sender": "user1",
                "name": "depositAndBorrow",
                "deposited_icx": 500 * ICX,
                "args": {
                    "_asset": "bnUSD",
                    "_amount": 9 * ICX
                },
                "expected": "1",
                "expected_sicx_baln_loan": 1000 * ICX,
                "expected_bnUSD_debt_baln_loan": 59 * ICX
            }
        },
        {
            "description": "user 2 deposits 500 ICX as collateral and borrows 9 bnUSD loan.",
            "actions": {
                "prev_sicx_bal_loan": 1000 * ICX,
                "prev_bnUSD_debt_bal_loan": 59 * ICX,
                "sender": "user2",
                "name": "depositAndBorrow",
                "deposited_icx": 500 * ICX,
                "args": {
                    "_asset": "bnUSD",
                    "_amount": 9 * ICX
                },
                "expected": "0",
                "revertMessage": "BalancedLoans: The initial loan of any asset must have a minimum value of 10.0 dollars.",
                "expected_sicx_baln_loan": 1000 * ICX,
                "expected_bnUSD_debt_baln_loan": 59 * ICX
            }
        },
        {
            "description": "user 2 deposits 100 ICX as collateral and borrows 100 bnUSD loan.",
            "actions": {
                "prev_sicx_bal_loan": 1000 * ICX,
                "prev_bnUSD_debt_bal_loan": 59 * ICX,
                "sender": "user2",
                "name": "depositAndBorrow",
                "deposited_icx": 100 * ICX,
                "args": {
                    "_asset": "bnUSD",
                    "_amount": 100 * ICX
                },
                "expected": "0",
                "revertMessage": "BalancedLoans: 100.0 collateral is insufficient to originate a loan of 100.0 bnUSD when max_debt_value = 25.0, new_debt_value = 60.393528307156785, which includes a fee of 1.0 bnUSD, given an existing loan value of 0.0.",
                "expected_sicx_baln_loan": 1000 * ICX,
                "expected_bnUSD_debt_baln_loan": 59 * ICX
            }
        }
        # {
        #     "description": "user 2 deposits 500 ICX as collateral and borrows -10 bnUSD loan.",
        #     "actions": {
        #         "prev_sicx_bal_loan": 1000 * ICX,
        #         "prev_bnUSD_debt_bal_loan": 59 * ICX,
        #         "sender": "user2",
        #         "name": "depositAndBorrow",
        #         "deposited_icx": 500 * ICX,
        #         "args": {
        #             "_asset": "bnUSD",
        #             "_amount": -10 * ICX
        #         },
        #         "expected": "0",
        #         "revertMessage": "BalancedLoans: Loans amount cannot be negative.",
        #         "expected_sicx_baln_loan": 1000 * ICX,
        #         "expected_bnUSD_debt_baln_loan": 59 * ICX
        #     }
        # }

    ]
}
