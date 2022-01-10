#-------------------------------------------------------------------------------
# DEFAULT VALUES
#-------------------------------------------------------------------------------

EXA = 10**18
U_SECONDS_DAY = 86400 * 10**6  # Microseconds in a day.
DAY_ZERO = 18647
DAY_START = 61200 * 10**6  # 17:00 UTC
MAJORITY = 666666666666666667
BALNBNUSD_ID = 3
BALNSICX_ID = 4
POINTS = 10000

CONTRACTS = ['loans', 'dex', 'staking', 'rewards', 'dividends', 'daofund',
             'reserve', 'sicx', 'bnUSD', 'baln', 'bwt', 'router', 'feehandler']

ADDRESSES = {'loans': ['rewards', 'dividends', 'staking', 'reserve'],
             'dex': ['rewards', 'dividends', 'staking', 'sicx', 'bnUSD', 'baln', 'feehandler'],
             'rewards': ['reserve', 'baln', 'bwt', 'daofund'],
             'dividends': ['loans', 'daofund', 'dex', 'baln'],
             'daofund': ['loans'],
             'reserve': ['loans', 'baln', 'sicx'],
             'bnUSD': ['oracle'],
             'baln': ['dividends', 'oracle', 'dex', 'bnUSD'],
             'bwt': ['baln'],
             'router': ['dex', 'sicx', 'staking'],
             'feehandler': []}

ADMIN_ADDRESSES = {'loans': 'governance',
                   'dex': 'governance',
                   'rewards': 'governance',
                   'dividends': 'governance',
                   'daofund': 'governance',
                   'reserve': 'governance',
                   'bnUSD': 'loans',
                   'baln': 'rewards',
                   'bwt': 'governance',
                   'router': 'governance'}

#-------------------------------------------------------------------------------
# REWARDS LAUNCH CONFIG
#-------------------------------------------------------------------------------

DATA_SOURCES = [{'name': 'Loans', 'address': 'loans'},
                {'name': 'sICX/ICX', 'address': 'dex'}]

# First day rewards recipients split
RECIPIENTS = [{'recipient_name': 'Loans', 'dist_percent': 25 * 10**16},
              {'recipient_name': 'sICX/ICX', 'dist_percent': 10 * 10**16},
              {'recipient_name': 'Worker Tokens', 'dist_percent': 20 * 10**16},
              {'recipient_name': 'Reserve Fund', 'dist_percent': 5 * 10**16},
              {'recipient_name': 'DAOfund', 'dist_percent': 40 * 10**16}]

#-------------------------------------------------------------------------------
# LOANS LAUNCH CONFIG
#-------------------------------------------------------------------------------

# TODO: Bigya: add defaults ltv and origination for collaterals
ASSETS = [{'address': 'sicx', 'active': True, 'collateral': True},
          {'address': 'bnUSD', 'active': True, 'collateral': False},
          {'address': 'baln', 'active': False, 'collateral': True}]
