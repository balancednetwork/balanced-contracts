# Balanced Test Guide

This file is  a complete guide to run tests  of Balanced Scores locally.
All the tests for Balanced are inside `tests` directory under specific folders. In order to run tests in different environment follow the below steps : 

Step 1 : Clone the repository

Testing in t-bears
- Step 1 : T-Bears test files are inside `tests/tbears_tests` and the test scenarios are inside `tests/test_scenarios` directory.
- Step 2 : To run the test , go to `tests` directory.  
- Step 3 : You can run tests in t-bears using the following command in the terminal: 
  - tbears test tbears_tests
- Test files:
    - test_loan_add_collateral.py - This file tests different cases of addCollateral method in loans score.
    - test_loan_liduidation.py - This file tests different cases of liquidate method in loans score.
    - test_loan_repay_loan.py - This file tests different cases of _repay_loan method in loans score.
    - test_loan_withdraw.py - This file tests different cases of withdraw method in loans score.
    
Testing in Python imported from Notebook

- Step 1 : Test files are inside `tests/tests_py`.
- Step 2 : These are the python test files imported from jupyter notebook . In order to run this test we need to run the
python file using a python command : python3 test_file_name.py. We can see output in the terminal.
  Example: python3 balance_test.py
  
- Test files:
    - test_loans_liquidation.py - This file tests the liquidation condition of an account in loan score, if an account
        is in liquidate state it liquidates that account.
    - test_loans_OriginateLoans.py - This  file tests different conditions for originanteLoan method in loans score.
    - test_loan_retireAssets.py - This file tests different condition for retireAsset method in loans score.
    - balance_test.py - This file tests the stake functionality of balance token.
    - test_staking - This file tests the functionality of staking .
    
Testing in NoteBook (Note: This will be removed soon.)

- Step 1 : Test files are inside `tests/notebook_tests`.
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
    