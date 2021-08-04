from iconservice import *


class ContractAddresses(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

        _DAOFUND = 'daofund'
        _GOVERNANCE = 'governance'
        _REBALANCE = 'rebalance'
        _DEX = 'dex'
        _DIVIDENDS = 'dividends'
        _RESERVE = 'reserve'
        _REWARDS = 'rewards'
        _STAKING = 'staking'
        _LOANS = 'loans'
        _ORACLE = 'oracle'

        self.daofund = VarDB(_DAOFUND, self.db, Address)
        self.dex = VarDB(_DEX, db, Address)
        self.dividends = VarDB(_DIVIDENDS, db, Address)
        self.governance = VarDB(_GOVERNANCE, db, Address)
        self.loans = VarDB(_LOANS, db, Address)
        self.oracle = VarDB(_ORACLE, db, Address)
        self.rebalance = VarDB(_REBALANCE, db, Address)
        self.reserve = VarDB(_RESERVE, db, Address)
        self.rewards = VarDB(_REWARDS, db, Address)
        self.staking = VarDB(_STAKING, db, Address)

        self.address_mapping = {_DAOFUND: self.daofund,
                                _DEX: self.dex,
                                _DIVIDENDS: self.dividends,
                                _GOVERNANCE: self.governance,
                                _LOANS: self.loans,
                                _ORACLE: self.oracle,
                                _REBALANCE: self.rebalance,
                                _RESERVE: self.reserve,
                                _REWARDS: self.rewards,
                                _STAKING: self.staking}

    @abstractmethod
    def on_install(self) -> None:
        """
        Invoked when the contract is deployed for the first time,
        and will not be called again on contract update or deletion afterward.
        This is the place where you initialize the state DB.
        """
        super().on_install()

    @abstractmethod
    def on_update(self) -> None:
        """
        Invoked when the contract is deployed for update.
        This is the place where you migrate old states.
        """
        super().on_update()
        self.governance.set(Address.from_string(governance_address))

    @external
    def set_contract_addresses(self, addresses: TypedDict) -> None:
        if self.msg.sender != self.governance.get():
            revert(f"Unauthorized: Governance only.")
        disallowed_addresses = set(addresses.keys()) - set(self.address_mapping.keys())
        if len(disallowed_addresses):
            revert(f"Unsupported names:{disallowed_addresses}")
        for key, value in addresses.items():
            if self.address == value:
                continue
            self.address_mapping[key].set(value)

    @external(readonly=True)
    def get_contract_address(self, name: str) -> Address:
        db_variable = self.address_mapping.get(name)
        if not db_variable:
            revert(f"Unsupported name:{name}")
        return db_variable.get()

    @external
    def changeGovernance(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert("Unauthorized: Governance only.")
        self.governance.set(_address)
