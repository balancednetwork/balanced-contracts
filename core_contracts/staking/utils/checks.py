
from .consts import *

# ================================================
#  Exceptions
# ================================================

class SenderNotScoreOwnerError(Exception):
	pass


class SenderNotAuthorized(Exception):
	pass


class NotAFunctionError(Exception):
	pass


def only_admin(func):
	if not isfunction(func):
		raise NotAFunctionError

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._admin.get():
			raise SenderNotAuthorized(self.msg.sender)

		return func(self, *args, **kwargs)
	return __wrapper


def only_owner(func):
	if not isfunction(func):
		raise NotAFunctionError

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self.owner:
			raise SenderNotScoreOwnerError(self.owner)

		return func(self, *args, **kwargs)
	return __wrapper


def staking_on(func):
	if not isfunction(func):
		revert(f"NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if not self._staking_on.get():
			revert(f'{TAG}: ICX Staking SCORE is not active.')

		return func(self, *args, **kwargs)
	return __wrapper
