from iconservice import *

EXA = 10**18

U_SECONDS_DAY = 86400 * 10**6  // 24 # Microseconds in a day.
MIN_UPDATE_TIME = 30 * 10**6  # 30 seconds

# All percentages expressed in terms of points.
POINTS = 10000
DEFAULT_MINING_RATIO = 50000
DEFAULT_LOCKING_RATIO = 40000
DEFAULT_LIQUIDATION_RATIO = 15000
LIQUIDATION_REWARD = 67
DEFAULT_ORIGINATION_FEE = 100
DEFAULT_REDEMPTION_FEE = 50
BAD_DEBT_RETIREMENT_BONUS = 1000

NEW_LOAN_MINIMUM = 50 * EXA # USD
REDEEM_MINIMUM = 1000 * EXA # USD
DEFAULT_MIN_MINING_DEBT = 50 * EXA # USD
REPLAY_BATCH_SIZE = 100
SNAP_BATCH_SIZE = 400
MAX_DIV_DEBT_LENGTH = 400

POSITION_DB_PREFIX = b'position'


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
