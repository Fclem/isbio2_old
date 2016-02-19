from models import Report, DataSet
from django.conf import settings
from os.path import isdir, exists, dirname


# This module contains LEGACY code for backward/forward compatibility
# This should be re-writen at some point


# Used to check for missing reports, following lost report event
def get_report_path(f_item, fname=None):
	"""
		Return the path of an object, and checks that the path is existent or fail with 404
		:param f_item: a Report.objects from db
		:type f_item: Report or DataSet
		:param fname: a specified file name (optional, default is report.html)
		:type fname: str
		:return: (local_path, path_to_file)
		:rtype: (str, str)
	"""
	from django.http import Http404
	assert isinstance(f_item, (Report, DataSet))
	error_msg = ''
	if fname is None:
		fname = '%s.html' % Report.REPORT_FILE_NAME

	if isinstance(f_item, DataSet):
		home = f_item.rdata
	else:
		home = f_item.home_folder_rel
	local_path = home + '/' + unicode.replace(unicode(fname), '../', '')
	path_to_file = str(settings.MEDIA_ROOT) + local_path

	# hack to access reports that were generated while dev was using prod folder
	if not exists(path_to_file) and settings.DEV_MODE:
		dir_exists = isdir(dirname(path_to_file))
		error_msg = 'File ' + str(path_to_file) + ' NOT found. The folder ' + (
			'DO NOT ' if not dir_exists else ' ') + 'exists.'
		path_to_file = str(settings.MEDIA_ROOT).replace('-dev', '') + local_path

	if not exists(path_to_file):
		dir_exists = isdir(dirname(path_to_file))
		raise Http404(error_msg + '<br />\n' + 'File ' + str(path_to_file) + ' NOT found. The folder ' + (
			'DO NOT ' if not dir_exists else ' ') + 'exists.')

	return local_path, path_to_file


# Used to check for missing reports, following lost report event
def get_report_path_test(f_item, fname=''):
	"""
	:param f_item: a Report.objects from db
	:type f_item: Report or DataSet
	:param fname: a specified file name (optional, default is report.html)
	:type fname: str
	:return: (old_local_path, path_to_file, file_exists, dir_exists)
	:rtype: (str, str, str, str)
	"""

	if not fname:
		fname = '%s.html' % Report.REPORT_FILE_NAME
	local_path = f_item.home_folder_rel + '/' + unicode.replace(unicode(fname), '../', '') # safety
	path_to_file = str(settings.MEDIA_ROOT) + local_path

	file_exists = exists(path_to_file)
	dir_exists = isdir(dirname(path_to_file))

	old_local_path = dirname(str(settings.MEDIA_ROOT) + local_path)

	# hack to access reports that were generated while dev was using prod folder
	if not (dir_exists and file_exists) and settings.DEV_MODE:
		path_to_file = str(settings.MEDIA_ROOT).replace('-dev', '') + local_path
		old_local_path = (old_local_path, dirname(path_to_file))
		file_exists = exists(path_to_file)
		dir_exists = isdir(dirname(path_to_file))

	return old_local_path, path_to_file, file_exists, dir_exists
