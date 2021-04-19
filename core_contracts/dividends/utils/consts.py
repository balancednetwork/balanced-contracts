DEFAULT_CAP_VALUE = 2 ** 256 - 1
DEFAULT_DECIMAL_VALUE = 18
ZERO_SCORE_ADDRESS = "cx0000000000000000000000000000000000000000"
DAYS_IN_A_WEEK = 7
MAX_LOOP = 100
MINIMUM_ELIGIBLE_DEBT = 50 * 10**18
BALNBNUSD = "BALNbnUSD"
BALN_HOLDERS = "baln_holders"
DAOFUND = "daofund"

class Status:
    DIVIDENDS_DISTRIBUTION_COMPLETE = 0
    COMPLETE_STAKED_BALN_UPDATES = 1
    FILTER_ELIGIBLE_STAKED_BALN_HOLDERS = 2
    TOTAL_DATA_FROM_BALN_LP_POOL = 3
    COMPUTE_BALN_FOR_LP_HOLDER = 4
    DAOFUND_DISTRIBUTION = 5
    DISTRIBUTE_FUND_TO_HOLDERS = 6

