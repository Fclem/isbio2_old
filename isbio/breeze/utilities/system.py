from threading import Thread, Lock
from sys import _getframe as get_frame
import json
import os
import copy
import abc
import subprocess as sp

__version__ = '0.1'
__author__ = 'clem'
__date__ = '27/05/2016'


class TermColoring(enumerate):
	HEADER = '\033[95m'
	OK_BLUE = '\033[94m'
	OK_GREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	END_C = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

	@classmethod
	def ok_blue(cls, text):
		return cls.OK_BLUE + text + cls.END_C

	@classmethod
	def ok_green(cls, text):
		return cls.OK_GREEN + text + cls.END_C

	@classmethod
	def fail(cls, text):
		return cls.FAIL + text + cls.END_C

	@classmethod
	def warning(cls, text):
		return cls.WARNING + text + cls.END_C

	@classmethod
	def header(cls, text):
		return cls.HEADER + text + cls.END_C

	@classmethod
	def bold(cls, text):
		return cls.BOLD + text + cls.END_C

	@classmethod
	def underlined(cls, text):
		return cls.UNDERLINE + text + cls.END_C


# clem 19/02/2016
def do_restart():
	try:
		sp.Popen('sleep 1 && killall python', shell=True, stdout=sp.PIPE) # relies on autorun.sh
	except Exception as e:
		raise e
	return True


# clem 19/02/2016
def do_reboot():
	try:
		sp.Popen('sleep 1 && sudo reboot -n', shell=True, stdout=sp.PIPE)
	except Exception as e:
		raise e
	return True


# clem 08/04/2016
def this_function_name(delta=0):
	return this_function_caller_name(delta)


# clem 08/04/2016
def this_function_caller_name(delta=0):
	return get_frame(2 + delta).f_code.co_name


# clem 20/06/2016
def is_command_available(cmd_str):
	return get_term_cmd_stdout(['which', cmd_str], False) not in ['', [''], []]


# clem 18/04/2016
def get_term_cmd_stdout(cmd_list_with_args, check_if_command_is_available=True):
	assert isinstance(cmd_list_with_args, list)
	ret = ''
	try:
		if not check_if_command_is_available or is_command_available(cmd_list_with_args[0]):
			a = sp.Popen(cmd_list_with_args, stdout=sp.PIPE)
			b = a.communicate()
			if b:
				s = b[0].split('\n')
				return s
		return ret
	except OSError as e:
		print 'EXCEPTION (UNLOGGED) while running cmd %s : %s' % (str(cmd_list_with_args), str(e))
		return ''


# moved from settings on 19/05/2016 # FIXME Django specific ?
def import_env():
	""" dynamically change the environement """
	source = 'source ~/.sge_profile'
	dump = 'python -c "import os, json;print json.dumps(dict(os.environ))"'
	pipe = sp.Popen(['/bin/bash', '-c', '%s && %s' % (source, dump)], stdout=sp.PIPE)
	env = json.loads(pipe.stdout.read())
	os.environ = env
