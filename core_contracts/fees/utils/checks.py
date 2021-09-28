from iconservice import *


# ================================================
#  Exceptions
# ================================================


class SenderNotGovernance(Exception):
    pass


class NotAFunctionError(Exception):
    pass


def only_governance(func):
    if not isfunction(func):
        raise NotAFunctionError

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._governance.get():
            raise SenderNotGovernance(self.msg.sender)

        return func(self, *args, **kwargs)

    return __wrapper