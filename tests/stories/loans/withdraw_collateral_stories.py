ICX = 10 ** 18
WITHDRAW_COLLATERAL = {
    "stories": [
        {
            "description": "User 1 deposits 500 ICX as collateral and borrows 50 bnUSD loan",
            "actions": {
                "prev_sicx_bal_loan": "0",
                "prev_icd_debt_bal_loan": "0",
                "sender": "user1",
                "name": "depositAndBorrow",
                "deposited_icx": "500000000000000000000",
                "args": {
                    "_asset": "bnUSD",
                    "_amount": "50000000000000000000"
                },
                "expected": "1",
                "expected_sicx_baln_loan": "500000000000000000000",
                "expected_icd_debt_baln_loan": "50000000000000000000"
            }
        },
        {
            "description": "User 1 withdraws 50 ICX from the available collateral",
            "actions": {
                "prev_sicx_bal_loan": "500000000000000000000",
                "prev_icd_debt_bal_loan": "50000000000000000000",
                "sender": "user1",
                "name": "withdrawCollateral",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_value": "50000000000000000000"
                },
                "expected": "1",
                "expected_sicx_baln_loan": "450000000000000000000",
                "expected_icd_debt_baln_loan": "50000000000000000000"
            }
        },
        {
            "description": "User 1 withdraws 330 ICX from the available collateral",
            "actions": {
                "prev_sicx_bal_loan": "450000000000000000000",
                "prev_icd_debt_bal_loan": "50000000000000000000",
                "sender": "user1",
                "name": "withdrawCollateral",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_value": "330000000000000000000"
                },
                "expected": "0",
                "revertMessage": "BalancedLoans: Requested withdrawal is more than available collateral. total debt value: 30196764153578393315 ICX remaining collateral value: 120000000000000000000 ICX locking value (max debt): 120787056614313573260 ICX",
                "expected_sicx_baln_loan": "450000000000000000000",
                "expected_icd_debt_baln_loan": "50000000000000000000"
            }
        },
        {
            "description": "User 1 withdraws 329 ICX from the available collateral",
            "actions": {
                "prev_sicx_bal_loan": "450000000000000000000",
                "prev_icd_debt_bal_loan": "50000000000000000000",
                "sender": "user1",
                "name": "withdrawCollateral",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_value": "329000000000000000000"
                },
                "expected": "1",
                "expected_sicx_baln_loan": "121000000000000000000",
                "expected_icd_debt_baln_loan": "50000000000000000000"
            }
        },
        {
            "description": "User 1 withdraws -50 ICX from the available collateral",
            "actions": {
                "prev_sicx_bal_loan": "121000000000000000000",
                "prev_icd_debt_bal_loan": "50000000000000000000",
                "sender": "user1",
                "name": "withdrawCollateral",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_value": "-50000000000000000000"
                },
                "expected": "0",
                "revertMessage": "BalancedLoans: Withdraw amount must be more than zero.",
                "expected_sicx_baln_loan": "121000000000000000000",
                "expected_icd_debt_baln_loan": "50000000000000000000"
            }
        },
        {
            "description": "User 1 withdraws 121 ICX from the available collateral",
            "actions": {
                "prev_sicx_bal_loan": "121000000000000000000",
                "prev_icd_debt_bal_loan": "50000000000000000000",
                "sender": "user1",
                "name": "withdrawCollateral",
                "deposited_icx": 0 * ICX,
                "args": {
                    "_value": "121000000000000000000"
                },
                "expected": "0",
                "revertMessage": "BalancedLoans: Requested withdrawal is more than available collateral. total debt value: 30196764153578393315 ICX remaining collateral value: 0 ICX locking value (max debt): 120787056614313573260 ICX",
                "expected_sicx_baln_loan": "121000000000000000000",
                "expected_icd_debt_baln_loan": "50000000000000000000"
            }
        }
    ]
}
