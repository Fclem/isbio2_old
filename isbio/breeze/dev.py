from utils import *
import cmd
import os
import atexit

csc = None
azure = None
targets = None


def init():
	pass


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
	global csc, azure, targets, b, r
	from models import ComputeTarget
	targets = ComputeTarget.objects.all()
	azure = targets[2]
	csc = targets[3]


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


def test_tree(report):
	from models import Report, RunServer, ObjectDoesNotExist
	try:
		a = report
		assert isinstance(a, Report)
		with RunServer(a) as b:
			b.parse_all()

		return b
	except (ObjectDoesNotExist, AssertionError):
		return None


def get_tree(rid):
	from models import Report, RunServer, ObjectDoesNotExist
	try:
		a = Report.objects.get(pk=rid)
		assert isinstance(a, Report)
		b = test_tree(a)
		assert isinstance(b, RunServer)

		return b.generate_source_tree(), b

	except (ObjectDoesNotExist, AssertionError):
		return None


# clem 07/04/2016
@atexit.register
def __cleanup__():
	print 'cleaning up...'

if __name__ == '__main__':
	# command line
	base()
	cmd_line()
elif __name__ == 'breeze.dev':
	# PyCharm python console
	base()
