from iconservice import *
from .utils.checks import *
from .scorelib.consts import *
from .scorelib.id_factory import *
from .scorelib.linked_list import *

# from .scorelib import *

TAG = 'StakedICXManager'

DENOMINATOR = 1000000000000000000
TOP_PREP_COUNT = 20


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
    _DAILY_REWARD = '_daily_reward'
    _TOTAL_LIFETIME_REWARD = '_total_lifetime_reward'
    _DISTRIBUTING = '_distributing'
    _LINKED_LIST_VAR = '_linked_list_var'
    _TOP_PREPS = '_top_preps'
    _PREP_LIST = '_prep_list'
    _ADDRESS_DELEGATIONS = '_address_delegations'
    _PREP_DELEGATIONS = '_prep_delegations'
    _TOTAL_UNSTAKE_AMOUNT = '_total_unstake_amount'

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
        self._daily_reward = VarDB(self._DAILY_REWARD, db, value_type=int)
        self._total_lifetime_reward = VarDB(self._TOTAL_LIFETIME_REWARD, db, value_type=int)
        self._distributing = VarDB(self._DISTRIBUTING, db, value_type=bool)
        # vardb to store total unstaking amount
        self._total_unstake_amount = VarDB(self._TOTAL_UNSTAKE_AMOUNT, db, value_type=int)
        # array for storing all the addresses and prep addresses
        # array to store top 100 preps
        self._top_preps = ArrayDB(self._TOP_PREPS, db, value_type=Address)
        self._prep_list = ArrayDB(self._PREP_LIST, db, value_type=Address)
        # dictdb for storing the address and their delegations
        self._address_delegations = DictDB(self._ADDRESS_DELEGATIONS, db, value_type=str)
        # dictdb for storing the prep address and their delegated value
        self._prep_delegations = DictDB(self._PREP_DELEGATIONS, db, value_type=int)
        # initializing the system score
        self._system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        # initialize the sicx score
        self.sICX_score = self.create_interface_score(self._sICX_address.get(), sICXTokenInterface)
        # initialize the linked list
        self._linked_list_var = LinkedListDB("unstake_dict", db)

    def on_install(self) -> None:
        super().on_install()
        next_prep_term = self._system.getIISSInfo()["nextPRepTerm"]
        # initializing the block height to check change in the top 100 preps
        self._block_height_week.set(next_prep_term)
        # initializing the block height to claim rewards once a day
        self._block_height_day.set(next_prep_term)
        # top 100 preps is initialized at first
        self._rate.set(DENOMINATOR)
        self._distributing.set(False)
        self._set_top_preps()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Staked ICX Manager"

    @external(readonly=True)
    def getTodayRate(self) -> int:
        return self._rate.get()

    def getRate(self) -> int:
        """
        Get the ratio of ICX to sICX.
        """
        if (self._total_stake.get()) == 0:
            rate = DENOMINATOR
        else:
            rate = (self._total_stake.get() + self._daily_reward.get()) * DENOMINATOR // self.sICX_score.totalSupply()
        return rate

    @external
    def setSicxSupply(self) -> None:
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
    def getPrepList(self) -> list:
        """
        Returns all the prep address as a list stored in the staking contract.
        """
        prep_list = []

        for address in self._prep_list:
            prep_list.append(address)
        return prep_list

    @external(readonly=True)
    def getUnstakingAmount(self) -> int:
        """
        Returns the total amount to be unstaked from the staking contract.
        """
        return self._total_unstake_amount.get()

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
        return self._total_lifetime_reward.get()

    @external(readonly=True)
    def getTopPreps(self) -> list:
        """
        Returns the top prep addresses that is set every week.
        """
        top_prep_list = []
        for single_prep in self._top_preps:
            top_prep_list.append(single_prep)
        return top_prep_list

    @external(readonly=True)
    def getAddressDelegations(self, _address: Address) -> dict:
        """
        Takes wallet address as a params and returns the dictionary of wallet/user delegation preferences in ICX
        i.e. prep address as a key and the ICX as value
         :params _address : the wallet address whose delegation is to be known.
         """
        dict_address_delegation = {}
        dict_address_votes = self._get_address_delegations_in_per(_address)
        total_icx_hold = (self.sICX_score.balanceOf(_address) * self._rate.get()) // DENOMINATOR
        if dict_address_votes != {}:
            for item in dict_address_votes.items():
                address = item[0]
                vote_in_per = item[1]
                votes_in_icx = (vote_in_per * total_icx_hold) // (DENOMINATOR * 100)
                dict_address_delegation[str(address)] = votes_in_icx
        return dict_address_delegation

    def _get_address_delegations_in_per(self, _address: Address) -> dict:
        """
        Takes wallet address as a params and returns the dictionary of wallet/user delegation preferences in ICX
        i.e. prep address as a key and the votes in percentage as value.
        :params _address : the wallet address whose delegation is to be known.
         """
        address_delegation_string = self._address_delegations[str(_address)]
        if address_delegation_string != '':
            dict_address_delegation_percent = {}
            split_string_to_list = (address_delegation_string.split("."))
            split_string_to_list.pop()
            for one in split_string_to_list:
                list_split = (one.split(":"))
                if list_split[0] not in dict_address_delegation_percent.keys():
                    dict_address_delegation_percent[list_split[0]] = int(list_split[1])
                else:
                    if list_split[1] != '0':
                        dict_address_delegation_percent[list_split[0]] = dict_address_delegation_percent[
                                                                             list_split[0]] + int(list_split[1])
                    else:
                        dict_address_delegation_percent[list_split[0]] = 0
            return dict_address_delegation_percent
        else:
            return {}

    @external(readonly=True)
    def getPrepDelegations(self) -> dict:
        """
        Returns a dictionary with prep addresses as a key and total ICX delegated to that prep address
        from staking contract as a value.
         """
        prep_address_votes = {}
        for single_prep in self._prep_list:
            prep_address_votes[str(single_prep)] = self._prep_delegations[str(single_prep)]
        return prep_address_votes

    @external
    def setSicxAddress(self, _address: Address) -> None:
        """
        Sets the sICX address from staking contract.
        :params _address : the address of sICX token contract.
        """
        self._sICX_address.set(_address)

    @external(readonly=True)
    def getUnstakeInfo(self) -> list:
        """
        Returns a list of unstaked amount,wallet address, unstake amount period
        and self.msg.sender of an unstaking request.
        """
        unstake_info_list = []
        for items in self._linked_list_var:
            unstake_info_list.append([items[1], items[2], items[3], items[4]])
        return unstake_info_list

    @external(readonly=True)
    def getUserUnstakeInfo(self, _address: Address) -> list:
        """
        Returns a list that shows a specific wallet's unstaked amount,wallet address, unstake amount period
        and self.msg.sender
        :params _address: the address of which the unstake request information is requested.
        """
        unstake_info_list = []
        for items in self._linked_list_var:
            if items[4] == _address:
                unstake_info_list.append([items[1], items[2], items[3], items[4]])
        return unstake_info_list

    def _set_top_preps(self) -> None:
        """Weekly this function is called to set the top 100 prep address in an arraydb"""
        prep_dict = self._system.getPReps(1, TOP_PREP_COUNT)
        preps = prep_dict['preps']
        for prep in preps:
            if prep not in self._prep_list:
                self._prep_list.put(prep['address'])
            self._top_preps.put(prep['address'])

    def _delegate_votes(self, _to: Address, _user_delegations: list, get_delegated_value: dict) -> int:
        """
        Returns the percentage of votes of the delegations preferences of the user and should be 100%.
        Calls another function to sets the delegations of a user.
        :params _to : Wallet address to set the delegation.
        :params _user_delegations: List of dictionaries of a wallet delegation preferences.
        :params get_delegated_value: Dictionaries that stores complete delegations.
        """
        amount_to_stake = 0
        similar_prep_list_check = []
        for single_prep in _user_delegations:
            if single_prep["_address"] not in self._prep_list:
                self._prep_list.put(single_prep["_address"])
            if single_prep["_address"] in similar_prep_list_check:
                revert(f'You can not delegate same Prep twice in a transaction')
            if single_prep["_votes_in_per"] < 10 ** 15:
                revert('You should provide delegation percentage more than 0.001')
            similar_prep_list_check.append(single_prep["_address"])
            amount_to_stake += single_prep["_votes_in_per"]
            self._set_address_delegations(_to, single_prep['_address'],
                                          single_prep["_votes_in_per"], get_delegated_value)
        return amount_to_stake

    def _distribute_evenly(self, amount_to_distribute: int, flags: int = 0, _to: Address = None) -> int:
        """
        Returns the amount to be evenly distributed to top 100 preps.
        :params amount_to_distribute : total amount in ICX that is to be distributed to top preps.
        :params flags:Flag is set to 1 if User sends empty delegation preferences in their first transaction.
        :params _to : Wallet address to set the delegation if the flag is 1.
        :params prep_list : complete prep list in staking contract.
        """
        _value = 0
        if flags == 1:
            prep_delegations = self.getPrepDelegations()
            evenly_ditribution = amount_to_distribute // TOP_PREP_COUNT
            for prep in self._top_preps:
                self._set_address_delegations(_to, prep, evenly_ditribution, prep_delegations)
        else:
            evenly_ditribution = (DENOMINATOR * amount_to_distribute) // TOP_PREP_COUNT
            _value = evenly_ditribution // DENOMINATOR
        return _value

    def _set_address_delegations(self, _to: Address, _prep: Address, _value: int, _delegations: dict) -> None:
        """
        Sets address delegations of a user in a dict db
        where key is the wallet addresses and value is
        the prep addresses and the ICX delegated to that
        prep address by a specific user in a string.
        :params _to: Wallet Address to set the delegation for.
        :params _prep : Prep addresses.
        :params _value : Percentage to store the delegations.
        :params _delegations : complete delegations of staking contract.
        """
        _to_str = str(_to)
        self._address_delegations[_to_str] += f'{str(_prep)}:{str(_value)}.'
        # _value is the delegation preferences of a user for a specific prep in 10 **18 form
        total_icx_hold = (self.sICX_score.balanceOf(_to) * self._rate.get()) // DENOMINATOR
        if total_icx_hold != 0:
            _value = (_value * total_icx_hold) // (100 * DENOMINATOR)
            self._set_prep_delegations(_prep, _value, _delegations)

    def _set_prep_delegations(self, _prep: Address, _value: int, _delegations: dict) -> None:
        """
        Sets Prep delegations to a dictdb where key is prep addresses
         and value is the ICX amount.
         :params _prep : prep address to set the delegation for.
         :params _value : Value in ICX in 10**18 form.
         :params _delegations : complete delegations of staking contract.
        """
        _prep_str = str(_prep)
        if _delegations == {}:
            self._prep_delegations[_prep_str] = _value
        else:
            if _prep_str in _delegations.keys():
                self._prep_delegations[_prep_str] += _value
            else:
                self._prep_delegations[_prep_str] = _value

    def _stake_and_delegate(self, evenly_distribute_value: int = 0) -> None:
        """
        It calls other internal functions that is used for staking and delegating.
        """
        self._stake(self.getTotalStake())
        self._delegations(evenly_distribute_value)

    def _remove_previous_delegations(self, _to: Address) -> dict:
        """
        Removes the previous delegations preferences of a user
        and initializing the delegation of a user as an
        empty string and returns the previous delegation preferences of that wallet.
        :params _to: Wallet Address of which delegation is to be removed from the total delegations.
        """
        address_str = str(_to)
        previous_address_delegations = self._get_address_delegations_in_per(_to)
        icx_hold_previously = (self.sICX_score.balanceOf(_to) * self._rate.get()) // DENOMINATOR
        if previous_address_delegations != {}:
            self._address_delegations[address_str] = ''
            for item in previous_address_delegations.items():
                x = Address.from_string(item[0])
                self._prep_delegations[str(x)] -= ((item[1] * icx_hold_previously) // (
                        100 * DENOMINATOR))
        return previous_address_delegations

    def _reset_top_preps(self) -> int:
        """
        Sums the value of ICX of those preps
        that are out of 100 and returns an integer.
        """
        to_distribute = 0
        for single_prep in self.getPrepDelegations().keys():
            if Address.from_string(single_prep) not in self._top_preps:
                to_distribute += self._prep_delegations[str(single_prep)]
        to_evenly_distribute_value = self._distribute_evenly(to_distribute)
        return to_evenly_distribute_value

    def _check_for_week(self) -> int:
        """
        Sets the new top 100 prep address in an array db weekly after checking the specific conditions.
        Calls the function _reset_top_preps and returns the sum of ICX of those preps
        that are out of 100 if there is any else 0.
        """
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_week.get() + (7 * 43200):
            self._block_height_week.set(self._system.getIISSInfo()["nextPRepTerm"])
            for i in range(TOP_PREP_COUNT):
                self._top_preps.pop()
            self._set_top_preps()
            return self._reset_top_preps()
        else:
            return self._reset_top_preps()

    def _check_for_iscore(self) -> None:
        """
        Claim iscore once a day.
        """
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_day.get() + 43200:
            self._block_height_day.set(self._system.getIISSInfo()["nextPRepTerm"])
            self._claim_iscore()

    def _checkForBalance(self) -> None:
        """
        Checks the balance of the score and transfer the
         unstaked amount to the address and removing the
         data from linked list one at a transaction.
         """
        balance_score = self.icx.get_balance(self.address) - self._daily_reward.get()
        if balance_score > 0:
            unstake_info_list = self.getUnstakeInfo()
            for each_info in unstake_info_list:
                value_to_transfer = each_info[0]
                if value_to_transfer <= balance_score:
                    self._send_ICX(each_info[3], value_to_transfer)
                    self._linked_list_var.remove(self._linked_list_var._head_id.get())
                    self._total_unstake_amount.set(self._total_unstake_amount.get() - value_to_transfer)
                break

    @payable
    @external
    def stakeICX(self, _to: Address = None, _data: bytes = None) -> None:
        """
        Adds received ICX to the pool then mints an equivalent value of sICX to
        the recipient address, _to.

        :params _to: Wallet address where sICX is minted to.
        :params _data: Data forwarded with the minted sICX.
        """
        if _data is None:
            _data = b'None'
        if _to is None:
            _to = self.msg.sender
        self._perform_checks()
        self._total_stake.set(self._total_stake.get() + self.msg.value)
        amount = DENOMINATOR * self.msg.value // self._rate.get()
        previous_address_delegations = self._remove_previous_delegations(_to)
        self.sICX_score.mintTo(_to, amount, _data)
        prep_delegations = self.getPrepDelegations()
        if previous_address_delegations == {}:
            flags = 1
            amount_to_stake_in_per = 100 * DENOMINATOR
            to_evenly_distribute_value = self._distribute_evenly(amount_to_stake_in_per, flags, _to)
        else:
            for dict_prep_delegation in previous_address_delegations.items():
                self._set_address_delegations(_to, Address.from_string(dict_prep_delegation[0]),
                                              dict_prep_delegation[1], prep_delegations)
        self._stake_and_delegate(self._check_for_week())
        self._sICX_supply.set(self._sICX_supply.get() + amount)
        self.TokenTransfer(_to, amount, f'{amount / DENOMINATOR} sICX minted to {_to}')
        return amount

    def _claim_iscore(self) -> None:
        """
        Claims the iScore and distributes it to the top 100 prep addresses.
         """
        iscore_details_dict = self._system.queryIScore(self.address)
        if iscore_details_dict['estimatedICX'] != 0:
            self._system.claimIScore()
            self._distributing.set(True)

    def _stake(self, _stake_value: int) -> None:
        """
        Stakes the ICX in the network.
        :params _stake_value: Amount to stake in the network.
        """
        self._system.setStake(_stake_value)

    def _calculate_percent_to_icx(self, _voting_percentage: int, _total_amount: int) -> int:
        """
        It converts delegation preferences of a user i.e. Percentage in ICX.
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
        sicx_to_icx_conversion = _value * self._rate.get() // DENOMINATOR
        receiver_delegation_preference_in_per = self._get_address_delegations_in_per(_to)
        sender_delegation_preference_in_per = self._get_address_delegations_in_per(_from)
        for single_delegation in sender_delegation_preference_in_per.items():
            amount_to_remove_from_prep = self._calculate_percent_to_icx(single_delegation[1], sicx_to_icx_conversion)
            self._prep_delegations[single_delegation[0]] -= amount_to_remove_from_prep
        if receiver_delegation_preference_in_per != {}:
            for one in receiver_delegation_preference_in_per.items():
                amount_to_add_to_prep = self._calculate_percent_to_icx(one[1], sicx_to_icx_conversion)
                self._prep_delegations[str(one[0])] += amount_to_add_to_prep
        else:
            self._distribute_evenly(100 * DENOMINATOR, 1, _to)
            pool_delegations = self.getPrepDelegations()
            total_icx_hold = (_value * self._rate.get()) // DENOMINATOR
            for delegations in self._get_address_delegations_in_per(_to).items():
                icx_value = (delegations[1] * total_icx_hold) // (100 * DENOMINATOR)
                self._set_prep_delegations(delegations[0], icx_value, pool_delegations)

        self._stake_and_delegate(self._check_for_week())

    def _perform_checks(self) -> None:
        """
        If the iscore is claimed then the new rate is set
        and it also calls multiple check functions.
        """
        if self._distributing.get() is True:
            stake_in_network = self._system.getStake(self.address)
            total_unstake_in_network = 0
            if 'unstakes' in stake_in_network.keys():
                for each in stake_in_network['unstakes']:
                    total_unstake_in_network += each['unstake']
            daily_reward = total_unstake_in_network + self.icx.get_balance(
                self.address) - self._total_unstake_amount.get() - self.msg.value
            self._daily_reward.set(daily_reward)
            self._total_lifetime_reward.set(self.getLifetimeReward() + daily_reward)
            self._rate.set(self.getRate())
            totalStake = self._total_stake.get()
            self._total_stake.set(self.getTotalStake() + daily_reward)
            for single_prep in self.getPrepList():
                value_in_icx = self._prep_delegations[str(single_prep)]
                weightage_in_per = ((value_in_icx * DENOMINATOR) // totalStake) * 100
                single_prep_reward = ((weightage_in_per // 100) * daily_reward) // DENOMINATOR
                self._set_prep_delegations(Address.from_string(str(single_prep)), single_prep_reward,
                                           self.getPrepDelegations())
            self._daily_reward.set(0)
            self._distributing.set(False)
        self._check_for_iscore()
        self._checkForBalance()

    @external
    def delegate(self, _user_delegations: List[PrepDelegations]):
        """
        Updates the delegation preferences of a
        user and redelegates in the network.
        :params _user_delegations: A list of dictionaries to store the delegation preferences of a user.
        """
        _to = self.msg.sender
        self._perform_checks()
        previous_address_delegations = self._remove_previous_delegations(_to)
        prep_delegations = self.getPrepDelegations()
        amount_to_stake_in_per = self._delegate_votes(_to, _user_delegations,
                                                      prep_delegations)
        if amount_to_stake_in_per != 100 * DENOMINATOR:
            revert('Total delegations should be 100 %')
        if previous_address_delegations != {}:
            self._stake_and_delegate(self._check_for_week())

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
        try:
            d = json_loads(_data.decode("utf-8"))
        except BaseException as e:
            revert(f'Invalid data: {_data}. Exception: {e}')
        if d["method"] == "unstake":
            if "user" in d.keys():
                self._unstake(_from, _value, Address.from_string(d["user"]))
            else:
                self._unstake(_from, _value)

    def _delegations(self, evenly_distribute_value: int) -> None:
        """
        Delegates the ICX to top prep addresses.

        :param evenly_distribute_value: Share of even distribution to each P-Rep.
        """
        delegation_list = []
        total_preps = len(self._top_preps)
        voting_power_check = 0
        count = 0
        for prep in self._top_preps:
            count += 1
            value_in_icx = self._prep_delegations[str(prep)] + evenly_distribute_value
            voting_power_check += value_in_icx
            # If this is the last prep, we add the dust.
            if count == total_preps:
                dust = self.getTotalStake() - voting_power_check
                value_in_icx += dust
                self._prep_delegations[str(prep)] += dust
            delegation_info: Delegation = {
                "address": prep,
                "value": value_in_icx
            }
            delegation_list.append(delegation_info)
        self._system.setDelegation(delegation_list)

    def _unstake(self, _to: Address, _value: int, _sender_address: Address = None) -> None:
        """
        Burns the sICX and removes delegations
        from the prep addresses and adds the
        unstaking request to the linked list.
        :params _to : Address that is making unstaking request.
        :params _value : Amount of sICX to be burned.
        """
        self.sICX_score.burn(_value)
        amount_to_unstake = (_value * self._rate.get()) // DENOMINATOR
        delegation_in_per = self._get_address_delegations_in_per(_to)
        self._total_unstake_amount.set(self._total_unstake_amount.get() + amount_to_unstake)
        for item in delegation_in_per.items():
            prep_percent = int(item[1])
            amount_to_remove_from_prep = ((prep_percent // 100) * amount_to_unstake) // DENOMINATOR
            self._prep_delegations[item[0]] -= amount_to_remove_from_prep
        self._total_stake.set(self._total_stake.get() - amount_to_unstake)
        self._delegations(self._reset_top_preps())
        self._stake(self._total_stake.get())
        stake_in_network = self._system.getStake(self.address)
        address_to_send = _to
        if _sender_address is not None:
            address_to_send = _sender_address
        self._linked_list_var.append(_to, amount_to_unstake,
                                     stake_in_network['unstakes'][-1]['unstakeBlockHeight'], address_to_send,
                                     self._linked_list_var._tail_id.get() + 1)
        self._sICX_supply.set(self._sICX_supply.get() - _value)

    def _send_ICX(self, _to: Address, amount: int, msg: str = '') -> None:
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
