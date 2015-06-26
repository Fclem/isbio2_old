from django.db import models
from django.template.defaultfilters import slugify
from django.db.models.fields.related import ForeignKey
from django.contrib.auth.models import User # as DjangoUser
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpRequest
import logging, sys

logger = logging.getLogger(__name__)

CATEGORY_OPT = (
	(u'general', u'General'),
	(u'visualization', u'Visualization'),
	(u'screening', u'Screening'),
	(u'sequencing', u'Sequencing'),
)


def remove_file_safe(fname):
	"""
	Remove a file or link if it exists
	:param fname: the path of the file/link to delete
	:type fname: str
	:return: True or False
	:rtype: bool
	"""
	import os.path

	try:
		if os.path.isfile(fname) or os.path.islink(fname):
			os.remove(fname)
			return True
	except:
		pass
	return False


def auto_symlink(target, holder):
	"""
	Make a soft-link and overwrite any previously existing file (be careful !) or link with the same name
	:param target: target path of the link
	:type target: str
	:param holder: path of the link holder
	:type holder: str
	"""
	import os

	log_obj = logger.getChild(sys._getframe().f_code.co_name)
	assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only

	remove_file_safe(holder)
	if settings.VERBOSE: print "symlink to", target, "@", holder
	log_obj.debug("symlink to %s @ %s" % (target, holder))
	os.symlink(target, holder)
	return True

# TODO : move all the logic into objects here

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
		import shutil, os.path
		shutil.rmtree(self._folder_path_base, ignore_errors=True)
		os.mkdir(self._folder_path_base, self.FS_ACL)
		os.mkdir(self._link_holder_path, self.FS_ACL)
		os.mkdir(self.folder_path, self.FS_ACL)
		# os.mkdir('%s%s/' % (self.folder_path, self.UI_FOLDER), self.FS_ACL)
		# os.mkdir('%s%s/' % (self.folder_path, self.SERVER_FOLDER), self.FS_ACL)
		os.mkdir('%s%s/' % (self.folder_path, self.RES_FOLDER), self.FS_ACL)
		# link the dashboard 'tag'
		# auto_symlink(self.path_dash_ui_r_template(), self.folder_path + self.FILE_DASH_UI)
		# auto_symlink(self.path_dash_server_r_template(), self.folder_path + self.FILE_DASH_SERVER)

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
		log_obj = logger.getChild(sys._getframe().f_code.co_name)
		assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only
		log_obj.debug("updating shinyReport %s slink for report %s %s" % (self.id, report.id, 'FORCING' if force else ''))

		import os
		assert isinstance(report, Report)
		# handles individually each generated report of this type
		report_home = report.get_home
		report_link = self.report_link(report)
		# if the home folder of the report exists, and the link doesn't yet
		if os.path.isdir(report_home[:-1]) and report_home != settings.MEDIA_ROOT:
			# check that the report has all required files
			if not force:
				j = self.related_files()
				for each in j: # for every required registered file
					path = '%s%s' % (report_home, each['path'])
					if each['required'] and not (os.path.isfile(path) and os.access(path, os.R_OK)):
						if settings.VERBOSE: print report.id, "missing file", path
						log_obj.debug("%s missing required file %s" % (report.id, path))
						return
			if force or not os.path.islink(report_link):
				# make of soft-link for each files/folder of the shinyReport folder into the Report folder
				for item in os.listdir(self.folder_path):
					auto_symlink('%s%s' % (self.folder_path, item), '%s%s' % (report_home, item))
				# Creates a slink in shinyReports to the actual report
				auto_symlink(report_home[:-1], report_link)
		else: # the target report is missing we remove the link
			self.unlink_report(report)

	def unlink_report(self, report):
		"""
		Do the opposite of link_report, usefull if a specific Report has been individually deleted
		:param report: a valid Report instance
		:type report: Report
		"""
		assert isinstance(report, Report)
		import os
		# handles individually each generated report of this type
		report_home = report.get_home
		report_link = self.report_link(report)

		# if the home folder of the report exists, and the link doesn't yet
		if os.path.isdir(report_home[:-1]) and report_home != settings.MEDIA_ROOT:
			# removes the soft-link for each files/folder of the shinyReport folder into the Report folder
			for item in os.listdir(self.folder_path):
				remove_file_safe('%s%s' % (report_home, item))
		if os.path.islink(report_link):
			# removes the slink in shinyReports to the actual report
			remove_file_safe(report_link) # unlink from shiny

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
		filein = open(self.path_server_r_template())
		src = Template(filein.read())
		# document data
		generated = 'Generated on %s for user %s (%s)' % (self.created, self.author.get_full_name(), self.author)
		updated = 'Last updated on %s for user %s (%s)' % (aux.dateT(), a_user.get_full_name(), a_user)
		alist = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				# add it to the source list
				alist.append('### Tag %s by %s (%s) %s%ssource("%s",local = TRUE)' % (
					each.name, each.author.get_full_name(), each.author, each.created, SEP, each.path_dashboard_server))
		loaders = self.get_parsed_loader()
		alist.append('') # avoid join errors if list is empty
		d = { 'title': self.title,
				'generated': generated,
				'updated': updated,
				'loaders': loaders,
				'sources': SEP.join(alist)
			}
		assert(isinstance(src, Template))
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
		filein = open(self.path_ui_r_template())
		src = Template(filein.read())
		filein.close()
		# document data
		generated = 'Generated on %s for user %s (%s)' % (self.created, self.author.get_full_name(), self.author)
		updated = 'Last updated on %s for user %s (%s)' % (aux.dateT(), a_user.get_full_name(), a_user)
		alist = list(); tag_vars = list(); menu_list = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				self.import_tag_res(each)
				alist.append('### Tag %s by %s (%s) %s%ssource("%s",local = TRUE)' % (
					each.name, each.author.get_full_name(), each.author, each.created, SEP, each.path_dashboard_body))
				tag_vars.append(each.get_name.upper())
				menu_list.append(each.menu_entry)
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
		filein = open(self.path_global_r_template())
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
		d = {'generated': generated,
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
		log_obj = logger.getChild(sys._getframe().f_code.co_name)
		assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only
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
		log_obj = logger.getChild(sys._getframe().f_code.co_name)
		assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only
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


class ReportType(models.Model):
	def __init__(self, *args, **kwargs):
		super(ReportType, self).__init__(*args, **kwargs)
		self.__important_fields = ['shiny_report_id', ]
		for field in self.__important_fields:
			setattr(self, '__original_%s'%field, getattr(self, field))

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
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(str(self.id) + '_' + self.type)
		return 'pipelines/%s/%s' % (slug, filename)
	
	config = models.FileField(upload_to=file_name, blank=True, null=True)
	manual = models.FileField(upload_to=file_name, blank=True, null=True)
	created = models.DateField(auto_now_add=True)

	shiny_report = models.ForeignKey(ShinyReport, help_text="Choose an existing Shiny report to attach it to", default=0)

	def has_changed(self):
		for field in self.__important_fields:
			orig = '__original_%s'%field
			if getattr(self, orig) != getattr(self, field):
				return True
		return False

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
	
	class Meta:
		ordering = ('type',)


class Script_categories(models.Model):
	category = models.CharField(max_length=55, unique=True)
	description = models.CharField(max_length=350, blank=True)
	# if the script is a drat then the category should be inactive
	# active = models.BooleanField(default=False)
	
	def __unicode__(self):
		return self.category


class User_date(models.Model):
	user = ForeignKey(User)
	install_date = models.DateField(auto_now_add=True)
	
	def __unicode__(self):
		return self.user.username


class Rscripts(models.Model):
	name = models.CharField(max_length=35, unique=True)
	inln = models.CharField(max_length=150, blank=True)
	details = models.CharField(max_length=5500, blank=True)
	# category = models.CharField(max_length=25, choices=CATEGORY_OPT, default=u'general')
	category = ForeignKey(Script_categories, to_field="category")
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
	#report_type = models.ForeignKey(ReportType, null=True, blank=True, default=None)  # assosiation with report type
	access = models.ManyToManyField(User, null=True, blank=True, default=None, related_name="users")
	#install date info
	install_date = models.ManyToManyField(User_date, blank=True, null=True, default=None, related_name="installdate")
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.name)
		return 'scripts/%s/%s.%s' % (slug, slug, extension)
	
	docxml = models.FileField(upload_to=file_name, blank=True)
	code = models.FileField(upload_to=file_name, blank=True)
	header = models.FileField(upload_to=file_name, blank=True)
	logo = models.FileField(upload_to=file_name, blank=True)
	
	def __unicode__(self):
		return self.name

	@property
	def sec_id(self):
		return 'Section_dbID_%s' % self.id

	_path_r_template = settings.TAGS_TEMPLATE_PATH

	@property
	def _code_path(self):
		return settings.MEDIA_ROOT + str(self.code)

	@property
	def _header_path(self):
		return settings.MEDIA_ROOT + str(self.header)

	@property
	def xml_path(self):
		return settings.MEDIA_ROOT + str(self.docxml)

	def get_R_code(self, gen_params):
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

	class Meta:
		ordering = ["name"]


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


# 04/06/2015 WIP
class Worker(models.Model):

	class Meta:
		abstract = True


class Jobs(models.Model):
	jname = models.CharField(max_length=55)
	jdetails = models.CharField(max_length=4900, blank=True)
	juser = ForeignKey(User)
	script = ForeignKey(Rscripts)
	# status may be changed to NUMVER later
	status = models.CharField(max_length=15, help_text="scheduled|active|succeed|failed|aborted")
	staged = models.DateTimeField(auto_now_add=True)
	progress = models.IntegerField()
	sgeid = models.CharField(max_length=15, blank=True, help_text="SGE job id")
	mailing = models.CharField(max_length=3, blank=True, help_text='configuration of mailing events : (b)egin (e)nd  (a)bort or empty')  # TextField(name="mailing", )
	email = models.CharField(max_length=75, help_text=
		"mail address to send the notification to (not working ATM : your personal mail adress will be user instead)")

	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.jname + '_' + self.juser.username)
		return 'jobs/%s/%s.%s'%(slug, slug, extension)

	docxml = models.FileField(upload_to=file_name)
	rexecut = models.FileField(upload_to=file_name)
	breeze_stat = models.CharField(max_length=16, default='init')

	def __unicode__(self):
		return self.jname


# 04/06/2015
class JobsH(Jobs):
	@property
	def type(self):
		return self.script

	@property
	def name(self):
		return self.jname

	@property
	def description(self):
		return self.jdetails

	@property
	def author(self):
		return self.juser

	@property
	def created(self):
		return self.staged

	@property
	def home(self):
		return ''

	@property
	def rexec(self):
		return self.rexecut

	@property
	def dochtml(self):
		return self.docxml

	@property
	def institute(self):
		return Institute.objects.get(id=0)

	@property
	def project(self):
		return ''

	@property
	def shared(self):
		return []

	@property
	def conf_params(self):
		return ''

	@property
	def conf_files(self):
		return ''

	@property
	def shiny_key(self):
		return ''

	@property
	def rora_id(self):
		return 0

	@property
	def args_string(self):
		return ''

	class Meta:
		abstract = True


class Report(models.Model):
	type = models.ForeignKey(ReportType)
	name = models.CharField(max_length=55)
	description = models.CharField(max_length=350, blank=True)
	author = ForeignKey(User)
	created = models.DateTimeField(auto_now_add=True)
	# home = models.CharField(max_length=155, blank=True)
	# _status = models.CharField(max_length=15, blank=True, db_column="status")
	# TODO change to StatusModel cf https://django-model-utils.readthedocs.org/en/latest/models.html#statusmodel
	status = models.CharField(max_length=15, blank=True)
	progress = models.PositiveSmallIntegerField(default=0)
	sgeid = models.CharField(max_length=15)
	# store the institute info of the user who creates this report
	institute = ForeignKey(Institute, default=Institute.objects.get(id=1))
	
	project = models.ForeignKey(Project, null=True, blank=True, default=None)
	shared = models.ManyToManyField(User, null=True, blank=True, default=None,
									related_name='report_shares')  # share list
	conf_params = models.TextField(null=True, help_text="!! DO NOT EDIT !!", editable=False)
	# conf_params = models.(null=True, blank=True, default=None)
	conf_files = models.TextField(null=True, help_text="!! DO NOT EDIT !!", editable=False)
	
	shiny_key = models.CharField(max_length=64, null=True, help_text="!! DO NOT EDIT !!", editable=False)
	rora_id = models.PositiveIntegerField(default=0)
	breeze_stat = models.CharField(max_length=16, default='init')

	# offsite_user_access = models.ManyToManyField(OffsiteUser)
	# conf_files = models.CharField(null=True, blank=True, default=None)
	
	def file_name(self, filename):
		# fname, dot, extension = filename.rpartition('.')
		slug = self.folder_name
		return 'reports/%s/%s' % (slug, filename)
	
	rexec = models.FileField(upload_to=file_name, blank=True)
	dochtml = models.FileField(upload_to=file_name, blank=True)

	fm_flag = models.BooleanField(default=False)

	# 04/06/2015
	@property
	def args_string(self):
		""" The query string to be passed for shiny apps, if Report is Shiny-enabled, or blank string	"""
		from django.utils.http import urlencode
		if self.rora_id > 0:
			return '?%s' % urlencode([('path', self.home), ('roraId', str(self.rora_id))])
		else:
			return ''

	# 25/06/15
	@property
	def folder_name(self):
		return slugify('%s_%s_%s' % (self.id, self.name, self.author.username))

	# 25/06/15
	@property
	def r_exec_path(self):
		return '%s%s/'%(settings.MEDIA_ROOT, self.rexec)

	# 25/06/15
	@property
	def home(self):
		"""
		Returns the relative path to this report folder
		:return: the relative path to this report folder
		:rtype: str
		"""
		return '%s%s/' % (settings.REPORTS_FOLDER, self.folder_name)

	# 16/06/15
	@property
	def get_home(self):
		"""
		Returns the absolute path to this report folder
		:return: the absolute path to this report folder
		:rtype: str
		"""
		return '%s%s' % (settings.MEDIA_ROOT, self.home)

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

	def has_access_to_shiny(self, this_user):
		assert isinstance(this_user, (User, OrderedUser))
		return this_user and (this_user in self.shared.all() or self.author == this_user) \
				and self.type.shiny_report.enabled

	_path_r_template = settings.NOZZLE_REPORT_TEMPLATE_PATH

	@property
	def _rtype_config_path(self):
		return settings.MEDIA_ROOT + str(self.type.config)

	# TODO : use clean or save ?
	def generate_R_file(self, sections, request_data):
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
		import xml.etree.ElementTree as xml

		filein = open(self._path_r_template)
		src = Template(filein.read())
		filein.close()
		tag_list = list()
		self.fm_flag = False
		for tag in sections:
			assert (isinstance(tag, Rscripts)) # useful for code assistance ONLY
			if tag.sec_id in request_data.POST and request_data.POST[tag.sec_id] == '1':
				tree = xml.parse(tag.xml_path)
				if tag.name == "Import to FileMaker":
					self.fm_flag = True

				gen_params = rshell.gen_params_string(tree, request_data.POST, self.home, request_data.FILES)
				tag_list.append( tag.get_R_code(gen_params) )

		d = { 'loc': self.get_home,
				'report_name': self.title,
				'project_parameters': self.dump_project_parameters,
				'pipeline_config': self.dump_pipeline_config,
				'tags': '\n'.join(tag_list),
				'dochtml': self.dochtml,
			}
		# do the substitution
		result = src.substitute(d)
		# save r-file
		self.rexec.save('script.r', base.ContentFile(result))

	@property
	def dump_project_parameters(self):
		import copy
		dump = '# <----------  Project Details  ----------> \n'
		dump += 'report.author          <- \"%s\"\n'%self.author.username
		dump += 'report.pipeline        <- \"%s\"\n'%self.type
		dump += 'project.name           <- \"%s\"\n'%self.project.name
		dump += 'project.manager        <- \"%s\"\n'%self.project.manager
		dump += 'project.pi             <- \"%s\"\n'%self.project.pi
		dump += 'project.author         <- \"%s\"\n'%self.project.author
		dump += 'project.collaborative  <- \"%s\"\n'%self.project.collaborative
		dump += 'project.wbs            <- \"%s\"\n'%self.project.wbs
		dump += 'project.external.id    <- \"%s\"\n'%self.project.external_id
		dump += '# <----------  end of Project Details  ----------> \n\n'
		
		return copy.copy(dump)

	@property
	def dump_pipeline_config(self):
		import copy
		dump = '# <----------  Pipeline Config  ----------> \n'
		dump += 'query.key          <- \"%s\"  # id of queried RORA instance \n'% self.rora_id
		dump += open(self._rtype_config_path).read() + '\n'
		dump += '# <------- end of Pipeline Config --------> \n\n\n'

		return copy.copy(dump)

	@property
	def title(self):
		return '%s Report :: %s  <br>  %s' % (self.type, self.name, self.type.description)

	@property
	def html_path(self):
		return '%sreport' % self.get_home

	def generate_shiny_key(self):
		"""
		Generate a sha256 key for outside access
		"""
		from datetime import datetime
		from hashlib import sha256
		m = sha256()
		m.update(settings.SECRET_KEY + self.folder_name + str(datetime.now()))
		self.shiny_key = str(m.hexdigest())

	def run(self):
		pass

	def save(self, *args, **kwargs):
		super(Report, self).save(*args, **kwargs) # Call the "real" save() method.
		if self.type.shiny_report_id > 0 and len(self.home) > 1:
			# call symbolic link update
			self.type.shiny_report.link_report(self, True)

	def delete(self, using=None):
		import os, shutil

		if os.path.isdir(self.get_home[:-1]):
			shutil.rmtree(self.get_home[:-1])
		if self.type.shiny_report_id > 0:
			self.type.shiny_report.unlink_report(self)
		super(Report, self).delete(using=using) # Call the "real" save() method.

		log_obj = logger.getChild(sys._getframe().f_code.co_name)
		assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only
		log_obj.info("report %s : %s has been deleted" % (self.id, self))

		return True
	#@property
	#def status(self):
	#	if self.status == 'init':
	#		return 'queued active'
	#	return self.status
	
	# @status.setter
	# def status(self, value):
	
	def __unicode__(self):
		return self.name


# 04/06/2015
# Mapper to enable usage of Jobs and Report alike (design/implementation ERROR)
class ReportH(Report):
	@property
	def jname(self):
		return self.name

	@property
	def jdetails(self):
		return self.description

	@property
	def juser(self):
		return self.author

	@property
	def staged(self):
		return self.created

	@property
	def mailing(self):
		return ''

	@property
	def email(self):
		return ''

	@property
	def docxml(self):
		return self.dochtml

	@property
	def rexecut(self):
		return self.rexec

	class Meta:
		abstract = True


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
	DEFAULT_MENU_ITEM = 'menuItem("Quality Control", icon = icon("filter", lib = "glyphicon"), tabName = "QC",' \
						'badgeLabel = "QC", badgeColor = "green")'

	name = models.CharField(max_length=55, unique=True, blank=False,
							help_text="Must be unique, no special characters.")
	label = models.CharField(max_length=32, blank=False,
								help_text="The text to be display on the dashboard")
	description = models.CharField(max_length=350, blank=True,
									help_text="Optional description text")
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

		try:
			if os.path.isfile(fname):
				os.remove(fname)
		except:
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
		name = str('%s%s_%s' % (settings.UPLOAD_FOLDER, self.get_name, slugify(filename)))
		self.remove_file_safe(name)
		return str(name)

	zip_file = models.FileField(upload_to=file_name_zip, blank=False, null=False,
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
		import zipfile, shutil, os

		# Regenerates every attached reports FS's
		# for each in self.attached_report.all():
		#	each.regen_report(self.author)

		def temp_cleanup(): # removes the zip from temp upload folder
			self.remove_file_safe(self.zip_file)

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
			path = '%s%s'%(self.folder_name, item)
			if os.path.isfile(path):
				print 'chmod %s' % path, self.ACL_RW_RW_R
				os.chmod(path, self.ACL_RW_RW_R)
		# removes the zip from temp upload folder
		temp_cleanup()
		self.save()

	def delete(self, using=None):
		import shutil
		log_obj = logger.getChild(sys._getframe().f_code.co_name)
		assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only
		log_obj.info("deleted shinyTag %s : %s"%(self.id, self))

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
	email = models.CharField(max_length=64, blank=False, unique=True, help_text="Valid email address of the off-site user")
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
