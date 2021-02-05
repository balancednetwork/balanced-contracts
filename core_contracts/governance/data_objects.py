from iconservice import *

class BalancedAddresses(TypedDict, total=False):
    loans: Address
    dex: Address
    staking: Address
    rewards: Address
    reserve_fund: Address
    dividends: Address
    oracle: Address
    sicx: Address
    icd: Address
    baln: Address
    bwt: Address


class Addresses(object):

    def __init__(self, db:IconScoreDatabase) -> None:
        self._loans = VarDB('loans', db, Address)
        self._dex = VarDB('dex', db, Address)
        self._staking = VarDB('staking', db, Address)
        self._rewards = VarDB('rewards', db, Address)
        self._reserve_fund = VarDB('reserve_fund', db, Address)
        self._dividends = VarDB('dividends', db, Address)
        self._oracle = VarDB('oracle', db, Address)
        self._sicx = VarDB('sicx', db, Address)
        self._icd = VarDB('icd', db, Address)
        self._baln = VarDB('baln', db, Address)
        self._bwt = VarDB('bwt', db, Address)

    def setAddresses(self, addresses: TypedDict) -> None:
        """
        Takes a TypedDict with 1 to 11 addresses and sets them.
        """
        set_func: dict = {'loans': self._loans.set,
                          'dex': self._dex.set,
                          'staking': self._staking.set,
                          'rewards': self._rewards.set,
                          'reserve_fund': self._reserve_fund.set,
                          'dividends': self._dividends.set,
                          'oracle': self._oracle.set,
                          'sicx': self._sicx.set,
                          'icd': self._icd.set,
                          'baln': self._baln.set,
                          'bwt': self._bwt.set}
        for key in addresses.keys():
            set_func[key](addresses[key])

    def getAddresses(self) -> dict:
        return {
                'loans': self._loans.get(),
                'dex': self._dex.get(),
                'staking': self._staking.get(),
                'rewards': self._rewards.get(),
                'reserve_fund': self._reserve_fund.get(),
                'dividends': self._dividends.get(),
                'oracle': self._oracle.get(),
                'sicx': self._sicx.get(),
                'icd': self._icd.get(),
                'baln': self._baln.get(),
                'bwt': self._bwt.get()
               }
