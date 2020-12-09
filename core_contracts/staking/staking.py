from iconservice import *
from .utils.checks import *
from .utils.consts import *

# from .scorelib import *


TAG = 'StakedICXManager'

DENOMINATOR = 1000000000000000000


# An interface of token to distribute daily rewards
class sICXTokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def symbol(self, _owner: Address) -> str:
        pass

    @interface
    def totalSupply(self) -> int:
        pass

    @interface
    def mintTo(self, _account: Address, _amount: int, _data: bytes = None) -> None:
        pass

    @interface
    def burn(self, _amount: int) -> None:
        pass


class InterfaceSystemScore(InterfaceScore):
    @interface
    def setStake(self, value: int) -> None: pass

    @interface
    def getStake(self, address: Address) -> dict: pass

    @interface
    def getMainPReps(self) -> dict: pass

    @interface
    def setDelegation(self, delegations: list = None): pass

    @interface
    def getDelegation(self, address: Address) -> dict: pass

    @interface
    def claimIScore(self): pass

    @interface
    def queryIScore(self, address: Address) -> dict: pass

    @interface
    def getIISSInfo(self) -> dict: pass

    @interface
    def getPRepTerm(self) -> dict: pass

    @interface
    def getPReps(self, startRanking: int, endRanking: int) -> list: pass

class PrepDelegations(TypedDict):
    _address:Address
    _votes_in_per:int


class Staking(IconScoreBase):
    _SICX_SUPPLY = 'sICX_supply'
    _SICX_ADDRESS = 'sICX_address'
    _BLOCK_HEIGHT_WEEK = '_block_height_week'
    _BLOCK_HEIGHT_DAY = '_block_height_day'
    _TOTAL_STAKE = 'total_stake'
    _TOTAL_REWARD = 'total_reward'
    _ADDRESS_LIST = '_address_list'
    _PREP_LIST = '_prep_list'
    _TOP_PREPS = '_top_preps'
    _ADDRESS_DELEGATIONS = '_address_delegations'
    _PREP_DELEGATIONS = '_prep_delegations'

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, destination: Address, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def TokenTransfer(self, recipient: Address, amount: int, note: str):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._sICX_supply = VarDB(self._SICX_SUPPLY, db, value_type=int)
        # to store the block height for checking the top 100 preps in a week
        self._block_height_week = VarDB(self._BLOCK_HEIGHT_WEEK,db,value_type=int)
        self._block_height_day = VarDB(self._BLOCK_HEIGHT_DAY,db,value_type=int)
        self._sICX_address = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        # total staked from contract
        self.total_stake = VarDB(self._TOTAL_STAKE, db, value_type=int)
        # vardb to store total rewards
        self.total_reward = VarDB(self._TOTAL_REWARD, db, value_type=int)
        # array for storing all the addresse and prep addresses
        self._address_list = ArrayDB(self._ADDRESS_LIST, db, value_type=Address)
        self._prep_list = ArrayDB(self._PREP_LIST, db, value_type=Address)
        self._top_preps = ArrayDB(self._TOP_PREPS, db, value_type=Address)
        # dictdb for storing the address and their delegations
        self._address_delegations = DictDB(self._ADDRESS_DELEGATIONS, db, value_type=str)
        # dictdb for storing the prep address and their delegated value
        self._prep_delegations = DictDB(self._PREP_DELEGATIONS, db, value_type=int)

        self._system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)



    def on_install(self) -> None:
        super().on_install()
        self._block_height_week.set(self._system.getIISSInfo()["nextPRepTerm"])
        self._block_height_day.set(self._system.getIISSInfo()["nextPRepTerm"])
        self._set_top_preps()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Staking"

    @external(readonly=True)
    def get_rate(self) -> int:
        sICX_score = self.create_interface_score(self._sICX_address.get(),
                                                 sICXTokenInterface)

        if (self.total_stake.get()  + self.total_reward.get()) == 0:
            rate = DENOMINATOR
        else:
            rate = (self.total_stake.get()  + self.total_reward.get()) * DENOMINATOR // sICX_score.totalSupply()
        return rate

    @external
    def set_sICX_supply(self) -> None:
        """Only necessary for the dummy contract."""
        sICX_score = self.create_interface_score(self._sICX_address.get(),
                                                 sICXTokenInterface)
        self._sICX_supply.set(sICX_score.totalSupply())

    @external(readonly=True)
    def get_sICX_address(self) -> Address:
        return self._sICX_address.get()

    @external(readonly=True)
    def get_stake_from_contract(self,address:Address) -> dict:
        return self._system.getStake(address)

    @external(readonly=True)
    def get_total_stake(self) -> int:
        return self.total_stake.get()

    @external(readonly=True)
    def get_total_reward(self) -> int:
        return self.total_reward.get()

    @external(readonly=True)
    def get_top_preps(self) -> list:
        lis1= []
        for x in self._top_preps:
            lis1.append(x)
        return lis1

    @external(readonly=True)
    def get_address_list(self) -> list:
        addresses = []
        for single in self._address_list:
            addresses.append(single)
        return addresses

    @external(readonly=True)
    def get_prep_list(self) -> list:
        addresses = []
        for single in self._prep_list:
            addresses.append(single)
        return addresses

    @external(readonly=True)
    def get_delegations(self,_address:Address) -> dict:
        return self._address_delegations[str(_address)]

    @external(readonly=True)
    def get_address_delegations(self, _address:Address) -> dict:
        str1 = self._address_delegations[str(_address)]
        if str1 != '':
            dict1 = {}
            lis1 = (str1.split("."))
            lis1.pop()
            for one in lis1:
                lis2 = (one.split(":"))
                if lis2[0] not in dict1.keys():
                    dict1[lis2[0]] = int(lis2[1])
                else:
                    if lis2[1]  != '0':
                        dict1[lis2[0]] =   dict1[lis2[0]] + int(lis2[1])
                    else:
                        dict1[lis2[0]] = 0
            return dict1
        else:
            return {}

    @external(readonly=True)
    def get_prep_delegations(self) -> dict:
        dict1 ={}
        for x in self.get_prep_list():
            dict1[str(x)] = self._prep_delegations[str(x)]
        return dict1

    @external(readonly=True)
    def reward_info(self, _address: Address) -> dict:
        return self._system.queryIScore(_address)

    @external
    def set_sICX_address(self, _address: Address) -> None:
        self._sICX_address.set(_address)

    @external(readonly=True)
    def get_balance(self) -> int:
        return self.icx.get_balance(self.address)

    def _set_top_preps(self) -> None :
        prep_dict =  self._system.getPReps(1,20)
        address = prep_dict['preps']
        for one in address:
            self._top_preps.put(one['address'])

    def _loop_in_params(self,_to:Address,_prep_address:list,prep_list_contract:list, top_preps:list, get_delegated_value:dict,total_sicx:int) -> int:
        amount_to_stake = 0
        prep_list_to_delegate=[]
        prep_amount_left = 0
        sum_votes =0
        for single_prep in _prep_address:
            if single_prep["_address"] not in prep_list_contract:
                self._prep_list.put(single_prep["_address"])
            amount_to_stake += single_prep["_votes_in_per"]
            self._set_address_delegations(_to, single_prep['_address'], single_prep["_votes_in_per"], get_delegated_value,total_sicx)
        return amount_to_stake

    def _distribute_evenly(self, amount_to_distribute: int, top_preps: list,total_sicx:int,flags:int=0) -> int:
        _value = 0
        if flags == 1:
            prep_delegations = self.get_prep_delegations()
            for one_prep in top_preps:
                self._set_address_delegations(_to, one_prep, _value, prep_delegations,
                                              total_sicx)
        else:
            evenly_ditribution = (DENOMINATOR * amount_to_distribute) // len(top_preps)
            _value = (evenly_ditribution) // DENOMINATOR
        return _value

    def _set_address_delegations(self, _to: Address, _prep: Address, _value:int,_delegations:dict,total_sicx:int,overwrite_flag:int=0) -> None:
        if overwrite_flag ==1:
            _value = (_value * DENOMINATOR) // DENOMINATOR
        else:
            _value = _value * DENOMINATOR
        self._address_delegations[str(_to)] += str(_prep) + ':' + str(_value) + '.'
        _value = (_value  * total_sicx) // (100 * DENOMINATOR)
        self._set_prep_delegations(_prep,_value,_delegations)

    def _set_prep_delegations(self,_prep:Address,_value:int,_delegations:dict) -> None:
        if _delegations == {} :
            self._prep_delegations[str(_prep)] = _value

        else:
            if str(_prep) in _delegations.keys():
                if _delegations[str(_prep)] != 0 :
                    self._prep_delegations[str(_prep)] = self._prep_delegations[
                                                             str(_prep)] + _value
                else:
                    self._prep_delegations[str(_prep)] = _value
            else:
                self._prep_delegations[str(_prep)] = _value

    def _stake_and_delegate(self,evenly_distribute_value:int = 0) -> None:
        self._stake(self.total_stake.get() + self.total_reward.get())
        self._delegations(evenly_distribute_value,{})

    def _update_internally(self,_to:Address,total_sicx_of_user:int) -> None:
        previous_address_delegations = self.get_address_delegations(_to)
        self._address_delegations[str(_to)] = ''
        total_icx_hold = (total_sicx_of_user * self.get_rate()) // DENOMINATOR
        total_icx_hold = total_icx_hold - self.msg.value
        for ab in previous_address_delegations.items():
            x = Address.from_string(str(ab[0]))
            self._prep_delegations[str(x)] = self._prep_delegations[
                                                 str(x)] - ((ab[1] * total_icx_hold) // (100 * DENOMINATOR))
            if self._prep_delegations[str(x)] < 0:
                self._prep_delegations[str(x)] = 0

    def _check_top_100_preps(self, top_preps: list,total_sicx_of_user:int) -> int:
        to_distribute = 0
        for single_prep in self.get_prep_delegations().keys():
            if Address.from_string(single_prep) not in top_preps:
                to_distribute += self._prep_delegations[str(single_prep)]
        to_evenly_distribute_value = self._distribute_evenly(to_distribute, top_preps, total_sicx_of_user,
                                                             0)
        return to_evenly_distribute_value

    def _check_for_week(self) -> None:
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_week.get() + (7 * 43200):
            self._block_height_week.set(self._system.getIISSInfo()["nextPRepTerm"])
            for i in range(len(self._top_preps)):
                self._top_preps.pop()
            self._set_top_preps()

    def _check_for_day(self) -> None:
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_day.get() +  43200:
            self._block_height_day.set(self._system.getIISSInfo()["nextPRepTerm"])
            self._claim_iscore()

    @payable
    @external
    def add_collateral(self, _to: Address, _prep_address: List[PrepDelegations] = None, _data: bytes = None) ->None:
        if _data is None:
            _data = b'None'
        if _to not in self.get_address_list():
            self._address_list.put(_to)
        self._check_for_week()
        self._check_for_day()
        if _prep_address is not None:
            if len(_prep_address) > 100:
                revert('Only 100 prep addresses should be provided')
        self.total_stake.set(self.total_stake.get()+self.msg.value)
        sicx = self._sICX_address.get()
        sICX_score = self.create_interface_score(sicx, sICXTokenInterface)
        supply = self._sICX_supply.get()
        # balance = self.icx.get_balance(self.address)
        balance = self._system.getStake(self.address)
        balance = balance['stake'] + self.msg.value
        if balance == self.msg.value:
            amount = self.msg.value
        else:
            amount = supply * self.msg.value // (balance - self.msg.value)
        sICX_score.mintTo(_to, amount, _data)
        total_sicx_of_user = sICX_score.balanceOf(_to)
        previous_address_delegations = self.get_address_delegations(_to)
        if previous_address_delegations != {}:
            self._update_internally(_to,total_sicx_of_user)
        prep_delegations = self.get_prep_delegations()
        to_evenly_distribute_value,amount_to_stake_in_per,prep_amount_left = 0,0,0
        prep_list_to_delegate = []
        top_preps = self.get_top_preps()
        prep_list_of_contract = self.get_prep_list()
        if _prep_address != None:
            amount_to_stake_in_per = self._loop_in_params(_to, _prep_address,
                                                                     prep_list_of_contract, top_preps, prep_delegations,
                                                                     total_sicx_of_user)

        else:
            if previous_address_delegations == {}:
                amount_to_stake_in_per = 100
                flags= 1
                to_evenly_distribute_value = self._distribute_evenly(amount_to_stake_in_per, top_preps, total_sicx_of_user,flags)

            else:
                for dict_prep_delegation in previous_address_delegations.items():
                    amount_to_stake_in_per += dict_prep_delegation[1]
                    self._set_address_delegations(_to, Address.from_string(str(dict_prep_delegation[0])),int(dict_prep_delegation[1]), prep_delegations, total_sicx_of_user,1)
        if amount_to_stake_in_per != 100:
            revert(f'The total delegations should be 100 %')
        to_evenly_distribute_value  = self._check_top_100_preps(top_preps, total_sicx_of_user)
        self._stake_and_delegate(to_evenly_distribute_value)
        self._sICX_supply.set(self._sICX_supply.get() + amount)
        self.TokenTransfer(_to, amount, f'{amount / DENOMINATOR} sICX minted to {_to}')

    @external
    def update_delegations(self,_prep_address: List[PrepDelegations]):
        _to = self.msg.sender
        if _to not in self.get_address_list():
            revert('You need to provide ICX before updating the votes')
        if _prep_address == None:
            revert('Delegation list should be provided')
        if len(_prep_address) > 100:
            revert('Only 100 prep addresses should be provided')
        self._check_for_week()
        self._check_for_day()
        sicx = self._sICX_address.get()
        sICX_score = self.create_interface_score(sicx, sICXTokenInterface)
        total_sicx_of_user = sICX_score.balanceOf(_to)
        evenly_distribute_value = 0
        previous_address_delegations = self.get_address_delegations(_to)
        self._update_internally(_to,total_sicx_of_user)
        top_preps = self.get_top_preps()
        prep_list_of_contract = self.get_prep_list()
        prep_delegations = self.get_prep_delegations()
        amount_to_stake_in_per= self._loop_in_params(_to, _prep_address,
                                                                 prep_list_of_contract, top_preps, prep_delegations,
                                                                 total_sicx_of_user)
        if amount_to_stake_in_per != 100:
            revert('Total delegations should be 100 %')
        to_evenly_distribute_value  = self._check_top_100_preps(top_preps, total_sicx_of_user)
        self._delegations(evenly_distribute_value,{})

    def _claim_iscore(self):
        dict1 = self._system.queryIScore(self.address)
        top_preps = self.get_preps()
        if dict1['estimatedICX'] != 0:
            claimed_ICX = dict1["estimatedICX"]
            self._system.claimIScore()
            self.total_reward.set(self.total_reward.get() + amount)
            prep_delegations = self.get_prep_delegations()
            total_staked = self._system.getStake(self.address)
            total_staked = total_staked['stake']
            dict_prep_reward= {}
            for single_prep in prep_delegations:
                value_in_icx = self._prep_delegations[str(one)]
                total_weightage_in_per = ((value_in_icx * DENOMINATOR) //total_staked) * 100
                single_prep_reward = ((total_weightage_in_per // 100) * amount) // DENOMINATOR
                dict_prep_reward[single_prep] = single_prep_reward
            self._stake(self.total_stake.get() + self.total_reward.get())
            self._delegations(0,dict_prep_reward)
        else:
            revert('There is no iscore to claim')


    @external
    def withdraw(self, _from: Address, _value:int = 0, _data: bytes = None):
        if _data is None:
            _data = b'None'
        if _from not in self.get_address_list():
            revert('You need to stake first before unstaking')
        unstaked_amount  = self.tokenFallback(_to,_value,_data)
        amount_to_unstake = _value * self.get_rate()
        delegation_dict = self.get_address_delegations(str(_to))
        self.total_stake.set(self.total_stake.get() - amount_to_unstake)


    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        """
        Used only to receive sICX for unstaking.
        :param _from: Token orgination address.
        :type _from: :class:`iconservice.base.address.Address`
        :param _value: Number of tokens sent.
        :type _value: int
        :param _data: Unused, ignored.
        :type _data: bytes
        """
        if self.msg.sender != self._sICX_address.get():
            revert(f'The Staking contract only accepts sICX tokens.')
        Logger.debug(f'({_value}) tokens received from {_from}.', TAG)
        return self._unstake(_from, _value)


    def _stake(self, _stake_value: int) -> None:
        self._system.setStake(_stake_value)

    def _delegations(self,evenly_distribute_value:int,dict_prep_reward:dict) -> None:
        prep_delegations = self.get_top_preps()
        delegation_list = []
        if dict_prep_reward !={}:
            for one in prep_delegations:
                one = Address.from_string(str(one))
                delegation_info: Delegation = {
                    "address": one,
                    "value": self._prep_delegations[str(one)] + dict_prep_reward[one]
                }
                delegation_list.append(delegation_info)

        else:
            for one in prep_delegations:
                one = Address.from_string(str(one))
                delegation_info: Delegation = {
                    "address": one,
                    "value": self._prep_delegations[str(one)] + evenly_distribute_value + claim_reward
                }
                delegation_list.append(delegation_info)
            # revert(f'{delegation_list} and {self.total_stake.get()} and {self.get_prep_delegations()} and {evenly_distribute_value}')
        self._system.setDelegation(delegation_list)

    def _unstake(self, _from: Address, _value: int) -> None:
        sICX_score = self.create_interface_score(self._sICX_address.get(),
                                                 sICXTokenInterface)
        unstaked = self.icx.get_balance(self.address) * _value // sICX_score.totalSupply()
        sICX_score.burn(_value)
        self._send_ICX(_from, unstaked, f'Unstaked sICX from {self.msg.sender}')

        self._sICX_supply.set(self._sICX_supply.get() - unstaked)
        return unstaked

    def _send_ICX(self, _to: Address, amount: int, msg: str) -> None:
        """
        Sends ICX to an address.
        :param _to: ICX destination address.
        :type _to: :class:`iconservice.base.address.Address`
        :param _amount: Number of ICX sent.
        :type _amount: int
        :param msg: Message for the event log.
        :type msg: str
        """
        try:
            self.icx.transfer(_to, amount)
            self.FundTransfer(_to, amount, msg + f' {amount} ICX sent to {_to}.')
        except BaseException as e:
            revert(f'{amount} ICX not sent to {_to}. '
                   f'Exception: {e}')

    @payable
    def fallback(self):
        """Only for the dummy contract, to simulate claiming Iscore."""
        pass

