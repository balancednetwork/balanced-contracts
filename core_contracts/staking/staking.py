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
    _prep_address:Address
    _votes:int

class Staking(IconScoreBase):
    _SICX_SUPPLY = 'sICX_supply'
    _SICX_ADDRESS = 'sICX_address'
    _TOTAL_STAKE = 'total_stake'
    _TOTAL_REWARD = 'total_reward'
    _ADDRESS_LIST = '_address_list'
    _PREP_LIST = '_prep_list'
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
        self._sICX_address = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        # total staked from contract
        self.total_stake = VarDB(self._TOTAL_STAKE, db, value_type=int)
        # vardb to store total rewards
        self.total_reward = VarDB(self._TOTAL_REWARD, db, value_type=int)
        # array for storing all the addresse and prep addresses
        self._address_list = ArrayDB(self._ADDRESS_LIST, db, value_type=Address)
        self._prep_list = ArrayDB(self._PREP_LIST, db, value_type=Address)
        # dictdb for storing the address and their delegations
        self._address_delegations = DictDB(self._ADDRESS_DELEGATIONS, db, value_type=str)
        # dictdb for storing the prep address and their delegated value
        self._prep_delegations = DictDB(self._PREP_DELEGATIONS, db, value_type=int)


    def on_install(self) -> None:
        super().on_install()

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
    def get_total_stake(self) -> int:
        return self.total_stake.get()

    @external(readonly=True)
    def get_total_reward(self) -> int:
        return self.total_reward.get()

    @external(readonly=True)
    def get_preps(self) -> list:
        system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        prep_dict =  system.getPReps(1,20)
        address = prep_dict['preps']
        list_prep_address=[]
        for one in address:
            list_prep_address.append(one['address'])
        return list_prep_address

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
        system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        return system.queryIScore(_address)

    @external
    def set_sICX_address(self, _address: Address) -> None:
        self._sICX_address.set(_address)

    @external(readonly=True)
    def get_balance(self) -> int:
        return self.icx.get_balance(self.address)

    def _out_of_prep_list(self,_to, prep_del, out_prep_list,top_preps) -> int:
        previous_prep_vote = 0
        dict1 = {}
        for z in out_prep_list:
            if str(z) in prep_del.keys():
                prep_address_amount =prep_del[str(z)]
                # previous_prep_vote += prep_address_amount
                if prep_address_amount != 0:
                    dict1[str(z)] = self.get_prep_delegations()[str(z)]
                    self._prep_delegations[str(z)] = self._prep_delegations[str(z)] - prep_address_amount
                    for x in self.get_address_list():
                        delegations_dict = self.get_address_delegations(x)
                        if str(z) in delegations_dict.keys():
                            amount_wallet = delegations_dict[str(z)]
                            self._address_delegations[str(_to)] += str(z) + ':' + str(-amount_wallet) + '.'
                            self._distribute_evenly(x, 0, amount_wallet, top_preps)
        return previous_prep_vote

    def _loop_in_params(self,_to,_prep_address,prep_list_contract, top_preps, get_delegated_value):
        amount_to_stake = 0
        prep_amount_left = 0
        for dict in _prep_address:
            if dict["_prep_address"] not in prep_list_contract:
                self._prep_list.put(dict["_prep_address"])
            if dict["_prep_address"] not in top_preps:
                prep_amount_left += dict["_votes"]
            else:
                amount_to_stake += dict["_votes"]
                self._set_address_delegations(_to, dict['_prep_address'], dict["_votes"], get_delegated_value)
        return amount_to_stake,prep_amount_left

    def _distribute_evenly(self,_to:Address, prep_amount_left: int, previous_prep_vote: int, top_preps: list):
        evenly_ditribution = (prep_amount_left + previous_prep_vote) // len(top_preps)
        prep_delegations = self.get_prep_delegations()
        prep_list = self.get_prep_list()
        for x in top_preps:
            if x not in prep_list:
                self._prep_list.put(x)
            self._set_address_delegations(_to,x,evenly_ditribution,prep_delegations)

    def _set_address_delegations(self, _to: Address, _prep: Address, _value: int,_delegations:dict,data:str=''):
        self._address_delegations[str(_to)] += str(_prep) + ':' + str(_value) + '.'
        if data != '':
            self._set_prep_delegations(_prep, _value,_delegations,data)
        else:
            self._set_prep_delegations(_prep,_value,_delegations)

    def _set_prep_delegations(self,_prep:Address,_value:int,_delegations:dict,data:str=''):
        if _delegations == {} :
            self._prep_delegations[str(_prep)] = _value
        else:
            if str(_prep) in _delegations.keys():
                if _delegations[str(_prep)] != 0 :
                    if data != '':
                        self._prep_delegations[str(_prep)] = self._prep_delegations[
                                                                 str(_prep)] - int(data)
                    else:
                        self._prep_delegations[str(_prep)] = self._prep_delegations[
                                                             str(_prep)] + _value
                else:
                    self._prep_delegations[str(_prep)] = _value
            else:
                self._prep_delegations[str(_prep)] = _value

    @payable
    @external
    def add_collateral(self, _to: Address, _prep_address: List[PrepDelegations], _data: bytes = None) -> None:
        if _data is None:
            _data = b'None'
        if _to not in self.get_address_list():
            self._address_list.put(_to)
        top_preps = self.get_preps()
        sicx = self._sICX_address.get()
        sICX_score = self.create_interface_score(sicx, sICXTokenInterface)
        supply = self._sICX_supply.get()
        balance = self.icx.get_balance(self.address)
        if balance == self.msg.value:
            amount = self.msg.value
        else:
            amount = supply * self.msg.value // (balance - self.msg.value)
        sICX_score.mintTo(_to, amount, _data)
        prep_list_contract = self.get_prep_list()
        # out_prep_list = [i for i in prep_list_contract + top_preps if i not in prep_list_contract or i not in top_preps]
        # previous_prep_vote = 0
        # prep_del = self.get_prep_delegations()
        # previous_prep_vote = self._out_of_prep_list(_to,prep_del,out_prep_list,top_preps)
        previous_prep_vote = 0
        get_delegated_value = self.get_prep_delegations()
        if _prep_address !=[]:
            amount_to_stake,prep_amount_left = self._loop_in_params(_to,_prep_address,prep_list_contract,top_preps,get_delegated_value)
            if ((amount_to_stake + prep_amount_left) / 100) * self.msg.value != self.msg.value:
                revert('Total delegations should be 100 %')
        else:
            amount_to_stake = 0
            prep_amount_left = 100
            previous_prep_vote = 0
        if prep_amount_left != 0:
            self._distribute_evenly(_to,prep_amount_left,previous_prep_vote,top_preps)
        amount_to_stake = int((amount_to_stake/100 )* self.msg.value)
        prep_amount_left = int((prep_amount_left/100) * self.msg.value)
        self.total_stake.set(self.total_stake.get() + amount_to_stake+ prep_amount_left )
        self._stake(self.total_stake.get()  + self.total_reward.get() )
        self._delegations()
        delegation_json  = self.get_address_delegations(_to)
        delegation_json = (str(delegation_json)).replace(' ','').replace("'",'').replace(",",'.')
        delegation_json = delegation_json[1:-1] + '.'
        self._address_delegations[str(_to)] = delegation_json
        self._sICX_supply.set(self._sICX_supply.get() + amount)
        self.TokenTransfer(_to, amount, f'{amount / DENOMINATOR} sICX minted to {_to}')

    @external
    def update_delegations(self,_prep_address: List[PrepDelegations]):
        _to = self.msg.sender
        get_delegated_value = self.get_prep_delegations()
        top_preps = self.get_preps()
        prep_list_contract = self.get_prep_list()
        if _to not in self.get_address_list():
            revert('You need to provide ICX before updating the votes')
        dict_delegation = self.get_address_delegations(_to)
        sum_delegations= 0
        for dict in dict_delegation.items():
            self._set_address_delegations(_to, dict[0], 0, get_delegated_value,str(dict[1]))
        # sum_rate = sum(dict_delegation.values())
        previous_prep_vote = 0
        amount_to_stake, prep_amount_left = self._loop_in_params(_to,_prep_address,prep_list_contract,top_preps,get_delegated_value)
        if 100 != (amount_to_stake + prep_amount_left):
            revert('Total delegations should be 100 %')
        if prep_amount_left != 0:
            self._distribute_evenly(_to, prep_amount_left, previous_prep_vote, top_preps)
        self._delegations()
        delegation_json = self.get_address_delegations(_to)
        delegation_json = (str(delegation_json)).replace(' ', '').replace("'", '').replace(",", '.')
        delegation_json = delegation_json[1:-1] + '.'
        self._address_delegations[str(_to)] = delegation_json

    @external
    def claim_iscore(self):
        system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        dict1 = system.queryIScore(self.address)
        top_preps = self.get_preps()
        if dict1['estimatedICX'] != 0:
            amount = dict1["estimatedICX"] // len(top_preps)
            system.claimIScore()
            self.total_reward.set(self.total_reward.get() + dict1["estimatedICX"])
            for x in top_preps:
                if x not in self.get_prep_list():
                    self._prep_list.put(x)
                if self.get_prep_delegations()[str(x)] != 0:
                    self._prep_delegations[str(x)] = self._prep_delegations[str(x)] + amount
                else:
                    self._prep_delegations[str(x)] = amount
            self._stake(self.total_stake.get() + self.total_reward.get())
            self._delegations()
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


    def _stake(self, _stake_value: int):
        system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        system.setStake(_stake_value)

    def _delegations(self):
        system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        prep_delegations = self.get_prep_delegations()
        address_list_prep = prep_delegations.keys()
        sum_rate = sum(prep_delegations.values())
        delegation_list = []
        for one in address_list_prep:
            one = Address.from_string(str(one))
            delegation_info: Delegation = {
                "address": one,
                "value": int((prep_delegations[str(one)] / sum_rate) * self.get_total_stake())
            }
            delegation_list.append(delegation_info)
        system.setDelegation(delegation_list)

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
