from iconservice import *


class IRC2Interface(InterfaceScore):

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


class GovernanceInterface(InterfaceScore):

    @interface
    def getContractAddress(self, contract: str) -> Address:
        pass