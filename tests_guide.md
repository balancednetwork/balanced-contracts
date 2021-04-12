# Balanced Test Guide

This file is  a complete guide to run tests  of Balanced Scores locally.

Step 1 : Clone the repository

Testing in t-bears
- Step 1 : Test files are inside `core_contracts` `tests` .
- Step 2 : Now you just need to change the file path for tests files and test-scenarios files.
- Step 3 : You can run tests in t-bears using a command : tbears test test_file_name . Here, test_file_name is tests.
    If you want to run some specific tests only then you can comment out other test files and run that test.
- Test files:
    - test_loan_add_collateral.py - This file tests different cases of addCollateral method in loans score.
    - test_loan_liduidation.py - This file tests different cases of liquidate method in loans score.
    - test_loan_repay_loan.py - This file tests different cases of _repay_loan method in loans score.
    - test_loan_withdraw.py - This file tests different cases of withdraw method in loans score.

Testing in NoteBook

- Step 1 : Test files are outside `core_contracts`.
- Step 2 : These are the tests written in jupyter notebook . You just need to run Jupyter Notebook in the folder 
    that contains these test files. 

- Test files:
    - test_loans_liquidation.ipynb - This file tests the liquidation condition of an account in loan score, if an account
        is in liquidate state it liquidates that account.
    - test_loans_OriginateLoans.ipynb - This  file tests different conditions for originanteLoan method in loans score.
    - test_loans_dead_market.ipynb - This file tests condition for a dead market and reviving market from dead state.
    - test_loan_retireAssets.ipynb - This file tests different condition for retireAsset method in loans score.
    - dex_liquidation_pair.ipynb - This file creates the pool for omm and balanced and tests different conditions of dex 
        and lp token distributions.
    - balance_test.ipynb - This file tests the functionality of balance token.
    
      

        