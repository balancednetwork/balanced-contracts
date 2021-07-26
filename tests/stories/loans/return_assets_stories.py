ICX = 10 ** 18
RETURN_ASSETS = {
    "stories": [
        {
            "description": "User 1 deposits 500 ICX as collateral and borrows 50 bnUSD loan",
            "actions": {
                "prev_sicx_bal_loan": 0,
                "prev_bnUSD_debt_bal_loan": 0,
                "prev_bnUSD_bal_wallet": 0,
                "sender": "user1",
                "name": "depositAndBorrow",
                "deposited_icx": 500 * ICX,
                "args": {
                    "_asset": "bnUSD",
                    "_amount": 50 * ICX
                },
                "expected": "1",
                "expected_sicx_baln_loan": 500 * ICX,
                "expected_bnUSD_debt_baln_loan": 50 * ICX,
                "expected_bnUSD_bal_wallet": 50 * ICX
            }
        },
        {
            "description": "user 1 repays a loan of 10 bnUSD by calling returnAsset method to loans score.",
            "actions": {
                "prev_sicx_bal_loan": 500 * ICX,
                "prev_bnUSD_debt_bal_loan": 50 * ICX,
                "prev_bnUSD_bal_wallet": 50 * ICX,
                "sender": "user1",
                "name": "returnAsset",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_symbol": "bnUSD",
                    "_value": 10 * ICX
                },
                "expected": "1",
                "expected_sicx_baln_loan": 500 * ICX,
                "expected_bnUSD_debt_baln_loan": 40 * ICX,
                "expected_bnUSD_bal_wallet": 40 * ICX
            }
        },
        {
            "description": "user 1 repays a loan of -10 bnUSD by calling returnAsset method to loans score.",
            "actions": {
                "prev_sicx_bal_loan": 500 * ICX,
                "prev_bnUSD_debt_bal_loan": 40 * ICX,
                "prev_bnUSD_bal_wallet": 40 * ICX,
                "sender": "user1",
                "name": "returnAsset",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_symbol": "bnUSD",
                    "_value": -10 * ICX
                },
                "expected": "0",
                "revertMessage": "BalancedLoans: Amount retired must be greater than zero.",
                "expected_sicx_baln_loan": 500 * ICX,
                "expected_bnUSD_debt_baln_loan": 40 * ICX,
                "expected_bnUSD_bal_wallet": 40 * ICX
            }
        },
        {
            "description": "user 1 repays a loan of 40 bnUSD by calling returnAsset method to loans score.",
            "actions": {
                "prev_sicx_bal_loan": 500 * ICX,
                "prev_bnUSD_debt_bal_loan": 40 * ICX,
                "prev_bnUSD_bal_wallet": 40 * ICX,
                "sender": "user1",
                "name": "returnAsset",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_symbol": "bnUSD",
                    "_value": 40 * ICX
                },
                "expected": "1",
                "expected_sicx_baln_loan": 500 * ICX,
                "expected_bnUSD_debt_baln_loan": 0,
                "expected_bnUSD_bal_wallet": 0
            }
        },
        {
            "description": "user 1 repays a loan of 40 bnUSD by calling returnAsset method to loans score.",
            "actions": {
                "prev_sicx_bal_loan": 500 * ICX,
                "prev_bnUSD_debt_bal_loan": 0,
                "prev_bnUSD_bal_wallet": 0,
                "sender": "user1",
                "name": "returnAsset",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_symbol": "bnUSD",
                    "_value": 40 * ICX
                },
                "expected": "0",
                "revertMessage": "BalancedLoans: Insufficient balance.",
                "expected_sicx_baln_loan": 500 * ICX,
                "expected_bnUSD_debt_baln_loan": 0,
                "expected_bnUSD_bal_wallet": 0
            }
        },
{
            "description": "User 1 again deposits 500 ICX as collateral and borrows 50 bnUSD loan",
            "actions": {
                "prev_sicx_bal_loan": 500 * ICX,
                "prev_bnUSD_debt_bal_loan": 0,
                "prev_bnUSD_bal_wallet": 0,
                "sender": "user1",
                "name": "depositAndBorrow",
                "deposited_icx": 500 * ICX,
                "args": {
                    "_asset": "bnUSD",
                    "_amount": 50 * ICX
                },
                "expected": "1",
                "expected_sicx_baln_loan": 1000 * ICX,
                "expected_bnUSD_debt_baln_loan": 50 * ICX,
                "expected_bnUSD_bal_wallet": 50 * ICX
            }
        },
{
            "description": "user 1 again repays a loan of 30 bnUSD by calling returnAsset method to loans score.",
            "actions": {
                "prev_sicx_bal_loan": 1000 * ICX,
                "prev_bnUSD_debt_bal_loan": 50 * ICX,
                "prev_bnUSD_bal_wallet": 50 * ICX,
                "sender": "user1",
                "name": "returnAsset",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_symbol": "bnUSD",
                    "_value": 30 * ICX
                },
                "expected": "1",
                "expected_sicx_baln_loan": 1000 * ICX,
                "expected_bnUSD_debt_baln_loan": 20 * ICX,
                "expected_bnUSD_bal_wallet": 20 * ICX
            }
        },
        {
            "description": "user 2 doesn't have position on balanced but has some bnUSD and tries to"
                           " repay a loan of 10 bnUSD by calling returnAsset method to loans score.",
            "actions": {
                "prev_sicx_bal_loan": 0 * ICX,
                "prev_bnUSD_debt_bal_loan": 0 * ICX,
                "prev_bnUSD_bal_wallet": 10 * ICX,
                "sender": "user2",
                "name": "returnAsset",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_symbol": "bnUSD",
                    "_value": 10 * ICX
                },
                "expected": "0",
                "revertMessage": "BalancedLoans: No debt repaid because,hxa7d00f90b669de7f4e3407c6d4468ef6fe86b8ce does not have a position in Balanced",
                "expected_sicx_baln_loan": 0 * ICX,
                "expected_bnUSD_debt_baln_loan": 10 * ICX,
                "expected_bnUSD_bal_wallet": 10 * ICX
            }
        }
    ]

}
