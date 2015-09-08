import drmaa
import sys
from django.template.defaultfilters import slugify
from django.db.models.fields.related import ForeignKey
from django.contrib.auth.models import User # as DjangoUser
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from breeze import managers
from utils import *
from os.path import isfile # , isdir, islink, exists, getsize
from django.conf import settings
from django.db import models
from breeze.b_exceptions import *

# from os import symlink
# import os.path
# from operator import isCallable


CATEGORY_OPT = (
	(u'general', u'General'),
	(u'visualization', u'Visualization'),
	(u'screening', u'Screening'),
	(u'sequencing', u'Sequencing'),
)

Trans = managers.Trans

# TODO : move all the logic into objects here


class JobState(drmaa.JobState):
	SUSPENDED = 'suspended'
	PENDING = 'pending'
	ON_HOLD = 'pending'


_JOB_PS = {
	'': JobState.UNDETERMINED,
	'r': JobState.RUNNING,
	'p': JobState.PENDING,
	'qw': JobState.QUEUED_ACTIVE,

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
		JobState.FAILED: 'job finished, but failed',
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
			return 0
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

		return self.status, self.breeze_stat, progress, self.textual(status)

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
	def textual(stat):
		"""
		Return string representation of current status
		:param stat: current status
		:type stat: str
		:return: string representation of current status
		:rtype: str
		"""
		if stat in JobStat.__decode_status:
			return JobStat.__decode_status[stat]
		else:
			return 'unknown status'

	def __str__(self):
		return self.stat_text


class FolderObj(object):
	BASE_FOLDER_NAME = None # To define

	@property # interface (To define)
	def folder_name(self):
		"""
		Should implement a generator for the name of the folder to store the instance
		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		raise self.not_imp()

	@property
	def _home_folder_rel(self):
		"""
		Returns the relative path to this object folder
		:return: the relative path to this object folder
		:rtype: str
		"""
		if self.BASE_FOLDER_NAME is None:
			raise NotDefined("BASE_FOLDER_NAME was not implemented in concrete class %s." % self.__class__.__name__)
		if self.folder_name is None or self.folder_name == '':
			raise NotDefined("folder_name is empty for %s." % self)
		return '%s%s/' % (self.BASE_FOLDER_NAME, self.folder_name)

	@property
	def home_folder_full_path(self):
		"""
		Returns the absolute path to this object folder
		:return: the absolute path to this object folder
		:rtype: str
		"""
		return '%s%s' % (settings.MEDIA_ROOT, self._home_folder_rel)

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
	FILE_DASH_UI = settings.SHINY_DASH_UI_FN
	FILE_DASH_SERVER = settings.SHINY_DASH_SERVER_FN
	FILE_HEADER_NAME = settings.SHINY_HEADER_FILE_NAME
	FILE_GLOBAL = settings.SHINY_GLOBAL_FILE_NAME
	FILE_LIST = settings.SHINY_FILE_LIST
	FILE_LOADER = settings.SHINY_LOADER_FILE_NAME
	SERVER_FOLDER = settings.SHINY_SERVER_FOLDER
	UI_FOLDER = settings.SHINY_UI_FOLDER
	RES_FOLDER = settings.SHINY_RES_FOLDER
	SHINY_REPORTS = settings.SHINY_REPORTS
	REPORT_TEMPLATE_PATH = settings.SHINY_REPORT_TEMPLATE_PATH
	FS_ACL = 0775

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
	def _folder_path_base(self):
		return str('%s%s/' % (self.SHINY_REPORTS, self.get_name))

	@property
	def folder_path(self):
		return str('%sapp/' % self._folder_path_base)

	@property
	def server_path(self):
		return str('%s%s' % (self.folder_path, self.FILE_SERVER_NAME))

	@property
	def ui_path(self):
		return str('%s%s' % (self.folder_path, self.FILE_UI_NAME))

	@property
	def global_path(self):
		return str('%s%s' % (self.folder_path, self.FILE_GLOBAL))

	@property
	def res_folder_path(self):
		return str('%s%s' % (self.folder_path, self.RES_FOLDER))

	path_template_folder = REPORT_TEMPLATE_PATH
	path_server_r_template = REPORT_TEMPLATE_PATH + FILE_SERVER_NAME
	path_ui_r_template = REPORT_TEMPLATE_PATH + FILE_UI_NAME
	path_global_r_template = REPORT_TEMPLATE_PATH + FILE_GLOBAL
	path_heade_r_template = REPORT_TEMPLATE_PATH + FILE_HEADER_NAME
	# path_global_r_template = REPORT_TEMPLATE_PATH + FILE_GLOBAL
	path_loader_r_template = str(REPORT_TEMPLATE_PATH + FILE_LOADER)
	path_file_lst_template = str(REPORT_TEMPLATE_PATH + FILE_LIST)
	path_dash_ui_r_template = REPORT_TEMPLATE_PATH + FILE_DASH_UI
	path_dash_server_r_template = REPORT_TEMPLATE_PATH + FILE_DASH_SERVER

	@property # relative path to link holder directory
	def _link_holder_rel_path(self):
		# the point of this property, is that you can change the folder structure by only changing this
		return '%s/lnk' % self.get_name

	@property
	def _link_holder_path(self): # full path to lnk holder directory
		return '%s%s/' % (self.SHINY_REPORTS, self._link_holder_rel_path)

	def report_link_rel_path(self, report):
		"""
		Return the path to the symlink file to the actual report WITHOUT a trailing /
		:param report: a valid Report instance
		:type report: Report
		:return: path to the symlink file to the actual report WITHOUT a trailing /
		:rtype: str
		"""
		return '%s/%s' % (self._link_holder_rel_path, report.id)

	def report_link(self, report, rel=False):
		if rel:
			return self.report_link_rel_path(report)
		return '%s%s' % (self.SHINY_REPORTS, self.report_link_rel_path(report))

	def update_folder(self):
		"""
		Creates the directory structure, removing any previously existing content,
		creates sever and ui sub-folders and link server and ui dashboard 'tag'
		"""
		import shutil
		import os.path

		shutil.rmtree(self._folder_path_base, ignore_errors=True)
		os.mkdir(self._folder_path_base, self.FS_ACL)
		os.mkdir(self._link_holder_path, self.FS_ACL)
		os.mkdir(self.folder_path, self.FS_ACL)
		# os.mkdir('%s%s/' % (self.folder_path, self.UI_FOLDER), self.FS_ACL)
		# os.mkdir('%s%s/' % (self.folder_path, self.SERVER_FOLDER), self.FS_ACL)
		os.mkdir('%s%s/' % (self.folder_path, self.RES_FOLDER), self.FS_ACL)

	# link the dashboard 'tag'
	# auto_symlink(self.path_dash_ui_r_template, self.folder_path + self.FILE_DASH_UI)
	# auto_symlink(self.path_dash_server_r_template, self.folder_path + self.FILE_DASH_SERVER)

	def _link_all_reports(self, force=False):
		"""
		Triggers the linking of each Reports that exists of every attached ReportType
		:param force: force linking of each Reports, even if files are missing, or the link already existent
		:type force: bool
		"""
		if ReportType.objects.filter(shiny_report=self).count() > 0: # if attached to any Report
			for rtype in ReportType.objects.filter(shiny_report=self):
				for report in Report.objects.filter(type=rtype):
					self.link_report(report, force)

	def link_report(self, report, force=False):
		"""
		Link a standard report to this ShinyReport using soft-links. (updates or creates linking)
		If the ShinyReport skeleton has previously been generated,
			this step is enough to enable a report to be visualized through Shiny
		:param report: a valid Report instance
		:type report: Report
		:param force: force linking even if files are missing, or the link already existent
		:type force: bool
		"""
		log_obj = get_logger()
		log_obj.debug(
			"updating shinyReport %s slink for report %s %s" % (self.id, report.id, 'FORCING' if force else ''))

		import os

		assert isinstance(report, Report)
		# handles individually each generated report of this type
		report_home = report.home_folder_full_path
		report_link = self.report_link(report)
		# if the home folder of the report exists, and the link doesn't yet
		if os.path.isdir(report_home[:-1]) and report_home != settings.MEDIA_ROOT:
			# check that the report has all required files
			if not force:
				j = self.related_files()
				for each in j: # for every required registered file
					path = '%s%s' % (report_home, each['path'])
					if each['required'] and not (os.path.isfile(path) and os.access(path, os.R_OK)):
						log_obj.critical("%s missing required file %s" % (report.id, path))
						return
			if force or not os.path.islink(report_link):
				# make of soft-link for each files/folder of the shinyReport folder into the Report folder
				for item in os.listdir(self.folder_path):
					auto_symlink('%s%s' % (self.folder_path, item), '%s%s' % (report_home, item))
				# Creates a slink in shinyReports to the actual report
				auto_symlink(report_home, report_link)
		else: # the target report is missing we remove the link
			self.unlink_report(report)

	def unlink_report(self, report):
		"""
		Do the opposite of link_report, useful if a specific Report has been individually deleted
		:param report: a valid Report instance
		:type report: Report
		"""
		assert isinstance(report, Report)
		import os
		# handles individually each generated report of this type
		report_home = report.home_folder_full_path
		report_link = self.report_link(report)

		# if the home folder of the report exists, and the link doesn't yet
		if os.path.isdir(report_home) and report_home != settings.MEDIA_ROOT:
			# removes the soft-link for each files/folder of the shinyReport folder into the Report folder
			for item in os.listdir(self.folder_path):
				remove_file_safe('%s%s' % (report_home, item)) # TODO check
		if os.path.islink(report_link):
			# removes the slink in shinyReports to the actual report
			remove_file_safe(report_link) # unlink from shiny TODO check

	def _unlink_all_reports(self):
		"""
		Do the opposite of _link_all_reports , usefull if a this ShinyReport has been delete, or unlink from a ReportType
		Triggers the unlinking of each Reports that exists of every attached ReportType
		"""
		if ReportType.objects.filter(shiny_report=self).count() > 0: # if attached to any Report
			for rtype in ReportType.objects.filter(shiny_report=self):
				for report in Report.objects.filter(type=rtype):
					self.unlink_report(report)

	def import_tag_res(self, tag):
		"""
		Import every resources ( www folder) of a specific tag
		:param tag: a valid ShinyTag instance
		:type tag: ShinyTag
		"""
		from distutils.dir_util import copy_tree

		assert isinstance(tag, ShinyTag)
		copy_tree(tag.path_res_folder, self.res_folder_path) # TODO replace with symlimks ?

	@staticmethod
	def related_files(formatted=False):
		"""
		Returns a list of related files for the report
		:rtype: dict or list
		"""
		import json

		try:
			jfile = open(ShinyReport.path_file_lst_template)
			j = json.load(jfile)
			jfile.close()
		except Exception as e:
			j = list()
		if formatted:
			d = dict()
			for each in j:
				d.update({ each['tname']: each['path'] })
			return d
		return j

	@staticmethod
	def get_parsed_loader():
		from string import Template

		file_loaders = open(ShinyReport.path_loader_r_template)
		src = Template(file_loaders.read())
		file_loaders.close()
		return src.safe_substitute(ShinyReport.related_files(formatted=True))

	def generate_server(self, a_user=None): # generate the report server.R file to include all the tags
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
		updated = 'Last updated on %s for user %s (%s)' % (aux.dateT(), a_user.get_full_name(), a_user)
		alist = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				if each.enabled:
					# add it to the source list
					alist.append('### Tag %s by %s (%s) %s%ssource("%s",local = TRUE)' % (
						each.name, each.author.get_full_name(), each.author, each.created, SEP, each.path_dashboard_server))
				else:
					alist.append('### DISABLED Tag %s by %s (%s) %s' % (
						each.name, each.author.get_full_name(), each.author, each.created))
		loaders = self.get_parsed_loader()
		alist.append('') # avoid join errors if list is empty
		d = { 'title': self.title,
				'generated': generated,
				'updated': updated,
				'loaders': loaders,
				'sources': SEP.join(alist)
			}
		assert (isinstance(src, Template))
		result = src.safe_substitute(d)
		f = open(self.server_path, 'w')
		f.write(result)
		f.close()
		return

	def generate_ui(self, a_user=None):  # generate the report ui.R file to include all the tags
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
		updated = 'Last updated on %s for user %s (%s)' % (aux.dateT(), a_user.get_full_name(), a_user)
		alist = list()
		tag_vars = list()
		menu_list = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				if each.enabled:
					self.import_tag_res(each)
					alist.append('### Tag %s by %s (%s) %s%ssource("%s",local = TRUE)' % (
						each.name, each.author.get_full_name(), each.author, each.created, SEP, each.path_dashboard_body))
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
		f = open(self.ui_path, 'w')
		f.write(result)
		f.close()
		return

	def generate_global(self, a_user=None):  # generate the report ui.R file to include all the tags
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
		updated = 'Last updated on %s for user %s (%s)' % (aux.dateT(), a_user.get_full_name(), a_user)
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
		f = open(self.global_path, 'w')
		f.write(result)
		f.close()
		return

	def regen_report(self, a_user=None):
		log_obj = get_logger()
		log_obj.info("rebuilding shinyReport %s for user %s" % (self.id, a_user))
		self.update_folder()
		self.generate_server(a_user)
		self.generate_ui(a_user)
		self.generate_global(a_user)
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
		super(ShinyReport, self).delete(using=using) # Call the "real" delete() method.

	class Meta:
		ordering = ('created',)

	def __unicode__(self):
		return self.get_name


class ReportType(FolderObj, models.Model):
	BASE_FOLDER_NAME = settings.REPORT_TYPE_FN

	type = models.CharField(max_length=17, unique=True)
	description = models.CharField(max_length=5500, blank=True)
	search = models.BooleanField(default=True)
	access = models.ManyToManyField(User, null=True, blank=True, default=None,
									related_name='pipeline_access')  # share list
	# tags = models.ManyToManyField(Rscripts, blank=True)
	
	# who creates this report
	author = ForeignKey(User)
	# store the institute info of the user who creates this report
	institute = ForeignKey(Institute, default=Institute.objects.get(id=1))
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.') # FIXME
		return '%s%s/%s' % (self.BASE_FOLDER_NAME, self.folder_name, filename)
	
	config = models.FileField(upload_to=file_name, blank=True, null=True)
	manual = models.FileField(upload_to=file_name, blank=True, null=True)
	created = models.DateField(auto_now_add=True)

	shiny_report = models.ForeignKey(ShinyReport, help_text="Choose an existing Shiny report to attach it to",
		default=0)

	@property
	def folder_name(self):
		return '%s_%s' % (self.id, slugify(self.type))

	@property
	def is_shiny_enabled(self):
		return self.shiny_report_id > 0

	def save(self, *args, **kwargs):
		obj = super(ReportType, self).save(*args, **kwargs) # Call the "real" save() method.

		for each in ShinyReport.objects.all():
			each.regen_report()
		# if self.shiny_report_id > 0:
		# 	# call symbolic link update
		# 	self.shiny_report._link_all_reports(True)
		return obj

	def __unicode__(self):
		return self.type

	def delete(self, using=None):
		super(ReportType, self).delete(using=using)
		return True

	class Meta:
		ordering = ('type',)
		abstract = False
		db_table = 'breeze_reporttype'


class ScriptCategories(models.Model):
	category = models.CharField(max_length=55, unique=True)
	description = models.CharField(max_length=350, blank=True)
	# if the script is a drat then the category should be inactive
	# active = models.BooleanField(default=False)
	
	def __unicode__(self):
		return self.category

	class Meta:
		db_table = 'breeze_script_categories'


class UserDate(models.Model):
	user = ForeignKey(User)
	install_date = models.DateField(auto_now_add=True)
	
	def __unicode__(self):
		return self.user.username

	class Meta:
		db_table = 'breeze_user_date'


class Rscripts(FolderObj, models.Model):
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
	install_date = models.ManyToManyField(UserDate, blank=True, null=True, default=None, related_name="installdate")
	
	def file_name(self, filename): # TODO check this
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

	#def delete(self, using=None):
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
	BASE_FOLDER_NAME = '' # folder name
	BASE_FOLDER_PATH = '' # absolute path to the container folder
	FAILED_FN = 'failed'
	SUCCESS_FN = 'done'
	SH_NAME = settings.GENERAL_SH_NAME
	FILE_MAKER_FN = settings.REPORTS_FM_FN
	INC_RUN_FN = settings.INCOMPLETE_RUN_FN
	REPORT_FILE_NAME = 'report'
	RQ_FIELDS = ['_name', '_author', '_type']
	R_FILE_NAME_BASE = 'script'
	R_FILE_NAME = R_FILE_NAME_BASE + '.r'
	R_OUT_FILE_NAME = R_FILE_NAME + '.Rout'
	RQ_SPECIFICS = ['request_data', 'sections']
	FAILED_R = 'Execution halted'
	SH_CL = '#!/bin/bash \ntouch ./%s' % INC_RUN_FN + ' && %sCMD BATCH --no-save %s && ' + 'touch ./%s\nrm ./%s\n' \
		% (SUCCESS_FN, INC_RUN_FN) + 'txt="%s"\nCMD=`tail -n1<%s`\nif [ "$CMD" = "%s" ];' % \
		(FAILED_R, R_OUT_FILE_NAME, FAILED_R) + '\nthen\n	touch ./%s\nfi' % FAILED_FN

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
	@property
	def institute(self):
		try:
			self._author.get_profile()
		except ValueError: # for some reason and because of using custom OrderedUser the first call
			# raise this exception while actually populating the cache for this value...
			pass
		return self._author.get_profile().institute_info

	@staticmethod
	def file_n_slug(file_name):
		"""
		Slugify filenames, saving the . if exists, and leading path
		:type file_name: str
		:rtype: str
		"""
		import os
		dir_n = os.path.dirname(file_name)
		base = os.path.basename(file_name)
		if '.' in base:
			base = os.path.splitext(base)
			f_name = '%s.%s' % (slugify(base[0]), slugify(base[1]))
		else:
			f_name = slugify(base)

		return '%s%s' % (Path(dir_n), f_name)

	##
	# PROPERTIES INTERFACES
	##
	# special interface (Generic)
	def file_name(self, filename):
		"""
		Special property
		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		return self.file_n_slug(filename)

	##
	# OTHER SHARED PROPERTIES
	##
	@property # UNUSED ?
	def html_path(self):
		return '%s%s' % (self.home_folder_full_path, self.REPORT_FILE_NAME)

	@property # UNUSED ?
	def _r_out_path(self):
		return '%s%s' % (self.home_folder_full_path, self.R_OUT_FILE_NAME)

	@property # used by write_sh_file()
	def _r_exec_path(self): # TODO problem here with jobs
		return '%s%s' % (settings.MEDIA_ROOT, self._rexec)

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
		return '%s%s' % (self.home_folder_full_path, self.R_OUT_FILE_NAME)

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
	def sh_file_path(self):
		"""
		the full path of the sh file used to run the job on the cluster.
		This is the file that SGE has to instruct the cluster to run.
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.SH_NAME)

	@property
	def fm_file_path(self):
		"""
		The full path of the file use for FileMaker transfer
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.FILE_MAKER_FN)

	@property
	def sge_job_name(self):
		"""
		The job name to submit to SGE
		:rtype: str
		"""
		return '%s_%s' % (slugify(self._name), self.instance_type.capitalize())

	@property
	def is_done(self):
		"""
		Tells if the job run is not running anymore, using it's breeze_stat or
		the confirmation file that allow confirmation even in case of management
		system failure (like breeze db being down, breeze server, or the worker)
		DOES NOT IMPLY ANYTHING ABOUT SUCCESS OF SGE JOB
		INCLUDES : FAILED, ABORTED, SUCCEED
		:rtype: bool
		"""
		if self._breeze_stat == JobStat.DONE:
			return True
		return isfile(self._test_file)

	@property
	def is_sge_successful(self):
		"""
		Tells if the job was properly run or not, using it's breeze_stat or
		the confirmation file that allow confirmation even in case of management
		system failure (like breeze db being down, breeze server, or the worker)
		INCLUDES : ABORTED, SUCCEED
		:rtype: bool
		"""
		return self.is_done and self._status != JobStat.FAILED

	@property
	def is_successful(self):
		"""
		Tells if the job was successfully done or not, using it's breeze_stat or
		the confirmation file that allow confirmation even in case of management
		system failure (like breeze db being down, breeze server, or the worker)
		This means completed run from sge, no user abort, and verified R success
		:rtype: bool
		"""
		return self.is_r_successful and self._status == JobStat.SUCCEED

	@property
	def is_r_successful(self):
		"""
		Tells if the job R job completed successfully
		:rtype: bool
		"""
		return self.is_done and not isfile(self._failed_file) and not isfile(self._incomplete_file) and \
			isfile(self._rout_file)

	##
	# SHARED CONCRETE METHODS (JOB MANAGEMENT RELATED)
	##
	def add_file(self, f):
		import os
		a_dir = self.home_folder_full_path
		if not os.path.exists(a_dir):
			os.makedirs(a_dir)

		f.name = self.file_n_slug(f.name)
		with open(os.path.join(a_dir, f.name), 'wb+') as destination:
			for chunk in f.chunks():
				destination.write(chunk)
		return f.name

	@property
	def aborting(self):
		"""
		state if job is being aborted
		:rtype: bool
		"""
		return self.breeze_stat == JobStat.ABORT or self.breeze_stat == JobStat.ABORTED

	def abort(self):
		"""
		Abort the job using qdel
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
		import stat
		# configure shell-file
		config = open(self.sh_file_path, 'w')

		# config should be executable
		st = os.stat(self.sh_file_path)
		os.chmod(self.sh_file_path, st.st_mode | stat.S_IEXEC)

		# Thanks to ' && touch ./done' breeze can always asses if the run was completed (successful or not)
		command = self.SH_CL % (settings.R_ENGINE_PATH, self._r_exec_path)
		config.write(command)
		config.close()

	def grant_write_access(self):
		"""
		Make the home folder writable for group
		"""
		import os
		import stat
		# open home's folder for others
		st = os.stat(self.home_folder_full_path)
		os.chmod(self.home_folder_full_path, st.st_mode | stat.S_IRWXG)

	# interface for extending assembling process
	def deferred_instance_specific(self, *args, **kwargs):
		"""
		Specific operations to generate job or report instance dependencies.
		N.B. : you CANNOT use m2m relations before this point
		YOU MUST DEFINE THIS METHOD
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
			os.makedirs(self.home_folder_full_path)

		# BUILD instance specific R-File
		self.generate_r_file(kwargs['sections'], kwargs['request_data'])
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

	# TODO re-check
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

		config = self.sh_file_path
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
			if self.email != '':
				jt.email = jt.email.append(str(self.email))
			jt.blockEmail = False

			jt.remoteCommand = config
			jt.joinFiles = True

			self.progress = 25
			self.save()
			import copy
			if not self.aborting:
				self.sgeid = copy.deepcopy(s.runJob(jt))
				log.debug('%s%s : ' % self.short_id + 'returned sgedid "%s"' % self.sgeid)
				self.breeze_stat = JobStat.SUBMITTED
			# waiting for the job to end
			self.waiter(s, True)

			jt.delete()
			s.exit()
			os.chdir(default_dir)

		except (drmaa.AlreadyActiveSessionException, drmaa.InvalidArgumentException, drmaa.InvalidJobException,
				Exception) as e:
			log.exception('%s%s : ' % self.short_id + 'drmaa error %s' % e)
			log.error('%s%s : ' % self.short_id + 'drmaa job submit process unexpectedly terminated')
			self.breeze_stat = JobStat.FAILED
			if s is not None:
				s.exit()
			return 1

		log.debug('%s%s : ' % self.short_id + 'drmaa job submit terminated successfully !')
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
		import json
		import os
		import time

		exit_code = 42
		aborted = False
		log = get_logger()
		if self.is_sgeid_empty:
			return
		SGEID = copy.deepcopy(self.sgeid) # uselees
		try:
			retval = None
			if drmaa_waiting:
				retval = s.wait(SGEID, drmaa.Session.TIMEOUT_WAIT_FOREVER)
			else:
				try:
					while True:
						time.sleep(1)
						self.qstat_stat()
						if self.aborting:
							break
				except NoSuchJob:
					exit_code = 0

			self.breeze_stat = JobStat.DONE
			self.save()
			# time.sleep(3)

			# TODO this is SHITTY
			if self.aborting:
				aborted = True
				exit_code = 1
				self.breeze_stat = JobStat.ABORTED

			if isinstance(retval, drmaa.JobInfo):
				if retval.hasExited:
					exit_code = retval.exitStatus
				dic = retval.resourceUsage # FUTURE use for mail reporting
				aborted = retval.wasAborted

			self.progress = 100
			if exit_code == 0:
				self.breeze_stat = JobStat.DONE
				# At this point we know that SGE job is done.
				# But R code may have failed, so we need to check a specific file.
				log.info('%s%s : ' % self.short_id + 'sge job finished !')
				if not self.is_r_successful:
					if isinstance(retval, drmaa.JobInfo) and isfile(self._failed_file):
						json.dump(retval, open(self._failed_file, 'w'))
					self.breeze_stat = JobStat.ABORTED
					if drmaa_waiting:
						log.info('%s%s : ' % self.short_id + 'But R process failed !')
						# TODO is R failure on 1st level wait
					else:
						log.info('%s%s : ' % self.short_id + 'But R process failed OR user abort !')
						# TODO or 2nd level wait either R failure or user abort
				else:
					if isinstance(retval, drmaa.JobInfo):
						json.dump(retval, open(self._test_file, 'w'))
					self.breeze_stat = JobStat.SUCCEED # FULL SUCCESS
					log.info('%s%s : ' % self.short_id + ' SUCCESS !')
					# Report specific
					if self.is_report and self.fm_flag and isfile(self.fm_file_path):
						run = open(self.fm_file_path).read().split("\"")[1]
						os.system(run)
			else:
				if not aborted:
					json.dump(retval, open(self._failed_file, 'w'))
					log.warning('%s%s : ' % self.short_id + 'exit code %s, SGE failed' % exit_code)
					self.breeze_stat = JobStat.FAILED
				else:
					log.info('%s%s : ' % self.short_id + 'exit code %s, user aborted' % exit_code)
					self.breeze_stat = JobStat.ABORTED # TODO change for user abort

			return exit_code
		except Exception as e:
			# TODO this is SHITTY
			if e.message == 'code 24: no usage information was returned for the completed job' or self.aborting:
				self.breeze_stat = JobStat.ABORTED
			log.exception('%s%s : ' % self.short_id + ' while waiting : %s' % e)
		return 1

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
		:rtype: str
		"""
		try:
			return self._stat_text
		except AttributeError:
			return JobStat.textual(self._status)

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

	def re_submit_to_cluster(self):
		""" Reset the job status, so it can be run again
		Use this, if it hadn't had an SGEid or the run was unexpectedly terminated
		DO NOT WORK on SUCCEEDED JOB."""
		if not self.is_successful:
			get_logger().info('%s%s : resetting job status' % self.short_id)
			self.submit_to_cluster()

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
		return 'report' if self.is_report else 'job' if self.is_job else 'abstract'

	@property
	def instance_of(self):
		# return Report if self.is_report else Jobs if self.is_job else self.__class__
		return self.__class__

	@property
	def short_id(self):
		return self.instance_type[0], self.id

	@property
	def text_id(self):
		return '%s%s %s' % (self.short_id + (self.name,))

	def __unicode__(self): # Python 3: def __str__(self):
		return '%s' % self.text_id

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

	def deferred_instance_specific(self, *args, **kwargs):
		kwargs['sections'].write(str(settings.TEMP_FOLDER) + 'job.xml') # change with ml

	def generate_r_file(self, tree, request_data):
		"""
		generate the Nozzle generator R file
		:param tree: Rscripts tree from xml
		:type tree: ?
		:param request_data:
		:type request_data: HttpRequest
		"""
		from django.core.files import base
		from breeze import shell as rshell

		# TODO : Find a way to solve this dependency issue
		params = rshell.gen_params_string_job_temp(tree, request_data.POST, self, request_data.FILES) # TODO funct
		code = "setwd('%s')\n%s" % (self.home_folder_full_path[:-1], self._type.get_R_code(params))

		# save r-file
		self._rexec.save(self.R_FILE_NAME, base.ContentFile(code))

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
		return '%sreport' % self.home_folder_full_path

	@property
	def _rtype_config_path(self):
		return settings.MEDIA_ROOT + str(self.type.config)

	@property
	def title(self):
		return '%s Report :: %s  <br>  %s' % (self.type, self.name, self.type.description)

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
			return '?%s' % urlencode([('path', self._home_folder_rel), ('roraId', str(self.rora_id))])
		else:
			return ''

	def has_access_to_shiny(self, this_user):
		assert isinstance(this_user, (User, OrderedUser))
		return this_user and (this_user in self.shared.all() or self._author == this_user) \
			and self._type.shiny_report.enabled

	_path_r_template = settings.NOZZLE_REPORT_TEMPLATE_PATH

	def deferred_instance_specific(self, *args, **kwargs):
		import pickle
		import json

		request_data = kwargs['request_data']# self.request_data
		sections = kwargs['sections']

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
		if self._type.is_shiny_enabled:
			self.generate_shiny_key()

		if 'shared_users' in kwargs.keys():
			self.shared = kwargs['shared_users']

	_path_tag_r_template = settings.TAGS_TEMPLATE_PATH

	# TODO : use clean or save ?
	def generate_r_file(self, sections, request_data):
		"""
		generate the Nozzle generator R file
		:param sections: Rscripts list
		:type sections: list
		:param request_data:
		:type request_data: HttpRequest
		"""
		from string import Template
		from django.core.files import base
		from breeze import shell as rshell
		import xml.etree.ElementTree as XmlET

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
				tag_list.append(tag.get_R_code(gen_params) + report_specific)

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
		dump += open(self._rtype_config_path).read() + '\n'
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
		if self._type.is_shiny_enabled and self.is_successful:
			# call symbolic link update
			self.type.shiny_report.link_report(self, True)

	def delete(self, using=None):
		if self.type.shiny_report_id > 0:
			self.type.shiny_report.unlink_report(self)

		return super(Report, self).delete(using=using) # Call the "real" delete() method.

	class Meta(Runnable.Meta): # TODO check if inheritance is required here
		abstract = False
		db_table = 'breeze_report'


class Statistics(models.Model):
	# script = models.CharField(max_length=55)
	script = ForeignKey(Rscripts)
	author = ForeignKey(User)
	istag = models.BooleanField(default=False)
	times = models.PositiveSmallIntegerField(default=0)
	
	def __unicode__(self):
		return self.script
	
	class Meta:
		ordering = ['-times']


class ShinyTag(models.Model):
	ACL_RW_RW_R = 0664
	FILE_UI_NAME = settings.SHINY_UI_FILE_NAME
	FILE_SERVER_NAME = settings.SHINY_SERVER_FILE_NAME
	FILE_DASH_UI = settings.SHINY_DASH_UI_FILE
	TAG_FOLDER = settings.SHINY_TAGS
	RES_FOLDER = settings.SHINY_RES_FOLDER
	FILE_TEMPLATE = settings.SHINY_TAG_CANVAS_PATH
	FILE_TEMPLATE_URL = settings.MEDIA_URL + settings.SHINY_TAG_CANVAS_FN
	DEFAULT_MENU_ITEM = 'menuItem("Quality Control", icon = icon("filter", lib = "glyphicon"), tabName = "REPLACE BY THE NAME OF YOUR TAG IN UPPER CASE HERE",' \
		'badgeLabel = "QC", badgeColor = "green")'

	name = models.CharField(max_length=55, unique=True, blank=False,
		help_text="Must be unique, no special characters, no withe spaces."
					"<br />NB : Use the same (in upper case) in the tabName field of the menu entry")
	label = models.CharField(max_length=32, blank=False, help_text="The text to be display on the dashboard")
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

	@property
	def folder_name(self):
		return str('%s%s/' % (self.TAG_FOLDER, self.get_name))

	@property
	def path_dashboard_server(self):
		return str('%s%s' % (self.folder_name, self.FILE_SERVER_NAME))

	@property
	def path_dashboard_body(self):
		return str('%s%s' % (self.folder_name, self.FILE_UI_NAME))

	@property
	def path_res_folder(self):
		return str('%s%s' % (self.folder_name, self.RES_FOLDER))

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
		(FILE_TEMPLATE_URL, settings.SHINY_LIBS_BREEZE_URL))
	enabled = models.BooleanField()
	attached_report = models.ManyToManyField(ShinyReport)

	def save(self, *args, **kwargs):
		super(ShinyTag, self).save(*args, **kwargs) # Call the "real" save() method.
		for each in self.attached_report.all():
			each.regen_report()

	# Manages folder creation, zip verification and extraction
	def clean(self):
		import zipfile
		import shutil
		import os

		def temp_cleanup(): # removes the zip from temp upload folder (thus forcing re-upload)
			self.remove_file_safe(self.zip_file)

		# TODO manage old zip deletion

		# Added 27/08/2015 : enables non re-upload of zip archive for each form validation
		# while being secure, preventing file spoofing (and thus code injection)
		from django.db.models.fields.files import FieldFile
		if type(self.zip_file) == file or type(self.zip_file) == FieldFile:
			md5 = get_md5(self.zip_file.read())
			dest = settings.UPLOAD_FOLDER + 'shiny_tag_%s.zip' % md5
			self.zip_file.name = dest

		try: # loads zip file
			zf = zipfile.ZipFile(self.zip_file)
		except Exception as e:
			temp_cleanup()
			raise ValidationError({ 'zip_file': ["while loading zip_lib says : %s" % e] })
		# check both ui.R and server.R are in the zip and non empty
		for filename in [self.FILE_SERVER_NAME, self.FILE_UI_NAME]:
			try:
				info = zf.getinfo(filename)
			except KeyError:
				temp_cleanup()
				raise ValidationError({ 'zip_file': ["%s not found in zip's root" % filename] })
			except Exception as e:
				temp_cleanup()
				raise ValidationError({ 'zip_file': ["while listing zip_lib says : %s" % e] })
			# check that the file is not empty
			if info.file_size < settings.SHINY_MIN_FILE_SIZE:
				temp_cleanup()
				raise ValidationError({ 'zip_file': ["%s file is empty" % filename] })
		# clear the folder
		shutil.rmtree(self.folder_name[:-1], ignore_errors=True)
		# extract the zip
		zf.extractall(path=self.folder_name)
		# changing files permission
		for item in os.listdir(self.folder_name[:-1]):
			path = '%s%s' % (self.folder_name, item)
			if os.path.isfile(path):
				# print 'chmod %s' % path, self.ACL_RW_RW_R
				os.chmod(path, self.ACL_RW_RW_R)
		# removes the zip from temp upload folder
		#temp_cleanup()
		self.save()

	def delete(self, using=None):
		import shutil

		log_obj = get_logger()
		log_obj.info("deleted shinyTag %s : %s" % (self.id, self))

		# Deleting the folder
		shutil.rmtree(self.folder_name[:-1], ignore_errors=True)
		super(ShinyTag, self).delete(using=using) # Call the "real" delete() method.

	class Meta:
		ordering = ('order',)

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

from watcher import with_drmaa
