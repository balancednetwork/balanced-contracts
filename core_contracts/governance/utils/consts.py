#-------------------------------------------------------------------------------
# DEFAULT VALUES
#-------------------------------------------------------------------------------

UNITS_PER_TOKEN = 10**18
U_SECONDS_DAY = 86400 * 10**6 // 24 # Microseconds in a day.
DAY_ZERO = 18647 * 24
DAY_START = 61200 * 10**6 // 24 # 17:00 UTC


CONTRACTS = ['loans', 'dex', 'staking', 'rewards', 'dividends', 'daofund',
             'reserve', 'sicx', 'bnUSD', 'baln', 'bwt']

ADDRESSES = {'loans': ['rewards', 'dividends', 'staking', 'reserve'],
             'dex': ['rewards', 'dividends', 'staking', 'sicx', 'bnUSD', 'baln'],
             'rewards': ['reserve', 'baln', 'bwt', 'daofund'],
             'dividends': ['loans', 'daofund'],
             'daofund': ['loans'],
             'reserve': ['loans', 'baln', 'sicx'],
             'bnUSD': ['oracle'],
             'baln': ['dividends', 'dex'],
             'bwt': ['baln']}

ADMIN_ADDRESSES = {'loans': 'governance',
                   'dex': 'governance',
                   'rewards': 'governance',
                   'dividends': 'governance',
                   'daofund': 'governance',
                   'reserve': 'governance',
                   'bnUSD': 'loans',
                   'baln': 'rewards',
                   'bwt': 'governance'}

#-------------------------------------------------------------------------------
# REWARDS LAUNCH CONFIG
#-------------------------------------------------------------------------------

DATA_SOURCES = [{'name': 'Loans', 'address': 'loans'},
                {'name': 'SICXICX', 'address': 'dex'},
                {'name': 'SICXbnUSD', 'address': 'dex'}]

# First day rewards recipients split
RECIPIENTS = [{'recipient_name': 'Loans', 'bal_token_dist_percent': 25 * 10**16},
              {'recipient_name': 'SICXICX', 'bal_token_dist_percent': 10 * 10**16},
              {'recipient_name': 'SICXbnUSD', 'bal_token_dist_percent': 175 * 10**15},
              {'recipient_name': 'Worker Tokens', 'bal_token_dist_percent': 20 * 10**16},
              {'recipient_name': 'Reserve Fund', 'bal_token_dist_percent': 5 * 10**16},
              {'recipient_name': 'DAOfund', 'bal_token_dist_percent': 225 * 10**15}]

#-------------------------------------------------------------------------------
# LOANS LAUNCH CONFIG
#-------------------------------------------------------------------------------

ASSETS = [{'address': 'sicx', 'active': True, 'collateral': True},
          {'address': 'bnUSD', 'active': True, 'collateral': False},
          {'address': 'baln', 'active': False, 'collateral': True}]
