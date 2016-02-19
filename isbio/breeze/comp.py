from models import Report, DataSet
from django.conf import settings
from os.path import isdir, exists, dirname

# This module contains hacks/fixes for backward/forward compatibility


class Trans:
	"""
	Translate property names for Jobs and Reports to a unified model.
	Used in manager to access similar properties from both Jobs and Reports using the same name
	"""
	def __init__(self, *args, **kwargs):
		self._translate(*args, **kwargs)

	translation = {
		'name': '_name', 'jname': '_name',
		'description': '_description', 'jdetails': '_description',
		'author': '_author', 'juser': '_author',
		'type': '_type', 'script': '_type',
		'created': '_created', 'staged': '_created',
		'breeze_stat': '_breeze_stat', 'status': '_status',
		'rexec': '_rexec', 'rexecut': '_rexec',
		'dochtml': '_doc_ml', 'docxml': '_doc_ml', 'doc_ml': '_doc_ml',
		'institute': '_institute',
	}

	@staticmethod
	def swap(item):
		a = Trans.has(item)
		if a is not None:
			return a
		return item

	@staticmethod
	def has(item):
		if isinstance(item, str) and item != '':
			text = item
			if text.endswith('_id'): # for ForeignKeys
				text = text[:-3]
			for key in Trans.translation.keys():
				if text.startswith(key) or text.startswith('-' + key):
					item = item.replace(key, Trans.translation[key])
					return item
		return None

	def _translate(self, args, kwargs):
		new_arg = list(args)
		for pos, el in enumerate(new_arg):
			new_key = self.has(el)
			if new_key is not None:
				new_arg[pos] = new_key
		new_arg = tuple(new_arg)

		for key in kwargs.keys():
			new_key = self.has(key)
			if new_key is not None:
				kwargs[new_key] = kwargs[key]
				del kwargs[key]
		self.args, self.kwargs = new_arg, kwargs

	def get(self):
		return self.args, self.kwargs


def translate(args, kwargs):
	return Trans(args, kwargs).get()

#
# LEGACY CODE FOLLOWING
#


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
	if fname is None: fname = '%s.html' % Report.REPORT_FILE_NAME

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
def get_report_path_test(f_item, fname=None, no_fail=False):
	"""
	:param f_item: a Report.objects from db
	:type f_item: Report or DataSet
	:param fname: a specified file name (optional, default is report.html)
	:type fname: str
	:return: (old_local_path, path_to_file, file_exists, dir_exists)
	:rtype: (str, str, str, str)
	"""

	if fname is None:
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
