from iconservice import *

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
        self._loans.set(addresses['loans'])
        self._dex.set(addresses['dex'])
        self._staking.set(addresses['staking'])
        self._rewards.set(addresses['rewards'])
        self._reserve_fund.set(addresses['reserve_fund'])
        self._dividends.set(addresses['dividends'])
        self._oracle.set(addresses['oracle'])
        self._sicx.set(addresses['sicx'])
        self._icd.set(addresses['icd'])
        self._baln.set(addresses['baln'])
        self._bwt.set(addresses['bwt'])

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
