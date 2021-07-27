from .consts import *


class Utils:
    @staticmethod
    def remove_from_array(array: ArrayDB, el) -> None:
        temp = []
        # find that element and remove it
        while array:
            current = array.pop()
            if current == el:
                break
            else:
                temp.append(current)
        # append temp back to arrayDB
        while temp:
            array.put(temp.pop())


# An interface of token score
class TokenInterface(InterfaceScore):
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
