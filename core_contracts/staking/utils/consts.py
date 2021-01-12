from iconservice import *

DEFAULT_CAP_VALUE = 2 ** 256 -1
DEFAULT_DECIMAL_VALUE = 18
ZERO_SCORE_ADDRESS = "cxf000000000000000000000000000000000000000"
SYSTEM_SCORE = Address.from_string('cx0000000000000000000000000000000000000000')

dict1 ={"ab":5,"bc":3}

c = (str(dict1))
c = c.replace(' ','').replace("'",'').replace(",",'.')

print(c[1:-1] + '.')