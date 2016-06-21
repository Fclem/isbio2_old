from django.template.defaultfilters import slugify
from django.db import models
from utils import *


__version__ = '0.1'
__author__ = 'clem'
__date__ = '27/05/2016'


class DrmaaJobState(object):
	UNDETERMINED = 'undetermined'
	QUEUED_ACTIVE = 'queued_active'
	SYSTEM_ON_HOLD = 'system_on_hold'
	USER_ON_HOLD = 'user_on_hold'
	USER_SYSTEM_ON_HOLD = 'user_system_on_hold'
	RUNNING = 'running'
	SYSTEM_SUSPENDED = 'system_suspended'
	USER_SUSPENDED = 'user_suspended'
	USER_SYSTEM_SUSPENDED = 'user_system_suspended'
	DONE = 'done'
	FAILED = 'failed'


class JobState(DrmaaJobState):
	SUSPENDED = 'suspended'
	PENDING = 'pending'
	TRANSFERRING = 'transferring'
	ON_HOLD = 'pending'
	ERROR_Q_WAIT = 'qw_error'
	SCRIPT_FAILED = 's_failed'


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
	PREPARE_SUBMIT = 'prep_submit' # TODO
	GETTING_RESULTS = 'get_results'
	SCRIPT_FAILED = JobState.SCRIPT_FAILED

	__decode_status = {
		JobState.UNDETERMINED       : 'process status cannot be determined',
		JobState.QUEUED_ACTIVE      : 'job is queued and active',
		JobState.SYSTEM_ON_HOLD     : 'job is queued and in system hold',
		JobState.USER_ON_HOLD       : 'job is queued and in user hold',
		JobState.USER_SYSTEM_ON_HOLD: 'job is queued and in user and system hold',
		JobState.RUNNING            : 'job is running',
		JobState.SYSTEM_SUSPENDED   : 'job is system suspended',
		JobState.USER_SUSPENDED     : 'job is user suspended',
		JobState.DONE               : 'job finished normally',
		SUCCEED                     : 'job finished normally',
		JobState.FAILED             : 'job failed to start due to a system error',
		JobState.SCRIPT_FAILED      : 'job completed but the script failed',
		SCRIPT_FAILED               : 'job completed but the script failed',
		ABORTED                     : 'job has been aborted',
		ABORT                       : 'job is being aborted...',
		INIT                        : 'job instance is being generated...',
		SCHEDULED                   : 'job is saved for later submission',
		PREPARE_RUN                 : 'job is being prepared for submission',
		PREPARE_SUBMIT              : 'job is being prepared for submission', # TODO finish
		SUBMITTED                   : 'job has been submitted, and should be running soon',
		GETTING_RESULTS             : 'job has completed, getting results',
		RUN_WAIT                    : 'job is about to be submitted',
		''                          : 'unknown/other'
	}
	job_ps = {
		''   : JobState.UNDETERMINED,
		'r'  : JobState.RUNNING,
		't'  : JobState.TRANSFERRING,
		'p'  : JobState.PENDING,
		'qw' : JobState.QUEUED_ACTIVE,
		'Eqw': JobState.ERROR_Q_WAIT,

		'h'  : JobState.ON_HOLD,
		'ho' : JobState.SYSTEM_ON_HOLD,
		'hs' : JobState.SYSTEM_ON_HOLD,
		'hd' : JobState.SYSTEM_ON_HOLD,
		'hu' : JobState.USER_ON_HOLD,
		'hus': JobState.USER_SYSTEM_ON_HOLD,

		's'  : JobState.SUSPENDED,
		'ss' : JobState.SYSTEM_SUSPENDED,
		'su' : JobState.USER_SUSPENDED,
		'us' : JobState.USER_SUSPENDED,
		'sus': JobState.USER_SYSTEM_SUSPENDED,
	}

	@classmethod
	def _progress_level(cls, stat):
		""" Return the progression value associated with a specific status

		:param stat:
		:type stat: str or Exception
		:return: progress value
		:rtype: int
		"""

		if stat is Exception:
			return 66
		elif stat == cls.SCHEDULED:
			return 2
		elif stat == cls.INIT:
			return 4
		elif stat == cls.RUN_WAIT:
			return 8
		elif stat in cls.PREPARE_RUN:
			return 15
		elif stat == cls.QUEUED_ACTIVE:
			return 30
		elif stat == cls.SUBMITTED:
			return 20
		elif stat == cls.RUNNING:
			return 55
		elif stat == cls.GETTING_RESULTS:
			return 85
		elif stat in (cls.FAILED, cls.SUCCEED, cls.DONE):
			return 100
		else:
			return None

	def status_logic(self):
		return self.status_logic_arg(self._init_stat)

	def status_logic_arg(self, status):
		""" Return relevant the relevant status, breeze_stat, progress and text display of current status code

		:param status: a JobStat constant
		:type status: str
		:return: status, breeze_stat, progress, textual(status)
		:rtype: str, str, int, str
		"""
		progress = JobStat._progress_level(status) # progression %
		if status == JobStat.ABORTED:
			self.status, self.breeze_stat = JobStat.ABORTED, JobStat.DONE
		elif status == JobStat.ABORT:
			self.status, self.breeze_stat = JobStat.ABORTED, JobStat.ABORT
		elif status == JobStat.PREPARE_RUN:
			self.status, self.breeze_stat = JobStat.INIT, JobStat.PREPARE_RUN
		elif status == JobStat.PREPARE_SUBMIT:
			self.status, self.breeze_stat = JobStat.INIT, JobStat.PREPARE_SUBMIT
		elif status == JobStat.QUEUED_ACTIVE:
			self.status, self.breeze_stat = JobStat.QUEUED_ACTIVE, JobStat.RUNNING
		elif status == JobStat.INIT:
			self.status, self.breeze_stat = JobStat.INIT, JobStat.INIT
		elif status == JobStat.SUBMITTED: # self.status remains unchanged
			self.breeze_stat = JobStat.SUBMITTED
		elif status in [JobStat.FAILED, JobStat.SCRIPT_FAILED]:
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
		elif status == JobStat.GETTING_RESULTS:
			self.breeze_stat = JobStat.GETTING_RESULTS
		else:
			self.status = status
		self.stat_text = JobStat.textual(status) # clear text status description

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

	@classmethod
	def textual(cls, stat, obj=None):
		""" Return string representation of current status

		:param stat: current status
		:type stat: str
		:param obj: runnable
		:type obj: Runnable
		:return: string representation of current status
		:rtype: str
		"""
		if stat == cls.FAILED:
			from models import Runnable
			if isinstance(obj, Runnable) and obj.is_r_failure:
				stat = cls.SCRIPT_FAILED
		if stat in cls.__decode_status:
			return cls.__decode_status[stat]
		else:
			return 'unknown status %s' % stat

	def __str__(self):
		return self.stat_text


class FolderObj(object):
	BASE_FOLDER_NAME = None # To define
	SYSTEM_FILES = [] # list of system files, that are required by the object
	HIDDEN_FILES = [] # list of file to hide from user upon download
	ALLOW_DOWNLOAD = False # if users can download content of object

	@property # interface (To define)
	def folder_name(self):
		""" Should implement a property generating the name of the folder to store the instance

		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		raise not_imp(self)

	@property
	def home_folder_rel(self):
		""" Returns the relative path to this object folder

		:return: the relative path to this object folder
		:rtype: str
		"""
		if self.BASE_FOLDER_NAME is None:
			raise NotDefined("BASE_FOLDER_NAME was not implemented in concrete class %s." % self.__class__.__name__)
		# if self.folder_name is None or self.folder_name == '':
		# 	raise NotDefined("folder_name is empty for %s." % self)
		return '%s%s/' % (self.BASE_FOLDER_NAME, slugify(self.folder_name))

	@property
	def home_folder_full_path(self):
		""" Returns the absolute path to this object folder

		:return: the absolute path to this object folder
		:rtype: str
		"""
		out = '%s%s' % (settings.MEDIA_ROOT, self.home_folder_rel)
		if not isdir(out):
			os.makedirs(out)
		return out

	@property
	def base_folder(self):
		return '%s%s' % (settings.MEDIA_ROOT, self.BASE_FOLDER_NAME)

	def move(self, target):
		try:
			return safe_copytree(self.home_folder_full_path, target)
		except Exception:
			return False

	@staticmethod
	def file_n_slug(file_name):
		""" Slugify file names, saving the . if exists, and leading path

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

	def file_name(self, filename):
		""" Special property

		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		return self.home_folder_full_path + self.file_n_slug(filename)

	def grant_write_access(self):
		""" Make the home folder writable for group
		"""
		# import os
		# import stat
		# open home's folder for others
		# st = os.stat(self.home_folder_full_path)
		# os.chmod(self.home_folder_full_path, st.st_mode | stat.S_IRWXG)
		return

	def add_file(self, f):
		""" write a file object at a specific location and return the slugified name

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
		:rtype: (list, list, str)
		"""
		raise not_imp(self)

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
						archive.write(new_p, str(name))
		except OSError as e:
			logger.exception(e)
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

	def delete(self, using=None):
		safe_rm(self.home_folder_full_path)
		super(FolderObj, self).delete(using=using)
		return True

	class Meta:
		abstract = True


# clem 13/05/2016
# META_CLASS
class ConfigObject(FolderObj):
	# __metaclass__ = abc.ABCMeta # problem with meta-subclassing
	from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError
	_not = "Class %s doesn't implement %s()"
	BASE_FOLDER_NAME = settings.CONFIG_FN
	ALLOW_DOWNLOAD = False

	def file_name(self, filename):
		return super(ConfigObject, self).file_name(filename)

	# config_file = abc.abstractproperty(None, None) # problem with meta-subclassing
	config_file = models.FileField(upload_to=file_name, blank=False, db_column='config',
		help_text="The config file for this exec resource")

	CONFIG_GENERAL_SECTION = 'DEFAULT'
	CONFIG_LOCAL_ENV_SECTION = 'local_env'
	CONFIG_REMOTE_ENV_SECTION = 'remote_env'

	__config = None
	use_cache = True
	_loader_mutex = Lock() # TODO should probably be instance specific

	def __unicode__(self): # Python 3: def __str__(self):
		return '%s (%s)' % (self.label, self.name)

	def __int__(self):
		return self.id

	# @abc.abstractproperty
	def folder_name(self):
		"""

		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		raise NotImplementedError(self._not % (self.__class__.__name__, this_function_name()))

	# clem 17/05/2016
	@property
	def log(self):
		runnable_obj = self.runnable if hasattr(self, 'runnable') else None
		return runnable_obj.log if hasattr(runnable_obj, 'log') else get_logger()

	# clem 27/05/2016
	def _load_config(self):
		""" Load the config file in a ConfigParser.SafeConfigParser object """
		config = self.SafeConfigParser()
		config.readfp(open(self.config_file.path))
		self.log.debug(
			'Config : loaded and parsed %s / %s ' % (os.path.basename(self.config_file.path), self.__class__.__name__))
		return config

	@property
	def config(self):
		""" The whole configuration object for this ConfigObject (Thread Safe) """
		if not self.__config: # instance level caching
			with self._loader_mutex:
				if isfile(self.config_file.path):
					key = 'ConfigObject:%s' % str(self)
					self.__config = ObjectCache.get_or_add(key,
						self._load_config) if self.use_cache else self._load_config()
				else:
					msg = 'Config file %s not found' % self.config_file.path
					self.log.error(msg)
					raise ConfigFileNotFound(msg)
		return self.__config

	# clem 27/05/2016
	def get_value(self, section, option):
		""" get a string value from the config file with error handling (i.e. config.get() )

		:param section: name of the section
		:type section: basestring
		:param option: name of the option value to get
		:type option: basestring
		:return: the option value
		:rtype: str
		:raise: self.ConfigParser.NoSectionError, AttributeError, self.ConfigParser.NoOptionError
		"""
		try:
			return self.config.get(section, option)
		except (self.NoSectionError, AttributeError, self.NoOptionError) as e:
			self.log.warning('While parsing file ')
			pp(self.config.__dict__)
			raise

	def set_local_env(self, sup_items=list()):
		""" Apply local system environement config, also replaces value in Django settings

		:param sup_items: optional supplementary items (like in config.items, i.e. a section)
		:type sup_items: list|None
		:return: if success
		:rtype: bool
		"""
		if not sup_items:
			sup_items = list()
		sup_items += self.local_env_config
		for (k, v) in sup_items:
			settings.__setattr__(k.upper(), v)
			os.environ[k.upper()] = v
		return True

	@property
	def local_env_config(self):
		""" The whole local env section

		:return: [(key, value), ]
		:rtype: list[(str, str)]
		"""
		if self.config.has_section(self.CONFIG_LOCAL_ENV_SECTION):
			return self.config.items(self.CONFIG_LOCAL_ENV_SECTION)
		return list()

	@property
	def remote_env_config(self):
		""" The whole remote env section

		:return: [(key, value), ]
		:rtype: list[(str, str)]
		"""
		if self.config.has_section(self.CONFIG_REMOTE_ENV_SECTION):
			return self.config.items(self.CONFIG_REMOTE_ENV_SECTION)
		return list()

	def get(self, property_name, section=None):
		""" get a string value from the config file with error handling (i.e. config.get() )

		:param property_name: name of the option value to get
		:type property_name: basestring
		:param section: name of the section
		:type section: basestring
		:return: the option value
		:rtype: str
		:raise: self.ConfigParser.NoSectionError, AttributeError, self.ConfigParser.NoOptionError
		"""
		if not section:
			section = self.CONFIG_GENERAL_SECTION
		return self.get_value(section, property_name)

	# clem 11/05/2016
	def _download_ignore(self, *args):
		pass

	class Meta(FolderObj.Meta):
		abstract = True


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


#
# NEW distributed POC
#

# clem 23/05/2016
class SwapObject(FolderObj):
	_not = "Class %s doesn't implement %s()"
	BASE_FOLDER_NAME = settings.SWAP_FN
	ALLOW_DOWNLOAD = False

	runnable = None

	def __init__(self, runnable):
		from models import Runnable
		assert isinstance(runnable, Runnable)
		self.runnable = runnable

	def file_name(self, filename):
		return super(SwapObject, self).file_name(filename)

	@property
	def folder_name(self):
		return self.runnable.short_id

	def _download_ignore(self, _=None):
		return list(), list(), str()

	class Meta(FolderObj.Meta):
		abstract = False


class SrcObj:
	def __init__(self, base_string):
		self.str = base_string

	@property
	def path(self):
		return self.str.replace('"', '').replace("'", "")

	@property
	def new(self): # TODO fix
		proj = settings.PROJECT_FOLDER.replace('/fs', '')
		proj_bis = settings.PROJECT_FOLDER
		return SrcObj(self.str.replace('"%s' % proj, '"~%s' % proj).replace("'%s" % proj, "'~%s" % proj).replace(
			'"%s' % proj_bis, '"~%s' % proj).replace("'%s" % proj_bis, "'~%s" % proj))

	# clem 21/10/15
	@property
	def base_name(self):
		import os
		return os.path.basename(self.path)

	# clem 21/10/15
	@staticmethod
	def _dir_name(path):
		import os
		return os.path.dirname(path)

	# clem 21/10/15
	@property
	def dir_name(self):
		return self._dir_name(self.path)

	def __repr__(self):
		return self.str

	def __str__(self):
		return self.str


# clem 20/10/2015 distributed POC +01/02/2016
class FileParser(SrcObj):
	# _verbose = True

	def __init__(self, file_n, dest, verbose=False):
		self.file_n = file_n
		self.__dest = ''
		self.destination = dest
		self.content = None
		self._new_content = None
		self.str = file_n
		self.parsed = list()
		self._verbose = verbose

	# super(self.__class__, self).__init__(self.file_n)
	# super(FileParser, self).__init__()

	def load(self):
		if not self._new_content and isfile(self.path):
			with open(self.path) as script:
				self.content = script.read()
				self._new_content = self.content
			return True
		return False

	# clem 02/02/2016
	def _write(self, a, b):
		try:
			self.new_content = u'%s\n%s' % (a, b)
		except UnicodeDecodeError: # TODO improve
			if type(a) != unicode:
				a = a.decode('utf-8')
			if type(b) != unicode:
				b = b.decode('utf-8')
			self._write(a, b)

	def add_on_top(self, content):
		self._write(content, self.new_content)

	def append(self, content):
		self._write(self.new_content, content)

	def replace(self, old, new):
		self.new_content = self.new_content.replace(str(old), str(new))

	def parse_and_save(self, pattern, callback):
		if self.parse(pattern, callback):
			return self.save_file()
		return False

	def parse(self, pattern, callback):
		# callback not a function or file content is empty (i.e. no file loadable) or already parsed with this pattern
		if not callable(callback) or not self.new_content or pattern in self.parsed:
			return False

		import re
		if self._verbose:
			print "parsing", self.base_name, 'with', pattern.name.upper(), '...'
		match = re.findall(str(pattern), self.new_content, re.DOTALL)
		if self._verbose:
			for each in match:
				print 'M', each
		# save this pattern in a list, so we don't parse this file with the same pattern again
		self.parsed.append(pattern)
		callback(self, match, pattern)

		return True

	# clem 25/05/2016
	@property
	def file_object(self):
		""" Open the destination file for writing operation, either as ascii or utf8

		:return: the file object
		:rtype: file
		"""
		if type(self.new_content) == unicode:
			import codecs
			return codecs.open(self.destination, 'w', 'utf8')
		else:
			return open(self.destination, 'w')

	def save_file(self):
		if not self.new_content:
			return False
		import os
		dest = os.path.dirname(self.destination)
		try:
			os.makedirs(dest, 0o0770)
		except OSError as e:
			pass

		with self.file_object as new_script:
			while new_script.write(self.new_content):
				pass
		if self._verbose:
			print 'saved!'
		return True

	@property # TODO code dt mod
	def mod_dt(self):
		return date_t(time_stamp=file_mod_time(self.path))

	# clem 02/02/2016
	@property
	def ext(self):
		"""
		:rtype: str
		"""
		_, _, extension = self.base_name.rpartition('.')
		return extension

	@property
	def new_content(self):
		if not self._new_content:
			if not self.load():
				return False
		return self._new_content

	@new_content.setter
	def new_content(self, value):
		if self._new_content:
			self._new_content = value

	@property
	def destination(self):
		return self.__dest

	@destination.setter
	def destination(self, value):
		self.__dest = value.replace('//', '/').replace('../', '').replace('..\\', '')

	# clem 21/10/15
	@property
	def destination_dir_name(self):
		return self._dir_name(self.destination)


# clem 02/02/2016
class Pattern:
	def __init__(self, name, pattern):
		self._pattern = pattern if type(pattern) == str else ''
		self._name = name if type(name) == str else ''

	@property
	def name(self):
		return self._name

	def __repr__(self):
		return self._pattern

	def __str__(self):
		return self._pattern


# clem 20/10/2015 distributed POC +01/02/2016
class RunServer:
	storage_path = str()
	_reports_path = str()
	_swap_object = None

	project_prefix = settings.PROJECT_FOLDER_PREFIX
	# lookup only sourced files inside PROJECT_FOLDER
	project_fold_name = settings.PROJECT_FOLDER_NAME
	project_fold = norm_proj_p(settings.PROJECT_FOLDER, '(?:%s)?' % project_prefix).replace('/',
		'\/')  # DEPLOY specific
	# regexp for matching. NB : MATCH GROUP 0 MUST ALWAYS BE THE FULL REPLACEMENT-TARGETED STRING
	LOAD_PATTERN = Pattern('load ',
		r'(?<!#)source\((?: |\t)*(("|\')(~?%s(?:(?!\2).)*)\2)(?: |\t)*\)' % project_fold) # 01/02/2016
	LIBS_PATTERN = Pattern('libs ',
		r'(?<!#)((?:(?:library)|(?:require))(?:\((?: |\t)*(?:("|\')?((?:\w|\.)+)\2?)(?: |\t)*\)))') # 02/02/2016
	ABS_PATH_PATTERN = Pattern('path ', r'(("|\')[^\'"]*(\/' + project_fold_name + r'\/[^\'"]*)\2)') #
	# 25/05/2016
	FILE_NAME_PATTERN = Pattern('file', r'(?:<-)(?:(?: |\t)*("|\')([\w\-\. ]+)\1)') # 03/02/2016

	added = [
		('%scfiere/csc_taito_dyn_lib_load_and_install.R' % norm_proj_p(settings.SPECIAL_CODE_FOLDER),
		'dynamic library loading and installer by clem 19-20/10/2015'),
	]

	def __init__(self, run_instance):
		from models import Runnable
		assert isinstance(run_instance, Runnable)
		self._run_inst = run_instance # instance or Runnable using this RunServer instance
		self._swap_object = SwapObject(self._run_inst)
		self.storage_path = self._swap_object.home_folder_full_path # local destination
		self._local = False # local or remote server
		self._remote_chroot = '/root/' # remote abs path of relative storage mounted in fs_path # FIXME
		# self._reports_path = reports_path # path of report folder storage in remote relative local path
		self._reports_path = norm_proj_p(settings.MEDIA_ROOT) # path of report folder storage in remote relative
		# local path
		self._add_source = self.added # list of files to add as source in script.R (special environment
		# specs, etc)
		self.target_name = self._run_inst.target_obj.name # name of this server
		self._user = self._run_inst.author # User object of user requesting
		self.count = dict()
		self.count['lib'] = 0
		self.count['load'] = 0
		self.count['abs'] = 0
		self._parsed = dict()
		self._rev = dict()

	# 23/05/2016
	def generate_source_tree(self):
		return self._generate_source_tree(self._run_inst.source_file_path)

	# DEPRECATED but useful for testing
	def _generate_source_tree(self, file_n, pf='', verbose=False):
		""" list the dependencies of a R file ("source()" calls)
		returns <b>tree</b>, <b>flat</b>, _

		<b>tree</b> is a dict of dict of (...)
		while <b>result</b> is a dict of list, nesting containing dedoubled list of all required files :
			keys being a list of all nodes in the original tree ( use result.keys() )
			values being lists of first child in the original tree
			this way you don't need to crawl the tree, and neither end up with doubles.

		:type file_n: str
		:type pf: str
		:type verbose: bool
		:rtype: dict, dict, list
		"""
		import re

		a_source_object = SrcObj(file_n) # or self._rexec.path
		with open(a_source_object.path) as script:
			tree = dict()
			flat = list()
			result = dict()

			pattern = r'source\(\s*("([^"]+)"|\'([^\']+)\')\s*\)'
			match = re.findall(str(pattern), script.read(), re.DOTALL)
			if verbose:
				print pf + str(a_source_object.path), ' X ', len(match)
			for el in match:
				line = SrcObj(el[0])
				sub_tree, total, sub_list = self._generate_source_tree(line.path, pf=pf + '\t', verbose=verbose)
				tree[line.path] = sub_tree
				flat.append(line.path)
				if total:
					result.update(total)
			result[a_source_object.path] = flat

		return { a_source_object.path: tree }, result, flat

	# clem 01/02/2016
	def stats(self):
		self._run_inst.log.debug('assembling completed : lib/load/abs : %s / %s / %s' % (
			self.count['lib'], self.count['load'], self.count['abs']))

	def parse_all(self):
		import os
		d = date_t()
		# source
		the_path = str(self._run_inst.source_file_path)
		# destination
		new_path = '%s%s%s%s' % \
				   (self.storage_path, self._reports_path, self._run_inst.home_folder_rel, os.path.basename(the_path))
		# parser
		the_file_p = FileParser(the_path, new_path)
		# add some source that may help with specific env / Renv / cluster / etc
		if type(self._add_source) is list and self._add_source != list():
			added = ''
			for each in self._add_source:
				added += 'source("%s") # %s\n' % each
			the_file_p.add_on_top('##### following sources ADDED BY BREEZE :\n%s' % added +
								  '##### END OF BREEZE ADDITIONS ###')
		the_file_p.add_on_top('## Transferred to %s started by BREEZE on %s' % (self.target_name, d))
		# parse the file to change path, library loading, and link files related to source()
		the_file_p.parse(self.LOAD_PATTERN,
			self._parser_main_recur_call_back) # saving here is not necessary nor sufficient
		# done
		self.stats()
		return True

	# clem 02/02/2016
	def already_parsed(self, file_parser_obj):
		"""
		Check if the file is has already been parsed.
		This avoids sending the same file several time to the parser in case of
			_ several reference to the same file,
			_ sourced file referencing a previously source file
			_ sourced loop/nesting

		:type file_parser_obj: FileParser
		:rtype: bool
		"""
		assert isinstance(file_parser_obj, FileParser)
		return str(file_parser_obj) in self._parsed

	def _parser_main_recur_call_back(self, file_obj, match, pattern):
		assert isinstance(file_obj, FileParser)
		imp_text = ''
		# FOR every match of self.LOAD_PATTERN in file_obj
		for el in match:
			# deals with the found sub-file (it's a load so it should be a R file)
			line = SrcObj(el[0])
			new_path = '%s%s' % (self.storage_path, line.path)
			sub_file_p = FileParser(line.path, new_path)

			self.count['load'] += 1
			# local sourcing
			file_obj.replace(line, line.new)

			# Lower level recursion (will parse this sourced file for loads, library, and paths)
			if not self.already_parsed(sub_file_p):
				sub_file_p.parse(pattern, self._parser_main_recur_call_back)

			imp_text += '## Imported and parsed sourced file %s to %s (local path on %s) \n' % \
						(line.base_name, line.new.dir_name, self.target_name)

		# FOR every file_obj, even those with no match of self.LOAD_PATTERN
		# DO NOT MOVE THIS SECTION in parse_all (recursive lower-lever call-backs) !

		# other non-recursive parsings (library/require call and plain paths)
		self._sub_parsers(file_obj)
		self._parsed[str(file_obj)] = True

		# file summary log
		d = date_t()
		dep = ''
		if len(match) > 0:
			dep = '## %s sourced dependencies found, parsed and imported (plus %s library, %s total load) :\n%s' % \
				  (len(match), self.count['lib'], self.count['load'], imp_text)
		file_obj.add_on_top(
			'##### BREEZE SUMMARY of file parsing to run on %s :\n' % self.target_name +
			'## Parsed on %s (org. modified on %s) for %s (%s) \n' %
			(d, file_obj.mod_dt, str(self._user.get_full_name()), self._user) + dep +
			'##### END OF BREEZE SUMMARY #####'
		)
		# save !important to save here because of lower-lever call-backs
		file_obj.save_file()

	def _sub_parsers(self, file_obj):
		assert isinstance(file_obj, FileParser)
		if not self.already_parsed(file_obj):
			file_obj.parse(self.LIBS_PATTERN, self._parser_libs_call_back) # library()/require()
			file_obj.parse(self.ABS_PATH_PATTERN, self._parser_abs_call_back) # plain absolute paths

	def _parser_libs_call_back(self, file_obj, match, pattern):
		assert isinstance(file_obj, FileParser)
		for el in match:
			self.count['lib'] += 1
			line = el[0]
			lib_name = el[2]
			replacement = "load_lib('%s') # Originally : %s" % (lib_name, line)
			file_obj.replace(line, replacement)

	def _parser_abs_call_back(self, file_obj, match, pattern):
		assert isinstance(file_obj, FileParser)
		for el in match:
			self.count['abs'] += 1
			line = SrcObj(el[0])
			# change the path to a relative one for the target server
			file_obj.replace(line, line.new)
			print 'replacing #%s# with #%s#' % (line, line.new)
			# remote location on a local mount
			new_path = '%s%s' % (self.storage_path, line.path)
			new_file = FileParser(line.path, new_path)
			ext = new_file.ext.lower()
			if new_file.load() and ext and ext != 'r': # existing file
				new_file.save_file() # copy to remote location

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		pass


#
# *END* NEW distributed POC
#
