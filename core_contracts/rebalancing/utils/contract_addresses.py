from iconservice import *


class AddressDict(TypedDict):
    name: str
    address: Address


class ContractAddresses(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self.contract_address_collection = DictDB("contract_address_collection", self.db, Address)
        self.contract_address_array = ArrayDB("contract_address_array", self.db, str)

    def on_install(self, *args, **kargs) -> None:
        """
        Invoked when the contract is deployed for the first time,
        and will not be called again on contract update or deletion afterward.
        This is the place where you initialize the state DB.
        """
        super().on_install()

    def on_update(self) -> None:
        """
        Invoked when the contract is deployed for update.
        This is the place where you migrate old states.
        """
        super().on_update()

    @external
    def changeGovernance(self, _address: Address) -> None:
        """
        Changes the governance address associated with the score
        :param _address: Address of the governance contract
        :return: None
        """
        if self.msg.sender != self.owner:
            revert("Unauthorized: Owner only.")
        self._set_address([{"name": "governance", "address": _address}])

    @external
    def set_contract_addresses(self, addresses: List[AddressDict]) -> None:
        """
        Sets contract addresses

        :param addresses: TypeDict containing names of contact as key
        and addresses of each contract as corresponding value

        :return:
        """
        if self.msg.sender != self.owner:
            if self.msg.sender != self.get_contract_address("governance"):
                revert(f"Unauthorized: Governance only.")
        self._set_address(addresses)

    def _set_address(self, addresses: List[AddressDict]):
        # and i["address"].is_contract)
        if any(not type(i["address"]) == Address for i in addresses):
            revert(f"All addresses should be contract addresses.")

        for address in addresses:
            if self.address == address["address"]:
                continue
            db_value = self.contract_address_collection[address["name"]]

            # NO UPDATE IF NO CHANGE IN ADDRESS
            if db_value != address["address"]:
                self.contract_address_collection[address["name"]] = address["address"]

            # ONLY INSERT INTO ARRAY THE FIRST TIME
            if db_value is None:
                self.contract_address_array.put(address["name"])

    @external(readonly=True)
    def get_contract_address(self, name: str) -> Address:
        db_variable = self.contract_address_collection[name]
        if db_variable is None:
            revert(f"Unset reference:{name}")
        return db_variable

    @external(readonly=True)
    def get_all_contract_addresses(self) -> Dict:
        return {k: self.contract_address_collection[k] for k in self.contract_address_array}
