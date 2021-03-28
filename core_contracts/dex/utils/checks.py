from iconservice import *


def only_admin(func):
	if not isfunction(func):
		revert(f"NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._admin.get():
			revert(f"SenderNotAdmin: sender({self.msg.sender}), admin({self._admin.get()})")

		return func(self, *args, **kwargs)
	return __wrapper


def only_governance(func):
	if not isfunction(func):
		revert(f"NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._governance.get():
			revert(f"SenderNotGovernance: sender({self.msg.sender}), governance({self._governance.get()})")

		return func(self, *args, **kwargs)
	return __wrapper


def only_owner(func):
	if not isfunction(func):
		revert(f"NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self.owner:
			revert(f"SenderNotOwner: sender({self.msg.sender}), owner({self.owner})")

		return func(self, *args, **kwargs)
	return __wrapper
