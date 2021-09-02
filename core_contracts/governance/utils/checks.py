from iconservice import *


# ================================================
#  Exceptions
# ================================================
class SenderNotScoreOwnerError(Exception):
    pass


class NotAFunctionError(Exception):
    pass


def only_owner(func):
    if not isfunction(func):
        raise NotAFunctionError

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            raise SenderNotScoreOwnerError(self.owner)

        return func(self, *args, **kwargs)

    return __wrapper


def address_wrapper(func):
    """Converts all the Address type in args and kwards from str to Address"""
    if not callable(func):
        raise NotAFunctionError

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        type_hints = dict(func.__annotations__)
        del type_hints["return"]

        if len(args):
            address_index = [idx for idx, key in enumerate(type_hints) if type_hints[key] == Address]
            args = (value if idx not in address_index
                    else (Address.from_string(value) if type(value) != Address else value)
                    for idx, value in enumerate(args))
        new_kwargs = {}
        if len(kwargs):
            address_keys = {k for k, v in type_hints.items() if v == Address}
            for key in address_keys:
                value = kwargs[key]
                new_kwargs[key] = Address.from_string(value) if type(value) != Address else value

        return func(self, *args, **new_kwargs)

    return __wrapper
