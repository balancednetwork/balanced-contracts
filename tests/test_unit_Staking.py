from unittest import mock
from unittest.mock import patch
import pprint
from iconservice import Address, IconScoreException, IconScoreBase
from tbears.libs.scoretest.patch.score_patcher import get_interface_score, ScorePatcher
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from pprint import pprint
from core_contracts.staking.staking import Staking
from core_contracts.staking.utils.checks import SenderNotScoreOwnerError

EXA = 10 ** 18


class Mock_Staking():

    def getIISSInfo(self):
        # print("next called")
        return {"nextPRepTerm": 1}

    def getPReps(self, x, y):
        # print("next called 1")
        return {"blockHeight": "0x246e21f", "startRanking": "0x1", "totalDelegated": "0x1442e60d8b6b6149d5e41e2",
                "totalStake": "0x15a91f6a769bc3588297b7a", "preps": [
                {"address": "hxf5a52d659df00ef0517921647516daaf7502a728", "status": "0x0", "penalty": "0x0",
                 "grade": "0x0", "name": "binance node", "country": "CYM", "city": "George town", "stake": "0x0",
                 "delegated": "0x2bcff93c61327dd1af4bc5", "totalblocks": "0x718e4c", "validatedblocks": "0x71887c",
                 "unvalidatedsequenceblocks": "0x0", "irep": "0x21e19e0c9bab2400000",
                 "irepupdateblockheight": "0x1cf1960", "lastgenerateblockheight": "0x246e1f0",
                 "blockheight": "0x1cf1960", "txindex": "0x1",
                 "nodeaddress": "hxf0bc67e700af57efc0a9140948c5678c50669f36", "email": "poolvip@binance.com",
                 "website": "https://binance.com", "details": "https://binance.com/json",
                 "p2pEndpoint": "170.106.8.247:7100"}]}


class Mock_staking_int:
    def __init__(self, _to, return_balanceOf, _amount, _data):
        #     class Mock_sICXTokenInterface:
        #         def balanceOf(self, _to):
        #             return return_balanceOf
        #         def mintTo(self, _to, _amount, _data):
        #             pass
        #
        #     self.mock_sICX = Mock_sICXTokenInterface()
        self._to = _to
        self.return_balanceOf = return_balanceOf
        self._amount = _amount
        self._data = _data

    def balanceOf(self, _to):
        return self.return_balanceOf

    def mintTo(self, _to, _amount, _data):
        pass

    # def get_sICX_score(self):


    #
    # def create_interface_score(self):
    #     return self.mock_sICX


class Mock_Staking_Method:
    def __init__(self):
        pass

    def _get_address_delegations_in_per(self):
        pass


class test_unit_Staking(ScoreTestCase):

    def __init__(self, methodName: str = ...):
        super().__init__(methodName)
        self.test_account3 = None

    def setUp(self):
        super().setUp()

        self._owner = self.test_account1
        self._to = self.test_account2
        self.test_account3 = Address.from_string(f"hx{'12331' * 8}")
        self._prep1 = self.test_account3
        self._prep2 = Address.from_string(f"hx{'12341' * 8}")
        self._prep3 = Address.from_string(f"hx{'12c31' * 8}")
        self.mock_InterfaceSystemScore = Address.from_string('cx0000000000000000000000000000000000000000')
        self.mock_sICXTokenInterface = Address.from_string('cx1000000000000000000000000000000000000000')
        # self.patch_internal_method(self.mock_InterfaceSystemScore, 'getIISSInfo', {'nextPRepTerm': 1})

        with patch('core_contracts.staking.staking.IconScoreBase.create_interface_score', return_value=Mock_Staking()):
            score = self.get_score_instance(Staking, self._owner)
            # print("called")

        self.score = score
        # self.set_msg(self._owner)

    def test_name(self):
        self.set_tx(self._owner)
        # print(self.score.name())
        self.assertEqual('Staked ICX Manager', self.score.name())

    def test_getTodayRate(self):
        DENOMINATOR = 10 ** 18
        self.set_msg(self._owner)
        # print(self.score.getTodayRate())

        self.assertEqual(DENOMINATOR, self.score.getTodayRate())

    def test_toggleStakingOn(self):
        self.set_msg(self._owner)
        # self.score.toggleStakingOn()

        self.score.toggleStakingOn()
        # NOT OWNER
        self.set_msg(self._to)
        with self.assertRaises(SenderNotScoreOwnerError) as err:  # executes when assertionError is raised
            print(str(err), 'method called by other than owner raise Error')
            self.score.toggleStakingOn()

    def test_getSicxAddress(self):
        self.set_msg(self._owner)
        self.score.setSicxAddress(self.mock_sICXTokenInterface)
        self.assertEqual(self.mock_sICXTokenInterface, self.score.getSicxAddress())

    def test_setSicxAddress(self):
        self.set_msg(self._owner)
        self.score.setSicxAddress(self.mock_sICXTokenInterface)
        self.set_msg(self._to)
        with self.assertRaises(SenderNotScoreOwnerError) as err:
            self.score.setSicxAddress(self.mock_sICXTokenInterface)

        self.set_msg(self._owner)
        with self.assertRaises(IconScoreException) as err:
            print(str(err), "is not a contract. an EOA")
            self.score.setSicxAddress(self._to)  # EOA address sent

    def test_getUnstakeInfo(self):
        self.score.getUnstakeInfo()

    def test_getUserUnstakeInfo(self):
        print(self.score.getUserUnstakeInfo(self._owner))

    def test_getTopPreps(self):
        self.score.getTopPreps()

    def test_getAddressDelegations(self):
        self.set_msg(self._owner)
        self.score.setSicxAddress(self.mock_sICXTokenInterface)
        _bln = 15 * 10 ** 18
        self.score._rate.set(1 * EXA)

        self.score._address_delegations = {
            str(self._owner): f'{self._prep1}:30.{self._prep2}:72.',
            str(self._to): f'{self._prep1}:50.{self._prep2}:40.{self._prep3}:80.',
            # has to end with '.' to get full value

        }
        expected_value = {
            str(self._prep1): 7,
            str(self._prep2): 6,
            str(self._prep3): 12,
        }

        _address = self._to
        self.patch_internal_method(self.mock_sICXTokenInterface, 'balanceOf', lambda _address: _bln)
        print(self.score.getAddressDelegations(_address))
        return_value = self.score.getAddressDelegations(_address)
        self.assert_internal_call(self.mock_sICXTokenInterface, 'balanceOf', _address)

        self.assertEqual(expected_value, return_value)

    def test_getPrepDelegations(self):
        self.score.getPrepDelegations()

    def test_delegate(self):
        self.set_msg(self._owner)
        self.score.toggleStakingOn()
        # print(self.score._staking_on.get())
        _bln = 100 * 10 ** 18

        to = self._to
        return_blnc = 20 * EXA
        amount = 50 * EXA
        Data = b'StakingICX'
        patch_value = Mock_staking_int(_to=to, return_balanceOf=return_blnc, _amount=amount,
                                       _data=Data)
        # with patch.object(self.mock_sICXTokenInterface, 'balanceOf', wraps=patch_value.balanceOf):
        #     print('===')
        #     self.score.stakeICX(self._to, b'stakeICX')
