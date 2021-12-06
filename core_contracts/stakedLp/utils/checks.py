from iconservice import *

TAG = 'Staked Lp'


def only_owner(func):
    if not isfunction(func):
        revert(f'{TAG}'
               'NotAFunctionError')

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")
        return func(self, *args, **kwargs)

    return __wrapper

def only_governance(func):
    if not isfunction(func):
        revert(f'{TAG}'
               'NotAFunctionError')

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _governance = self._governance.get()
        if self.msg.sender != _governance:
            revert(f"{TAG}: "f"SenderNotScoreGovernanceError: (sender){self.msg.sender} (governance){_governance}")
        return func(self, *args, **kwargs)

    return __wrapper


def only_dex(func):
    if not isfunction(func):
        revert(f'{TAG}'
               'NotAFunctionError')

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _dex=self._dex.get()
        if self.msg.sender != _dex:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (dex){_dex}")
        return func(self, *args, **kwargs)

    return __wrapper

def only_admin(func):
	if not isfunction(func):
		revert(f"NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._admin.get():
			revert(f"SenderNotAdmin: sender({self.msg.sender}), admin({self._admin.get()})")

		return func(self, *args, **kwargs)
	return __wrapper