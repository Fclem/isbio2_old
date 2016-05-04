# from .utils import advanced_pretty_print as pp
import docker_csc
from utils import pp
import cmd
import os
import atexit


class TempClass:
	pass

docker = TempClass()
docker.csc = None
docker.azure = None
targets = None
b = None


def azure():
	from docker_azure import DockerAzure
	return DockerAzure()


def csc():
	from docker_csc import DockerCSC
	return DockerCSC()


def init():
	pass
	# return dev()


def same(a, b):
	return a is b or '%s != %s' % (hex(id(a)), hex(id(b)))


class HelloWorld(cmd.Cmd):
	_locals = dict()

	def __init__(self, *args, **kwargs):
		cmd.Cmd.__init__(self, *args, **kwargs)
		self.prompt = 'docker> '

	def completedefault(self, *ignored):
		if not ignored:
			completions = globals()
		else:
			completions = [ignored]
		return completions

	@classmethod
	def kill_self(cls):
		global docker
		try:
			__cleanup__()
			bash_command = "kill -15 %s" % os.getpid()
			print "$ %s" % bash_command
			os.system(bash_command)
		except Exception as e:
			print e
			pass

	@classmethod
	def do_exit(cls, _):
		cls.kill_self()

	@classmethod
	def _has_valid_object(cls, line):
		a_list = [line.partition('.'), line.partition('('), line.partition('[')]
		all_keys = globals().keys()
		for each in a_list:
			if each[0].lower() in [a.lower() for a in all_keys]:
				return each
		return False

	def default(self, line=''):
		import sys

		parsed = self._has_valid_object(line)
		# if parsed:
		# 	return
		if parsed or line:
			try:
				res = eval(compile(line, sys.stderr.name, 'single'), globals(), self._locals)
				if res:
					print 'ret:', type(res), res
			except Exception as e:
				raise e
		# print "def:", line

	def completenames(self, text, *ignored):
		dotext = 'do_' + text
		lst = self._advanced_get_names(text)
		result = list()
		for a in lst:
			item = a[3:] if a.startswith(dotext) else a if text.lower() in a.lower() else None
			result.append(item) if item else None
		return result

	def _advanced_get_names(self, text=''):
		a_object = self._has_valid_object(text)
		# print a_object
		if a_object[1] == '.':
			# return dir(eval(a_object[0], globals())) # getattr(eval(a_object[0], globals()), '__dict__')
			return dir(globals()[a_object[0]]) # getattr(eval(a_object[0], globals()), '__dict__')
		return self._get_names()

	def _get_names(self):
		# This method used to pull in base class attributes
		# at a time dir() didn't do it yet.
		return dir(self.__class__) + globals().keys()


def base():
	global docker, targets, b
	# docker = object()
	# docker.csc = csc()
	# docker.azure = azure()
	from breeze.models import ComputeTarget
	targets = ComputeTarget.objects.all()
	b = targets[2]


def cmd_line():
	try:
		HelloWorld().cmdloop()
	except KeyboardInterrupt:
		HelloWorld.kill_self()
	except Exception as e:
		print e
		return cmd_line()


def kill_self():
	__cleanup__()


# clem 07/04/2016
@atexit.register
def __cleanup__():
	print 'cleaning up...'
	if docker.csc:
		docker.csc.__cleanup__()
	if docker.azure:
		docker.azure.__cleanup__()

if __name__ == '__main__':
	# command line
	base()
	cmd_line()
elif __name__ == 'breeze.dev':
	# PyCharm python console
	base()
