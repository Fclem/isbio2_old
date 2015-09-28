import logging
import sys, hashlib
from isbio import settings
from os.path import isfile, isdir, islink, exists, getsize
from os import symlink
from subprocess import call
from datetime import datetime
from breeze.b_exceptions import *

logger = logging.getLogger(__name__)


class Bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
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
		return Bcolors.FAIL + text + Bcolors.ENDC

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


# 25/06/2015 Clem
def console_print(text, datef=None):
	print console_print_sub(text, datef=datef)


def console_print_sub(text, datef=None):
	return "[%s] %s" % (dateT(datef), text)


# 10/03/2015 Clem / ShinyProxy
def dateT(dateF=None):
	if dateF is None:
		dateF = settings.USUAL_DATE_FORMAT
	return str(datetime.now().strftime(dateF))


# clem on 20/08/2015
def is_host_online(host, deadline=5):
	"""
	Check if given host is online (whether it respond to ping)
	:param host: the IP address to test
	:type host: str
	:param deadline: the maximum time to wait in second (text format)
	:type deadline: str | int
	:rtype: bool
	"""
	import subprocess
	res = call(['ping', '-c', '3', '-i', '0.2', '-W', '0.1', '-w', str(deadline), host], stdout=subprocess.PIPE)
	return res == 0


# clem on 21/08/2015
def get_md5(content):
	"""
	Return md5 checksum of content argument
	:type content: list|str
	:rtype: str
	"""
	m = hashlib.md5()
	if type(content) == list:
		for eachLine in content:
			m.update(eachLine)
	else:
		m.update(content)
	return m.hexdigest()


# clem on 21/08/2015
def get_file_md5(file_path):
	"""
	Return md5 checksum of file
	:param file_path: location of the file
	:type file_path: str
	:rtype: str
	"""
	try:
		content = list()
		fd = open(file_path, "rb")
		content = fd.readlines()
		fd.close()
	except IOError:
		# print "Can't retrieve MD5sum for ", file
		return ''

	return get_md5(content)


def get_logger(name=None):
	if name is None:
		name = sys._getframe(1).f_code.co_name
	log_obj = logger.getChild(name)
	assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only
	return log_obj


# Shortcut for handling path ( TEST DESIGN )
class Path(object):
	import os
	SEP = os.path.sep

	def __init__(self, path_str):
		"""
		Path object always return the path string with a trailing slash ( / ) for folders
		:param path_str: the path to use
		:type path_str: str
		"""
		self.__path_str = ''
		self.set_path(path_str)

	def get_path(self):
		return self.__path_str

	def set_path(self, path_str):
		if path_str is not None and path_str != '':
			if path_str[-1] != self.SEP and isdir(path_str + self.SEP):
				path_str += self.SEP
		self.__path_str = path_str

	path_str = property(get_path, set_path)

	def __str__(self): # Python 3: def __str__(self):
		return '%s' % self.path_str

	def is_dir(self):
		return isdir(self.path_str)

	def is_file(self):
		return isfile(self.path_str)

	def is_link(self):
		return islink(self.path_str)

	def exists(self):
		return exists(self.path_str)

	def get_size(self):
		return getsize(self.path_str)

	def is_non_empty_file(self):
		"""
		Return if the path is pointing to an non empty file
		:return: is path pointing to an non empty file
		:rtype: bool
		"""
		return isfile(self.path_str) and getsize(self.path_str) > 0

	def remove_file_safe(self):
		"""
		Remove a file or link if it exists
		:return: True or False
		:rtype: bool
		"""
		from os import remove
		try:
			if isfile(self.path_str) or islink(self.path_str):
				get_logger().info("removing %s" % self.path_str)
				remove(self.path_str)
				return True
		except OSError:
			return self.remove_lnk_safe()
		return False

	def remove_lnk_safe(self):
		"""
		Remove a link file or a dir and all sub content (to use for links only)
		"""
		from os import unlink

		path = self.path_str
		if self.is_dir() and self.path_str.endswith(self.SEP):
			path = path[:-1]

		try:
			get_logger().debug("unlinking %s" % path)
			unlink(path)
			return True
		except OSError as e:
			get_logger().debug("unable to unlink : %s" % e)
		return False

	def auto_symlink(self, holder):
		"""
		Make a soft-link and overwrite any previously existing file (be careful !) or link with the same name
		:param holder: path of the link holder
		:type holder: str
		"""
		log_obj = get_logger()
		Path(holder).remove_lnk_safe()

		log_obj.debug("symlink to %s @ %s" % (self.path_str, holder))
		symlink(self.path_str, holder)
		return True


def safe_rm(path, ignore_errors=False):
	"""
	Delete a folder recursively
	Provide a smart shutil.rmtree wrapper with system folder protection
	Avoid mistake caused by malformed auto generated paths
	:param path: folder to delete
	:type path: str
	:type ignore_errors: bool
	:return:
	:rtype: bool
	"""
	import os
	import shutil
	if path not in settings.FOLDERS_LST:
		if os.path.isdir(path):
			log_txt = 'rmtree %s had %s object(s)' % (path, len(os.listdir(path)))
			get_logger().debug(log_txt)
			shutil.rmtree(path, ignore_errors)
			return True
		else:
			log_txt = 'not a folder : %s' % path
			get_logger().warning(log_txt)
	else:
		log_txt = 'attempting to delete system folder : %s' % path
		get_logger().exception(log_txt)
	return False


# Clem 24/09/2015
def safe_copytree(source, destination, symlinks=True, ignore=None):
	"""
	Copy a folder recursively
	Provide a smart shutil.copytree wrapper with system folder protection
	Avoid mistake caused by malformed auto generated paths
	Avoid non existent source folder, and warn about existent destination folders
	:type source: str
	:type destination: str
	:type symlinks: bool
	:type ignore: callable
	:rtype: bool
	"""
	import os
	import shutil
	if destination not in settings.FOLDERS_LST:
		if os.path.isdir(source):
			if os.path.isdir(destination):
			# 	os.mkdir(destination)
			# else:
				log_txt = 'copytree, destination folder %s exists, STOP' % destination
				get_logger().error(log_txt)
			shutil.copytree(source, destination, symlinks, ignore)
			return True
		else:
			log_txt = 'copytree, source folder %s don\'t exists, STOP' % source
			get_logger().warning(log_txt)
	else:
		log_txt = 'attempting to copy to a system folder : %s, STOP' % destination
		get_logger().exception(log_txt)
	return False


def is_non_empty_file(file_path):
	return Path(file_path).is_non_empty_file()


def remove_file_safe(fname):
	"""
	Remove a file or link if it exists
	:param fname: the path of the file/link to delete
	:type fname: str
	:return: True or False
	:rtype: bool
	"""
	return Path(fname).remove_file_safe()


def auto_symlink(target, holder):
	"""
	Make a soft-link and overwrite any previously existing file (be careful !) or link with the same name
	:param target: target path of the link
	:type target: str
	:param holder: path of the link holder
	:type holder: str
	"""
	return Path(target).auto_symlink(holder)
