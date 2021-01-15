from iconservice import *
from .utils.checks import *
from .utils.consts import *
from .scorelib.consts import *
from .scorelib.scorelib.consts import *
from .scorelib.scorelib.id_factory import *
from .scorelib.scorelib.linked_list import *

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
    _address: Address
    _votes_in_per: int


class Staking(IconScoreBase):
    _SICX_SUPPLY = 'sICX_supply'
    _RATE = '_rate'
    _SICX_ADDRESS = 'sICX_address'
    _BLOCK_HEIGHT_WEEK = '_block_height_week'
    _BLOCK_HEIGHT_DAY = '_block_height_day'
    _TOTAL_STAKE = '_total_stake'
    _TOTAL_REWARD = '_total_reward'
    _DISTRIBUTING = '_distributing'
    _ADDRESS_LIST = '_address_list'
    _PREP_LIST = '_prep_list'
    _LINKED_LIST_VAR = '_linked_list_var'
    _TOP_PREPS = '_top_preps'
    _ADDRESS_DELEGATIONS = '_address_delegations'
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
        self._block_height_week = VarDB(self._BLOCK_HEIGHT_WEEK, db, value_type=int)
        self._block_height_day = VarDB(self._BLOCK_HEIGHT_DAY, db, value_type=int)
        self._sICX_address = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        # total staked from staking contract
        self._total_stake = VarDB(self._TOTAL_STAKE, db, value_type=int)
        # vardb to store total rewards
        self._total_reward = VarDB(self._TOTAL_REWARD, db, value_type=int)
        self._distributing = VarDB(self._DISTRIBUTING, db, value_type=bool)
        # vardb to store total unstaking amount
        self._unstake_amount = VarDB(self._UNSTAKE_AMOUNT, db, value_type=int)
        # array for storing all the addresses and prep addresses
        self._address_list = ArrayDB(self._ADDRESS_LIST, db, value_type=Address)
        self._prep_list = ArrayDB(self._PREP_LIST, db, value_type=Address)
        # array to store top 100 preps
        self._top_preps = ArrayDB(self._TOP_PREPS, db, value_type=Address)
        # dictdb for storing the address and their delegations
        self._address_delegations = DictDB(self._ADDRESS_DELEGATIONS, db, value_type=str)
        # dictdb for storing the prep address and their delegated value
        self._prep_delegations = DictDB(self._PREP_DELEGATIONS, db, value_type=int)
        # initializing the system score
        self._system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        # initialize the sicx score
        self.sICX_score = self.create_interface_score(self._sICX_address.get(), sICXTokenInterface)
        # initialize the linked list
        self._linked_list_var = LinkedListDB("unstake_dict", db, value_type=str)

    def on_install(self) -> None:
        super().on_install()
        # initializing the block height to check change in the top 100 preps
        self._block_height_week.set(self._system.getIISSInfo()["nextPRepTerm"])
        # initializing the block height to claim rewards once a day
        self._block_height_day.set(self._system.getIISSInfo()["nextPRepTerm"])
        # top 100 preps is initialized at first
        self._rate.set(self.getRate())
        self._distributing.set(False)
        self._set_top_preps()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Staking"

    @external(readonly=True)
    def getRate(self) -> int:
        """
        Get the ratio of ICX to sICX.
        """
        if (self._total_stake.get()) == 0:
            rate = DENOMINATOR
        else:
            rate = (self._total_stake.get()) * DENOMINATOR // self.sICX_score.totalSupply()
        return rate

    @external
    def set_sICX_supply(self) -> None:
        """
        Only necessary for the dummy contract.
        """
        self._sICX_supply.set(self.sICX_score.totalSupply())

    @external(readonly=True)
    def getSicxAddress(self) -> Address:
        """
        Get the address of sICX token contract.
        """
        return self._sICX_address.get()

    @external(readonly=True)
    def getUnstakingAmount(self) -> int:
        """
        Returns the total amount to be unstaked from the staking contract.
        """
        return self._unstake_amount.get()

    @external(readonly=True)
    def getStakeFromNetwork(self) -> dict:
        """
        Returns a dictionary that specifies the total value staked in a network.
        """
        return self._system.getStake(self.address)

    @external(readonly=True)
    def getDelegationFromNetwork(self) -> dict:
        """
        Returns the delegations sent to the network.
        """
        return self._system.getDelegation(self.address)

    @external(readonly=True)
    def getTotalStake(self) -> int:
        """
        Returns the total staked amount stored in a vardb _total_stake.
        """
        return self._total_stake.get()

    @external(readonly=True)
    def getLifetimeReward(self) -> int:
        """
        Returns the total rewards earned up to now by the staking contract.
        """
        return self._total_reward.get()

    @external(readonly=True)
    def getTopPreps(self) -> list:
        """
        Returns the top prep addresses that is set every week.
        """
        lis1 = []
        for x in self._top_preps:
            lis1.append(x)
        return lis1

    @external(readonly=True)
    def getUserAddressList(self) -> list:
        """
        Returns the User Addresses stored in the staking contract.
        """
        addresses = []
        for single in self._address_list:
            addresses.append(single)
        return addresses

    @external(readonly=True)
    def getPrepList(self) -> list:
        """
        Returns the addresses of preps stored in the contract.
        """
        addresses = []
        for single in self._prep_list:
            addresses.append(single)
        return addresses

    @external(readonly=True)
    def getAddressDelegations(self, _address: Address) -> dict:
        """
        Takes wallet address as a params and returns the dictionary of wallet/user delegation preferences in ICX
        i.e. prep address as a key and the ICX as value
         :params _address : the wallet address whose delegation is to be known.
         """
        dict1 = {}
        dict_address_votes = self.getAddressDelegationsInPer(_address)
        total_sicx_of_user = self.sICX_score.balanceOf(_address)
        total_icx_hold = (total_sicx_of_user * self.getRate()) // DENOMINATOR
        for one in dict_address_votes.items():
            address = one[0]
            vote_in_per = one[1]
            votes_in_icx = ((vote_in_per // 100) * total_icx_hold) // DENOMINATOR
            dict1[str(address)] = votes_in_icx
        return dict1

    def getAddressDelegationsInPer(self, _address: Address) -> dict:
        """
        Takes wallet address as a params and returns the dictionary of wallet/user delegation preferences in ICX
        i.e. prep address as a key and the votes in percentage as value.
        :params _address : the wallet address whose delegation is to be known.
         """
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
                    if lis2[1] != '0':
                        dict1[lis2[0]] = dict1[lis2[0]] + int(lis2[1])
                    else:
                        dict1[lis2[0]] = 0
            return dict1
        else:
            return {}

    @external(readonly=True)
    def getUnstakeRequest(self) -> dict:
        """
        Returns a dictionary that shows wallet address as a key and the request of unstaked amount by that address
        as a value.
        """
        dict1 = {}
        for items in self._linked_list_var:
            split_string = items[1].split(':')
            dict1[str(split_string[0])] = split_string[1]
        return dict1

    @external(readonly=True)
    def getPrepDelegations(self) -> dict:
        """
        Returns the dictionary with prep addresses as a key and total ICX delegated to that prep address as a
        value.
         """
        dict1 = {}
        for x in self.getPrepList():
            dict1[str(x)] = self._prep_delegations[str(x)]
        return dict1

    @external
    def setSicxAddress(self, _address: Address) -> None:
        """
        Sets the sICX address from staking contract.
        :params _address : the address of sICX token contract.
        """
        self._sICX_address.set(_address)

    def _set_top_preps(self) -> None:
        """Weekly this function is called to set the top 100 prep address in an arraydb"""
        prep_dict = self._system.getPReps(1, 20)
        address = prep_dict['preps']
        for one in address:
            self._top_preps.put(one['address'])

    def _delegate_votes(self, _to: Address, _user_delegations: list, complete_prep_list: list, get_delegated_value: dict,
                      total_icx_hold: int) -> int:
        """
        Returns the percentage of votes of the delegations preferences of the user and should be 100%.
        Calls another function to sets the delegations of a user.
        :params _to : Wallet address to set the delegation.
        :params _user_delegations: List of dictionaries of a wallet delegation preferences.
        :params complete_prep_list: Complete prep list in staking contract.
        :params get_delegated_value: Dictionaries that stores complete delegations.
        :params total_icx_hold: Equivalent ICX of the sICX of that wallet address.
        """
        amount_to_stake = 0
        for single_prep in _user_delegations:
            if single_prep["_address"] not in complete_prep_list:
                self._prep_list.put(single_prep["_address"])
            if single_prep["_address"] not in self.getTopPreps():
                revert(f'The delegation should be given to top 100 preps of the staking contract')
            amount_to_stake += single_prep["_votes_in_per"]
            self._setAddressDelegations(_to, single_prep['_address'], single_prep["_votes_in_per"], get_delegated_value,
                                        total_icx_hold)
        return amount_to_stake

    def _distributeEvenly(self, amount_to_distribute: int, total_icx_hold: int = 0, flags: int = 0, _to: Address = None,
                          prep_list=None) -> int:
        """
        Returns the amount to be evenly distributed to top 100 preps.
        :params amount_to_distribute : total amount in ICX that is to be distributed to top preps.
        :params total_icx_hold: Equivalent ICX of the sICX of that wallet address.
        :params flags:Flag is set to 1 if User sends empty delegation preferences in their first transaction.
        :params _to : Wallet address to set the delegation if the flag is 1.
        :params prep_list : complete prep list in staking contract.
        """
        top_preps = self.getTopPreps()
        if prep_list is None:
            prep_list = []
        _value = 0
        if flags == 1:
            prep_delegations = self.getPrepDelegations()
            evenly_ditribution = (DENOMINATOR * amount_to_distribute) // len(top_preps)
            for one_prep in top_preps:
                if one_prep not in prep_list:
                    self._prep_list.put(one_prep)
                self._setAddressDelegations(_to, one_prep, evenly_ditribution, prep_delegations,
                                            total_icx_hold, 1)
        else:
            evenly_ditribution = (DENOMINATOR * amount_to_distribute) // len(top_preps)
            _value = evenly_ditribution // DENOMINATOR
        return _value

    def _getAmountToMint(self):
        """Returns the amount to be minted to a address"""
        supply = self._sICX_supply.get()
        # balance = self.get_stake_from_network(self.address)
        # balance = balance['stake'] + self.msg.value
        balance = self.getTotalStake()
        if balance == self.msg.value:
            amount = self.msg.value
        else:
            amount = supply * self.msg.value // (balance - self.msg.value)
        return amount

    def _setAddressDelegations(self, _to: Address, _prep: Address, _value: int, _delegations: dict, total_icx_hold: int,
                               overwrite_flag: int = 0) -> None:
        """
        Sets address delegations of a user in a dict db
        where key is the wallet addresses and value is
        the prep addresses and the ICX delegated to that
        prep address by a specific user in a string.
        :params _to: Wallet Address to set the delegation for.
        :params _prep : Prep addresses.
        :params _value : Percentage to store the delegations.
        :params _delegations : complete delegations of staking contract.
        :params total_icx_hold: Equivalent ICX of the sICX of that wallet address.
        """
        if overwrite_flag != 1:
            _value = _value * DENOMINATOR
        self._address_delegations[str(_to)] += str(_prep) + ':' + str(_value) + '.'
        # _value is the delegation preferences of a user for a specific prep in 10 **18 form
        _value = (_value * total_icx_hold) // (100 * DENOMINATOR)
        self._setPrepDelegations(_prep, _value, _delegations)

    def _setPrepDelegations(self, _prep: Address, _value: int, _delegations: dict) -> None:
        """
        Sets Prep delegations to a dictdb where key is prep addresses
         and value is the ICX amount.
         :params _prep : prep address to set the delegation for.
         :params _value : Value in ICX in 10**18 form.
         :params _delegations : complete delegations of staking contract.
        """
        if _delegations == {}:
            self._prep_delegations[str(_prep)] = _value
        else:
            if str(_prep) in _delegations.keys():
                if _delegations[str(_prep)] != 0:
                    self._prep_delegations[str(_prep)] = self._prep_delegations[
                                                             str(_prep)] + _value
                else:
                    self._prep_delegations[str(_prep)] = _value
            else:
                self._prep_delegations[str(_prep)] = _value

    def _stake_and_delegate(self, evenly_distribute_value: int = 0) -> None:
        """
        It calls other internal functions that is used for staking and delegating.
        """
        self._stake(self.getTotalStake())
        self._delegations(evenly_distribute_value, {})

    def _remove_previous_delegations(self, _to: Address, current_icx_hold: int) -> dict:
        """
        Removes the previous delegations preferences of a user
        and initializing the delegation of a user as an
        empty string.
        :params _to: Wallet Address of which delegation is to be removed from the total delegations.
        :params total_icx_hold: Equivalent ICX of the sICX of that wallet address.
        """
        previous_address_delegations = self.getAddressDelegationsInPer(_to)
        if previous_address_delegations != {}:
            self._address_delegations[str(_to)] = ''
            previous_icx_hold = current_icx_hold - self.msg.value
            for each in previous_address_delegations.items():
                x = Address.from_string(str(each[0]))
                self._prep_delegations[str(x)] = self._prep_delegations[
                                                     str(x)] - ((each[1] * previous_icx_hold) // (100 * DENOMINATOR))
                if self._prep_delegations[str(x)] < 0:
                    self._prep_delegations[str(x)] = 0
        else:
            revert('You need to have delegations before updating')

        return previous_address_delegations

    def _checkTop100Preps(self) -> int:
        """
        Sums the value of ICX of those preps
        that are out of 100.
        """
        to_distribute = 0
        for single_prep in self.getPrepDelegations().keys():
            if Address.from_string(single_prep) not in top_preps:
                to_distribute += self._prep_delegations[str(single_prep)]
        to_evenly_distribute_value = self._distributeEvenly(to_distribute)
        return to_evenly_distribute_value
        # self._stake_and_delegate(to_evenly_distribute_value)

    def _checkForWeek(self) -> int:
        """
        Sets the new top 100 prep address in an array db weekly after checking the specific conditions.
        """
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_week.get() + (7 * 43200):
            self._block_height_week.set(self._system.getIISSInfo()["nextPRepTerm"])
            for i in range(len(self._top_preps)):
                self._top_preps.pop()
            self._set_top_preps()
            return self._checkTop100Preps()
        else:
            return 0

    def _checkForDay(self) -> None:
        """
        Claim iscore and sets new rate daily.
        """
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_day.get() + 43200:
            self._block_height_day.set(self._system.getIISSInfo()["nextPRepTerm"])
            self._rate.set(self.getRate())
            self._claim_iscore()

    def _checkForBalance(self) -> None:
        """
        Checks the balance of the score and transfer the
         unstaked amount to the address and removing the
         data from linked list .
         """
        balance_score = self.icx.get_balance(self.address) - self._daily_reward.get()
        # revert(f'{self.icx.get_balance(self.address)}, {self.msg.value}')
        # revert(f'{balance_score}, {self.icx.get_balance(self.address)},{self._daily_reward.get()}')
        if balance_score > 0:
            unstake_info_list = self.getUserUnstakeInfo()
            for each_info in unstake_info_list:
                value_to_transfer = each_info[0]
                if value_to_transfer <= balance_score:
                    self._send_ICX(each_info[1], value_to_transfer)
                    self._linked_list_var.remove(self._linked_list_var._head_id.get())
                    self._total_unstake_amount.set(self._total_unstake_amount.get() - value_to_transfer)
                break

    @payable
    @external
    def addCollateral(self, _to: Address = None, _user_delegations: List[PrepDelegations] = None) -> None:
        """
        Provides delegation preferences as a params
        and stakes and delegates some ICX to different prep
        addresses and receives equivalent of sICX by the user address.
        :params _to: Wallet address where sICX is minted to.
        :params _user_delegations: A list of dictionaries to store the delegation preferences of a user.
        """
        if _user_delegations is not None:
            if len(_user_delegations) > 100:
                revert('Only 100 prep addresses should be provided')
        if _to is None:
            _to = self.tx.origin
        self._perform_checks()
        self._total_stake.set(self._total_stake.get() + self.msg.value)
        amount = self._getAmountToMint()
        self.sICX_score.mintTo(_to, amount)
        total_sicx_of_user = self.sICX_score.balanceOf(_to)
        # total_icx_hold is the equivalent of sICX to ICX at the time.
        total_icx_hold = (total_sicx_of_user * self._rate.get()) // DENOMINATOR
        previous_address_delegations = self._remove_previous_delegations(_to, total_icx_hold)
        prep_delegations = self.getPrepDelegations()
        to_evenly_distribute_value = 0
        complete_prep_list = self.getPrepList()
        if _user_delegations is not None:
            amount_to_stake_in_per = self._delegate_votes(_to, _user_delegations,
                                                        complete_prep_list, prep_delegations,
                                                        total_icx_hold)
            if amount_to_stake_in_per != 100:
                revert(f'The total delegations should be 100 %')

        else:
            if previous_address_delegations == {}:
                # If it is the first transaction of the user and doesn't provide the delegation preferences.
                flags = 1
                amount_to_stake_in_per = 100
                to_evenly_distribute_value = self._distributeEvenly(amount_to_stake_in_per, total_icx_hold, flags, _to,
                                                                    complete_prep_list)

            else:
                for dict_prep_delegation in previous_address_delegations.items():
                    # If the user doesn't provide with the delegations preferences then the previous delegation is used by doing some modification.
                    self._setAddressDelegations(_to, Address.from_string(str(dict_prep_delegation[0])),
                                                int(dict_prep_delegation[1]), prep_delegations, total_icx_hold, 1)
        self._stake_and_delegate(to_evenly_distribute_value+self._checkForWeek())
        self._sICX_supply.set(self._sICX_supply.get() + amount)
        self.TokenTransfer(_to, amount, f'{amount / DENOMINATOR} sICX minted to {_to}')

    def _calculatePercentToICX(self, _voting_percentage: int, _total_amount: int) -> int:
        """
        It takes voting percentage and total amount of staked by that user as params and returns the equivalent in ICX.
        :params _voting_percentage : the percentage of delegations of a user.
        :params _total_amount : the total amount of ICX staked by the user.
        """
        return (_voting_percentage * _total_amount) // (100 * DENOMINATOR)

    @external
    def transferUpdateDelegations(self, _from: Address, _to: Address, _value: int) -> None:
        """
        Deducts the sICX amount from the sender
        and adds the sICX amount to the receiver
        and if the receiver is new to the staking
        contract the receiver replicates the sender's
        delegation preferences.
        :params _from : Address that transfers the sICX token.
        :params _to : Address that receives the sICX token.
        :params _value : Amount of token to be transferred.
        """
        if self.msg.sender != self._sICX_address.get():
            revert('Only sicx token contract can call this function')
        # provides delegation preferences of sender in percentage
        _value_in_icx = (_value * self._rate.get()) // DENOMINATOR
        receiver_delegation_preference_in_per = self.getAddressDelegationsInPer(_to)
        sender_delegation_preference_in_per = self.getAddressDelegationsInPer(_from)
        for single_delegation in sender_delegation_preference_in_per.items():
            amount_to_remove_from_prep = self._calculatePercentToICX(single_delegation[1], _value_in_icx)
            # removing the value from prep dictdb
            self._prep_delegations[str(single_delegation[0])] = self._prep_delegations[str(
                single_delegation[0])] - amount_to_remove_from_prep
        if receiver_delegation_preference_in_per == {}:
            self._address_list.put(_to)
            self._address_delegations[str(_to)] = self._address_delegations[str(_from)]
            receiver_delegation_preference_in_per = self.getAddressDelegationsInPer(_to)
        for one in receiver_delegation_preference_in_per.items():
            amount_to_add_to_prep = self._calculatePercentToICX(one[1], _value_in_icx)
            self._prep_delegations[str(one[0])] = self._prep_delegations[str(one[0])] + amount_to_add_to_prep
        self._stake_and_delegate()

    def _perform_checks(self) -> None:
        if self._distributing.get() is True:
            stake_in_network = self._system.getStake(self.address)
            total_unstake_in_network = 0
            if 'unstakes' in stake_in_network.keys():
                for each in stake_in_network['unstakes']:
                    total_unstake_in_network += each['unstake']
            daily_reward = total_unstake_in_network + self.icx.get_balance(
                self.address) - self._total_unstake_amount.get() - self.msg.value
            self._daily_reward.set(daily_reward)
            self._total_reward.set(self.getLifetimeReward() + daily_reward)
            self._rate.set(self.getRate())
            self._total_stake.set(self.getTotalStake() + daily_reward)
            prep_delegations = self.getPrepList()
            total_staked_amount = self.getTotalStake()
            for single_prep in prep_delegations:
                value_in_icx = self._prep_delegations[str(single_prep)]
                total_weightage_in_per = ((value_in_icx * DENOMINATOR) // total_staked_amount) * 100
                single_prep_reward = ((total_weightage_in_per // 100) * daily_reward) // DENOMINATOR
                dict_prep_reward[single_prep] = single_prep_reward
                self._setPrepDelegations(Address.from_string(str(single_prep)), single_prep_reward,
                                         self.getPrepDelegations())
            self._distributing.set(False)
        self._checkForDay()
        self._checkForBalance()

    @external
    def updateDelegations(self, _user_delegations: List[PrepDelegations]):
        """
        Updates the delegation preferences of a
        user and redelegates in the network.
        :params _user_delegations: A list of dictionaries to store the delegation preferences of a user.
        """
        _to = self.msg.sender
        if len(_user_delegations) > 100:
            revert('Only 100 prep addresses should be provided')
        self._perform_checks()
        total_sicx_of_user = self.sICX_score.balanceOf(_to)
        total_icx_hold = (total_sicx_of_user * self._rate.get()) // DENOMINATOR
        previous_prep_delegations  = self._remove_previous_delegations(_to, total_icx_hold)
        prep_list_of_contract = self.getPrepList()
        prep_delegations = self.getPrepDelegations()
        amount_to_stake_in_per = self._delegate_votes(_to, _user_delegations,
                                                    prep_list_of_contract, prep_delegations,
                                                    total_icx_hold)
        if amount_to_stake_in_per != 100:
            revert('Total delegations should be 100 %')
        self._delegations(0 + self._checkForWeek(), {})

    def _claim_iscore(self) -> None:
        """
        Claims the iScore and distributes it to the prep addresses on the basis
         of their weightage of votes in a network.
         """
        dict1 = self._system.queryIScore(self.address)
        if dict1['estimatedICX'] != 0:
            self._system.claimIScore()
            self._distributing.set(True)


    @external
    def withdraw(self, _to: Address = None, _value: int = 0, _data: bytes = None) -> None:
        """
        Burns the sICX into ICX and unstakes from the network.
        :params _to : Address that is making unstaking request.
        :params _value : Amount of sICX to be burned.
        :params _data : data.
        """
        if _data is None:
            _data = b'None'
        if _to is None:
            _to = self.msg.sender
        if _to not in self.getUserAddressList():
            revert('You need to stake first before unstaking')
        self._checkForWeek()
        self._checkForDay()
        self._checkForBalance()
        stake_info = self.getStakeFromNetwork()
        if 'unstakes' in stake_info:
            if len(stake_info['unstakes']) == 1000:
                revert('You can try unstaking later')
        # self.tokenFallback(_to,_value,_data)
        self._unstake(_to, _value)

    # @external
    # def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
    #     """
    #     Used only to receive sICX for unstaking.
    #     :param _from: Token orgination address.
    #     :type _from: :class:`iconservice.base.address.Address`
    #     :param _value: Number of tokens sent.
    #     :type _value: int
    #     :param _data: Unused, ignored.
    #     :type _data: bytes
    #     """
    #     if self.msg.sender != self._sICX_address.get():
    #         revert(f'The Staking contract only accepts sICX tokens.')
    #     Logger.debug(f'({_value}) tokens received from {_from}.', TAG)
    #     return self._unstake(_from, _value)

    def _stake(self, _stake_value: int) -> None:
        """
        Stakes the ICX in the network.
        :params _stake_value: Amount to stake in the network.
        """
        self._system.setStake(_stake_value)

    def _delegations(self, evenly_distribute_value: int, source: dict) -> None:
        """
        Delegates the ICX to top prep addresses.
        :params evenly_distribute_value : Amount to be distributed to all the preps evenly.
        :params source : to find out the source of the function call.
        """
        prep_delegations = self.getTopPreps()
        delegation_list = []
        if source == {'source': 'unstake'}:
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

    def _unstake(self, _to: Address, _value: int) -> None:
        """
        Burns the sICX and removes delegations
        from the prep addresses and adds the
        unstaking request to the linked list.
        :params _to : Address that is making unstaking request.
        :params _value : Amount of sICX to be burned.
        """
        # unstaked = self.icx.get_balance(self.address) * _value // sICX_score.totalSupply()
        self.sICX_score.burn(_value)
        user_total_sicx = self.sICX_score.balanceOf(_to)
        amount_to_unstake = _value * self.getRate()
        top_preps = self.getTopPreps()
        evenly_deduct = 0
        if _value == user_total_sicx:
            self._address_delegations[str(_to)] = ''
        else:
            delegation_in_per = self.getAddressDelegationsInPer(_to)
            amount = 0
            for single in delegation_in_per.items():
                if single not in top_preps:
                    # here we calculate the total sum of delegation percentage of out of 100 preps
                    evenly_deduct += single[1]
                else:
                    # in else the amount to be deducted is directly updated in dictdb
                    prep_percent = int(single[1])
                    amount_to_remove_from_prep = ((prep_percent // 100) * amount_to_unstake) // DENOMINATOR
                    amount += amount_to_remove_from_prep
                    self._prep_delegations[str(single[0])] = self._prep_delegations[
                                                                 str(single[0])] - amount_to_remove_from_prep
        deduct_value_in_per = self._distributeEvenly(evenly_deduct)
        # this value is only the value that needs to be deducted from all top preps
        value_to_unstake_in_icx = ((deduct_value_in_per // 100) * amount_to_unstake) // DENOMINATOR
        # a dictdb is created for storing the address requesting for unstaking and the total amount to unstake
        self._linked_list_var.append(str(_to) + ":" + str(amount_to_unstake), self._linked_list_var._tail_id.get() + 1)
        # removing the amount to be unstaked from stake
        self._stake(self._total_stake.get() - amount_to_unstake)
        self._delegations(value_to_unstake_in_icx, {'source': 'unstake'})
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
