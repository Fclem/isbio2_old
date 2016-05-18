from django.conf import settings
from datetime import datetime
from multipledispatch import dispatch # enables method overloading
from breeze.b_exceptions import *
from utilities import *

# 01/04/2016 : Moved all non-Django related code to utilities package


# 25/06/2015 Clem
def console_print(text, date_f=None):
	print console_print_sub(text, date_f=date_f)


def console_print_sub(text, date_f=None):
	return "[%s] %s" % (date_t(date_f), text)


# 10/03/2015 Clem / ShinyProxy
def date_t(date_f=None, time_stamp=None):
	if date_f is None:
		date_f = settings.USUAL_DATE_FORMAT
	if not time_stamp:
		date = datetime.now()
	else:
		date = datetime.fromtimestamp(time_stamp)
	return str(date.strftime(date_f))


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
	if destination not in settings.FOLDERS_LST:
		if os.path.isdir(source):
			if os.path.isdir(destination):
				log_txt = 'copytree, destination folder %s exists, proceed' % destination
				get_logger().warning(log_txt)
			custom_copytree(source, destination, symlinks, ignore)
			return True
		else:
			log_txt = 'copytree, source folder %s don\'t exists, STOP' % source
			get_logger().warning(log_txt)
	else:
		log_txt = 'attempting to copy to a system folder : %s, STOP' % destination
		get_logger().exception(log_txt)
	return False


# clem 09/10/2015
def saved_fs_state():
	""" Read the saved file system FS_LIST_FILE descriptor and chksums list and return the contained JSON object
	"""
	from django.utils import simplejson
	with open(settings.FS_LIST_FILE) as f:
		return simplejson.load(f)


# clem 09/10/2015
def fix_file_acl_interface(fid):
	""" Resolves the file designed by <i>fid</i> (for safety) and fix it's access permisions
	:type fid: int
	:rtype: bool
	"""
	# from os.path import join
	saved_state = saved_fs_state()

	if type(fid) != int:
		fid = int(fid)

	for each in saved_state:
		ss = saved_state[each]
		for file_n in ss:
			if ss[file_n][2] == fid:
				path = join(each, file_n)
				return set_file_acl(path)

	return False

# TODO : Review and move
@dispatch(basestring)
def file_mod_time(path):
	from os.path import getmtime # , join

	return getmtime(path)


@dispatch(basestring, basestring)
def file_mod_time(dirName, fname):
	from os.path import join

	return file_mod_time(join(dirName, fname))


def norm_proj_p(path, repl=''):
	"""
	:type path: str
	:type repl: str
	:rtype: str
	"""
	return path.replace(settings.PROJECT_FOLDER_PREFIX, repl)


def get_r_package(name=''):
	# TEST function for R lib retrieval
	from cran_old import CranArchiveDownloader
	if name:
		cran = CranArchiveDownloader(name)
		if cran.find() and cran.download():
			return cran.extract_to()
	return False





