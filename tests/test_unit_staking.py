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


class Mock_Staking:

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

    def setStake(self, _stake_value):
        pass

    def getStake(self, address):
        return {'unstakes': {
            -1: {'unstakeBlockHeight': 10000}
        }}

    def setDelegation(self, a):
        pass


class Mock_staking_int:

    def __init__(self, sICXInterface_address, _to, return_balanceOf, _amount, _data):
        self.sICX_address = sICXInterface_address
        outer_class = self

        class Mock_sICXTokenInterface:
            def balanceOf(self, _to):
                return return_balanceOf

            def mintTo(self, _to, _amount, _data):
                pass

            def burn(self, _amount):
                pass

        self.mock_sICX = Mock_sICXTokenInterface()

    def create_interface_score(self, address, score):
        if address == self.sICX_address:
            return self.mock_sICX

        else:
            raise NotImplemented()


class Mock_Staking_Method:
    def __init__(self):
        pass

    def _get_address_delegations_in_per(self):
        pass


class Test_unit_staking(ScoreTestCase):

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
            # print(str(err), 'method called by other than owner raise Error')
            self.score.toggleStakingOn()

    def test_setSicxAddress(self):
        self.set_msg(self._owner)
        self.score.setSicxAddress(self.mock_sICXTokenInterface)
        self.set_msg(self._to)
        # self.score.setSicxAddress(self.mock_sICXTokenInterface)

        with self.assertRaises(SenderNotScoreOwnerError) as err:
            self.score.setSicxAddress(self.mock_sICXTokenInterface)
        self.set_msg(self._owner)
        try:
            self.score.setSicxAddress(self._to)  # EOA sent instead of contract
        except IconScoreException as err:

            self.assertEqual('StakedICXManager: Address provided is an EOA address. A contract address is required.',
                             err.message)

    def test_getSicxAddress(self):
        self.set_msg(self._owner)
        self.score.setSicxAddress(self.mock_sICXTokenInterface)
        self.assertEqual(self.mock_sICXTokenInterface, self.score.getSicxAddress())

    def test_setUnstakeBatchLimit(self):
        self.set_msg(self._owner)
        self.score.setUnstakeBatchLimit(2)

    def test_getUnstakeBatchLimit(self):
        print(self.score.getUnstakeBatchLimit())

    def test_getPrepList(self):
        print(self.score.getPrepList())

    def test_getUnstakingAmount(self):
        print(self.score.getUnstakingAmount())

    def test_getTotalStake(self):
        print(self.score.getTotalStake())

    def test_getLifetimeReward(self):
        print(self.score.getLifetimeReward())

    def test_getTopPreps(self):
        self.score.getTopPreps()

    def test_getAddressDelegations(self):
        self.set_msg(self._owner)
        self.score.setSicxAddress(self.mock_sICXTokenInterface)
        _bln = 15 * 10 ** 18
        self.score._rate.set(1 * EXA)

        self.score._address_delegations = {
            str(self._owner): f'{self._prep1}:50.{self._prep2}:50.',
            str(self._to): f'{self._prep1}:50.{self._prep2}:40.{self._prep3}:10.',
            # has to end with '.' to get full value

        }
        expected_value = {
            str(self._prep1): 7,
            str(self._prep2): 6,
            str(self._prep3): 1,
        }

        _address = self._to
        self.patch_internal_method(self.mock_sICXTokenInterface, 'balanceOf', lambda _address: _bln)
        print(self.score.getAddressDelegations(_address))
        return_value = self.score.getAddressDelegations(_address)
        self.assert_internal_call(self.mock_sICXTokenInterface, 'balanceOf', _address)

        self.assertEqual(expected_value, return_value)


    def test_getPrepDelegations(self):
        self.score.getPrepDelegations()

    def test_getUnstakeInfo(self):
        self.score.getUnstakeInfo()

    def test_getUserUnstakeInfo(self):
        print(self.score.getUserUnstakeInfo(self._owner))

    def test_claimUnstakedICX(self):
        self.score.claimUnstakedICX(self._owner)

    def test_claimableICX(self):
        print(self.score.claimableICX(self._owner))

    def test_stakeICX(self):
        try:
            self.score.transferUpdateDelegations()
        except IconScoreException as err:
            self.assertEqual('StakedICXManager: ICX Staking SCORE is not active.', err.message)

        self.set_msg(self._owner, 20 * EXA)
        self.score._sICX_address.set(self.mock_sICXTokenInterface)
        self.score.toggleStakingOn()
        self.score._total_stake.set(200 * EXA)

        self.score._rate.set(3 * EXA)
        _bln = 150 * 10 ** 18
        amount = 50 * EXA
        Data = b'StakingICX'
        _to = self._to
        expected_value = 6666666666666666666  #
        patch_sicx_interface = Mock_staking_int(sICXInterface_address=self.mock_sICXTokenInterface,
                                                _to=_to,
                                                return_balanceOf=_bln,
                                                _amount=amount,
                                                _data=Data).create_interface_score
        with patch.object(self.score, 'create_interface_score', wraps=patch_sicx_interface):
            print("I'm IN")
            val = self.score.stakeICX()
            print(val)
            print("I'm OUT")
            self.assertEqual(expected_value, val)

    def test_transferUpdateDelegations(self):
        try:
            self.score.transferUpdateDelegations()
        except IconScoreException as err:
            self.assertEqual('StakedICXManager: ICX Staking SCORE is not active.', err.message)

        self.set_msg(self._owner)
        self.score._sICX_address.set(self.mock_sICXTokenInterface)
        self.score.toggleStakingOn()
        # CALLING FUNCTION WITH OWNER ADDRESS
        try:
            self.score.transferUpdateDelegations(self._owner, self._to, 10 * 10 ** 18)
        except IconScoreException as err:
            self.assertEqual("StakedICXManager: Only sicx token contract can call this function.", err.message)

        self.set_msg(self.mock_sICXTokenInterface)  # SETTING SICXINTERFACE ADDRESS AS IN CALLING FUNCTION
        _bln = 150 * 10 ** 18
        amount = 50 * EXA
        Data = b'StakingICX'

        patch_sicx_interface = Mock_staking_int(sICXInterface_address=self.mock_sICXTokenInterface,
                                                _to=0,
                                                return_balanceOf=_bln,
                                                _amount=amount,
                                                _data=Data).create_interface_score
        with patch.object(self.score, 'create_interface_score', wraps=patch_sicx_interface):
            print("I'm IN")
            self.score.transferUpdateDelegations(self._owner, self._to, 10 * 10 ** 18)
            print("I'm OUT")

    def test_delegate(self):
        self.set_msg(self._owner)
        try:
            self.score.delegate()
        except IconScoreException as err:
            self.assertEqual('StakedICXManager: ICX Staking SCORE is not active.', err.message)

        self.score.toggleStakingOn()

        _bln = 100 * 10 ** 18

        self.score._rate.set(1 * EXA)

        self.score._address_delegations = {
            str(self._owner): f'{self._prep1}:50.{self._prep2}:50.',
            str(self._to): f'{self._prep1}:50.{self._prep2}:40.{self._prep3}:10.',

        }

        _user_delegations = [
            {'_address': 'hxe0cde6567eb6529fe31b0dc2f2697af84847f321', '_votes_in_per': 100 * 10 ** 18}]
        _to = self._owner

        self.score._sICX_address.set(self.mock_sICXTokenInterface)
        self.score._total_stake.set(1000 * 10 ** 18)

        # self.patch_internal_method(self.mock_sICXTokenInterface, 'balanceOf', lambda _to: _bln)
        # # ScorePatcher.register_interface_score(self.mock_sICXTokenInterface)
        # # ScorePatcher.patch_internal_method(self.mock_sICXTokenInterface, 'balanceOf', lambda _to: 2* 10**18)
        # self.score.delegate(_user_delegations)
        # self.assert_internal_call(self.mock_sICXTokenInterface, 'balanceOf', _to)

        # raise Exception("not completed")
        return_blnc = 20 * EXA
        amount = 50 * EXA
        Data = b'StakingICX'

        patch_sicx_interface = Mock_staking_int(sICXInterface_address=self.mock_sICXTokenInterface,
                                                _to=_to,
                                                return_balanceOf=_bln,
                                                _amount=amount,
                                                _data=Data).create_interface_score
        with patch.object(self.score, 'create_interface_score', wraps=patch_sicx_interface):
            print("I'm here")
            self.score.delegate(_user_delegations)
            print("I'm here")

    def test_tokenFallback(self):
        # CHECKING FOR STAKING ON
        self.set_msg(self._owner)
        try:
            self.score.tokenFallback()
        except IconScoreException as err:
            self.assertEqual('StakedICXManager: ICX Staking SCORE is not active.', err.message)
        # CHECKING FOR METHOD CALLED BY EOA ADDRESS
        self.score.toggleStakingOn()
        _from = self._owner
        _value = 100 * 10 ** 18
        _data = b"{\"method\": \"unstake\",\"user\":\"hx436106433144e736a67710505fc87ea9becb141d\"}"
        _to = self._to
        try:
            self.score.tokenFallback(_from, _value, _data)
        except IconScoreException as err:
            self.assertEqual("StakedICXManager: The Staking contract only accepts sICX tokens.", err.message)

        self.set_msg(self.mock_sICXTokenInterface)
        self.score._sICX_address.set(self.mock_sICXTokenInterface)
        patch_sicx_interface = Mock_staking_int(sICXInterface_address=self.mock_sICXTokenInterface,
                                                _to=_to,
                                                return_balanceOf=_value,
                                                _amount=_value,
                                                _data=_data).create_interface_score
        with patch.object(self.score, 'create_interface_score', wraps=patch_sicx_interface):
            print("I'm here")
            self.score.tokenFallback(_from, _value, _data)
            print("I'm here")
