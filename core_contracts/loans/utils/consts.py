from iconservice import *

EXA = 10**18

U_SECONDS_DAY = 86400 * 10**6  # Microseconds in a day.
MIN_UPDATE_TIME = 30 * 10**6  # 30 seconds

POINTS = 10000
DEFAULT_MINING_RATIO = 500
DEFAULT_LOCKING_RATIO = 400
DEFAULT_LIQUIDATION_RATIO = 150
LIQUIDATION_REWARD = 67 # Points of collateral sent to liquidator as a reward.
DEFAULT_ORIGINATION_FEE = 100
DEFAULT_REDEMPTION_FEE = 50
BAD_DEBT_RETIREMENT_BONUS = 1000

REDEEM_MINIMUM = 10 # USD
REPLAY_BATCH_SIZE = 100

POSITION_DB_PREFIX = b'position'


class Standing:
    LIQUIDATE = 0
    LOCKED = 1
    NOT_MINING = 2
    MINING = 3
    UNDETERMINED = 4
    STANDINGS = ['Liquidate', 'Locked', 'Not Mining', 'Mining', 'Undetermined']
