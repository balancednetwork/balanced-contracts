from iconservice import *
from .utils.consts import *
from .interfaces import *

class BalancedAddresses(TypedDict, total=False):
    loans: Address
    dex: Address
    staking: Address
    rewards: Address
    reserve: Address
    dividends: Address
    oracle: Address
    sicx: Address
    icd: Address
    bal: Address
    bwt: Address


class Addresses(object):

    def __init__(self, db:IconScoreDatabase, gov: IconScoreBase) -> None:
        self._db = db
        self._gov = gov
        self._loans = VarDB('loans', db, Address)
        self._dex = VarDB('dex', db, Address)
        self._staking = VarDB('staking', db, Address)
        self._rewards = VarDB('rewards', db, Address)
        self._reserve = VarDB('reserve', db, Address)
        self._dividends = VarDB('dividends', db, Address)
        self._oracle = VarDB('oracle', db, Address)
        self._sicx = VarDB('sicx', db, Address)
        self._icd = VarDB('icd', db, Address)
        self._baln = VarDB('bal', db, Address)
        self._bwt = VarDB('bwt', db, Address)

    def __getitem__(self, key: str) -> Address:
        if key == 'governance':
            return self._gov.address
        return VarDB(key, self._db, Address).get()

    def __setitem__(self, key, value):
        revert('illegal access')

    def setAddresses(self, addresses: TypedDict) -> None:
        """
        Takes a TypedDict with 1 to 11 addresses and sets them.
        """
        set_func: dict = {'loans': self._loans.set,
                          'dex': self._dex.set,
                          'staking': self._staking.set,
                          'rewards': self._rewards.set,
                          'reserve': self._reserve.set,
                          'dividends': self._dividends.set,
                          'oracle': self._oracle.set,
                          'sicx': self._sicx.set,
                          'icd': self._icd.set,
                          'bal': self._baln.set,
                          'bwt': self._bwt.set}
        for key in addresses.keys():
            set_func[key](addresses[key])

    def getAddresses(self) -> dict:
        return {
                'loans': self._loans.get(),
                'dex': self._dex.get(),
                'staking': self._staking.get(),
                'rewards': self._rewards.get(),
                'reserve': self._reserve.get(),
                'dividends': self._dividends.get(),
                'oracle': self._oracle.get(),
                'sicx': self._sicx.get(),
                'icd': self._icd.get(),
                'bal': self._baln.get(),
                'bwt': self._bwt.get()
               }

    def setContractAddresses(self) -> None:
        """
        Set the addresses in each SCORE for the other SCOREs.
        """
        for contract in ADDRESSES:
            score = self._gov.create_interface_score(self[contract], SetAddressesInterface)
            set_methods = {'admin': score.setAdmin, 'loans': score.setLoans,
                           'rewards': score.setRewards, 'dividends': score.setDividends,
                           'staking': score.setStaking, 'reserve': score.setReserve,
                           'oracle': score.setOracle, 'sicx': score.setSicx,
                           'icd': score.setIcd, 'bal': score.setBaln, 'bwt': score.setBwt}
            for method in ADDRESSES[contract]:
                try:
                    set_methods[method](self[method])
                except BaseException as e:
                    revert(f'Problem setting {method} on {contract}. '
                           f'Exception: {e}')

    def setAdmins(self) -> None:
        """
        Set the admin addresses for each SCORE.
        """
        for contract in ADMIN_ADDRESSES:
            score = self._gov.create_interface_score(self[contract], SetAddressesInterface)
            try:
                score.setAdmin(self[ADMIN_ADDRESSES[contract]])
            except BaseException as e:
                revert(f'Problem setting admin address to {ADMIN_ADDRESSES[contract]} '
                       f'on {contract}. Exception: {e}')
