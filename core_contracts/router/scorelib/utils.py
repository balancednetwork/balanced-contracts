from iconservice import *

# An interface of token score
class TokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def decimals(self) -> int:
        pass


# An interface of token score
class IRC31ReceiverInterface(InterfaceScore):

    @interface
    def onIRC31Received(self, _operator: Address, _from: Address, _id: int, _value: int, _data: bytes):
        pass

    @interface
    def onIRC31BatchReceived(self, _operator: Address, _from: Address, _ids: List[int], _values: List[int], _data: bytes):
        pass
