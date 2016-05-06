from django.conf import settings
from datetime import datetime
from utilities import *

# 01/04/2016 : Moved all non-Django related code to utilities package


# 25/06/2015 Clem
def console_print(text, date_f=None):
	print console_print_sub(text, date_f=date_f)


def console_print_sub(text, date_f=None):
	return "[%s] %s" % (date_t(date_f), text)


# 10/03/2015 Clem / ShinyProxy
def date_t(date_f=None):
	if date_f is None:
		date_f = settings.USUAL_DATE_FORMAT
	return str(datetime.now().strftime(date_f))


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
def safe_copytree(source, destination, symlinks=True, ignore=None, force=False):
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
	# import shutil
	if destination not in settings.FOLDERS_LST:
		if os.path.isdir(source):
			if os.path.isdir(destination):
			# 	os.mkdir(destination)
			# else:
				log_txt = 'copytree, destination folder %s exists, proceed' % destination
				get_logger().warning(log_txt)
			# shutil.copytree(source, destination, symlinks, ignore)
			custom_copytree(source, destination, symlinks, ignore, verbose=True)
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


# clem 06/05/2016
def gen_file_from_template(template_path, sub_dict, output_path=None, safe=True):
	"""
	generate a content from a template

	:param template_path: the path of the template file to use
		(c.f. https://docs.python.org/2.7/library/string.html#string.Template )
	:type template_path: str or unicode
	:param sub_dict: the substitution dictionary to use. Keys are used to match the $-var in the template
	:type sub_dict: dict
	:param output_path: the full path (including file name) where to save the output to. If None, then the
		result is returned
	:type output_path: basestring or None
	:param safe: If True, the sub-engine will not raise error for non-matched $-keys
	:type safe: bool
	:return: Either a success flag is output_path was provided, or the result of the replacement if successful, or False
	:rtype: bool or basestring
	"""
	from os.path import exists
	assert isinstance(template_path, (str, unicode))
	assert exists(template_path)
	assert output_path is None or isinstance(output_path, (str, unicode))
	assert isinstance(sub_dict, dict)

	from string import Template

	# load the template
	with open(template_path) as template_fd:
		src = Template(template_fd.read())

	# do the substitution
	result = src.safe_substitute(sub_dict) if safe else src.substitute(sub_dict)

	if output_path:
		with open(output_path, 'w') as output_fd:
			# writes the result to the output file
			while output_fd.write(result):
				pass
		return True
	return result
