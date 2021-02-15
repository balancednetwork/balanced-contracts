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
             'dex': ['rewards', 'dividends', 'staking', 'sicx', 'icd'],
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
