import drmaa
from django.template.defaultfilters import slugify
from django.db.models.fields.related import ForeignKey
from django.contrib.auth.models import User # as DjangoUser
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from breeze import managers, utils
from breeze.comp import Trans
from utils import *
from os.path import isfile # , isdir, islink, exists, getsize
from django.conf import settings
from django.db import models
# import sys
# from breeze.b_exceptions import *
# from pandas.tslib import re_compile
# from os import symlink
# import os.path
# from operator import isCallable

import system_check

system_check.db_conn.inline_check()

CATEGORY_OPT = (
	(u'general', u'General'),
	(u'visualization', u'Visualization'),
	(u'screening', u'Screening'),
	(u'sequencing', u'Sequencing'),
)

# TODO : move all the logic into objects here


class JobState(drmaa.JobState):
	SUSPENDED = 'suspended'
	PENDING = 'pending'
	TRANSFERRING = 'transferring'
	ON_HOLD = 'pending'
	ERROR_Q_WAIT = 'qw_error'

	@staticmethod
	def R_FAILDED():
		pass


JOB_PS = {
	'': JobState.UNDETERMINED,
	'r': JobState.RUNNING,
	't': JobState.TRANSFERRING,
	'p': JobState.PENDING,
	'qw': JobState.QUEUED_ACTIVE,
	'Eqw': JobState.ERROR_Q_WAIT,

	'h': JobState.ON_HOLD,
	'ho': JobState.SYSTEM_ON_HOLD,
	'hs': JobState.SYSTEM_ON_HOLD,
	'hd': JobState.SYSTEM_ON_HOLD,
	'hu': JobState.USER_ON_HOLD,
	'hus': JobState.USER_SYSTEM_ON_HOLD,

	's': JobState.SUSPENDED,
	'ss': JobState.SYSTEM_SUSPENDED,
	'su': JobState.USER_SUSPENDED,
	'us': JobState.USER_SUSPENDED,
	'sus': JobState.USER_SYSTEM_SUSPENDED,
}


# 30/06/2015 & 10/07/2015
class JobStat(object):
	"""
	Has all the job status logic for updates (except concerning aborting).
	Some of the logic regarding requests, lies in WorkersManager
	DB use 2 different fields :
	_ status : store the sge actual status
	_ breeze_stat : store the current state of the job to be reported
	This is kind of messy, but work well
	"""
	RUN_WAIT = 'run_wait'
	ABORT = 'abort'
	ABORTED = 'aborted'
	RUNNING = JobState.RUNNING
	DONE = JobState.DONE
	SCHEDULED = 'scheduled'
	FAILED = JobState.FAILED
	QUEUED_ACTIVE = JobState.QUEUED_ACTIVE
	INIT = 'init'
	SUCCEED = 'succeed'
	SUBMITTED = 'submitted'
	PREPARE_RUN = 'prep_run'
	R_FAILED = JobState.R_FAILDED

	__decode_status = {
		JobState.UNDETERMINED: 'process status cannot be determined',
		JobState.QUEUED_ACTIVE: 'job is queued and active',
		JobState.SYSTEM_ON_HOLD: 'job is queued and in system hold',
		JobState.USER_ON_HOLD: 'job is queued and in user hold',
		JobState.USER_SYSTEM_ON_HOLD: 'job is queued and in user and system hold',
		JobState.RUNNING: 'job is running',
		JobState.SYSTEM_SUSPENDED: 'job is system suspended',
		JobState.USER_SUSPENDED: 'job is user suspended',
		JobState.DONE: 'job finished normally',
		SUCCEED: 'job finished normally',
		JobState.FAILED: 'job finished, but SGE failed',
		JobState.R_FAILDED: 'job finished but R script failed',
		ABORTED: 'job has been aborted',
		ABORT: 'job is being aborted...',
		INIT: 'job instance is being generated...',
		SCHEDULED: 'job is saved for later submission',
		PREPARE_RUN: 'job is being prepared for submission',
		SUBMITTED: 'job has been submitted, and should be running soon',
		RUN_WAIT: 'job is about to be submitted',
		'': 'unknown/other'
	}

	@staticmethod
	def _progress_level(stat):
		"""
		Return the progression value associated with a specific status
		:param stat:
		:type stat: str or Exception
		:return: progress value
		:rtype: int
		"""
		# if isinstance(stat,
		# 			(drmaa.AlreadyActiveSessionException, drmaa.InvalidArgumentException, drmaa.InvalidJobException)):
		# 	return 67
		# elif stat is Exception:
		if stat is Exception:
			return 66
		elif stat == JobStat.SCHEDULED:
			return 2
		elif stat == JobStat.INIT:
			return 4
		elif stat == JobStat.RUN_WAIT:
			return 8
		elif stat in JobStat.PREPARE_RUN:
			return 15
		elif stat == JobStat.QUEUED_ACTIVE:
			return 30
		elif stat == JobStat.SUBMITTED:
			return 20
		elif stat == JobStat.RUNNING:
			return 55
		elif stat in (JobStat.FAILED, JobStat.SUCCEED, JobStat.DONE):
			return 100
		else:
			# return self.progress
			return None

	def status_logic(self):
		return self.status_logic_arg(self._init_stat)

	def status_logic_arg(self, status):
		"""
		Return relevant the relevant status, breeze_stat, progress and text display of current status code
		:param status: a JobStat constant
		:type status: str
		:return: status, breeze_stat, progress, textual(status)
		:rtype: str, str, int, str
		"""
		progress = self._progress_level(status) # progression %
		if status == JobStat.ABORTED:
			self.status, self.breeze_stat = JobStat.ABORTED, JobStat.DONE
		elif status == JobStat.ABORT:
			self.status, self.breeze_stat = JobStat.ABORTED, JobStat.ABORT
		elif status == JobStat.PREPARE_RUN:
			self.status, self.breeze_stat = JobStat.INIT, JobStat.PREPARE_RUN
		elif status == JobStat.QUEUED_ACTIVE:
			self.status, self.breeze_stat = JobStat.QUEUED_ACTIVE, JobStat.RUNNING
		elif status == JobStat.INIT:
			self.status, self.breeze_stat = JobStat.INIT, JobStat.INIT
		elif status == JobStat.SUBMITTED:
			# self.status remains unchanged
			self.breeze_stat = JobStat.SUBMITTED
		elif status == JobStat.FAILED:
			self.status, self.breeze_stat = JobStat.FAILED, JobStat.DONE
		elif status == JobStat.RUN_WAIT:
			self.status, self.breeze_stat = JobStat.INIT, JobStat.RUN_WAIT
		elif status == JobStat.RUNNING:
			self.status, self.breeze_stat = JobStat.RUNNING, JobStat.RUNNING
		elif status == JobStat.DONE:
			# self.status remains unchanged (because it could be failed, succeed or aborted)
			self.breeze_stat = JobStat.DONE
		elif status == JobStat.SUCCEED:
			self.status, self.breeze_stat = JobStat.SUCCEED, JobStat.DONE
		elif status == JobStat.SCHEDULED:
			self.status, self.breeze_stat = JobStat.SCHEDULED, JobStat.SCHEDULED
		else:
			self.status = status
		self.stat_text = self.textual(status) # clear text status description

		return self.status, self.breeze_stat, progress, self.stat_text

	def __init__(self, status):
		self._init_stat = None
		self.status = None
		self.breeze_stat = None
		self.stat_text = ''
		if status in self.__decode_status.keys():
			self._init_stat = status
			self.status_logic()
		else:
			raise InvalidArgument

	@staticmethod
	def textual(stat, obj=None):
		"""
		Return string representation of current status
		:param stat: current status
		:type stat: str
		:return: string representation of current status
		:rtype: str
		"""
		if stat == JobStat.FAILED:
			if isinstance(obj, Runnable) and obj.is_r_failure:
				stat = JobStat.R_FAILED
		if stat in JobStat.__decode_status:
			return JobStat.__decode_status[stat]
		else:
			return 'unknown status'

	def __str__(self):
		return self.stat_text


class FolderObj(object):
	BASE_FOLDER_NAME = None # To define
	SYSTEM_FILES = [] # list of system files, that are required by the object
	HIDDEN_FILES = [] # list of file to hide from user upon download
	ALLOW_DOWNLOAD = False # if users can download content of object

	@property # interface (To define)
	def folder_name(self):
		"""
		Should implement a property generating the name of the folder to store the instance
		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		raise self.not_imp()

	@property
	def home_folder_rel(self):
		"""
		Returns the relative path to this object folder
		:return: the relative path to this object folder
		:rtype: str
		"""
		if self.BASE_FOLDER_NAME is None:
			raise NotDefined("BASE_FOLDER_NAME was not implemented in concrete class %s." % self.__class__.__name__)
		if self.folder_name is None or self.folder_name == '':
			raise NotDefined("folder_name is empty for %s." % self)
		return '%s%s/' % (self.BASE_FOLDER_NAME, slugify(self.folder_name))

	@property
	def home_folder_full_path(self):
		"""
		Returns the absolute path to this object folder
		:return: the absolute path to this object folder
		:rtype: str
		"""
		return '%s%s' % (settings.MEDIA_ROOT, self.home_folder_rel)

	@property
	def base_folder(self):
		return '%s%s' % (settings.MEDIA_ROOT, self.BASE_FOLDER_NAME)

	def move(self, target):
		# if os.path.is_dir(target) or os.makedirs(target):
		try:
			return utils.safe_copytree(self.home_folder_full_path, target, force=True)
		except Exception:
			return False

	@staticmethod
	def file_n_slug(file_name):
		"""
		Slugify filenames, saving the . if exists, and leading path
		:type file_name: str
		:rtype: str
		"""
		# print 'fn before', file_name # TODO del
		import os
		dir_n = os.path.dirname(file_name)
		base = os.path.basename(file_name)
		if '.' in base:
			base = os.path.splitext(base)
			f_name = '%s.%s' % (slugify(base[0]), slugify(base[1]))
		else:
			f_name = slugify(base)

		# print 'fn after', '%s%s' % (Path(dir_n), f_name) # TODO del
		return '%s%s' % (Path(dir_n), f_name)

	def file_name(self, filename):
		"""
		Special property
		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		return self.home_folder_full_path + self.file_n_slug(filename)
		# return self._home_folder_rel + self.file_n_slug(filename)

	def grant_write_access(self):
		"""
		Make the home folder writable for group
		"""
		import os
		import stat
		# open home's folder for others
		# st = os.stat(self.home_folder_full_path)
		# os.chmod(self.home_folder_full_path, st.st_mode | stat.S_IRWXG)

	def add_file(self, f):
		"""
		write a file object at a specific location and return the slugified name
		:type f: file
		:rtype: str
		"""
		import os
		a_dir = self.home_folder_full_path
		if not os.path.exists(a_dir):
			os.makedirs(a_dir)

		f.name = self.file_n_slug(f.name)
		with open(os.path.join(a_dir, f.name), 'wb+') as destination:
			for chunk in f.chunks():
				destination.write(chunk)
		return f.name

	@property # PSEUDO-INTERFACE
	def system_files(self):
		return self.SYSTEM_FILES

	@property # PSEUDO-INTERFACE
	def hidden_files(self):
		return self.HIDDEN_FILES

	# clem 02/10/2015
	def _download_ignore(self, cat=None):
		"""
		Should return two list of filters, and a name related to cat :
			_ files to include only,
			_ files to exclude,
			_ name to add to the downloadable zip file name
		:return: exclude_list, filer_list, name
		:rtype: list, list, str
		"""
		raise self.not_imp()

	# clem 02/10/2015
	# TODO : download with no subdirs
	def download_zip(self, cat=None, auto_cache=True):
		""" Compress the folder object for download
		<i>cat</i> argument enables to implement different kind of selective downloads into <i>download_ignore(cat)</i>
		auto_cache determine if generated zip should be saved for caching purposes

		Returns
			_ a zip file using <i>download_ignore(cat)</i> as  a filtering function, in a Django FileWrapper
			_ the name of the generated file
			_ the size of the generated file

		Return : Tuple(wrapper, file_name, file_size)
		:type cat : str
		:type auto_cache : bool
		:return: wrapper of zip object, file name, file size
		:rtype: FileWrapper, str, int
		"""
		if not self.ALLOW_DOWNLOAD:
			raise PermissionDenied
		import tempfile
		import zipfile
		import os
		from django.core.servers.basehttp import FileWrapper
		loc = self.home_folder_full_path # writing shortcut
		arch_name = str(self.folder_name)

		ignore_list, filter_list, sup = self._download_ignore(cat)
		arch_name += sup
		# check if cache folder exists
		if not os.path.isdir(os.path.join(self.base_folder, '_cache')):
			os.mkdir(os.path.join(self.base_folder, '_cache'))
		# full path to cached zip_file
		cached_file_full_path = os.path.join(self.base_folder, '_cache', arch_name + '.zip')
		# if cached zip file exists, send it instead
		if os.path.isfile(cached_file_full_path):
			return open(cached_file_full_path, "rb"), arch_name, os.path.getsize(cached_file_full_path)
		# otherwise, creates a new zip
		temp = tempfile.TemporaryFile()
		archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)

		def filters(file_n, a_pattern_list):
			return not a_pattern_list or file_inter_pattern_list(file_n, a_pattern_list)

		def no_exclude(file_n, a_pattern_list):
			return not a_pattern_list or not file_inter_pattern_list(file_n, a_pattern_list)

		def file_inter_pattern_list(file_n, a_pattern_list):
			""" Returns if <i>file_n</i> is match at least one pattern in <i>a_pattern_list</i>
			"""
			import fnmatch
			for each in a_pattern_list:
				if fnmatch.fnmatch(file_n, each):
					return True
			return False
		# walks loc to add files and folder to archive, while allying filters and exclusions
		try:
			for root, dirs, files in os.walk(loc):
				for name in files:
					if filters(name, filter_list) and no_exclude(name, ignore_list):
						new_p = os.path.join(root, name)
						name = new_p.replace(loc, '')
						# print new_p, name
						archive.write(new_p, str(name))
		except OSError as e:
			print 'OSError', e
			raise OSError(e)

		archive.close()
		wrapper = FileWrapper(temp)
		size = temp.tell()
		# save this zipfile for caching (disalbe to save space vs CPU)
		temp.seek(0)
		if auto_cache:
			with open(cached_file_full_path, "wb") as f: # use `wb` mode
				f.write(temp.read())
			temp.seek(0)

		return wrapper, arch_name, size

	def not_imp(self):
		if self.__class__ == Runnable.__class__:
			raise NotImplementedError("Class % doesn't implement %s, because it's an abstract/interface class." % (
				self.__class__.__name__, sys._getframe(1).f_code.co_name))
		else:
			raise NotImplementedError("%s was not implemented in concrete class %s." % (
				sys._getframe(1).f_code.co_name, self.__class__.__name__))

	def delete(self, using=None):
		safe_rm(self.home_folder_full_path)
		super(FolderObj, self).delete(using=using)
		return True

	class Meta:
		abstract = True


# 04/06/2015
class OrderedUser(User):
	class Meta:
		ordering = ["username"]
		proxy = True


class Post(models.Model):
	author = ForeignKey(User)
	title = models.CharField(max_length=150)
	body = models.TextField(max_length=3500)
	time = models.DateTimeField(auto_now_add=True)
	
	def __unicode__(self):
		return self.title


class Institute(models.Model):
	institute = models.CharField(max_length=75, default='FIMM')
	
	def __unicode__(self):
		return self.institute


class Project(models.Model):
	name = models.CharField(max_length=50, unique=True)
	manager = models.CharField(max_length=50)
	pi = models.CharField(max_length=50)
	author = ForeignKey(User)
	# store the institute info of the user who creates this report
	institute = ForeignKey(Institute, default=Institute.objects.get(id=1))
	
	collaborative = models.BooleanField(default=False)
	
	wbs = models.CharField(max_length=50, blank=True)
	external_id = models.CharField(max_length=50, blank=True)
	description = models.CharField(max_length=1100, blank=True)
	
	def __unicode__(self):
		return self.name


class Group(models.Model):
	name = models.CharField(max_length=50, unique=True)
	author = ForeignKey(User)
	team = models.ManyToManyField(User, null=True, blank=True, default=None, related_name='group_content')

	def delete(self):
		self.team.clear()

	def __unicode__(self):
		return self.name


def shiny_header():
	fileh = open(str(settings.SHINY_REPORT_TEMPLATE_PATH + settings.SHINY_HEADER_FILE_NAME))
	return str(fileh.read())


# 17/06/2015
def shiny_loader():
	fileh = open(str(settings.SHINY_REPORT_TEMPLATE_PATH + settings.SHINY_LOADER_FILE_NAME))
	return str(fileh.read())


# 17/06/2015
def shiny_files():
	fileh = open(str(settings.SHINY_REPORT_TEMPLATE_PATH + settings.SHINY_FILE_LIST))
	return str(fileh.read())


# 08/06/2015
class ShinyReport(models.Model):
	FILE_UI_NAME = settings.SHINY_UI_FILE_NAME
	FILE_SERVER_NAME = settings.SHINY_SERVER_FILE_NAME
	# FILE_DASH_UI = settings.SHINY_DASH_UI_FN
	# FILE_DASH_SERVER = settings.SHINY_DASH_SERVER_FN
	FILE_HEADER_NAME = settings.SHINY_HEADER_FILE_NAME
	FILE_GLOBAL = settings.SHINY_GLOBAL_FILE_NAME
	FILE_LIST = settings.SHINY_FILE_LIST
	# FILE_LOADER = settings.SHINY_LOADER_FILE_NAME
	# SERVER_FOLDER = settings.SHINY_SERVER_FOLDER
	# UI_FOLDER = settings.SHINY_UI_FOLDER
	RES_FOLDER = settings.SHINY_RES_FOLDER
	SHINY_REPORTS = settings.SHINY_REPORTS
	REPORT_TEMPLATE_PATH = settings.SHINY_REPORT_TEMPLATE_PATH
	SYSTEM_FILE_LIST = [FILE_UI_NAME, FILE_SERVER_NAME, FILE_GLOBAL, FILE_HEADER_NAME, RES_FOLDER, RES_FOLDER[:-1]]
	# FS_ACL = 0775
	FS_ACL = ACL.RWX_RX_
	FS_REMOTE_ACL = ACL.RWX_RX_

	title = models.CharField(max_length=55, unique=True, blank=False, help_text="Choose a title for this Shiny Report")
	description = models.CharField(max_length=350, blank=True, help_text="Optional description text")
	author = ForeignKey(User)
	created = models.DateTimeField(auto_now_add=True)
	institute = ForeignKey(Institute, default=Institute.objects.get(id=1))

	custom_header = models.TextField(blank=True, default=shiny_header(),
		help_text="Use R Shiny code here to customize the header of the dashboard<br />"
		"Here is a basic example of what you can do.<br />\n"
		"For more information, please refer to Shiny documentation.")

	custom_loader = models.TextField(blank=True, default=shiny_loader(),
		help_text="Use R Shiny code here to customize the global server part of the "
		"dashboard<br />This is usefull to load files, or declare variables "
		"that will be accessible to each attached tags:<br />NB : you may "
		"reference, in the next field, every file you use here. Use a $ to "
		"reference your file according to the 'tname' you associated with it.")

	custom_files = models.TextField(blank=True, default=shiny_files(),
		help_text="Use the following JSON format to reference your files<br />This "
		"enables Breeze to dynamically check for the files you marked as "
		"required.<br />")

	enabled = models.BooleanField(default=True)

	@property
	def get_name(self):
		return slugify(str(self.title))

	@property
	def __folder_path_remote(self):
		return str('%s%s/app/' % (settings.SHINY_REMOTE_REPORTS_INTERNAL, self.get_name))

	def __folder_path_base_gen(self, remote=False):
		return str('%s%s/' % (self.SHINY_REPORTS if not remote else settings.SHINY_REMOTE_REPORTS, self.get_name))

	@property
	def _folder_path_base(self):
		return self.__folder_path_base_gen()

	def __folder_path_gen(self, remote=False):
		return str('%sapp/' % self.__folder_path_base_gen(remote))

	@property
	def folder_path(self):
		return self.__folder_path_gen()

	def server_path(self, remote=False):
		return str('%s%s' % (self.__folder_path_gen(remote), self.FILE_SERVER_NAME))

	def ui_path(self, remote=False):
		return str('%s%s' % (self.__folder_path_gen(remote), self.FILE_UI_NAME))

	def global_path(self, remote=False):
		return str('%s%s' % (self.__folder_path_gen(remote), self.FILE_GLOBAL))

	def res_folder_path(self, remote=False):
		return str('%s%s' % (self.__folder_path_gen(remote), self.RES_FOLDER))

	# path_template_folder = REPORT_TEMPLATE_PATH
	path_server_r_template = REPORT_TEMPLATE_PATH + FILE_SERVER_NAME
	path_ui_r_template = REPORT_TEMPLATE_PATH + FILE_UI_NAME
	path_global_r_template = REPORT_TEMPLATE_PATH + FILE_GLOBAL
	# path_heade_r_template = REPORT_TEMPLATE_PATH + FILE_HEADER_NAME
	# path_global_r_template = REPORT_TEMPLATE_PATH + FILE_GLOBAL
	# path_loader_r_template = str(REPORT_TEMPLATE_PATH + FILE_LOADER)
	# path_file_lst_template = str(REPORT_TEMPLATE_PATH + FILE_LIST)
	# path_dash_ui_r_template = REPORT_TEMPLATE_PATH + FILE_DASH_UI
	# path_dash_server_r_template = REPORT_TEMPLATE_PATH + FILE_DASH_SERVER

	# TODO rework the next 3 functions
	@property
	def shiny_mode(self):
		if self.shiny_remote_ok:
			return 'remote'
		elif self.shiny_local_ok:
			return 'local'

	@property
	def shiny_remote_ok(self):
		return settings.SHINY_REMOTE_ENABLE and settings.SHINY_MODE == 'remote'

	@property
	def shiny_local_ok(self):
		return settings.SHINY_LOCAL_ENABLE and settings.SHINY_MODE == 'local'

	def url(self, report, force_remote=False, force_local=False):
		assert isinstance(report, Report)
		if force_remote or self.shiny_remote_ok and not force_local:
			return '%s%s/' % (settings.SHINY_TARGET_URL, report.shiny_key)
		elif self.shiny_local_ok:
			from django.core.urlresolvers import reverse
			from views import report_shiny_in_wrapper
			return reverse(report_shiny_in_wrapper, kwargs={ 'rid': report.id })

	@property # relative path to link holder directory
	def _link_holder_rel_path(self):
		# the point of this property, is that you can change the folder structure by only changing this
		return '%s/lnk' % self.get_name

	def _link_holder_path(self, remote=False): # full path to lnk holder directory
		return '%s%s/' % (self.SHINY_REPORTS if not remote else settings.SHINY_REMOTE_REPORTS, self._link_holder_rel_path)

	def report_link_rel_path(self, data):
		"""
		Return the path to the symlink file to the actual report WITHOUT a trailing /
		:param data: a valid Report id
		:return: path to the symlink file to the actual report WITHOUT a trailing /
		:rtype: str
		"""
		return '%s/%s' % (self._link_holder_rel_path, data)

	def report_link(self, data, rel=False, remote=False):
		if rel:
			return self.report_link_rel_path(data)
		return '%s%s' % (self.SHINY_REPORTS if not remote else settings.SHINY_REMOTE_REPORTS, self.report_link_rel_path(data))

	# Clem 22/09/2015
	@staticmethod
	def check_csc_mount():
		from system_check import check_csc_mount
		return check_csc_mount()

	# Clem 05/10/2015
	@staticmethod
	def remote_shiny_ready():
		return settings.SHINY_REMOTE_ENABLE and ShinyReport.check_csc_mount()

	# Clem 23/09/2015
	@property # may be dynamic in the future and return if this very report should go to remote Shiny
	def make_remote_too(self):
		"""
		If remote Shiny report should be generated, if SHINY_REMOTE_ENABLE and CSC FS is mounted
		:return:
		:rtype:
		"""
		return self.remote_shiny_ready()

	def update_folder(self):
		"""
		Creates the directory structure, removing any previously existing content,
		creates sever and ui sub-folders and link server and ui dashboard 'tag'
		Handles both local and remote Shiny
		"""
		# import os.path
		from os import mkdir

		if settings.SHINY_LOCAL_ENABLE:
			safe_rm(self._folder_path_base, ignore_errors=True)
			mkdir(self._folder_path_base, self.FS_ACL)
			mkdir(self._link_holder_path(), self.FS_ACL)
			mkdir(self.folder_path, self.FS_ACL)
			mkdir('%s%s/' % (self.folder_path, self.RES_FOLDER), self.FS_ACL)

		if self.make_remote_too:
			safe_rm(self.__folder_path_base_gen(True), ignore_errors=True)
			mkdir(self.__folder_path_base_gen(True), self.FS_REMOTE_ACL)
			mkdir(self.report_link('', remote=True), self.FS_REMOTE_ACL)
			mkdir(self.__folder_path_gen(True), self.FS_REMOTE_ACL)
			mkdir('%s%s/' % (self.__folder_path_gen(True), self.RES_FOLDER), self.FS_REMOTE_ACL)

	def _link_all_reports(self, force=False):
		"""
		Triggers the linking of each Reports that exists of every attached ReportType
		Handle both local and remote Shiny
		:param force: force linking of each Reports, even if files are missing, or the link already existent
		:type force: bool
		"""
		has_remote = self.make_remote_too
		if ReportType.objects.filter(shiny_report=self).count() > 0: # if attached to any Report
			for rtype in ReportType.objects.filter(shiny_report=self):
				for report in Report.objects.f.get_done(False, False).filter(type=rtype):
					if True: # report.is_r_successful:
						self.link_report(report, force, has_remote)

	# Clem 24/09/2015
	def _remote_ignore_wrapper(self, report):
		"""
		return the remote_ignore with specific report context to be called by copythree
		:type report: Report
		:rtype: callable()
		"""
		assert isinstance(report, Report)

		def remote_ignore(_, names):
			"""
			:type names: str
			:rtype: list
			Return a list of files to ignores amongst names
			"""
			import fnmatch
			ignore_list = self.SYSTEM_FILE_LIST + report.hidden_files
			# print names
			out = list()
			for each in names:
				#if each in ignore_list or each[:-1] == '~' or fnmatch.fnmatch():
				if each[:-1] == '~':
					out.append(each)
				else:
					for ignore in ignore_list:
						if fnmatch.fnmatch(each, ignore):
							out.append(each)
							break
			# print out
			return out

		return remote_ignore

	def link_report(self, report, force=False, remote_too=False):
		"""
		Link a standard report to this ShinyReport using soft-links. (updates or creates linking)
		If the ShinyReport skeleton has previously been generated,
			this step is enough to enable a report to be visualized through Shiny
		Handle both local and remote Shiny (with remote_too = True)
		:param report: a valid Report instance
		:type report: Report
		:param force: force linking even if files are missing, or the link already existent
		:type force: bool
		"""
		log_obj = get_logger()
		log_obj.debug(
			"updating shinyReport %s-%s slink for report %s %s" % (self.get_name, self.id, report.id, 'FORCING' if force else ''))

		from os.path import isdir, isfile, islink
		from os import listdir, access, R_OK #, mkdir

		assert isinstance(report, Report)
		# handles individually each generated report of this type
		report_home = report.home_folder_full_path
		report_link = self.report_link(report.id)
		report_remote_link = self.report_link(report.shiny_key, remote=True) if remote_too else ''
		# if the home folder of the report exists, and the link doesn't yet
		if isdir(report_home[:-1]) and report_home != settings.MEDIA_ROOT:
			# check that the report has all required files
			if not force:
				j = self.related_files()
				for each in j: # for every required registered file
					path = '%s%s' % (report_home, each['path'])
					if each['required'] and not (isfile(path) and access(path, R_OK)):
						log_obj.warning("%s missing required file %s" % (report.id, path))
						return
			# LOCAL make of soft-link for each files/folder of the shinyReport folder into the Report folder
			if settings.SHINY_LOCAL_ENABLE and (force or not islink(report_link)):
				for item in listdir(self.folder_path): # TODO should be recursive ?
					auto_symlink('%s%s' % (self.folder_path, item), '%s%s' % (report_home, item))
				# Creates a slink in shinyReports to the actual report
				auto_symlink(report_home, report_link)
			# REMOTE make of soft-link for each files/folder of the shinyReport folder into the Report folder
			if remote_too and (force or not islink(report_remote_link)):
				# del the remote report copy folder
				safe_rm(report.remote_shiny_path, ignore_errors=True)
				try:
					# copy the data content of the report
					safe_copytree(report.home_folder_full_path, report.remote_shiny_path,
									ignore=self._remote_ignore_wrapper(report))
				except Exception as e:
					log_obj.warning("%s ShinyReport copy error %s" % (report.id, e))

				# link ShinyReport files
				for item in listdir(self.folder_path): # TODO should be recursive ?
					# remove_file_safe('%s%s' % (report.remote_shiny_path, item))
					auto_symlink('%s%s' % (self.__folder_path_remote, item), '%s%s' % (report.remote_shiny_path, item))

				# Creates a slink in shinyReports to the actual report
				auto_symlink(report.remote_shiny_path, report_remote_link)
		else: # the target report is missing we remove the link
			self.unlink_report(report)

	# TODO upgrade to remote shiny
	def unlink_report(self, report, remote=False):
		"""
		Do the opposite of link_report, useful if a specific Report has been individually deleted
		:param report: a valid Report instance
		:type report: Report
		"""
		assert isinstance(report, Report)
		import os
		# handles individually each generated report of this type
		report_home = report.home_folder_full_path
		report_link = self.report_link(report.id)

		# if the home folder of the report exists, and the link doesn't yet
		if os.path.isdir(report_home) and report_home != settings.MEDIA_ROOT:
			# removes the soft-link for each files/folder of the shinyReport folder into the Report folder
			for item in os.listdir(self.folder_path):
				remove_file_safe('%s%s' % (report_home, item)) # TODO check
		if os.path.islink(report_link):
			# removes the slink in shinyReports to the actual report
			remove_file_safe(report_link) # unlink from shiny TODO check

	# TODO upgrade to remote shiny
	def _unlink_all_reports(self, remote=False):
		"""
		Do the opposite of _link_all_reports , usefull if a this ShinyReport has been delete, or unlink from a ReportType
		Triggers the unlinking of each Reports that exists of every attached ReportType
		"""
		if ReportType.objects.filter(shiny_report=self).count() > 0: # if attached to any Report
			for rtype in ReportType.objects.filter(shiny_report=self):
				for report in Report.objects.filter(type=rtype):
					self.unlink_report(report, remote)

	def import_tag_res(self, tag):
		"""
		Import every resources ( www folder) of a specific tag
		:param tag: a valid ShinyTag instance
		:type tag: ShinyTag
		"""
		from distutils.dir_util import copy_tree

		assert isinstance(tag, ShinyTag)
		copy_tree(tag.path_res_folder, self.res_folder_path()) # TODO replace with symlimks ?
		if self.make_remote_too:
			copy_tree(tag.path_res_folder, self.res_folder_path(True)) # TODO replace with symlimks ?

	def related_files(self, formatted=False):
		"""
		Returns a list of related files for the report
		:rtype: dict or list
		"""
		# fixed on 11/09/2015
		# fixed on 18/12/2015
		# TODO check expected behavior regarding templates
		j = list()
		if self.custom_files is not None and self.custom_files != '':
			import json
			log_obj = get_logger()

			try:
				# jfile = open(ShinyReport.path_file_lst_template)
				# j = json.load(jfile)
				j = json.loads(self.custom_files)
				# jfile.close()
			except ValueError as e:
				log_obj.exception(e.message)
				# raise ValueError(e)
			if formatted:
				d = dict()
				for each in j:
					d.update({ each['tname']: each['path'] })
				return d
		return j

	# TODO expired design
	def get_parsed_loader(self):
		from string import Template

		# file_loaders = open(ShinyReport.path_loader_r_template)
		# src = Template(file_loaders.read())
		if self.custom_loader is not None and self.custom_loader!='':
			src = Template(self.custom_loader)
			# file_loaders.close()
			# return src.safe_substitute(ShinyReport.related_files(formatted=True))
			return src.safe_substitute(self.related_files(formatted=True))

	def generate_server(self, a_user=None, remote=False): # generate the report server.R file to include all the tags
		"""
		Handle either LOCAL or REMOTE at once
		:param a_user:
		:type a_user:
		:param remote:
		:type remote:
		:return:
		:rtype:
		"""
		from string import Template
		import auxiliary as aux

		SEP = '\n  '

		if a_user is None or not isinstance(a_user, (User, OrderedUser)):
			a_user = self.author
		# opens server.R template file
		filein = open(self.path_server_r_template)
		src = Template(filein.read())
		# document data
		generated = 'Generated on %s for user %s (%s)' % (self.created, self.author.get_full_name(), self.author)
		updated = 'Last updated on %s for user %s (%s)' % (aux.date_t(), a_user.get_full_name(), a_user)
		alist = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				if each.enabled:
					# add it to the source list
					alist.append('### Tag %s by %s (%s) %s%ssource("%s",local = TRUE)' % (
						each.name, each.author.get_full_name(), each.author, each.created, SEP,
						each.path_dashboard_server(remote)))
				else:
					alist.append('### DISABLED Tag %s by %s (%s) %s' % (
						each.name, each.author.get_full_name(), each.author, each.created))
		loaders = self.get_parsed_loader() # TODO redo
		alist.append('') # avoid join errors if list is empty
		d = { 'title': self.title,
				'generated': generated,
				'updated': updated,
				'loaders': loaders,
				'sources': SEP.join(alist)
			}
		assert (isinstance(src, Template))
		result = src.safe_substitute(d)
		f = open(self.server_path(remote), 'w')
		f.write(result)
		f.close()
		return

	def generate_ui(self, a_user=None, remote=False):  # generate the report ui.R file to include all the tags
		"""
		Handle either LOCAL or REMOTE at once
		:param a_user:
		:type a_user:
		:param remote:
		:type remote:
		:return:
		:rtype:
		"""
		from string import Template
		import auxiliary as aux

		SEP = '\n'
		SEP2 = ',\n  '

		if a_user is None or not isinstance(a_user, (User, OrderedUser)):
			a_user = self.author
		# opens ui.R template file
		filein = open(self.path_ui_r_template)
		src = Template(filein.read())
		filein.close()
		# document data
		generated = 'Generated on %s for user %s (%s)' % (self.created, self.author.get_full_name(), self.author)
		updated = 'Last updated on %s for user %s (%s)' % (aux.date_t(), a_user.get_full_name(), a_user)
		alist = list()
		tag_vars = list()
		menu_list = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				if each.enabled:
					self.import_tag_res(each)
					alist.append('### Tag %s by %s (%s) %s%ssource("%s",local = TRUE)' % (
						each.name, each.author.get_full_name(), each.author, each.created, SEP,
						each.path_dashboard_body(remote)))
					tag_vars.append(each.get_name.upper())
					menu_list.append(each.menu_entry)
				else:
					alist.append('### DISABLED Tag %s by %s (%s) %s' % (
						each.name, each.author.get_full_name(), each.author, each.created))
		alist.append('')
		menu_list.append('')
		d = { 'title': self.title,
				'header': self.custom_header,
				'generated': generated,
				'updated': updated,
				'menu_items': SEP2.join(menu_list),
				'sources': SEP.join(alist),
				'tag_vars': SEP2.join(tag_vars),
			}
		# do the substitution
		result = src.substitute(d)
		f = open(self.ui_path(remote), 'w')
		f.write(result)
		f.close()
		return

	def generate_global(self, a_user=None, remote=False):  # generate the report ui.R file to include all the tags
		"""
		Handle either LOCAL or REMOTE at once
		:param a_user:
		:type a_user:
		:param remote:
		:type remote:
		:return:
		:rtype:
		"""
		from string import Template
		import auxiliary as aux

		SEP = '\n'

		if a_user is None or not isinstance(a_user, (User, OrderedUser)):
			a_user = self.author
		# opens ui.R template file
		filein = open(self.path_global_r_template)
		src = Template(filein.read())
		# document data
		generated = 'Generated on %s for user %s (%s)' % (self.created, self.author.get_full_name(), self.author)
		updated = 'Last updated on %s for user %s (%s)' % (aux.date_t(), a_user.get_full_name(), a_user)
		alist = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				# base, ui_path, _ = self.get_tag_path(each)
				file_glob = open(each.folder_name + self.FILE_GLOBAL)
				alist.append('### from tag %s by %s (%s) %s\n%s' % (
					each.name, each.author.get_full_name(), each.author, each.created, file_glob.read()))
				file_glob.close()
		alist.append('')
		d = { 'generated': generated,
				'updated': updated,
				'tag_global': SEP.join(alist)
			}
		# do the substitution
		result = src.substitute(d)
		f = open(self.global_path(remote), 'w')
		f.write(result)
		f.close()
		return

	# TODO implement a lock mechanism for concurrency safety
	def regen_report(self, a_user=None):
		"""
		Handle BOTH local and remote Shiny at Once
		:param a_user:
		:type a_user:
		:return:
		:rtype:
		"""
		log_obj = get_logger()
		log_obj.info("rebuilding shinyReport %s-%s for user %s" % (self.id, self.get_name, a_user))
		self.update_folder()
		# local : TODO should generate disregarding of local shiny status ?
		if settings.SHINY_LOCAL_ENABLE:
			log_obj.debug("rebuilding LOCAL on shinyReport %s-%s" % (self.id, self.get_name))
			self.generate_server(a_user)
			self.generate_ui(a_user)
			self.generate_global(a_user)
		# remote
		if self.make_remote_too:
			log_obj.debug("rebuilding REMOTE on shinyReport %s-%s" % (self.id, self.get_name))
			self.generate_server(a_user, True)
			self.generate_ui(a_user, True)
			self.generate_global(a_user, True)
		log_obj.debug("re-linking and eventual remote copy on shinyReport %s-%s" % (self.id, self.get_name))
		self._link_all_reports()

	def clean(self):
		pass

	def save(self, *args, **kwargs):
		super(ShinyReport, self).save(*args, **kwargs) # Call the "real" save() method.
		self.regen_report()

	def delete(self, using=None):
		import shutil

		log_obj = get_logger()
		log_obj.info("deleted shinyReport %s : %s" % (self.id, self))
		# unlinking all attached Reports
		self._unlink_all_reports()
		# Deleting the folder
		shutil.rmtree(self._folder_path_base, ignore_errors=True)
		if self.make_remote_too:
			log_obj.info("deleted remote shinyReport %s : %s" % (self.id, self))
			self._unlink_all_reports(True)
			shutil.rmtree(self.__folder_path_base_gen(True), ignore_errors=True)
		super(ShinyReport, self).delete(using=using) # Call the "real" delete() method.

	class Meta:
		ordering = ('created',)

	def __unicode__(self):
		return self.get_name


class ReportType(FolderObj, models.Model):
	BASE_FOLDER_NAME = settings.REPORT_TYPE_FN

	# objects = managers.ReportTypeManager()

	type = models.CharField(max_length=17, unique=True)
	description = models.CharField(max_length=5500, blank=True)
	search = models.BooleanField(default=False, help_text="NB : LEAVE THIS UN-CHECKED")
	access = models.ManyToManyField(User, null=True, blank=True, default=None,
									related_name='pipeline_access')  # share list
	# tags = models.ManyToManyField(Rscripts, blank=True)
	
	# who creates this report
	author = ForeignKey(User)
	# store the institute info of the user who creates this report
	institute = ForeignKey(Institute, default=Institute.objects.get(id=1))
	
	def file_name(self, filename):
		# FIXME check for FolderObj property fitness
		fname, dot, extension = filename.rpartition('.')
		return '%s%s/%s' % (self.BASE_FOLDER_NAME, self.folder_name, filename)
	
	config = models.FileField(upload_to=file_name, blank=True, null=True)
	manual = models.FileField(upload_to=file_name, blank=True, null=True)
	created = models.DateField(auto_now_add=True)

	shiny_report = models.ForeignKey(ShinyReport, help_text="Choose an existing Shiny report to attach it to",
		default=0, blank=True, null=True)

	# clem 21/12/2015
	def __init__(self, *args, **kwargs):
		super(ReportType, self).__init__(*args, **kwargs)
		self.__prev_shiny_report = self.shiny_report_id

	@property
	def folder_name(self):
		return '%s_%s' % (self.id, slugify(self.type))

	@property
	def is_shiny_enabled(self):
		""" Is this report associated to a ShinyReport, and if so is this ShinyReport enabled ?
		:rtype: bool
		"""
		return self.shiny_report_id > 0 and self.shiny_report.enabled

	# clem 11/12/15
	@property
	def config_path(self):
		""" Return the path of th econfiguration file of this pipeline
		:rtype:
		"""
		return settings.MEDIA_ROOT + str(self.config)

	# clem 11/12/15
	def get_config(self):
		"""
		Return the configuration lines of the pipeline as a string.
		Can be integrated directly into generated script.R
		:rtype: str
		"""
		uri = self.config_path
		conf = ''
		try:
			if isfile(uri):
				conf = str(open(uri).read()) + '\n'
		except IOError:
			pass
		return conf

	def __shiny_changed(self):
		return self.__prev_shiny_report != self.shiny_report_id

	def save(self, *args, **kwargs):
		obj = super(ReportType, self).save(*args, **kwargs) # Call the "real" save() method.

		if self.__shiny_changed:
			if self.__prev_shiny_report:
				ShinyReport.objects.get(pk=self.__prev_shiny_report).regen_report()
			if self.shiny_report:
				self.shiny_report.regen_report()

		try:
			if not isfile(self.config_path):
				with open(self.config_path, 'w') as f:
					f.write('#	Configuration module (Generated by Breeze)\n#	You can place here any pipeline-wide R config')
		except IOError:
			pass

		return obj

	def __unicode__(self):
		return self.type

	def delete(self, using=None):
		shiny_r = self.shiny_report
		super(ReportType, self).delete(using=using)
		if shiny_r is not None:
			shiny_r.regen_report()
		return True

	class Meta:
		ordering = ('type',)
		abstract = False
		db_table = 'breeze_reporttype'


# from django.db.models.signals import pre_save
# from django.dispatch import receiver


# @receiver(pre_save, sender=ReportType)
# def my_handler(sender, **kwargs):
#	print 'pre-save', sender, kwargs


class ScriptCategories(models.Model):
	category = models.CharField(max_length=55, unique=True)
	description = models.CharField(max_length=350, blank=True)
	# if the script is a drat then the category should be inactive
	# active = models.BooleanField(default=False)
	
	def __unicode__(self):
		return self.category

	class Meta:
		db_table = 'breeze_script_categories'


class User_Date(models.Model):
	user = ForeignKey(User)
	install_date = models.DateField(auto_now_add=True)
	
	def __unicode__(self):
		return self.user.username

	class Meta:
		db_table = 'breeze_user_date'


class Rscripts(FolderObj, models.Model):
	objects = managers.ObjectsWithAuth() # The default manager.

	BASE_FOLDER_NAME = settings.RSCRIPTS_FN

	name = models.CharField(max_length=35, unique=True)
	inln = models.CharField(max_length=150, blank=True)
	details = models.CharField(max_length=5500, blank=True)
	# category = models.CharField(max_length=25, choices=CATEGORY_OPT, default=u'general')
	category = ForeignKey(ScriptCategories, to_field="category")
	author = ForeignKey(User)
	creation_date = models.DateField(auto_now_add=True)
	draft = models.BooleanField(default=True)
	price = models.DecimalField(max_digits=19, decimal_places=2, default=0.00)
	# tag related
	istag = models.BooleanField(default=False)
	must = models.BooleanField(default=False)  # defines wheather the tag is enabled by default
	order = models.DecimalField(max_digits=3, decimal_places=1, blank=True, default=0)
	report_type = models.ManyToManyField(ReportType, null=True, blank=True,
										 default=None)  # assosiation with report type
	# report_type = models.ForeignKey(ReportType, null=True, blank=True, default=None)  # assosiation with report type
	access = models.ManyToManyField(User, null=True, blank=True, default=None, related_name="users")
	# install date info
	install_date = models.ManyToManyField(User_Date, blank=True, null=True, default=None, related_name="installdate")
	
	def file_name(self, filename): # TODO check this
		# TODO check for FolderObj fitness
		fname, dot, extension = filename.rpartition('.')
		slug = self.folder_name
		return '%s%s/%s.%s' % (self.BASE_FOLDER_NAME, slug, slug, slugify(extension))
	
	docxml = models.FileField(upload_to=file_name, blank=True)
	code = models.FileField(upload_to=file_name, blank=True)
	header = models.FileField(upload_to=file_name, blank=True)
	logo = models.FileField(upload_to=file_name, blank=True)
	
	def __unicode__(self):
		return self.name

	@property
	def folder_name(self):
		return slugify(self.name)

	@property
	def sec_id(self):
		return 'Section_dbID_%s' % self.id

	@property
	def _code_path(self):
		return settings.MEDIA_ROOT + str(self.code)

	@property
	def _header_path(self):
		return settings.MEDIA_ROOT + str(self.header)

	@property
	def xml_path(self):
		return settings.MEDIA_ROOT + str(self.docxml)

	@property
	def xml_tree(self):
		if not hasattr(self, '_xml_tree'): # caching
			import xml.etree.ElementTree as xml
			self._xml_tree = xml.parse(self.xml_path)
		return self._xml_tree

	def is_valid(self):
		"""
		Return true if the tag XML file is present and non empty
		:return: tell if the tag is usable
		:rtype: bool
		"""
		return is_non_empty_file(self.xml_path)

	# _path_r_template = settings.TAGS_TEMPLATE_PATH
	_path_r_template = settings.SCRIPT_TEMPLATE_PATH

	def get_R_code(self, gen_params, template_file=None):
		"""
		Generates the R code for the report generation of this tag, using the template
		:param gen_params: the result of shell.gen_params_string
		:type gen_params: str
		:return: R code for this tag
		:rtype: str
		"""
		from string import Template

		filein = open(self._path_r_template)
		src = Template(filein.read())
		filein.close()
		# source main code segment
		body = open(self._code_path).read()
		# final step - fire header
		headers = open(self._header_path).read()

		d = { 'tag_name': self.name,
				'body': body,
				'gen_params': gen_params,
				'headers': headers,
			}
		# do the substitution
		return src.substitute(d)

	# def delete(self, using=None):
	#	super(Rscripts, self).delete(using=using)
	#	return True

	class Meta:
		ordering = ["name"]
		abstract = False
		db_table = 'breeze_rscripts'


# define the table to store the products in user's cart
class CartInfo(models.Model):
	script_buyer = ForeignKey(User)
	product = ForeignKey(Rscripts)
	# if free or not
	type_app = models.BooleanField(default=True)
	date_created = models.DateField(auto_now_add=True)
	date_updated = models.DateField(auto_now_add=True)
	# if the user does not pay active == True else active == False
	active = models.BooleanField(default=True)
	
	def __unicode__(self):
		return self.product.name
	
	class Meta:
		ordering = ["active"]


class DataSet(models.Model):
	name = models.CharField(max_length=55, unique=True)
	description = models.CharField(max_length=350, blank=True)
	author = ForeignKey(User)
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.name)
		return 'datasets/%s.%s' % (slug, extension)
	
	rdata = models.FileField(upload_to=file_name)
	
	def __unicode__(self):
		return self.name


class InputTemplate(models.Model):
	name = models.CharField(max_length=55, unique=True)
	description = models.CharField(max_length=350, blank=True)
	author = ForeignKey(User)
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.name)
		return 'mould/%s.%s' % (slug, extension)
	
	file = models.FileField(upload_to=file_name)
	
	def __unicode__(self):
		return self.name


class UserProfile(models.Model):
	user = models.ForeignKey(OrderedUser, unique=True)
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.user.username)
		return 'profiles/%s/%s.%s' % (slug, slug, extension)
	
	fimm_group = models.CharField(max_length=75, blank=True)
	logo = models.FileField(upload_to=file_name, blank=True)
	institute_info = models.ForeignKey(Institute, default=Institute.objects.get(id=1))
	# if user accepts the agreement or not
	db_agreement = models.BooleanField(default=False)
	last_active = models.DateTimeField(default=timezone.now)
	
	def __unicode__(self):
		return self.user.get_full_name()  # return self.user.username


class Runnable(FolderObj, models.Model):
	##
	# CONSTANTS
	##
	ALLOW_DOWNLOAD = True
	BASE_FOLDER_NAME = '' # folder name
	BASE_FOLDER_PATH = '' # absolute path to the container folder
	FAILED_FN = 'failed'
	SUCCESS_FN = 'done'
	SH_NAME = settings.GENERAL_SH_NAME
	FILE_MAKER_FN = settings.REPORTS_FM_FN
	R_HOME = settings.R_HOME
	INC_RUN_FN = settings.INCOMPLETE_RUN_FN
	# output file name (without extension) for nozzle report. MIGHT not be enforced everywhere
	REPORT_FILE_NAME = 'report'
	RQ_FIELDS = ['_name', '_author', '_type']
	R_FILE_NAME_BASE = 'script'
	R_FILE_NAME = R_FILE_NAME_BASE + '.r'
	R_OUT_EXT = '.Rout'
	R_OUT_FILE_NAME = R_FILE_NAME + R_OUT_EXT
	RQ_SPECIFICS = ['request_data', 'sections']
	FAILED_R = 'Execution halted'
	SH_CL = '#!/bin/bash \nexport R_HOME=%s\ntouch ./%s' % (R_HOME, INC_RUN_FN) +\
			' && %sCMD BATCH --no-save %s && ' + 'touch ./%s\nrm ./%s\n' \
		% (SUCCESS_FN, INC_RUN_FN) + 'txt="%s"\n' % FAILED_R + 'CMD=`tail -n1<%s`\n' \
		+ 'if [ "$CMD" = "$txt" ]; \nthen\n	touch ./%s\nfi' % FAILED_FN # TODO make a template
	SYSTEM_FILES = [R_FILE_NAME, R_OUT_FILE_NAME, SH_NAME, INC_RUN_FN, FAILED_FN, SUCCESS_FN, FILE_MAKER_FN]
	HIDDEN_FILES = [R_FILE_NAME, R_OUT_FILE_NAME, SH_NAME, SUCCESS_FN, FILE_MAKER_FN] # TODO add FM file ?

	objects = managers.WorkersManager() # The default manager.

	def __init__(self, *args, **kwargs):
		super(Runnable, self).__init__(*args, **kwargs)
		self.__can_save = False

	##
	# DB FIELDS
	##
	_breeze_stat = models.CharField(max_length=16, default=JobStat.INIT, db_column='breeze_stat')
	_status = models.CharField(max_length=15, blank=True, default=JobStat.INIT, db_column='status')
	progress = models.PositiveSmallIntegerField(default=0)
	sgeid = models.CharField(max_length=15, help_text="job id, as returned by SGE", blank=True)

	##
	# WRAPPERS
	##

	# GENERICS
	def __getattr__(self, item):
		try:
			return super(Runnable, self).__getattribute__(item)
		except AttributeError: # backward compatibility
			return super(Runnable, self).__getattribute__(Trans.swap(item))

	def __setattr__(self, attr_name, value):
		if attr_name == 'breeze_stat':
			self._set_status(value)
		elif attr_name == 'status':
			raise ReadOnlyAttribute # prevent direct writing
		else:
			attr_name = Trans.swap(attr_name) # backward compatibility

		# if attr_name == 'sgeid':
		# 	print self.short_id, 'set sgeid to', str(value)

		super(Runnable, self).__setattr__(attr_name, value)

	# SPECIFICS
	# clem 17/09/2015
	def find_sge_instance(self, sgeid):
		"""
		Return a runnable instance from an sge_id
		:param sgeid: an sgeid from qstat
		:type sgeid: str | int
		:rtype: Runnable
		"""
		if sgeid == self.sgeid:
			return self
		return Runnable.find_sge_instance(sgeid)

	@staticmethod
	def find_sge_instance(sgeid):
		"""
		Return a runnable instance from an sge_id
		:param sgeid: an sgeid from qstat
		:type sgeid: str | int
		:rtype: Runnable
		"""
		result = None
		try:
			result = Report.objects.get(sgeid=sgeid)
		except ObjectDoesNotExist:
			pass
		try:
			result = Jobs.objects.get(sgeid=sgeid)
		except ObjectDoesNotExist:
			pass
		return result

	@property
	def institute(self):
		try:
			self._author.get_profile()
		except ValueError: # for some reason and because of using custom OrderedUser the first call
			# raise this exception while actually populating the cache for this value...
			pass
		return self._author.get_profile().institute_info

	##
	# OTHER SHARED PROPERTIES
	##
	@property # Interface : has to be implemented in Report
	def get_shiny_report(self):
		"""
		To be overridden by Report :
		ShinyReport
		:rtype: ShinyReport | NoneType
		"""
		return None

	@property # Interface : has to be implemented in Report
	def is_shiny_enabled(self):
		"""
		To be overridden by Report :
		Is this report's type associated to a ShinyReport, and if so is this ShinyReport enabled ?
		:rtype: bool
		"""
		return False

	# Interface : has to be implemented in Report
	def has_access_to_shiny(self, this_user=None):
		"""
		To be overridden by Report
		:type this_user: User | OrderedUser
		:rtype: bool
		"""
		return False

	@property
	def sh_command_line(self):
		return self.SH_CL % (settings.R_ENGINE_PATH, self._r_exec_path, self._rout_file)

	@property # UNUSED ?
	def html_path(self):
		return '%s%s' % (self.home_folder_full_path, self.REPORT_FILE_NAME)

	@property # UNUSED ?
	def _r_out_path(self):
		return self._rout_file

	@property # used by write_sh_file() # useless #Future ?
	def _r_exec_path(self):
		return self._rexec

	@property # UNUSED ?
	def _html_full_path(self):
		return '%s.html' % self.html_path

	@property
	def _test_file(self):
		"""
		full path of the job competition verification file
		used to store the retval value, that has timings and perf related datas
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.SUCCESS_FN)

	@property
	def _rout_file(self):
		# return '%s%s' % (self.home_folder_full_path, self.R_OUT_FILE_NAME)
		return '%s%s' % (self._rexec, self.R_OUT_EXT)

	@property
	def _failed_file(self):
		"""
		full path of the job failure verification file
		used to store the retval value, that has timings and perf related datas
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.FAILED_FN)

	@property
	def _incomplete_file(self):
		"""
		full path of the job incomplete run verification file
		exist only if job was interrupted, or aborted
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.INC_RUN_FN)

	@property
	def _sge_log_file(self):
		"""
		Return the name of the autogenerated debug/warning file from SGE
		:rtype: str
		"""
		return '%s_%s.o%s' % (self._name.lower(), self.instance_of.__name__, self.sgeid)

	# clem 11/09/2015
	@property
	def _shiny_files(self):
		"""
		Return a list of files related to shiny if applicable, empty list otherwise
		:rtype: list
		"""
		res = list()
		if self.is_report:
			shiny_rep = self.get_shiny_report
			if shiny_rep is not None:
				res = shiny_rep.SYSTEM_FILE_LIST
		return res

	@property
	def _sh_file_path(self):
		"""
		the full path of the sh file used to run the job on the cluster.
		This is the file that SGE has to instruct the cluster to run.
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.SH_NAME)

	# clem 11/09/2015
	@property
	def system_files(self):
		"""
		Return a list of system requires files
		:rtype: list
		"""
		return self.SYSTEM_FILES + [self._sge_log_file] + self._shiny_files

	# clem 16/09/2015
	@property
	def r_error(self):
		""" Returns the last line of script.R which may contain an error message
		:rtype: str
		"""
		out = ''
		if self.is_r_failure:
			lines = open(self._rout_file).readlines()
			i = len(lines)
			size = i
			for i in range(len(lines)-1, 0, -1):
				if lines[i].startswith('>'):
					break
			if i != size:
				out = ''.join(lines[i:])[:-1]
		return out

	# clem 11/09/2015
	@property
	def hidden_files(self):
		"""
		Return a list of system required files
		:rtype: list
		"""
		return self.HIDDEN_FILES + [self._sge_log_file, '*~', '*.o%s' % self.sgeid] + self._shiny_files

	def _download_ignore(self, cat=None):
		"""
		:type cat: str
		:return: exclude_list, filer_list, name
		:rtype: list, list, str
		"""

		exclude_list = list()
		filer_list = list()
		name = '_full'
		if cat == "-code":
			name = '_Rcode'
			filer_list = ['*.r*', '*.Rout']
			# exclude_list = self.system_files + ['*~']
		elif cat == "-result":
			name = '_result'
			exclude_list = self.hidden_files # + ['*.xml', '*.r*', '*.sh*']
		return exclude_list, filer_list, name

	@property
	def sge_job_name(self):
		"""The job name to submit to SGE
		:rtype: str
		"""
		name = self._name if not self._name[0].isdigit() else '_%s' % self._name
		return '%s_%s' % (slugify(name), self.instance_type.capitalize())

	@property
	def is_done(self):
		"""
		Tells if the job run is not running anymore, using it's breeze_stat or
		the confirmation file that allow confirmation even in case of management
		system failure (like breeze db being down, breeze server, or the worker)
		<b>DOES NOT IMPLY ANYTHING ABOUT SUCCESS OF SGE JOB</b>
		INCLUDES : FAILED, ABORTED, SUCCEED
		:rtype: bool
		"""
		# if self._breeze_stat == JobStat.DONE:
		# 	return True
		# return isfile(self._test_file)
		return self._breeze_stat == JobStat.DONE or isfile(self._test_file)

	@property
	def is_sge_successful(self):
		"""
		Tells if the job was properly run or not, using it's breeze_stat or
		the confirmation file that allow confirmation even in case of management
		system failure (like breeze db being down, breeze server, or the worker)
		INCLUDES : ABORTED, SUCCEED
		:rtype: bool
		"""
		return self._status != JobStat.FAILED and self.is_done

	@property
	def is_successful(self):
		"""
		Tells if the job was successfully done or not, using it's breeze_stat or
		the confirmation file that allow confirmation even in case of management
		system failure (like breeze db being down, breeze server, or the worker)
		This means completed run from sge, no user abort, and verified R success
		:rtype: bool
		"""
		return self._status == JobStat.SUCCEED and self.is_r_successful

	@property
	def is_r_successful(self):
		"""Tells if the job R job completed successfully
		:rtype: bool
		"""
		return self.is_done and not isfile(self._failed_file) and not isfile(self._incomplete_file) and \
			isfile(self._rout_file)

	@property
	def is_r_failure(self):
		"""Tells if the job R job has failed (not equal to the oposite of is_r_successful)
		:rtype: bool
		"""
		return self.is_done and isfile(self._failed_file) and not isfile(self._incomplete_file) and \
			isfile(self._rout_file)

	@property
	def aborting(self):
		"""Tells if job is being aborted
		:rtype: bool
		"""
		return self.breeze_stat == JobStat.ABORT or self.breeze_stat == JobStat.ABORTED

	##
	# SHARED CONCRETE METHODS (SGE_JOB MANAGEMENT RELATED)
	##
	def abort(self):
		""" Abort the job using qdel
		:rtype: bool
		"""
		if self.breeze_stat != JobStat.DONE:
			self.breeze_stat = JobStat.ABORT
			if not self.is_sgeid_empty:
				print self.sge_obj.abort()
			else:
				self.breeze_stat = JobStat.ABORTED
			return True
		return False

	def write_sh_file(self):
		"""
		Generate the SH file that will be executed on the cluster by SGE
		"""
		import os
		# import stat
		# configure shell-file
		config = open(self._sh_file_path, 'w')

		# st = os.stat(self._sh_file_path)

		# Thanks to ' && touch ./done' breeze can always asses if the run was completed (successful or not)
		command = self.sh_command_line # self.SH_CL % (settings.R_ENGINE_PATH, self._r_exec_path)
		config.write(command)
		config.close()

		# config should be readable and executable but not writable, same for script.R
		os.chmod(self._sh_file_path, ACL.RX_RX_)
		os.chmod(self._r_exec_path.path, ACL.R_R_)

	# INTERFACE for extending assembling process
	def generate_r_file(self, *args, **kwargs):
		""" Place Holder for instance specific R files generation
		THIS METHOD MUST BE overridden in subclasses
		"""
		raise self.not_imp()

	# INTERFACE for extending assembling process
	def deferred_instance_specific(self, *args, **kwargs):
		"""
		Specific operations to generate job or report instance dependencies.
		N.B. : you CANNOT use m2m relations before this point
		THIS METHOD MUST BE overridden in subclasses
		"""
		raise self.not_imp()

	def assemble(self, *args, **kwargs):
		"""
		Assembles instance home folder, configures DRMAA and R related files.
		Call deferred_instance_specific()
		and finally triggers self.save()
		"""
		import os
		for each in self.RQ_SPECIFICS:
			if each not in kwargs.keys():
				raise InvalidArguments("'%s' should be provided as an argument of assemble()" % each)

		# The instance is now fully generated and ready to be submitted to SGE
		# NO SAVE can happen before this point, to avoid any inconsistencies
		# that could occur if an Exception happens anywhere in the process
		self.__can_save = True
		self.save()

		if not os.path.exists(self.home_folder_full_path):
			os.makedirs(self.home_folder_full_path, ACL.RWX_RWX_)

		# BUILD instance specific R-File
		# self.generate_r_file(kwargs['sections'], kwargs['request_data'], custom_form=kwargs['custom_form'])
		# self.generate_r_file(sections=kwargs['sections'], request_data=kwargs['request_data'], custom_form=kwargs['custom_form'])
		self.generate_r_file(*args, **kwargs)
		# other stuff that might be needed by specific kind of instances (Report and Jobs)
		self.deferred_instance_specific(*args, **kwargs)
		# open instance home's folder for other to write
		self.grant_write_access()
		# Build and write SH file
		self.write_sh_file()

		self.save()

	def submit_to_cluster(self):
		if not self.aborting:
			from django.utils import timezone
			self.created = timezone.now() # important to be able to timeout sgeid
			self.breeze_stat = JobStat.RUN_WAIT

	def run(self):
		"""
			Submits reports as an R-job to cluster with SGE;
			This submission implements REPORTS concept in BREEZE
			(For SCRIPTS submission see Jobs.run)
			TO BE RUN IN AN INDEPENDENT PROCESS
		"""
		import os
		import django.db

		drmaa = None
		s = None
		if settings.HOST_NAME.startswith('breeze'):
			import drmaa

		config = self._sh_file_path
		log = get_logger('run_%s' % self.instance_type )
		default_dir = os.getcwd() # Jobs specific ? or Report specific ?

		try:
			default_dir = os.getcwd()
			os.chdir(self.home_folder_full_path)
			if self.is_report and self.fm_flag: # Report specific
				os.system(settings.JDBC_BRIDGE_PATH)

			# *MAY* prevent db from being dropped
			django.db.close_connection()
			self.breeze_stat = JobStat.PREPARE_RUN
		except Exception as e:
			log.exception('%s%s : ' % self.short_id + 'pre-run error %s (process continues)' % e)

		try:
			s = drmaa.Session()
			s.initialize()

			jt = s.createJobTemplate()
			jt.workingDirectory = self.home_folder_full_path
			jt.jobName = self.sge_job_name
			jt.email = [str(self._author.email)]
			if self.mailing != '':
				jt.nativeSpecification = "-m " + self.mailing
			if self.email is not None and self.email != '':
				jt.email.append(str(self.email))
			jt.blockEmail = False

			jt.remoteCommand = config
			jt.joinFiles = True
			# jt.outputPath = ':./out'

			self.progress = 25
			self.save()
			import copy
			if not self.aborting:
				self.sgeid = copy.deepcopy(s.runJob(jt))
				log.debug('%s%s : ' % self.short_id + 'returned sge_id "%s"' % self.sgeid)
				self.breeze_stat = JobStat.SUBMITTED
			# waiting for the job to end
			self.waiter(s, True)

			jt.delete()
			s.exit()
			os.chdir(default_dir)

		except (drmaa.AlreadyActiveSessionException, drmaa.InvalidArgumentException, drmaa.InvalidJobException,
				Exception) as e:
			log.error('%s%s : ' % self.short_id + 'drmaa submit failed : %s' % e)
			self.__manage_run_failed(None, '')
			if s is not None:
				s.exit()
			raise e
			return 1

		log.debug('%s%s : ' % self.short_id + 'drmaa submit ended successfully !')
		return 0

	@property
	def sge_obj(self):
		from qstat import Qstat
		return Qstat().job_info(self.sgeid)

	def qstat_stat(self):
		return self.sge_obj.state

	def waiter(self, s, drmaa_waiting=False):
		"""
		:param s:
		:type s: drmaa.Session
		:param drmaa_waiting:
		:type drmaa_waiting: bool
		:rtype: drmaa.JobInfo
		"""
		import drmaa
		import copy
		import time

		exit_code = 42
		aborted = False
		log = get_logger()
		if self.is_sgeid_empty:
			return
		sge_id = copy.deepcopy(self.sgeid) # uselees
		try:
			ret_val = None
			if drmaa_waiting:
				ret_val = s.wait(sge_id, drmaa.Session.TIMEOUT_WAIT_FOREVER)
			else:
				try:
					while True:
						time.sleep(1)
						self.qstat_stat()
						if self.aborting:
							break
				except NoSuchJob:
					exit_code = 0

			# ?? FIXME
			self.breeze_stat = JobStat.DONE
			self.save()

			# FIXME this is SHITTY
			if self.aborting:
				aborted = True
				exit_code = 1
				self.breeze_stat = JobStat.ABORTED

			if isinstance(ret_val, drmaa.JobInfo):
				if ret_val.hasExited:
					exit_code = ret_val.exitStatus
				dic = ret_val.resourceUsage # FUTURE use for mail reporting
				aborted = ret_val.wasAborted

			self.progress = 100
			if exit_code == 0:  # normal termination
				self.breeze_stat = JobStat.DONE
				log.info('%s%s : ' % self.short_id + 'sge job finished !')
				if not self.is_r_successful: # R FAILURE or USER ABORT (to check if that is true)
					get_logger().info('%s%s : ' % self.short_id + 'exit code %s, SGE success !' % exit_code)
					self.__manage_run_failed(ret_val, exit_code, drmaa_waiting, 'r')
				else: # FULL SUCCESS
					self.__manage_run_success(ret_val)
			else: # abnormal termination
				if not aborted: # SGE FAILED
					get_logger().info('%s%s : ' % self.short_id + 'exit code %s, SGE FAILED !' % exit_code)
					self.__manage_run_failed(ret_val, exit_code, drmaa_waiting, 'sge')
				else: # USER ABORTED
					self.__manage_run_aborted(ret_val, exit_code)
			self.save()
			return exit_code
		except Exception as e:
			# FIXME this is SHITTY
			log.error('%s%s : ' % self.short_id + ' while waiting : %s' % e)
			# if e.message == 'code 24: no usage information was returned for the completed job' or self.aborting:
			#	self.__manage_run_failed(None, exit_code)
			#	log.info('%s%s : ' % self.short_id + ' FAIL CODE 24 (FIXME) : %s' % e)
		return 1

	@staticmethod
	def __auto_json_dump(ret_val, file_n):
		""" Dumps JobInfo retval from drmaa to failed or succeed file
		:type ret_val: drmaa.JobInfo
		:type file_n: str
		"""
		import json
		import os

		if isinstance(ret_val, drmaa.JobInfo):
			try:
				os.chmod(file_n, ACL.RW_RW_)
				json.dump(ret_val, open(file_n, 'w+'))
				os.chmod(file_n, ACL.R_R_)
			except Exception as e:
				pass

	# Clem 11/09/2015
	def __manage_run_success(self, ret_val):
		""" !!! DO NOT OVERRIDE !!!
		instead do override 'trigger_run_success'

		Actions on Job successful completion

		:type ret_val: drmaa.JobInfo
		"""
		log = get_logger()
		self.__auto_json_dump(ret_val, self._test_file)
		self.breeze_stat = JobStat.SUCCEED
		log.info('%s%s : ' % self.short_id + ' SUCCESS !')

		self.trigger_run_success(ret_val)

	# Clem 11/09/2015
	def __manage_run_aborted(self, ret_val, exit_code):
		""" !!! DO NOT OVERRIDE !!!
		instead do override 'trigger_run_user_aborted'

		Actions on Job abortion

		:type ret_val: drmaa.JobInfo
		"""
		log = get_logger()
		# self.__auto_json_dump(ret_val, ## )
		self.breeze_stat = JobStat.ABORTED
		log.info('%s%s : ' % self.short_id + 'exit code %s, user aborted' % exit_code)
		self.trigger_run_user_aborted(ret_val, exit_code)

	# Clem 11/09/2015
	def __manage_run_failed(self, ret_val, exit_code, drmaa_waiting=None, type=''):
		""" !!! DO NOT OVERRIDE !!!
		instead do override 'trigger_run_failed'
		Actions on Job Failure

		:type ret_val: drmaa.JobInfo
		"""
		self.__auto_json_dump(ret_val, self._failed_file)
		log = get_logger()

		if drmaa_waiting is not None:
			if drmaa_waiting:
				log.info('%s%s : ' % self.short_id + 'Also R process failed ! (%s)' % type)
				# TODO is R failure on 1st level wait
			else:
				log.info('%s%s : ' % self.short_id + 'Also R process failed OR user abort ! (%s)' % type)
				return self.__manage_run_aborted(ret_val, exit_code)
				# TODO or 2nd level wait either R failure or user abort (for ex when job was aborted before it started)
		self.breeze_stat = JobStat.FAILED

		self.trigger_run_failed(ret_val, exit_code)

	# Clem 11/09/2015
	def trigger_run_success(self, ret_val):
		"""
		Trigger for subclass to override
		:type ret_val: drmaa.JobInfo
		"""
		pass

	def trigger_run_user_aborted(self, ret_val, exit_code):
		"""
		Trigger for subclass to override
		:type ret_val: drmaa.JobInfo
		"""
		pass

	def trigger_run_failed(self, ret_val, exit_code):
		"""
		Trigger for subclass to override
		:type ret_val: drmaa.JobInfo
		"""
		pass

	def _set_status(self, status):
		"""
		Save a specific status state of the instance.
		Changes the progression % and saves the object
		ONLY PLACE WHERE ONE SHOULD CHANGE _breeze_stat and _status
		HAS NOT EFFECT if breeze_stat = DONE
		:param status: a JobStat value
		:type status: str

		"""
		# if self._status == JobStat.SUCCEED and status != JobStat.ABORTED or status is None:
		if self._breeze_stat == JobStat.SUCCEED or self._breeze_stat == JobStat.ABORTED or status is None:
			return # Once the job is marked as done, its stat cannot be changed anymore

		# we use JobStat object to provide further extensibility to the job management system
		_status, _breeze_stat, progress, text = JobStat(status).status_logic()
		l1, l2 = '', ''

		if _status is not None:
			l1 = 'status changed from %s to %s' % (self._status, _status) if _status != self._status else ''
			self._status = _status
		if _breeze_stat is not None:
			l2 = 'breeze_stat changed from %s to %s' % (
				self._breeze_stat, _breeze_stat) if _breeze_stat != self._breeze_stat else ''
			self._breeze_stat = _breeze_stat
		if progress is not None:
			self.progress = progress

		total = '%s%s%s' % (l1, ', and ' if l1 != '' and l2 != '' else '', l2)
		if total != '':
			get_logger().debug('%s%s : %s %s%%' % (self.short_id + (total, progress)))

		self._stat_text = text

		if self.id > 0:
			self.save()

	def get_status(self):
		""" Textual representation of current status
		NO refresh on _status
		:rtype: str
		"""
		return JobStat.textual(self._status, self)

	@property
	def is_sgeid_empty(self):
		""" Tells if the job has no sgeid yet
		:rtype: bool
		"""
		return (self.sgeid is None) or self.sgeid == ''

	@property
	def is_sgeid_timeout(self):
		""" Tells if the waiting time for the job to get an SGEid has expired
		:rtype: bool
		"""
		if self.is_sgeid_empty:
			from datetime import timedelta
			t_delta = timezone.now() - self.created
			get_logger().debug(
				'%s%s : sgeid has been empty for %s sec' % (self.short_id + (t_delta.seconds,)))
			assert isinstance(t_delta, timedelta) # code assist only
			return t_delta > timedelta(seconds=settings.NO_SGEID_EXPIRY)
		return False

	def re_submit_to_cluster(self, force=False, duplicate=True):
		""" Reset the job status, so it can be run again
		Use this, if it hadn't had an SGEid or the run was unexpectedly terminated
		DO NOT WORK on SUCCEEDED JOB."""
		if not self.is_successful or force:
			# TODO finnish
			import copy
			import os
			from django.core.files import base
			get_logger().info('%s%s : resetting job status' % self.short_id)
			new_name = unicode(self.name) + u'_re'
			old_path = self.home_folder_full_path
			with open(self._r_exec_path.path) as f:
				r_code = f.readlines()

			self.name = new_name

			content = "setwd('%s')\n" % self.home_folder_full_path[:-1] + ''.join(r_code[1:])
			os.rename(old_path, self.home_folder_full_path)
			get_logger().debug('%s%s : renamed to %s' % (self.short_id + (self.home_folder_full_path,)))
			self._rexec.save(self.file_name(self.R_FILE_NAME), base.ContentFile(content))
			self._doc_ml.name = self.home_folder_full_path + os.path.basename(str(self._doc_ml.name))

			utils.remove_file_safe(self._test_file)
			utils.remove_file_safe(self._failed_file)
			utils.remove_file_safe(self._incomplete_file)
			utils.remove_file_safe(self._sh_file_path)
			self.save()
			self.write_sh_file()
			# self.submit_to_cluster()

	###
	# DJANGO RELATED FUNCTIONS
	###
	def all_required_are_filled(self, fail=False):
		for each in self.RQ_FIELDS:
			if each not in self.__dict__:
				if fail:
					raise AssertionError('You must assign every required fields of job before '
						+ 'setting breeze_stat. (You forgot %s)\n Required fields are : %s' %
						(each, self.RQ_FIELDS))
				else:
					return False
		return True

	# TODO check if new item or not
	def save(self, *args, **kwargs):
		# self.all_required_are_filled()
		if self.id is None and not self.__can_save:
			raise AssertionError('The instance has to complete self.assemble() before any save can happen')
		super(Runnable, self).save(*args, **kwargs) # Call the "real" save() method.

	def delete(self, using=None):
		self.abort()
		txt = str(self)
		super(Runnable, self).delete(using=using) # Call the "real" delete() method.
		get_logger().info("%s has been deleted" % txt)
		return True

	###
	# SPECIAL PROPERTIES FOR INTERFACE INSTANCE
	###
	def not_imp(self):
		if self.__class__ == Runnable.__class__:
			raise NotImplementedError("Class % doesn't implement %s, because it's an abstract/interface class." % (
				self.__class__.__name__, sys._getframe(1).f_code.co_name))
		else:
			raise NotImplementedError("%s was not implemented in concrete class %s." % (
			sys._getframe(1).f_code.co_name, self.__class__.__name__))

	@property
	def is_report(self):
		return isinstance(self, Report)

	@property
	def is_job(self):
		return isinstance(self, Jobs)

	@property
	def instance_type(self):
		# print self.ins
		# return 'report' if self.is_report else 'job' if self.is_job else 'abstract'
		return self.instance_of.__name__.lower()

	@property
	def instance_of(self):
		# return Report if self.is_report else Jobs if self.is_job else self.__class__
		return self.__class__

	@property
	def md5(self):
		"""
		Return the md5 of the current object status
		Used for long_poll refresh
		:return:
		:rtype: str
		"""
		from hashlib import md5
		m = md5()
		m.update(u'%s%s%s' % (self.text_id, self.get_status(), self.sgeid))
		return m.hexdigest()

	@property
	def short_id(self):
		return self.instance_type[0], self.id

	@property
	def text_id(self):
		return u'%s%s %s' % (self.short_id + (unicode(self.name),))

	def __unicode__(self): # Python 3: def __str__(self):
		return u'%s' % self.text_id

	class Meta:
		abstract = True


class Jobs(Runnable):
	def __init__(self, *args, **kwargs):

		super(Jobs, self).__init__(*args, **kwargs)
		allowed_keys = Trans.translation.keys()

		self.__dict__.update((k, v) for k, v in kwargs.iteritems() if k in allowed_keys)

	##
	# CONSTANTS
	##
	BASE_FOLDER_NAME = settings.JOBS_FN
	BASE_FOLDER_PATH = settings.JOBS_PATH
	SH_FILE = settings.JOBS_SH
	# RQ_SPECIFICS = ['request_data', 'sections']
	##
	# DB FIELDS
	##
	_name = models.CharField(max_length=55, db_column='jname')
	_description = models.CharField(max_length=4900, blank=True, db_column='jdetails')
	_author = ForeignKey(User, db_column='juser_id')
	_type = ForeignKey(Rscripts, db_column='script_id')
	_created = models.DateTimeField(auto_now_add=True, db_column='staged')

	def _institute(self):
		return self.institute

	def file_name(self, filename):
		return super(Jobs, self).file_name(filename)

	_rexec = models.FileField(upload_to=file_name, db_column='rexecut')
	_doc_ml = models.FileField(upload_to=file_name, db_column='docxml')

	# Jobs specific
	mailing = models.CharField(max_length=3, blank=True, help_text= \
		'configuration of mailing events : (b)egin (e)nd  (a)bort or empty')  # TextField(name="mailing", )
	email = models.CharField(max_length=75,
		help_text="mail address to send the notification to (not working ATM : your personal mail adress will be user instead)")

	@property
	def folder_name(self):
		return slugify('%s_%s' % (self._name, self._author))

	_path_r_template = settings.SCRIPT_TEMPLATE_PATH

	@property
	def xml_tree(self):
		if not hasattr(self, '_xml_tree'): # caching
			import xml.etree.ElementTree as xml
			self._xml_tree = xml.parse(self._doc_ml.path)
		return self._xml_tree

	def deferred_instance_specific(self, *args, **kwargs):
		if 'sections' in kwargs:
			tree = kwargs.pop('sections')
			a_path = self.file_name('form.xml')
			tree.write(a_path)
			self._doc_ml = a_path
		else:
			raise InvalidArgument
		# kwargs['sections'].write(str(settings.TEMP_FOLDER) + 'job.xml') # change with ml

	# TODO merge inside of runnable
	def generate_r_file(self, *args, **kwargs):
		"""
		generate the Nozzle generator R file
		:param tree: Rscripts tree from xml
		:type tree: ?
		:param request_data:
		:type request_data: HttpRequest
		"""
		from django.core.files import base
		# from breeze import shell as rshell

		# params = rshell.gen_params_string_job_temp(sections, request_data.POST, self, request_data.FILES) # TODO funct
		params = self.gen_params_string_job_temp(*args, **kwargs)
		code = "setwd('%s')\n%s" % (self.home_folder_full_path[:-1], self._type.get_R_code(params))

		# save r-file
		self._rexec.save(self.R_FILE_NAME, base.ContentFile(code))

	# def gen_params_string_job_temp(tree, data, runnable_inst, files, custom_form):
	# TODO merge with the report
	def gen_params_string_job_temp(self, *args, **kwargs):
		"""
			Iterates over script's/tag's parameters to bind param names and user input;
			Produces a (R-specific) string with one parameter definition per lines,
			so the string can be pushed directly to R file.
		"""
		import re
		# can be replaced by
		# return gen_params_string(tree, data, runnable_inst, files)

		tree = kwargs.pop('sections', None)
		request_data = kwargs.pop('request_data', None)
		data = kwargs.pop('custom_form', None)
		files = request_data.FILES

		tmp = dict()
		params = ''
		# FIXME no access to cleaned data here
		for item in tree.getroot().iter('inputItem'): # for item in tree.getroot().iter('inputItem'):
			#  item.set('val', str(data.cleaned_data[item.attrib['comment']]))
			if item.attrib['type'] == 'CHB':
				params = params + str(item.attrib['rvarname']) + ' <- ' + str(
					data.cleaned_data[item.attrib['comment']]).upper() + '\n'
			elif item.attrib['type'] == 'NUM':
				params = params + str(item.attrib['rvarname']) + ' <- ' + str(
					data.cleaned_data[item.attrib['comment']]) + '\n'
			elif item.attrib['type'] == 'TAR':
				lst = re.split(', |,|\n|\r| ', str(data.cleaned_data[item.attrib['comment']]))
				seq = 'c('
				for itm in lst:
					if itm != "":
						seq += '\"%s\",' % itm

				seq = seq + ')' if lst == [''] else seq[:-1] + ')'
				params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
			elif item.attrib['type'] == 'FIL' or item.attrib['type'] == 'TPL':
				# add_file_to_job(jname, juser, FILES[item.attrib['comment']])
				# add_file_to_report(runnable_inst.home_folder_full_path, files[item.attrib['comment']])
				self.add_file(files[item.attrib['comment']])
				params = params + str(item.attrib['rvarname']) + ' <- "' + str(
					data.cleaned_data[item.attrib['comment']]) + '"\n'
			elif item.attrib['type'] == 'DTS':
				path_to_datasets = str(settings.MEDIA_ROOT) + "datasets/"
				slug = slugify(data.cleaned_data[item.attrib['comment']]) + '.RData'
				params = params + str(item.attrib['rvarname']) + ' <- "' + str(path_to_datasets) + str(slug) + '"\n'
			elif item.attrib['type'] == 'MLT':
				res = ''
				seq = 'c('
				for itm in data.cleaned_data[item.attrib['comment']]:
					if itm != "":
						res += str(itm) + ','
						seq += '\"%s\",' % itm
				seq = seq[:-1] + ')'
				item.set('val', res[:-1])
				params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
			else:  # for text, text_are, drop_down, radio
				params = params + str(item.attrib['rvarname']) + ' <- "' + str(
					data.cleaned_data[item.attrib['comment']]) + '"\n'
		return params

	class Meta(Runnable.Meta): # TODO check if inheritance is required here
		abstract = False
		db_table = 'breeze_jobs'


class Report(Runnable):
	def __init__(self, *args, **kwargs):
		super(Report, self).__init__( *args, **kwargs)
		allowed_keys = Trans.translation.keys() + ['shared', 'title', 'project', 'rora_id']
		self.__dict__.update((k, v) for k, v in kwargs.iteritems() if k in allowed_keys)

	##
	# CONSTANTS
	##
	BASE_FOLDER_NAME = settings.REPORTS_FN
	BASE_FOLDER_PATH = settings.REPORTS_PATH
	SH_FILE = settings.REPORTS_SH
	# RQ_SPECIFICS = ['request_data', 'sections']
	##
	# DB FIELDS
	##
	_name = models.CharField(max_length=55, db_column='name')
	_description = models.CharField(max_length=350, blank=True, db_column='description')
	_author = ForeignKey(User, db_column='author_id')
	_type = models.ForeignKey(ReportType, db_column='type_id')
	_created = models.DateTimeField(auto_now_add=True, db_column='created')
	_institute = ForeignKey(Institute, default=1, db_column='institute_id')
	# TODO change to StatusModel cf https://django-model-utils.readthedocs.org/en/latest/models.html#statusmodel

	def file_name(self, filename):
		return super(Report, self).file_name(filename)

	_rexec = models.FileField(upload_to=file_name, blank=True, db_column='rexec')
	_doc_ml = models.FileField(upload_to=file_name, blank=True, db_column='dochtml')
	email = ''
	mailing = ''

	# Report specific
	project = models.ForeignKey(Project, null=True, blank=True, default=None)
	shared = models.ManyToManyField(User, null=True, blank=True, default=None, related_name='report_shares')
	conf_params = models.TextField(null=True, editable=False)
	conf_files = models.TextField(null=True, editable=False)
	fm_flag = models.BooleanField(default=False)
	# Shiny specific
	shiny_key = models.CharField(max_length=64, null=True, editable=False)
	rora_id = models.PositiveIntegerField(default=0)

	##
	# Defining meta props
	##
	# 25/06/15
	@property
	def folder_name(self):
		return slugify('%s_%s_%s' % (self.id, self._name, self._author.username))

	# 26/06/15
	@property
	def _dochtml(self):
		return '%s%s' % (self.home_folder_full_path, settings.NOZZLE_REPORT_FN)

	# @property
	# def _rtype_config_path(self):
	#	return settings.MEDIA_ROOT + str(self._type.config)

	@property
	def title(self):
		return u'%s Report :: %s  <br>  %s' % (self.type, unicode(self.name).decode('utf8'), self.type.description)

	@property
	def fm_file_path(self):
		"""
		The full path of the file use for FileMaker transfer
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.FILE_MAKER_FN)

	@property
	def nozzle_url(self):
		"""
		Return the url to nozzle view of this report
		:return: the url to nozzle view of this report
		:rtype: str
		"""
		from django.core.urlresolvers import reverse
		from breeze import views

		return reverse(views.report_file_view, kwargs={ 'rid': self.id })

	# 04/06/2015
	@property # TODO check
	def args_string(self):
		""" The query string to be passed for shiny apps, if Report is Shiny-enabled, or blank string	"""
		from django.utils.http import urlencode

		if self.rora_id > 0:
			return '?%s' % urlencode([('path', self.home_folder_rel), ('roraId', str(self.rora_id))])
		else:
			return ''

	# clem 02/10/2015
	@property
	def get_shiny_report(self):
		"""
		:rtype: ShinyReport
		"""
		if self.is_shiny_enabled:
			return self._type.shiny_report
		return ShinyReport()

	# clem 05/10/2015
	@property
	def shiny_url(self):
		"""
		:rtype: str
		"""
		return self.get_shiny_report.url(self)

	# clem 11/09/2015
	@property
	def is_shiny_enabled(self):
		""" Is this report's type associated to a ShinyReport, and if so is this ShinyReport enabled ?
		:rtype: bool
		"""
		return self._type.is_shiny_enabled

	def has_access_to_shiny(self, this_user=None):
		"""
		States if specific user is entitled to access this report through Shiny and if this report is entitled to Shiny
		And the attached Shiny Report if any is Enabled
		:type this_user: User | OrderedUser
		:rtype: bool
		"""
		assert isinstance(this_user, (User, OrderedUser))
		return this_user and (this_user in self.shared.all() or self._author == this_user) \
			and self.is_shiny_enabled

	# clem 23/09/2015
	@property
	def remote_shiny_path(self):
		if self.shiny_key is None or self.shiny_key == '':
			if self.is_shiny_enabled:
				self.generate_shiny_key()
				self.save()
		# return settings.SHINY_REMOTE_BREEZE_REPORTS_PATH + self.shiny_key
		return '%s%s/' % (settings.SHINY_REMOTE_BREEZE_REPORTS_PATH, self.shiny_key)

	_path_r_template = settings.NOZZLE_REPORT_TEMPLATE_PATH

	def deferred_instance_specific(self, *args, **kwargs):
		import pickle
		import json

		request_data = kwargs['request_data']# self.request_data
		# sections = kwargs['sections']

		# clem : saves parameters into db, in order to be able to duplicate report
		self.conf_params = pickle.dumps(request_data.POST)
		if request_data.FILES:
			tmp = dict()
			for each in request_data.FILES:
				tmp[str(each)] = str(request_data.FILES[each])
			self.conf_files = json.dumps(tmp)
		# self.save()

		# generate shiny access for offsite users
		# if report_data['report_type'] == 'ScreenReport': # TODO dynamic
		# if self._type ==  'ScreenReport': # TODO dynamic
		if self.is_shiny_enabled:
			self.generate_shiny_key()

		if 'shared_users' in kwargs.keys():
			self.shared = kwargs['shared_users']

	_path_tag_r_template = settings.TAGS_TEMPLATE_PATH

	# TODO : use clean or save ?
	# def generate_r_file(self, sections, request_data):
	def generate_r_file(self, *args, **kwargs):
		"""
		generate the Nozzle generator R file
		:param sections: Rscripts list
		:param request_data: HttpRequest
		"""
		from string import Template
		from django.core.files import base
		from breeze import shell as rshell
		import xml.etree.ElementTree as XmlET

		sections = kwargs.pop('sections', list())
		request_data = kwargs.pop('request_data', None)
		# custom_form = kwargs.pop('custom_form', None)

		report_specific = open(self._path_tag_r_template).read()

		filein = open(self._path_r_template)
		src = Template(filein.read())
		filein.close()
		tag_list = list()
		self.fm_flag = False
		for tag in sections:
			assert (isinstance(tag, Rscripts)) # useful for code assistance ONLY
			if tag.is_valid() and tag.sec_id in request_data.POST and request_data.POST[tag.sec_id] == '1':
				tree = XmlET.parse(tag.xml_path)
				if tag.name == "Import to FileMaker":
					self.fm_flag = True

				# TODO : Find a way to solve this dependency issue
				gen_params = rshell.gen_params_string(tree, request_data.POST, self,
					request_data.FILES)
				# tag_list.append(tag.get_R_code(gen_params) + report_specific)
				tag_list.append(tag.get_R_code(gen_params) + Template(report_specific).substitute(
					{ 'loc': self.home_folder_full_path[:-1] }))

		d = { 'loc': self.home_folder_full_path[:-1],
			'report_name': self.title,
			'project_parameters': self.dump_project_parameters,
			'pipeline_config': self.dump_pipeline_config,
			'tags': '\n'.join(tag_list),
			'dochtml': str(self._dochtml),
			}
		# do the substitution
		result = src.substitute(d)
		# save r-file
		self._rexec.save(self.R_FILE_NAME, base.ContentFile(result))

	# Clem 11/09/2015
	def trigger_run_success(self, ret_val):
		"""
		Specific actions to do on SUCCESSFUL report runs
		:type ret_val: drmaa.JobInfo
		"""
		import os
		# TODO even migrate to SGE
		if self.is_report and self.fm_flag and isfile(self.fm_file_path):
			run = open(self.fm_file_path).read().split("\"")[1]
			os.system(run)

	@property
	def dump_project_parameters(self):
		import copy

		dump = '# <----------  Project Details  ----------> \n'
		dump += 'report.author          <- \"%s\"\n' % self.author.username
		dump += 'report.pipeline        <- \"%s\"\n' % self.type
		dump += 'project.name           <- \"%s\"\n' % self.project.name
		dump += 'project.manager        <- \"%s\"\n' % self.project.manager
		dump += 'project.pi             <- \"%s\"\n' % self.project.pi
		dump += 'project.author         <- \"%s\"\n' % self.project.author
		dump += 'project.collaborative  <- \"%s\"\n' % self.project.collaborative
		dump += 'project.wbs            <- \"%s\"\n' % self.project.wbs
		dump += 'project.external.id    <- \"%s\"\n' % self.project.external_id
		dump += '# <----------  end of Project Details  ----------> \n\n'

		return copy.copy(dump)

	@property
	def dump_pipeline_config(self):
		import copy

		dump = '# <----------  Pipeline Config  ----------> \n'
		dump += 'query.key          <- \"%s\"  # id of queried RORA instance \n' % self.rora_id
		dump += self._type.get_config() # 11/12/15
		dump += '# <------- end of Pipeline Config --------> \n\n\n'

		return copy.copy(dump)

	def generate_shiny_key(self):
		"""
		Generate a sha256 key for outside access
		"""
		from datetime import datetime
		from hashlib import sha256

		m = sha256()
		m.update(settings.SECRET_KEY + self.folder_name + str(datetime.now()))
		self.shiny_key = str(m.hexdigest())

	def save(self, *args, **kwargs):
		super(Report, self).save(*args, **kwargs) # Call the "real" save() method.
		# if self.type.shiny_report_id > 0 and len(self._home_folder_rel) > 1:
		if self.is_shiny_enabled and self.is_successful:
			# call symbolic link update
			self.type.shiny_report.link_report(self, True, self.get_shiny_report.make_remote_too)

	def delete(self, using=None):
		if self.type.shiny_report_id > 0:
			self.type.shiny_report.unlink_report(self)

		return super(Report, self).delete(using=using) # Call the "real" delete() method.

	class Meta(Runnable.Meta): # TODO check if inheritance is required here
		abstract = False
		db_table = 'breeze_report'


class CustomList(list):
	def unique(self):
		""" return the list with duplicate elements removed """
		return CustomList(set(self))

	def intersect(self, b):
		""" return the intersection of two lists """
		return CustomList(set(self) & set(b))

	def union(self, b):
		""" return the union of two lists """
		return CustomList(set(self) | set(b))


class ShinyTag(models.Model):
	# ACL_RW_RW_R = 0664
	FILE_UI_NAME = settings.SHINY_UI_FILE_NAME
	FILE_SERVER_NAME = settings.SHINY_SERVER_FILE_NAME
	# FILE_DASH_UI = settings.SHINY_DASH_UI_FILE
	TAG_FOLDER = settings.SHINY_TAGS
	RES_FOLDER = settings.SHINY_RES_FOLDER
	FILE_TEMPLATE = settings.SHINY_TAG_CANVAS_PATH
	FILE_TEMPLATE_URL = settings.MOULD_URL + settings.SHINY_TAG_CANVAS_FN
	DEFAULT_MENU_ITEM = 'menuItem("Quality Control", icon = icon("filter", lib = "glyphicon"), tabName = "REPLACE BY THE NAME OF YOUR TAG IN UPPER CASE HERE",' \
		'badgeLabel = "QC", badgeColor = "green")'

	name = models.CharField(max_length=55, unique=True, blank=False,
		help_text="Must be unique, no special characters, no withe spaces."
					"<br />NB : Use the same (in upper case) in the tabName field of the menu entry")
	# label = models.CharField(max_length=32, blank=False, help_text="The text to be display on the dashboard")
	description = models.CharField(max_length=350, blank=True, help_text="Optional description text")
	author = ForeignKey(OrderedUser)
	created = models.DateTimeField(auto_now_add=True)
	institute = ForeignKey(Institute, default=Institute.objects.get(id=1))
	order = models.PositiveIntegerField(default=0, help_text="sorting index number (0 is the topmost)")
	menu_entry = models.TextField(default=DEFAULT_MENU_ITEM,
		help_text="Use menuItem or other Shiny  Dashboard items to customize the menu entry "
				"of your tag.<br /><u>NB : tabName MUST be identical to the uppercase name of your tag.</u>")



	@property
	def get_name(self):
		return str(slugify(str(self.name)))

	@staticmethod
	def remove_file_safe(fname):
		import os.path
		from django.db.models.fields.files import FieldFile
		if type(fname) == file or type(fname) == FieldFile:
			fname = fname.path
		try:
			if os.path.isfile(fname):
				os.remove(fname)
		except os.error:
			pass

	def folder_name_gen(self, remote=False):
		return str('%s%s/' % (self.TAG_FOLDER if not remote else settings.SHINY_REMOTE_TAGS, self.get_name))

	@property
	def folder_name_remote_internal(self):
		return str('%s%s/' % (settings.SHINY_REMOTE_TAGS_INTERNAL, self.get_name))

	@property
	def folder_name(self):
		return self.folder_name_gen()

	def path_dashboard_server(self, remote=False):
		if not remote:
			return str('%s%s' % (self.folder_name, self.FILE_SERVER_NAME))
		else:
			return str('%s%s' % (self.folder_name_remote_internal, self.FILE_SERVER_NAME))

	def path_dashboard_body(self, remote=False):
		if not remote:
			return str('%s%s' % (self.folder_name, self.FILE_UI_NAME))
		else:
			return str('%s%s' % (self.folder_name_remote_internal, self.FILE_UI_NAME))

	def path_res_folder_gen(self, remote=False):
		if not remote:
			return str('%s%s' % (self.folder_name, self.RES_FOLDER))
		else:
			return str('%s%s' % (self.folder_name_remote_internal, self.RES_FOLDER))

	@property
	def path_res_folder(self):
		return self.path_res_folder_gen()

	def file_name_zip(self, filename):
		import os
		base = os.path.splitext(os.path.basename(filename))
		path = str('%s%s_%s.%s' % (settings.UPLOAD_FOLDER, self.get_name, slugify(base[0]), slugify(base[1])))
		return str(path)

	zip_file = models.FileField(upload_to=file_name_zip, blank=True, null=False,
		help_text="Upload a zip file containing all the files required for your tag, and "
		" following the structure of the <a href='%s'>provided canvas</a>.<br />\n"
		"Check the <a href='%s'>available libraries</a>. If the one you need is not"
		" present, please contact an admin." %
		(FILE_TEMPLATE_URL, settings.SHINY_LIBS_TARGET_URL))
	enabled = models.BooleanField()
	attached_report = models.ManyToManyField(ShinyReport)

	# clem 22/12/2015
	def __init__(self, *args, **kwargs):
		super(ShinyTag, self).__init__(*args, **kwargs)
		self.__prev_reports = list()
		if self.id:
			self.__prev_reports = list(self.attached_report.all() or None)
		self.__prev_name = self.name or None

	# clem 05/10/2015
	def copy_to_remote(self):
		import os
		log_obj = get_logger()
		log_obj.debug("updating %s on RemoteShiny" % self.__repr__)

		# del the remote report copy folder
		path = self.folder_name_gen(True)
		if not os.path.isdir(path) or safe_rm(path):
			try:
				# copy the data content of the report
				safe_copytree(self.folder_name, path)
			except Exception as e:
				log_obj.warning("%s copy error %s" % (self.__repr__, e))
			return True
		log_obj.warning("failed to copy %s to %s" % (self.__repr__, path))
		return False

	def save(self, *args, **kwargs):
		import shutil
		import os
		import zipfile

		# zf = kwargs.pop('zf', None)
		zf = None
		try:
			zf = zipfile.ZipFile(self.zip_file)
		except Exception as e:
			pass
		# rebuild = kwargs.pop('rebuild', False)

		new_name = self.name
		if self.name != self.__prev_name and self.__prev_name:
			# name has changed we should rename the folder as well
			self.name = self.__prev_name
			print 'old path :', self.folder_name[:-1], 'to:', new_name
			old_dir = self.folder_name[:-1]
			self.name = new_name
			shutil.move(old_dir, self.folder_name[:-1])

		if zf:
			# clear the folder
			shutil.rmtree(self.folder_name[:-1], ignore_errors=True)
			print 'new path:', self.folder_name[:-1]

			# extract the zip
			zf.extractall(path=self.folder_name)
			# changing files permission
			for item in os.listdir(self.folder_name[:-1]):
				path = '%s%s' % (self.folder_name, item)
				if os.path.isfile(path):
					# print 'chmod %s' % path, self.ACL_RW_RW_R
					os.chmod(path, ACL.RW_RW_)
			# removes the zip from temp upload folder
			self._zip_clean()

		super(ShinyTag, self).save(*args, **kwargs) # Call the "real" save() method.

		# refresh ??
		# self = ShinyTag.objects.get(pk=self.id)
		# print self.attached_report.

		if self.enabled and ShinyReport.remote_shiny_ready():
			self.copy_to_remote()
		print 'before list', self.__prev_reports
		print 'after list', self.attached_report.all()
		for each in (CustomList(self.attached_report.all()).union(self.__prev_reports)).unique():
			each.regen_report()

	# clem 22/12/2015
	def _zip_clean(self): # removes the zip from temp upload folder (thus forcing re-upload)
		import os
		if os.path.isfile(self.zip_file.path):
			self.remove_file_safe(self.zip_file.path)

	# Manages folder creation, zip verification and extraction
	def clean(self):
		import zipfile
		if self.__prev_reports and len(self.__prev_reports):
			print 'list before', self.__prev_reports  # self.attached_report.all()
		log_obj = get_logger()

		# checks if attached list changed :
		# shared_users = request_data.POST.getlist('shared')
		##
		# Zip file and folder management
		##
		try: # loads zip file
			zf = zipfile.ZipFile(self.zip_file)
		except Exception as e:
			zf = None
			self._zip_clean()
			if self.id: # not the first time this item is saved, so no problem
				log_obj.info("%s, No zip submitted, no rebuilding" % self.__repr__)
				# rebuild = False
				return # self.save()
			else:
				raise ValidationError({ 'zip_file': ["while loading zip_lib says : %s" % e] })
		# check both ui.R and server.R are in the zip and non empty
		for filename in [self.FILE_SERVER_NAME, self.FILE_UI_NAME]:
			try:
				info = zf.getinfo(filename)
			except KeyError:
				self._zip_clean()
				raise ValidationError({ 'zip_file': ["%s not found in zip's root" % filename] })
			except Exception as e:
				self._zip_clean()
				raise ValidationError({ 'zip_file': ["while listing zip_lib says : %s" % e] })
			# check that the file is not empty
			if info.file_size < settings.SHINY_MIN_FILE_SIZE:
				self._zip_clean()
				raise ValidationError({ 'zip_file': ["%s file is empty" % filename] })
		log_obj.info("%s, Rebuilding..." % self.__repr__)

	def delete(self, using=None):
		import shutil

		log_obj = get_logger()
		log_obj.info("deleted %s" % self.__repr__)

		# Deleting the folder
		shutil.rmtree(self.folder_name[:-1], ignore_errors=True)
		super(ShinyTag, self).delete(using=using) # Call the "real" delete() method.

	class Meta:
		ordering = ('order',)

	def __repr__(self):
		return '<%s %s:%s>' % (self.__class__.__name__, self.id, self.__unicode__())

	def __unicode__(self):
		return self.name


class OffsiteUser(models.Model):
	first_name = models.CharField(max_length=32, blank=False, help_text="First name of the off-site user to add")
	last_name = models.CharField(max_length=32, blank=False, help_text="Last name of the off-site user to add")
	email = models.CharField(max_length=64, blank=False, unique=True,
							help_text="Valid email address of the off-site user")
	institute = models.CharField(max_length=32, blank=True, help_text="Institute name of the off-site user")
	role = models.CharField(max_length=32, blank=True, help_text="Position/role of this off-site user")
	user_key = models.CharField(max_length=32, null=False, blank=False, unique=True, help_text="!! DO NOT EDIT !!")
	added_by = ForeignKey(User, related_name='owner', help_text="!! DO NOT EDIT !!")
	belongs_to = models.ManyToManyField(User, related_name='display', help_text="!! DO NOT EDIT !!")

	created = models.DateTimeField(auto_now_add=True)
	shiny_access = models.ManyToManyField(Report, blank=True)

	@property
	def firstname(self):
		return unicode(self.first_name).capitalize()

	@property
	def lastname(self):
		return unicode(self.last_name).capitalize()

	@property
	def full_name(self):
		return self.firstname + ' ' + self.lastname

	@property
	def fullname(self):
		return self.full_name

	class Meta:
		ordering = ('first_name',)

	# 04/06/2015
	def unlink(self, user):
		"""
		Remove the reference of user to this off-site user
		This off-site user, won't show up in user contact list any more
			and won't have access to any previously shared by this user
		:param user: current logged in user, usually : request.user
		:type user: User
		"""
		# removes access to any report user might have shared with him
		rep_list = self.shiny_access.filter(author=user)
		for each in rep_list:
			self.shiny_access.remove(each)
		# remove the attachment link
		self.belongs_to.remove(user)

	def delete(self, using=None, force=None, *args, **kwargs):
		"""
		Remove this off-site user from the database, provided no user reference it anymore
		:param force: force deletion and remove any remaining reference (shiny_access and belongs_to)
		:type force: bool
		:return: if actually deleted from database
		:rtype: bool
		"""
		if force: # delete any relation to this off-site user
			self.belongs_to.clear()
			self.shiny_access.clear()
		# if no other breeze user reference this off-site user, we remove it
		att_list = self.belongs_to.all()
		if att_list.count() == 0:
			super(OffsiteUser, self).delete(*args, **kwargs)
		else:
			return False
		return True

	def drop(self, user):
		"""
		Remove this off-site user from the user contact list, and remove any access it has to report shared by user
		If any other user reference this  off-site user, it won't be deleted.
		You can force this contact to be totally removed by using .delete(force=True)
		:param user: current logged in user, usually : request.user
		:type user: User
		"""
		self.unlink(user)
		self.delete()

	def __unicode__(self):
		return unicode(self.full_name)

