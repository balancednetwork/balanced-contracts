from iconservice import *

TAG = 'BalancedLoans'

EXA = 10**18

U_SECONDS_DAY = 86400 * (10 ** 6)
MIN_UPDATE_TIME = 30 * 10**6  # 30 seconds

# All percentages expressed in terms of points.
POINTS = 10000
MINING_RATIO = 50000
LOCKING_RATIO = 40000
LIQUIDATION_RATIO = 15000
LIQUIDATION_REWARD = 67
ORIGINATION_FEE = 100
REDEMPTION_FEE = 50
BAD_DEBT_RETIREMENT_BONUS = 1000
MAX_RETIRE_PERCENT = 100

NEW_LOAN_MINIMUM = 10 * EXA # USD
MIN_MINING_DEBT = 50 * EXA # USD

MAX_DEBTS_LIST_LENGTH = 400
SNAP_BATCH_SIZE = 50
REDEEM_BATCH_SIZE = 50


class Standing:
    INDETERMINATE = 0
    ZERO = 1
    LIQUIDATE = 2
    LOCKED = 3
    NOT_MINING = 4
    MINING = 5
    NO_DEBT = 6
    STANDINGS = ['Indeterminate', 'Zero', 'Liquidate', 'Locked',
                 'Not Mining', 'Mining', 'No Debt']

    @staticmethod
    def __getitem__(_standing: int) -> str:
        return Standing.STANDINGS[_standing]


class Outcome:
    NO_SUCCESS = 0
    SUCCESS = 1
    OUTCOMES = ['No Success', 'Success']


class Complete:
    NOT_DONE = 0
    DONE = 1
    COMPLETE = ['Not done', 'Done']
