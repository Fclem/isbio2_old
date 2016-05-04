import os
import sys
import abc

__version__ = '0.1'
__author__ = 'clem'
__date__ = '04/05/2016'


# clem 06/04/2016
def password_from_file(the_path):
	from os.path import exists, expanduser
	if not exists(the_path):
		temp = expanduser(the_path)
		if exists(temp):
			the_path = temp
		else:
			return False
	return open(the_path).read().replace('\n', '')


# TODO set this configs :
__DEV__ = True
__path__ = os.path.realpath(__file__)
__dir_path__ = os.path.dirname(__path__)
__file_name__ = os.path.basename(__file__)

# general config
ENV_JOB_ID = ('JOB_ID', '')


# clem 08/04/2016 (from utilities)
def function_name(delta=0):
	return sys._getframe(1 + delta).f_code.co_name


# clem on 21/08/2015 (from utilities)
def get_md5(content):
	""" compute the md5 checksum of the content argument

	:param content: the content to be hashed
	:type content: list or str
	:return: md5 checksum of the provided content
	:rtype: str
	"""
	import hashlib
	m = hashlib.md5()
	if type(content) == list:
		for eachLine in content:
			m.update(eachLine)
	else:
		m.update(content)
	return m.hexdigest()


# clem on 21/08/2015 (from utilities)
def get_file_md5(file_path):
	""" compute the md5 checksum of a file

	:param file_path: path of the local file to hash
	:type file_path: str
	:return: md5 checksum of file
	:rtype: str
	"""
	try:
		fd = open(file_path, "rb")
		content = fd.readlines()
		fd.close()
		return get_md5(content)
	except IOError:
		return ''


# from utilities
class Bcolors(object):
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[33m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

	@staticmethod
	def ok_blue(text):
		return Bcolors.OKBLUE + text + Bcolors.ENDC

	@staticmethod
	def ok_green(text):
		return Bcolors.OKGREEN + text + Bcolors.ENDC

	@staticmethod
	def fail(text):
		return Bcolors.FAIL + text + Bcolors.ENDC + ' (%s)' % __name__

	@staticmethod
	def warning(text):
		return Bcolors.WARNING + text + Bcolors.ENDC

	@staticmethod
	def header(text):
		return Bcolors.HEADER + text + Bcolors.ENDC

	@staticmethod
	def bold(text):
		return Bcolors.BOLD + text + Bcolors.ENDC

	@staticmethod
	def underlined(text):
		return Bcolors.UNDERLINE + text + Bcolors.ENDC


class StorageModule:
	__metaclass__ = abc.ABCMeta
	_not = "Class %s doesn't implement %s()"
	_interface = None # as to be defined as a BlobStorageObject that support argument list : (account_name=self

	def __init__(self):
		pass

	def _print_call(self, fun_name, args):
		arg_list = ''
		if isinstance(args, basestring):
			args = [args]
		for each in args:
			arg_list += "'%s', " % Bcolors.warning(each)
		print Bcolors.bold(fun_name) + "(%s)" % arg_list[:-2]

