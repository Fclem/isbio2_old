from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
__author__ = 'clem'
__date__ = '25/05/2015'
#
# System checks
#


class SystemCheckFailed(RuntimeWarning):
	pass


class FileSystemNotMounted(SystemCheckFailed):
	pass


class MysqlDbUnreachable(BaseException):
	def __init__(self):
		self.__str__()

	def __str__(self): # FIXME code unreachable
		try:
			import logging
			logging.getLogger(__name__).critical('DB was unreachable')
		except Exception:
			pass
		# try to
		#  restart breeze :
		from utils import do_restart
		do_restart()
		# return repr(self.value)

	def __call__(self, *args, **kwargs):
		self.__str__()


class FileServerUnreachable(BaseException):
	pass


class NetworkUnreachable(SystemCheckFailed):
	pass


class InternetUnreachable(SystemCheckFailed):
	pass


class RORAUnreachable(SystemCheckFailed):
	pass


class SGEImproperlyConfigured(SystemCheckFailed):
	pass


class DOTMUnreachable(SystemCheckFailed):
	pass


class ShinyUnreachable(SystemCheckFailed):
	pass


class WatcherIsNotRunning(SystemCheckFailed):
	pass


class SGEUnreachable(SystemCheckFailed):
	pass


class CASUnreachable(SystemCheckFailed):
	pass


class GlobalSystemChecksFailed(SystemError):
	pass
#
# END
#


class SGEError(RuntimeWarning):
	pass


class NoSuchJob(RuntimeWarning):
	pass


class InvalidArgument(BaseException):
	pass


class InvalidArguments(BaseException):
	pass


class ReadOnlyAttribute(RuntimeWarning):
	pass


class NotDefined(BaseException):
	pass

