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
    _RATE = '_rate'
    _SICX_ADDRESS = 'sICX_address'
    _BLOCK_HEIGHT_WEEK = '_block_height_week'
    _BLOCK_HEIGHT_DAY = '_block_height_day'
    _UNSTAKE_TIME_PERIOD = '_unstake_time_period'
    _TOTAL_STAKE = '_total_stake'
    _TOTAL_REWARD = '_total_reward'
    _ADDRESS_LIST = '_address_list'
    _PREP_LIST = '_prep_list'
    _UNSTAKE_ADDRESS = '_unstake_address'
    _TOP_PREPS = '_top_preps'
    _ADDRESS_DELEGATIONS = '_address_delegations'
    _UNSTAKING_DICT = '_unstaking_dict'
    _PREP_DELEGATIONS = '_prep_delegations'
    _UNSTAKE_AMOUNT = '_unstake_amount'

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
        self._rate = VarDB(self._RATE, db, value_type=int)
        # to store the block height for checking the top 100 preps in a week
        self._block_height_week = VarDB(self._BLOCK_HEIGHT_WEEK,db,value_type=int)
        self._block_height_day = VarDB(self._BLOCK_HEIGHT_DAY,db,value_type=int)
        self._unstake_time_period = VarDB(self._UNSTAKE_TIME_PERIOD,db,value_type=int)
        self._sICX_address = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        # total staked from staking contract
        self._total_stake = VarDB(self._TOTAL_STAKE, db, value_type=int)
        # vardb to store total rewards
        self._total_reward = VarDB(self._TOTAL_REWARD, db, value_type=int)
        # vardb to store total unstaking amount
        self._unstake_amount = VarDB(self._UNSTAKE_AMOUNT, db, value_type=int)
        # array for storing all the addresses and prep addresses
        self._address_list = ArrayDB(self._ADDRESS_LIST, db, value_type=Address)
        self._prep_list = ArrayDB(self._PREP_LIST, db, value_type=Address)
        self._unstake_address = ArrayDB(self._UNSTAKE_ADDRESS, db, value_type=Address)
        # array to store top 100 preps
        self._top_preps = ArrayDB(self._TOP_PREPS, db, value_type=Address)
        # dictdb for storing the address and their delegations
        self._address_delegations = DictDB(self._ADDRESS_DELEGATIONS, db, value_type=str)
        #dictdb for storing address as a key and unstaking amount as value
        self._unstaking_dict = DictDB(self._UNSTAKING_DICT, db, value_type=int)
        # dictdb for storing the prep address and their delegated value
        self._prep_delegations = DictDB(self._PREP_DELEGATIONS, db, value_type=int)
        # initializing the system score
        self._system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        #initialize the sicx score
        self.sICX_score = self.create_interface_score(self._sICX_address.get(), sICXTokenInterface)




    def on_install(self) -> None:
        super().on_install()
        # initializing the block height to check change in the top 100 preps
        self._block_height_week.set(self._system.getIISSInfo()["nextPRepTerm"])
        # initializing the block height to claim rewards once a day
        self._block_height_day.set(self._system.getIISSInfo()["nextPRepTerm"])
        self._unstake_time_period.set(self._system.getIISSInfo()["nextPRepTerm"])
        # top 100 preps is initialized at first
        self._rate.set(self.getRate())
        self._set_top_preps()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Staking"

    @external(readonly=True)
    def getRate(self) -> int:
        # sICX_score = self.create_interface_score(self._sICX_address.get(),
                                                 # sICXTokenInterface)

        if (self._total_stake.get() ) == 0:
            rate = DENOMINATOR
        else:
            rate = (self._total_stake.get()) * DENOMINATOR // self.sICX_score.totalSupply()
        return rate

    @external
    def set_sICX_supply(self) -> None:
        """Only necessary for the dummy contract."""
        # sICX_score = self.create_interface_score(self._sICX_address.get(),
        #                                          sICXTokenInterface)
        self._sICX_supply.set(self.sICX_score.totalSupply())

    @external(readonly=True)
    def getSicxAddress(self) -> Address:
        return self._sICX_address.get()

    @external(readonly=True)
    def getUnstakingAmount(self):
        return self._unstake_amount.get()

    @external(readonly=True)
    def getStakeFromNetwork(self) -> dict:
        return self._system.getStake(self.address)

    @external(readonly=True)
    def getDelegationFromNetwork(self) -> dict:
        return self._system.getDelegation(self.address)

    @external(readonly=True)
    def getTotalStake(self) -> int:
        return self._total_stake.get()

    @external(readonly=True)
    def getLifetimeReward(self) -> int:
        return self._total_reward.get()

    @external(readonly=True)
    def getTopPreps(self) -> list:
        lis1= []
        for x in self._top_preps:
            lis1.append(x)
        return lis1

    @external(readonly=True)
    def getUserAddressList(self) -> list:
        addresses = []
        for single in self._address_list:
            addresses.append(single)
        return addresses

    @external(readonly=True)
    def getUnstakingPendingAddress(self) -> list:
        addresses = []
        for single in self._unstake_address:
            addresses.append(single)
        return addresses

    @external(readonly=True)
    def getPrepList(self) -> list:
        addresses = []
        for single in self._prep_list:
            addresses.append(single)
        return addresses

    @external(readonly=True)
    def getAddressDelegations(self,_address:Address) -> dict:
        dict1 ={}
        dict_address_votes = self.getAddressDelegationsInPer(_address)
        total_sicx_of_user = self.sICX_score.balanceOf(_address)
        total_icx_hold = (total_sicx_of_user * self.getRate()) // DENOMINATOR
        for one in dict_address_votes.items():
            address = one[0]
            vote_in_per = one[1]
            votes_in_icx = ((vote_in_per // 100 ) * total_icx_hold) // DENOMINATOR
            dict1[str(address)] = votes_in_icx
        return dict1

    def getAddressDelegationsInPer(self, _address:Address) -> dict:
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
    def getUnstakeRequest(self) -> dict:
        unstake_request_address = self.getUnstakingPendingAddress()
        dict1={}
        for single_address in unstake_request_address:
            dict1[str(single_address)] = self._unstaking_dict[str(single_address)]
        return dict1

    @external(readonly=True)
    def getPrepDelegations(self) -> dict:
        dict1 ={}
        for x in self.getPrepList():
            dict1[str(x)] = self._prep_delegations[str(x)]
        return dict1

    @external
    def setSicxAddress(self, _address: Address) -> None:
        self._sICX_address.set(_address)

    def _set_top_preps(self) -> None :
        prep_dict =  self._system.getPReps(1,20)
        address = prep_dict['preps']
        for one in address:
            self._top_preps.put(one['address'])

    def _loop_in_params(self,_to:Address,_user_delegations:list,prep_list_contract:list, get_delegated_value:dict,total_sicx:int) -> int:
        amount_to_stake = 0
        for single_prep in _user_delegations:
            if single_prep["_address"] not in prep_list_contract:
                self._prep_list.put(single_prep["_address"])
            if single_prep["_address"] not in self.getTopPreps():
                revert(f'The delegation should be given to top 100 preps of the staking contract')
            amount_to_stake += single_prep["_votes_in_per"]
            self._set_address_delegations(_to, single_prep['_address'], single_prep["_votes_in_per"], get_delegated_value,total_sicx)
        return amount_to_stake

    def _distribute_evenly(self, amount_to_distribute: int, top_preps: list,total_sicx:int=0,flags:int=0,_to:Address=None,prep_list:list=[]) -> int:
        _value = 0
        if flags == 1:
            prep_delegations = self.getPrepDelegations()
            evenly_ditribution = (DENOMINATOR * amount_to_distribute) // len(top_preps)
            for one_prep in top_preps:
                if one_prep not in prep_list:
                    self._prep_list.put(one_prep)
                self._set_address_delegations(_to, one_prep, evenly_ditribution, prep_delegations,
                                              total_sicx,1)
        else:
            evenly_ditribution = (DENOMINATOR * amount_to_distribute) // len(top_preps)
            _value = (evenly_ditribution) // DENOMINATOR
        return _value

    def _get_amount_to_mint(self):
        supply = self._sICX_supply.get()
        # balance = self.get_stake_from_network(self.address)
        # balance = balance['stake'] + self.msg.value
        balance = self.getTotalStake()
        if balance == self.msg.value:
            amount = self.msg.value
        else:
            amount = supply * self.msg.value // (balance - self.msg.value)
        return amount

    def _set_address_delegations(self, _to: Address, _prep: Address, _value:int,_delegations:dict,total_sicx:int,overwrite_flag:int=0) -> None:
        if overwrite_flag ==1:
            _value = (_value * DENOMINATOR) // DENOMINATOR
        else:
            _value = _value * DENOMINATOR
        self._address_delegations[str(_to)] += str(_prep) + ':' + str(_value) + '.'
        _value = (_value  * total_sicx) // (100 * DENOMINATOR)
        self._set_prep_delegations(_prep,_value,_delegations)

    def _set_prep_delegations(self,_prep:Address,_value:int,_delegations:dict,flag:int=0) -> None:
        if flag == 1:
            if str(_prep) in _delegations.keys():
                if _delegations[str(_prep)] != 0 :
                    self._prep_delegations[str(_prep)] = self._prep_delegations[
                                                             str(_prep)] - _value
        else:
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
        self._stake(self.getTotalStake())
        self._delegations(evenly_distribute_value,{})

    def _update_internally(self,_to:Address,total_sicx_of_user:int) -> None:
        previous_address_delegations = self.getAddressDelegationsInPer(_to)
        if previous_address_delegations != {}:
            self._address_delegations[str(_to)] = ''
            total_icx_hold = (total_sicx_of_user * self._rate.get()) // DENOMINATOR
            total_icx_hold = total_icx_hold - self.msg.value
            for each in previous_address_delegations.items():
                x = Address.from_string(str(each[0]))
                self._prep_delegations[str(x)] = self._prep_delegations[
                                                     str(x)] - ((each[1] * total_icx_hold) // (100 * DENOMINATOR))
                if self._prep_delegations[str(x)] < 0:
                    self._prep_delegations[str(x)] = 0
        else:
            revert('You need to have delegations before updating')

    def _check_top_100_preps(self, top_preps: list) -> None:
        to_distribute = 0
        for single_prep in self.getPrepDelegations().keys():
            if Address.from_string(single_prep) not in top_preps:
                to_distribute += self._prep_delegations[str(single_prep)]
        to_evenly_distribute_value = self._distribute_evenly(to_distribute, top_preps, total_sicx_of_user,
                                                             0)
        self._stake_and_delegate(to_evenly_distribute_value)

    def _check_for_week(self) -> None:
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_week.get() + (7 * 43200):
            self._block_height_week.set(self._system.getIISSInfo()["nextPRepTerm"])
            for i in range(len(self._top_preps)):
                self._top_preps.pop()
            self._set_top_preps()
            self._check_top_100_preps(self.getTopPreps())

    def _check_for_day(self) -> None:
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_day.get() +  43200:
            self._block_height_day.set(self._system.getIISSInfo()["nextPRepTerm"])
            self._rate.set(self.getRate())
            self._claim_iscore()

    def _check_for_balance(self) -> None:
        balance_score = self.icx.get_balance(self.address)
        if balance_score > 0:
            unstake_address_list = self.getUnstakingPendingAddress()
            for one in unstake_address_list:
                value_to_transfer = self._unstaking_dict[str(one)]
                if value_to_transfer < balance_score:
                    self._send_ICX(one,self._unstaking_dict[str(one)])
                    del self._unstaking_dict[str(one)]
                    top = self._unstake_address.pop()
                    if top != one:
                        for i in range(len(self._unstake_address)):
                            if self._unstake_address[i] == one:
                                self._unstake_address[i] = top
                else:
                    break


    @payable
    @external
    def addCollateral(self, _to: Address = None , _user_delegations: List[PrepDelegations] = None) -> None:
        if _user_delegations is not None:
            if len(_user_delegations) > 100:
                revert('Only 100 prep addresses should be provided')
        if _to == None:
            _to = self.msg.sender
        if _to not in self.getUserAddressList():
            self._address_list.put(_to)
        self._check_for_week()
        self._check_for_day()
        self._check_for_balance()
        self._total_stake.set(self._total_stake.get()+self.msg.value)
        # sicx = self._sICX_address.get()
        # sICX_score = self.create_interface_score(sicx, sICXTokenInterface)
        amount = self._get_amount_to_mint()
        self.sICX_score.mintTo(_to, amount)
        total_sicx_of_user = self.sICX_score.balanceOf(_to)
        previous_address_delegations = self.getAddressDelegationsInPer(_to)
        if previous_address_delegations != {}:
            self._update_internally(_to,total_sicx_of_user)
        prep_delegations = self.getPrepDelegations()
        to_evenly_distribute_value,amount_to_stake_in_per = 0,0
        top_preps = self.getTopPreps()
        prep_list_of_contract = self.getPrepList()
        if _user_delegations != None:
            amount_to_stake_in_per = self._loop_in_params(_to, _user_delegations,
                                                                     prep_list_of_contract, prep_delegations,
                                                                     total_sicx_of_user)

        else:
            if previous_address_delegations == {}:
                amount_to_stake_in_per = 100
                flags= 1
                to_evenly_distribute_value = self._distribute_evenly(amount_to_stake_in_per, top_preps, total_sicx_of_user,flags,_to,prep_list_of_contract)

            else:
                for dict_prep_delegation in previous_address_delegations.items():
                    amount_to_stake_in_per += dict_prep_delegation[1]
                    self._set_address_delegations(_to, Address.from_string(str(dict_prep_delegation[0])),int(dict_prep_delegation[1]), prep_delegations, total_sicx_of_user,1)
                amount_to_stake_in_per = amount_to_stake_in_per // DENOMINATOR
        if amount_to_stake_in_per != 100:
            revert(f'The total delegations should be 100 %')
        self._stake_and_delegate(to_evenly_distribute_value)
        self._sICX_supply.set(self._sICX_supply.get() + amount)
        self.TokenTransfer(_to, amount, f'{amount / DENOMINATOR} sICX minted to {_to}')

    @external
    def updateDelegations(self,_user_delegations: List[PrepDelegations]):
        _to = self.msg.sender
        if _to not in self.getUserAddressList():
            revert('You need to provide ICX before updating the votes')
        if _user_delegations == None:
            revert('Delegation list should be provided')
        if len(_user_delegations) > 100:
            revert('Only 100 prep addresses should be provided')
        self._check_for_week()
        self._check_for_day()
        self._check_for_balance()
        sicx = self._sICX_address.get()
        # sICX_score = self.create_interface_score(sicx, sICXTokenInterface)
        total_sicx_of_user = self.sICX_score.balanceOf(_to)
        self._update_internally(_to,total_sicx_of_user)
        prep_list_of_contract = self.getPrepList()
        prep_delegations = self.getPrepDelegations()
        amount_to_stake_in_per= self._loop_in_params(_to, _user_delegations,
                                                                 prep_list_of_contract, prep_delegations,
                                                                 total_sicx_of_user)
        if amount_to_stake_in_per != 100:
            revert('Total delegations should be 100 %')
        self._delegations(0,{})

    def _claim_iscore(self):
        dict1 = self._system.queryIScore(self.address)
        if dict1['estimatedICX'] != 0:
            amount = dict1["estimatedICX"]
            self._system.claimIScore()
            self._total_reward.set(self.getLifetimeReward() + amount)
            self._total_stake.set(self.getTotalStake()+ amount)
            prep_delegations = self.getPrepDelegations()
            # prep_delegations = self.getPrepList()
            total_staked_amount = self.getTotalStake()
            for single_prep in prep_delegations:
                value_in_icx = self._prep_delegations[str(single_prep)]
                total_weightage_in_per = ((value_in_icx * DENOMINATOR) //total_staked_amount) * 100
                single_prep_reward = ((total_weightage_in_per // 100) * amount) // DENOMINATOR
                dict_prep_reward[single_prep] = single_prep_reward
                self._set_prep_delegations(Address.from_string(str(single_prep)), single_prep_reward,
                                           self.getPrepDelegations())
            self._check_top_100_preps(self.getTopPreps())


    @external
    def withdraw(self, _to: Address = None, _value:int = 0, _data: bytes = None) -> None:
        if _data is None:
            _data = b'None'
        if _to is None:
            _to = self.msg.sender
        if _to not in self.getUserAddressList():
            revert('You need to stake first before unstaking')
        if _to not in self.getUnstakingPendingAddress:
            self._unstake_address.put(_to)
        self._check_for_week()
        self._check_for_day()
        self._check_for_balance()
        stake_info =self.getStakeFromNetwork()
        if 'unstakes' in stake_info:
            if len(stake_info['unstakes']) == 1000:
                revert('You can try unstaking later')
        self.tokenFallback(_to,_value,_data)


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

    def _delegations(self,evenly_distribute_value:int,source:dict) -> None:
        prep_delegations = self.getTopPreps()
        delegation_list = []
        if source == {'source':'unstake'}:
            for one in prep_delegations:
                one = Address.from_string(str(one))
                delegation_info: Delegation = {
                    "address": one,
                    "value": self._prep_delegations[str(one)] - evenly_distribute_value
                }
                delegation_list.append(delegation_info)

        else:
            for one in prep_delegations:
                one = Address.from_string(str(one))
                delegation_info: Delegation = {
                    "address": one,
                    "value": self._prep_delegations[str(one)] + evenly_distribute_value
                }
                delegation_list.append(delegation_info)
        # revert(f'{delegation_list} and {self._total_stake.get()} and {self.getPrepDelegations()} and {evenly_distribute_value} ')
        self._system.setDelegation(delegation_list)

    def _unstake(self, _from: Address, _value: int) -> None:
        # unstaked = self.icx.get_balance(self.address) * _value // sICX_score.totalSupply()
        self.sICX_score.burn(_value)
        flag =1
        user_total_sicx = self.sICX_score.balanceOf(_to)
        amount_to_unstake = _value * self.getRate()
        top_preps = self.getTopPreps()
        if _value == user_total_sicx:
            self._address_delegations[str(_to)] = ''
        else:
            delegation_in_per = self.getAddressDelegationsInPer()
            evenly_deduct =0
            amount = 0
            for single in delegation_in_per.items():
                if single not in top_preps:
                    # here we calculate the total sum of delegation percentage of out of 100 preps
                    evenly_deduct +=single[1]
                else:
                    # in else the amount to be deducted is directly updated in dictdb
                    prep_percent = int(single[1])
                    amount_to_remove_from_prep = ((prep_percent // 100) * amount_to_unstake) // DENOMINATOR
                    amount += amount_to_remove_from_prep
                    self._set_prep_delegations(Address.from_string(str(single[0])), amount_to_remove_from_prep, self.getPrepDelegations(),flag)
        deduct_value_in_per = self._distribute_evenly(evenly_deduct,top_preps)
        #this value is only the value that needs to be deducted from all top preps
        value_to_unstake_in_icx = ((deduct_value_in_per // 100)  * amount_to_unstake) // DENOMINATOR
        # a dictdb is created for storing the address requesting for unstaking and the total amount to unstake
        self._unstaking_dict[str(_from)] = value_to_unstake_in_icx + amount
        # removing the amount to be unstaked from stake
        self._stake(self._total_stake.get() - amount_to_unstake)
        self._delegations(value_to_unstake_in_icx,{'source':'unstake'})
        self._sICX_supply.set(self._sICX_supply.get() - _value)

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


