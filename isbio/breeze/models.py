from django.db import models
from django.template.defaultfilters import slugify
from django.db.models.fields.related import ForeignKey
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

CATEGORY_OPT = (
	(u'general', u'General'),
	(u'visualization', u'Visualization'),
	(u'screening', u'Screening'),
	(u'sequencing', u'Sequencing'),
)


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
	institute = ForeignKey(Institute)
	
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
	
	def __unicode__(self):
		return self.name


class ReportType(models.Model):
	type = models.CharField(max_length=17, unique=True)
	description = models.CharField(max_length=5500, blank=True)
	search = models.BooleanField(default=True)
	access = models.ManyToManyField(User, null=True, blank=True, default=None,
									related_name='pipeline_access')  # share list
	# tags = models.ManyToManyField(Rscripts, blank=True)
	
	# who creates this report
	author = ForeignKey(User)
	# store the institute info of the user who creates this report
	institute = ForeignKey(Institute)
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(str(self.id) + '_' + self.type)
		return 'pipelines/%s/%s' % (slug, filename)
	
	config = models.FileField(upload_to=file_name, blank=True, null=True)
	manual = models.FileField(upload_to=file_name, blank=True, null=True)
	created = models.DateField(auto_now_add=True)
	
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
	mailing = models.CharField(max_length=3, blank=True, help_text="configuration of mailing events : (b)egin (e)nd "
																  "(a)bort or empty")  # TextField(name="mailing", )
	email = models.CharField(max_length=75,
							help_text="mail address to send the notification to (not working ATM : your personal mail adress will be user instead)")
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.jname + '_' + self.juser.username)
		return 'jobs/%s/%s.%s' % (slug, slug, extension)
	
	docxml = models.FileField(upload_to=file_name)
	rexecut = models.FileField(upload_to=file_name)
	breeze_stat = models.CharField(max_length=16, default='init')
	
	def __unicode__(self):
		return self.jname


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
	user = models.ForeignKey(User, unique=True)
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.name)
		return 'profiles/%s/%s.%s' % (slug, slug, extension)
	
	fimm_group = models.CharField(max_length=75, blank=True)
	logo = models.FileField(upload_to=file_name, blank=True)
	institute_info = models.ForeignKey(Institute)
	# if user accepts the agreement or not
	db_agreement = models.BooleanField(default=False)
	last_active = models.DateTimeField(default=timezone.now)
	
	def __unicode__(self):
		return self.user.get_full_name()  # return self.user.username


class BlobField(models.Field):
	description = "Blob"
	
	def db_type(self, connection):
		return 'blob'
	
	def __unicode__(self):
		return self.value_to_string()


class Report(models.Model):
	type = models.ForeignKey(ReportType)
	name = models.CharField(max_length=55)
	description = models.CharField(max_length=350, blank=True)
	author = ForeignKey(User)
	created = models.DateTimeField(auto_now_add=True)
	home = models.CharField(max_length=155, blank=True)
	# _status = models.CharField(max_length=15, blank=True, db_column="status")
	# TODO change to StatusModel cf https://django-model-utils.readthedocs.org/en/latest/models.html#statusmodel
	status = models.CharField(max_length=15, blank=True)
	progress = models.PositiveSmallIntegerField(default=0)
	sgeid = models.CharField(max_length=15)
	# store the institute info of the user who creates this report
	institute = ForeignKey(Institute)
	
	project = models.ForeignKey(Project, null=True, blank=True, default=None)
	shared = models.ManyToManyField(User, null=True, blank=True, default=None,
									related_name='report_shares')  # share list
	conf_params = models.TextField(null=True, help_text="!! DO NOT EDIT !!")
	# conf_params = models.(null=True, blank=True, default=None)
	conf_files = models.TextField(null=True, help_text="!! DO NOT EDIT !!")
	
	shiny_key = models.CharField(max_length=64, null=True, help_text="!! DO NOT EDIT !!")
	rora_id = models.PositiveIntegerField(default=0)
	breeze_stat = models.CharField(max_length=16, default='init')

	# offsite_user_access = models.ManyToManyField(OffsiteUser)
	# conf_files = models.CharField(null=True, blank=True, default=None)
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(str(self.id) + '_' + self.name + '_' + self.author.username)
		return 'reports/%s/%s' % (slug, filename)
	
	rexec = models.FileField(upload_to=file_name, blank=True)
	dochtml = models.FileField(upload_to=file_name, blank=True)
	
	# TODO way to do it (use props everywhere)
	#@property
	#def status(self):
	#	if self.status == 'init':
	#		return 'queued active'
	#	return self.status
	
	# @status.setter
	# def status(self, value):
	
	def __unicode__(self):
		return self.name


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


class ShinyApp(models.Model):
	FILE_UI_NAME = 'ui.R'
	FILE_SERVER_NAME = 'server.R'

	name = models.CharField(max_length=55, unique=True, blank=False,
							help_text="Must be unique, no special characters, as it will be used as the folder name")
	label = models.CharField(max_length=64, blank=False,
							help_text="The text to be displayed on the report index list")
	
	description = models.CharField(max_length=350, blank=True,
								  help_text="Optional description text")
	author = ForeignKey(User)
	created = models.DateTimeField(auto_now_add=True)
	# _home = models.CharField(max_length=155, unique=True, blank=False)
	institute = ForeignKey(Institute, default=Institute.objects.get(id=1))

	order = models.PositiveIntegerField(default=0, help_text="index number (0 is the topmost)")

	@property
	def home(self):
		return str(settings.SHINY_APPS + '%s' % slugify(str(self.name)))

	@property
	def get_name(self):
		return slugify(str(self.name))

	@staticmethod
	def remove_file_safe(fname):
		import os.path
		try:
			if os.path.isfile(fname):
				os.remove(fname)
		except:
			pass

	def file_name_gen(self):
		return str(settings.SHINY_APPS + '%s'%slugify(str(self.name)))

	def file_name_ui(self):
		return str(self.folder_name()) + settings.SHINY_UI_FILE_NAME

	def file_name_server(self):
		return str(self.folder_name()) + settings.SHINY_SERVER_FILE_NAME

	def folder_name(self):
		return str(settings.SHINY_APPS + '%s/'%slugify(str(self.name)))

	def file_name_zip(self, filename):
		name = str(settings.UPLOAD_FOLDER + '%s_%s'%(slugify(str(self.name)), slugify(filename)))
		self.remove_file_safe(name)
		return str(name)
	
	# Rui = models.FileField(upload_to=file_name_ui, blank=True, null=True)
	# Rserver = models.FileField(upload_to=file_name_server, blank=True, null=True)
	zip_file = models.FileField(upload_to=file_name_zip, blank=False, null=False,
								help_text="Upload a zip file containing at least %s and %s files;<br />Any included file named 'report' will be discarded"%
									(settings.SHINY_UI_FILE_NAME, settings.SHINY_SERVER_FILE_NAME))
	enabled = models.BooleanField()
	attached_report = models.ManyToManyField(ReportType)

	# Manages folder creation, soft-linking to reports and zip verification and extraction
	def clean(self):
		import zipfile, shutil, subprocess, os

		def temp_cleanup(): # removes the zip from temp upload folder
			self.remove_file_safe(self.zip_file)

		try: # loads zip file
			zf = zipfile.ZipFile(self.zip_file)
		except Exception as e:
			temp_cleanup()
			raise ValidationError({ 'zip_file': ["while loading zip_lib says : %s"%e] })
		# check both ui.R and server.R are in the zip and non empty
		for filename in [settings.SHINY_UI_FILE_NAME, settings.SHINY_SERVER_FILE_NAME]:
			try:
				info = zf.getinfo(filename)
			except KeyError:
				temp_cleanup()
				raise ValidationError({ 'zip_file': ["%s not found in zip's root"%filename] })
			except Exception as e:
				temp_cleanup()
				raise ValidationError({ 'zip_file': ["while listing zip_lib says : %s"%e] })
			# check that the file is not empty
			if info.file_size < settings.SHINY_MIN_FILE_SIZE:
				temp_cleanup()
				raise ValidationError({ 'zip_file': ["%s file is empty"%filename] })
		# clear the folder
		shutil.rmtree(self.folder_name(), ignore_errors=True)
		# extract the zip
		zf.extractall(path=self.folder_name())
		# removes the zip from temp upload folder
		temp_cleanup()
		# creates symbolic link to reports inside the shiny app folder
		self.remove_file_safe(self.folder_name() + 'reports') # just in case it was included in the zip
		os.symlink(settings.REPORTS_PATH, '%sreports'%self.folder_name())
		# if self.attached_report.count() == 0:
		# raise Validation_Error('ShinyApp must be attached to at least one ReportType')


	class Meta:
		ordering = ('name',)
	
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

	def __unicode__(self):
		return unicode(self.full_name)
