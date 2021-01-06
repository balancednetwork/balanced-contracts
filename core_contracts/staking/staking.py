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

TOTAL_PREPS = 20

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

class Staking(IconScoreBase):
    _SICX_SUPPLY = 'sICX_supply'
    _RATE = '_rate'
    _DISTRIBUTING = '_distributing'
    _SICX_ADDRESS = 'sICX_address'
    _BLOCK_HEIGHT_WEEK = '_block_height_week'
    _BLOCK_HEIGHT_DAY = '_block_height_day'
    _TOTAL_STAKE = '_total_stake'
    _TOTAL_LIFETIME_REWARD = '_total_lifetime_reward'
    _DAILY_REWARD = '_daily_reward'
    _LINKED_LIST_VAR = '_linked_list_var'
    _TOP_PREPS = '_top_preps'

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
        self._sICX_address = VarDB(self._SICX_ADDRESS, db, value_type=Address)
        # total staked from staking contract
        self._total_stake = VarDB(self._TOTAL_STAKE, db, value_type=int)
        # vardb to store total rewards
        self._total_lifetime_reward = VarDB(self._TOTAL_LIFETIME_REWARD, db, value_type=int)
        self._daily_reward = VarDB(self._DAILY_REWARD, db, value_type=int)
        self._distributing = VarDB(self._DISTRIBUTING,db,value_type=bool)
        # vardb to store total unstaking amount
        # array to store top 100 preps
        self._top_preps = ArrayDB(self._TOP_PREPS, db, value_type=Address)
        # initializing the system score
        self._system = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        #initialize the sicx score
        self.sICX_score = self.create_interface_score(self._sICX_address.get(), sICXTokenInterface)
        #initialize the linked list
        self._linked_list_var = LinkedListDB("unstake_dict", db)

    def on_install(self) -> None:
        super().on_install()
        # initializing the block height to check change in the top 100 preps
        self._block_height_week.set(self._system.getIISSInfo()["nextPRepTerm"])
        # initializing the block height to claim rewards once a day
        self._block_height_day.set(self._system.getIISSInfo()["nextPRepTerm"])
        # top 100 preps is initialized at first
        self._rate.set(DENOMINATOR)
        self._set_top_preps()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "Staking"

    @external(readonly=True)
    def getTodayRate(self) -> int:
        return self._rate.get()

    def getRate(self) -> int:
        """
        Get the ratio of ICX to sICX.
        """
        if self.sICX_score.totalSupply() == 0:
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

    # @external(readonly=True)
    # def getStakeFromNetwork(self) -> dict:
    #     """
    #     Returns a dictionary that specifies the total value staked in a network.
    #     """
    #     return self._system.getStake(self.address)
    #
    # @external(readonly=True)
    # def getDelegationFromNetwork(self) -> dict:
    #     """
    #     Returns the delegations sent to the network.
    #     """
    #     return self._system.getDelegation(self.address)

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
        top_prep_list= []
        for x in self._top_preps:
            top_prep_list.append(x)
        return top_prep_list

    @external(readonly=True)
    def getUserUnstakeInfo(self) -> list:
        """
        Returns a dictionary that shows wallet address as a key and the request of unstaked amount by that address
        as a value.
        """
        unstake_info_list =[]
        for items in self._linked_list_var:
            unstake_info_list.append([items[1],items[2]])
        return unstake_info_list

    @external
    def setSicxAddress(self, _address: Address) -> None:
        """
        Sets the sICX address from staking contract.
        :params _address : the address of sICX token contract.
        """
        self._sICX_address.set(_address)

    def _set_top_preps(self) -> None :
        """Weekly this function is called to set the top 100 prep address in an arraydb"""
        prep_dict =  self._system.getPReps(1, 20)
        prep_address_list = prep_dict['preps']
        for each_prep in prep_address_list:
            self._top_preps.put(each_prep['address'])

    def _get_amount_to_mint(self) -> int:
        """Returns the amount to be minted to a address"""
        supply = self._sICX_supply.get()
        balance = self.getTotalStake()
        if balance == self.msg.value:
            amount = self.msg.value
        else:
            amount = supply * self.msg.value // (balance - self.msg.value)
        return amount

    def _reset_top_preps(self) -> None:
        """
        Sets the new top 100 prep address in an array db weekly after checking the specific conditions.
        """
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_week.get() + (7 * 43200):
            self._block_height_week.set(self._system.getIISSInfo()["nextPRepTerm"])
            for i in range(len(self._top_preps)):
                self._top_preps.pop()
            self._set_top_preps()

    def _check_for_iscore(self) -> None:
        """
        Claim iscore and sets new rate daily.
        """
        if self._system.getIISSInfo()["nextPRepTerm"] > self._block_height_day.get() +  432:
            self._block_height_day.set(self._system.getIISSInfo()["nextPRepTerm"])
            self._claim_iscore()

    def _check_unstake_result(self) -> None:
        """
        Checks the balance of the score and transfer the
         unstaked amount to the address and removing the
         data from linked list .
         """
        balance_score = self.icx.get_balance(self.address) - self._daily_reward.get()
        if balance_score > 0:
            unstake_info_list = self.getUserUnstakeInfo()
            for each_info in unstake_info_list:
                value_to_transfer = each_info[0]
                if value_to_transfer <= balance_score:
                    self._send_ICX(each_info[1], value_to_transfer)
                    self._linked_list_var.remove(self._linked_list_var._head_id.get())
                break

    def _perform_checks(self) -> None:
        if self._distributing.get() == True:
            if self._sICX_supply.get() == 0:
                last_unstaking_address = self._linked_list_var.node_key(self._linked_list_var._tail_id.get())
                self._send_ICX(last_unstaking_address,self._daily_reward.get())
            else:
                self._total_stake.set(self._total_stake.get() + self._daily_reward.get())
                self._distributing.set(False)
                self._daily_reward.set(0)
        self._reset_top_preps()
        self._check_for_iscore()
        self._check_unstake_result()

    def _evenly_distrubuted_amount(self) -> tuple:
        return (self._total_stake.get() // TOTAL_PREPS, self._total_stake.get()% TOTAL_PREPS)

    @payable
    @external
    def addCollateral(self, _to: Address = None) -> None:
        """
        stakes and delegates some ICX to top prep
        addresses and receives equivalent of sICX by the user address.
        :params _to: Wallet address where sICX is minted to.
        """
        if _to == None:
            _to = self.tx.origin
        self._perform_checks()
        self._total_stake.set(self._total_stake.get()+self.msg.value)
        amount = self._get_amount_to_mint()
        self.sICX_score.mintTo(_to, amount)
        self._stake(self._total_stake.get())
        icx_to_distribute = self._evenly_distrubuted_amount()
        remainder_icx = icx_to_distribute[1]
        evenly_distributed_amount = icx_to_distribute[0]
        self._delegations(evenly_distributed_amount,remainder_icx)
        self._sICX_supply.set(self._sICX_supply.get() + amount)
        self.TokenTransfer(_to, amount, f'{amount / DENOMINATOR} sICX minted to {_to}')

    def _claim_iscore(self) -> None:
        """
        Claims the iScore and distributes it to the top 100 prep addresses.
         """
        iscore_details_dict = self._system.queryIScore(self.address)
        if iscore_details_dict['estimatedICX'] != 0:
            amount = iscore_details_dict["estimatedICX"]
            self._system.claimIScore()
            self._daily_reward.set(amount)
            self._rate.set(self.getRate())
            self._total_lifetime_reward.set(self.getLifetimeReward() + amount)
            self._distributing.set(True)

    def _stake(self, _stake_value: int) -> None:
        """
        Stakes the ICX in the network.
        :params _stake_value: Amount to stake in the network.
        """
        self._system.setStake(_stake_value)

    def _delegations(self, evenly_distribute_value: int, remainder: int) -> None:
        """
        Delegates the ICX to top prep addresses.
        :params evenly_distribute_value : Amount to be distributed to all the preps evenly.
        """
        delegation_list = []
        for each_prep in self._top_preps:
            if len(delegation_list) == (TOTAL_PREPS - 1):
                evenly_distribute_value = evenly_distribute_value + remainder
            delegation_info: Delegation = {
                "address": each_prep,
                "value": evenly_distribute_value
            }
            delegation_list.append(delegation_info)
        self._system.setDelegation(delegation_list)

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
        if set(d.keys()) != set(["method"]):
            revert('Invalid parameters.')
        if d["method"] == "unstake":
            self._unstake(_from, _value)

    def _unstake(self, _to: Address, _value: int) -> None:
        """
        Burns the sICX and removes delegations
        from the prep addresses and adds the
        unstaking request to the linked list.
        :params _to : Address that is making unstaking request.
        :params _value : Amount of sICX to be burned.
        """
        try:
            self._perform_checks()
            self.sICX_score.burn(_value)
            amount_to_unstake = (_value * self._rate.get()) // DENOMINATOR
            if self._sICX_supply.get() - _value == 0:
                amount_to_unstake = _value
            self._linked_list_var.append(_to, amount_to_unstake, self._linked_list_var._tail_id.get() + 1)
            self._total_stake.set(self._total_stake.get() - amount_to_unstake)
            icx_to_distribute = self._evenly_distrubuted_amount()
            remainder_icx = icx_to_distribute[1]
            evenly_distributed_amount = icx_to_distribute[0]
            self._delegations(evenly_distributed_amount, remainder_icx)
            self._stake(self._total_stake.get())
            self._sICX_supply.set(self._sICX_supply.get() - _value)
        except BaseException as e:
            revert(f'You can try unstaking later, {e}')


    def _send_ICX(self, _to: Address, amount: int, msg: str='') -> None:
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