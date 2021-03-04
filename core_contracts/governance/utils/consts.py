#-------------------------------------------------------------------------------
# DEFAULT VALUES
#-------------------------------------------------------------------------------

UNITS_PER_TOKEN = 10**18
U_SECONDS_DAY = 86400 * 10**6 // 24 # Microseconds in a day.
DAY_ZERO = 18647 * 24
DAY_START = 61200 * 10**6 // 24 # 17:00 UTC


CONTRACTS = ['loans', 'dex', 'staking', 'rewards', 'dividends', 'reserve',
             'sicx', 'icd', 'bal', 'bwt']

ADDRESSES = {'loans': ['rewards', 'dividends', 'staking', 'reserve'],
             'dex': ['rewards', 'dividends', 'staking', 'sicx', 'icd', 'bal'],
             'rewards': ['reserve', 'bal', 'bwt'],
             'dividends': ['loans'],
             'reserve': ['loans', 'bal', 'sicx'],
             'icd': ['oracle'],
             'bal': ['dividends'],
             'bwt': ['bal']}

ADMIN_ADDRESSES = {'loans': 'governance',
                   'dex': 'governance',
                   'rewards': 'governance',
                   'dividends': 'governance',
                   'reserve': 'governance',
                   'icd': 'loans',
                   'bal': 'rewards',
                   'bwt': 'governance'}

#-------------------------------------------------------------------------------
# REWARDS LAUNCH CONFIG
#-------------------------------------------------------------------------------

DATA_SOURCES = [{'name': 'Loans', 'address': 'loans'},
                {'name': 'SICXICX', 'address': 'dex'},
                {'name': 'SICXICD', 'address': 'dex'},
                {'name': 'BALNICD', 'address': 'dex'}]

RECIPIENTS = [{'recipient_name': 'Loans', 'bal_token_dist_percent': 25 * 10**16},
              {'recipient_name': 'SICXICX', 'bal_token_dist_percent': 10 * 10**16},
              {'recipient_name': 'SICXICD', 'bal_token_dist_percent': 20 * 10**16},
              {'recipient_name': 'BALNICD', 'bal_token_dist_percent': 20 * 10**16},
              {'recipient_name': 'Worker Tokens', 'bal_token_dist_percent': 20 * 10**16},
              {'recipient_name': 'Reserve Fund', 'bal_token_dist_percent': 5 * 10**16}]

#-------------------------------------------------------------------------------
# LOANS LAUNCH CONFIG
#-------------------------------------------------------------------------------

ASSETS = [{'address': 'sicx', 'active': True, 'collateral': True},
          {'address': 'icd', 'active': True, 'collateral': False},
          {'address': 'bal', 'active': False, 'collateral': True}]
