from iconservice import Address
from iconservice.base.exception import IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from core_contracts.loans.loans.loans import Loans

GOV = Address.from_string(f"cx{'1596' * 10}")
REWARDS = Address.from_string(f"cx{'1578' * 10}")
SICX = Address.from_string(f"cx{'9584' * 10}")
BNUSD = Address.from_string(f"cx{'1254' * 10}")
BALN = Address.from_string(f"cx{'6589' * 10}")
STAKING = Address.from_string(f"cx{'8421' * 10}")
FEE = Address.from_string(f"cx{'8426' * 10}")
from unittest import mock


class Token:

    def __init__(self, token):
        self.total_supply = 0
        self.balance = {}
        self.token = token

    def symbol(self):
        return self.token

    def priceInLoop(self):
        return 1  10 * 18

    def totalSupply(self):
        return self.total_supply

    def mint(self, from, amount):
        self.total_supply += _amount
        self.balance[_from] = self.balance.get(_from, 0) + _amount

    def mintTo(self, from, amount, _data=None):
        self.total_supply += _amount
        self.balance[_from] = self.balance.get(_from, 0) + _amount

    def lastPriceInLoop(self):
        return self.priceInLoop()

class Interfaces:
    def __init__(self, score):
        self.score = score

    class Staking:
        def __init__(self1, self):
            self1.self = self

        def icx(self1, deposit):
            class ICX:
                def stakeICX(self2):
                    self1.self.score._sICX_received.set(deposit)

            return ICX

    class sicx(Token):
        pass

    class bnusd(Token):
        pass

    class baln(Token):
        pass

    class feeHandler():
        pass

    class gov():
        def getContractAddress(self, name):
            if name == "feehandler":
                return FEE

    def create_interface_score(self, address, interface):
        if address == SICX:
            return self.sicx("sICX")
        if address == BNUSD:
            return self.bnusd("bnUSD")
        if address == BALN:
            return self.baln("BALN")
        if address == STAKING:
            return self.Staking(self)
        if address == FEE:
            return self.feeHandler()
        if address == GOV:
            return self.gov()


class TestDividendsUnit(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.loans = self.get_score_instance(Loans, self.test_account1,
                                             on_install_params={"_governance": GOV})
        self.test_account3 = Address.from_string(f"hx{'12345' * 8}")
        self.test_account4 = Address.from_string(f"hx{'1234' * 10}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)
        self._setup()

    def _setup(self):
        self.set_msg(GOV)
        self.set_tx(timestamp=0)
        self.loans.setAdmin(GOV)
        self.loans.setContinuousRewardsDay(3)
        self.loans.setStaking(STAKING)

        with mock.patch.object(self.loans, "create_interface_score",
                               wraps=Interfaces(self.loans).create_interface_score):
            self.loans.addAsset(**{'_token_address': SICX, '_active': True, '_collateral': True})
            self.loans.addAsset(**{'_token_address': BNUSD, '_active': True, '_collateral': False})
            self.loans.addAsset(**{'_token_address': BALN, '_active': False, '_collateral': True})

        with mock.patch.object(self.loans, "getDay", return_value=1):
            self.loans._positions._snapshot_db.start_new_snapshot()
            self.loans.turnLoansOn()
        self.loans.setRewards(REWARDS)
        self.loans._time_offset.set(self.loans.now())
        self.loans._current_day.set(1)

    def test_precompute(self):
        m1 = mock.patch.object(self.loans, "create_interface_score",
                               wraps=Interfaces(self.loans).create_interface_score)
        m1.start()





        with mock.patch.object(self.loans, "getDay", return_value=2):
            self.set_msg(REWARDS)
            self.set_tx(timestamp=1)
            self.loans.precompute(1, 50)
            self.set_msg(self.test_account3, 500 *10 ** 18)
            self.loans.depositAndBorrow(_asset='bnUSD', amount=100 * 10 ** 18, from=None, _value=50 * 10 ** 18)


        data = self.loans.getSnapshot(1)
        print(data)

        with mock.patch.object(self.loans, "getDay", return_value=3):

            self.set_tx(timestamp=2)
            self.set_msg(REWARDS)
            self.loans.precompute(2, 50)
        data = self.loans.getSnapshot(2)
        print(data)

        m1.stop()
