__author__ = 'clem'
__date__ = '25/05/2015'


class InvalidArgument(BaseException):
	pass


class FileSystemNotMounted(BaseException):
	pass


class FileServerUnreachable(BaseException):
	pass


class NetworkUnreachable(BaseException):
	pass


class InternetUnreachable(RuntimeWarning):
	pass


class RORAUnreachable(RuntimeWarning):
	pass


class ShinyUnreachable(RuntimeWarning):
	pass


class SGEUnreachable(RuntimeWarning):
	pass


class SGEError(RuntimeWarning):
	pass


class NoSuchJob(RuntimeWarning):
	pass


class InvalidArguments(BaseException):
	pass


class ReadOnlyAttribute(RuntimeWarning):
	pass


class NotDefined(BaseException):
	pass
