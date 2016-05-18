# Django settings for isbio project.
from configurations import Settings
import logging
import os
import socket
import time
from datetime import datetime

ENABLE_DATADOG = True
try:
	from datadog import statsd
	if ENABLE_DATADOG:
		ENABLE_DATADOG = True
except Exception:
	ENABLE_DATADOG = False
	pass
ENABLE_REMOTE_FW = False

# TODO : redesign


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


def recur(nb, funct, args):
	while nb > 0:
		args = funct(args)
		nb -= 1
	return args


# TODO make a generator
def getkey(path=''):
	try:
		with open(path + 'secret') as f:
			return f.read()
	except Exception as e:
		pass
	return None


def recur_rec(nb, funct, args):
	if nb > 0:
		return recur_rec(nb - 1, funct, funct(args))
	return args


PID = os.getpid()

MAINTENANCE = False
USUAL_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
USUAL_LOG_FORMAT = \
	'%(asctime)s,%(msecs)03d  P%(process)05d %(levelname)-8s %(lineno)04d:%(module)-14s %(funcName)-25s %(message)s'
USUAL_LOG_FORMAT_DESCRIPTOR =\
	'DATE       TIME,milisec  PID   LEVEL     LINE:MODULE         FUNCTION                  MESSAGE'
DB_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FOLDER = '/var/log/breeze/'
# log_fname = 'breeze_%s.log' % datetime.now().strftime("%Y-%m-%d_%H-%M-%S%z")
log_fname = 'rotating.log'
log_hit_fname = 'access.log'
LOG_PATH = '%s%s' % (LOG_FOLDER, log_fname)
LOG_HIT_PATH = '%s%s' % (LOG_FOLDER, log_hit_fname)


class BreezeSettings(Settings):
	# RUN only on prod it seems
	global USUAL_DATE_FORMAT, LOG_PATH, LOG_HIT_PATH
	DEBUG = False
	TEMPLATE_DEBUG = DEBUG

	ADMINS = (
		('Clement FIERE', 'clement.fiere@helsinki.fi'),
		# ('Dmitrii Bychkov', 'piter.dmitry@gmail.com'),
	)

	MANAGERS = ADMINS

	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
			'NAME': 'biodb',  # Or path to database file if using sqlite3.
			'USER': 'biouser',  # Not used with sqlite3.
			'PASSWORD': 'rna',  # Not used with sqlite3.
			'HOST': '/var/run/mysqld/mysqld.sock',  # Set to empty string for localhost. Not used with sqlite3.
			'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
			# 'OPTIONS': { "init_command": "SET foreign_key_checks = 0;", },
			'OPTIONS': {
				"init_command": "SET storage_engine=INNODB, SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED", }
		}
	}

	# Local time zone for this installation. Choices can be found here:
	# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
	# although not all choices may be available on all operating systems.
	# In a Windows environment this must be set to your system time zone.
	TIME_ZONE = 'Europe/Helsinki'

	# Language code for this installation. All choices can be found here:
	# http://www.i18nguy.com/unicode/language-identifiers.html
	LANGUAGE_CODE = 'en-us'

	SITE_ID = 1

	# If you set this to False, Django will make some optimizations so as not
	# to load the internationalization machinery.
	USE_I18N = True

	# If you set this to False, Django will not format dates, numbers and
	# calendars according to the current locale.
	USE_L10N = True

	# If you set this to False, Django will not use timezone-aware datetimes.
	USE_TZ = True

	# !CUSTOM!
	# Tempory folder for the application
	# # TEMP_FOLDER = '/home/comrade/Projects/fimm/tmp/'
	# Path to R installation
	R_ENGINE_PATH = 'R '

	# Absolute filesystem path to the directory that will hold user-uploaded files.
	# Example: "/home/media/media.lawrence.com/media/"
	# #MEDIA_ROOT = '/home/comrade/Projects/fimm/db/'
	# #RORA_LIB = '/home/comrade/Projects/fimm/roralib/'

	# URL that handles the media served from MEDIA_ROOT. Make sure to use a
	# trailing slash.
	# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
	MEDIA_URL = '/media/'

	# Absolute path to the directory static files should be collected to.
	# Don't put anything in this directory yourself; store your static files
	# in apps' "static/" subdirectories and in STATICFILES_DIRS.
	# Example: "/home/media/media.lawrence.com/static/"
	STATIC_ROOT = ''

	# URL prefix for static files.
	# Example: "http://media.lawrence.com/static/"
	STATIC_URL = '/static/'

	# Additional locations of static files
	STATICFILES_DIRS = (
		#"/home/comrade/Projects/fimm/isbio/breeze/",
		# Put strings here, like "/home/html/static" or "C:/www/django/static".
		# Always use forward slashes, even on Windows.
		# Don't forget to use absolute paths, not relative paths.
	)

	# List of finder classes that know how to find static files in
	# various locations.
	STATICFILES_FINDERS = (
		'django.contrib.staticfiles.finders.FileSystemFinder',
		'django.contrib.staticfiles.finders.AppDirectoriesFinder',
		'django.contrib.staticfiles.finders.DefaultStorageFinder',
	)

	# Make this unique, and don't share it with anybody.
	SECRET_KEY = str(getkey())

	# List of callables that know how to import templates from various sources.
	TEMPLATE_LOADERS = (
		'django.template.loaders.filesystem.Loader',
		'django.template.loaders.app_directories.Loader',
		#     'django.template.loaders.eggs.Loader',
	)

	MIDDLEWARE_CLASSES = (
		'breeze.middlewares.BreezeAwake',
		'django.middleware.common.CommonMiddleware',
		'django.contrib.sessions.middleware.SessionMiddleware',
		'django.middleware.csrf.CsrfViewMiddleware',
		'django.contrib.auth.middleware.AuthenticationMiddleware',
		'django.contrib.messages.middleware.MessageMiddleware',
		'django.middleware.doc.XViewMiddleware',
		'breeze.middlewares.JobKeeper',
		'breeze.middlewares.CheckUserProfile',
		'django_requestlogging.middleware.LogSetupMiddleware',
		'breeze.middlewares.DataDog' if ENABLE_DATADOG else 'breeze.middlewares.Empty',
		'breeze.middlewares.RemoteFW' if ENABLE_REMOTE_FW else 'breeze.middlewares.Empty',
		'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',
		# 'breeze.middleware.Log',
		# Uncomment the next line for simple clickjacking protection:
		# 'django.middleware.clickjacking.XFrameOptionsMiddleware',
	)
	# from django_cas.backends import CASBackend
	AUTHENTICATION_BACKENDS = (
		'django.contrib.auth.backends.ModelBackend',
		'django_cas.backends.CASBackend',
	)

	# CAS_SERVER_IP = '192.168.0.218'
	CAS_SERVER_IP = 'cas-prot.fimm.fi'
	CAS_SERVER_URL = 'https://%s:8443/cas/' % CAS_SERVER_IP
	CAS_REDIRECT_URL = '/home/'

	ROOT_URLCONF = 'isbio.urls'
	APPEND_SLASH = True

	# Python dotted path to the WSGI application used by Django's runserver.
	WSGI_APPLICATION = 'isbio.wsgi.application'

	TEMPLATE_DIRS = (
		'/home/comrade/Projects/fimm/isbio/breeze/templates',
		# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
		# Always use forward slashes, even on Windows.
		# Don't forget to use absolute paths, not relative paths.
	)

	# provide our profile model
	AUTH_PROFILE_MODULE = 'breeze.UserProfile'

	INSTALLED_APPS = (
		'django.contrib.auth',
		'django.contrib.contenttypes',
		'django.contrib.sessions',
		'django.contrib.sites',
		'django.contrib.messages',
		'django.contrib.staticfiles',
		'bootstrap_toolkit',
		'breeze',
		'down',
		'south',
		'gunicorn',
		'mathfilters',
		# Uncomment the next line to enable the admin:
		'django.contrib.admin',
		'django_requestlogging',
		# Uncomment the next line to enable admin documentation:
		# 'django.contrib.admindocs',
	)

	# A sample logging configuration. The only tangible logging
	# performed by this configuration is to send an email to
	# the site admins on every HTTP 500 error when DEBUG=False.
	# See http://docs.djangoproject.com/en/dev/topics/logging for
	# more details on how to customize your logging configuration.
	LOGGING = {
		'version': 1,
		'disable_existing_loggers': False,
		'formatters': {
			'standard': {
				'format': USUAL_LOG_FORMAT,
				'datefmt': USUAL_DATE_FORMAT,
			},
		},
		'filters': {
			'require_debug_false': {
				'()': 'django.utils.log.RequireDebugFalse'
			}
		},
		'handlers': {
			'default': {
				'level': 'DEBUG',
				'class': 'logging.handlers.RotatingFileHandler',
				'filename': LOG_PATH,
				'maxBytes': 1024 * 1024 * 5, # 5 MB
				'backupCount': 10,
				'formatter': 'standard',
			},
			'mail_admins': {
				'level': 'ERROR',
				'filters': ['require_debug_false'],
				'class': 'django.utils.log.AdminEmailHandler'
			},
		},
		'loggers': {
			'': {
				'handlers': ['default'],
				'level': logging.INFO,
				'propagate': True
			},
			'django.request': {
				'handlers': ['mail_admins'],
				'level': 'ERROR',
				'propagate': True,
			},

		}
	}

	TEMPLATE_CONTEXT_PROCESSORS = (
		'django.contrib.auth.context_processors.auth',
		'django.core.context_processors.media',
		'django.core.context_processors.static',
		'breeze.context.user_context'
	)


class DevSettings(BreezeSettings):
	# general setting / common
	global USUAL_DATE_FORMAT, LOG_PATH
	DEBUG = True
	VERBOSE = False
	SQL_DUMP = False
	APPEND_SLASH = True

	ADMINS = (
	('Clement FIERE', 'clement.fiere@helsinki.fi'),  # ('Dmitrii Bychkov', 'piter.dmitry@gmail.com'),
	)

	MANAGERS = ADMINS

	# os.system('. ~/.sge_profile')
	# dynamically change the environement
	import os, subprocess as sp, json
	source = 'source ~/.sge_profile'
	dump = 'python -c "import os, json;print json.dumps(dict(os.environ))"'
	pipe = sp.Popen(['/bin/bash', '-c', '%s && %s' % (source, dump)], stdout=sp.PIPE)
	env = json.loads(pipe.stdout.read())
	os.environ = env

	# sge_arch = "lx26-amd64"
	# os.environ['SGE_ROOT'] = '/opt/gridengine'
	# os.environ['QSTAT_BIN'] = os.environ['SGE_ROOT']+'/bin/'+sge_arch+'/qstat'
	# Q_BIN = '/usr/bin/'
	Q_BIN = os.environ.get('Q_BIN', '')
	QSTAT_BIN = '%sqstat' % Q_BIN
	QDEL_BIN = '%sqdel' % Q_BIN
	SGE_QUEUE_NAME = os.environ.get('SGE_QUEUE', '')
	# os.environ['QSTAT_BIN'] = QSTAT_BIN
	# os.environ['SGE_ARCH'] = 'UNSUPPORTED-lx3.2.0-40-generic-amd64'
	# os.environ['LD_LIBRARY_PATH'] = os.environ['SGE_ROOT'] + '/lib/' + os.environ['SGE_ARCH']
	# os.environ['SGE_QMASTER_PORT'] = '6444'
	# os.environ['SGE_EXECD_PORT'] = '6445'
	# os.environ['SGE_CELL'] = 'default'
	# os.environ['DRMAA_LIBRARY_PATH'] = os.environ['SGE_ROOT']+'/lib/'+sge_arch+'/libdrmaa.so'
	# os.environ['DRMAA_LIBRARY_PATH'] = os.environ['SGE_ROOT'] + '/lib/' + sge_arch + '/libdrmaa.so.1.0'
	os.environ['MAIL'] = '/var/mail/dbychkov'

	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
			'NAME': 'breezedb',  # Or path to database file if using sqlite3.
			'USER': 'comrade',  # Not used with sqlite3.
			'PASSWORD': 'find!comrade',  # Not used with sqlite3.
			'HOST': '/var/run/mysqld/mysqld.sock',  # Set to empty string for localhost. Not used with sqlite3.
			'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
			'OPTIONS': {

				"init_command": "SET default_storage_engine=INNODB; SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED", }
				# "init_command": "SET transaction isolation level READ COMMITTED", }
		}
	}

	CONSOLE_DATE_F = "%d/%b/%Y %H:%M:%S"
	# auto-sensing if running on dev or prod, for dynamic environment configuration
	FULL_HOST_NAME = socket.gethostname()
	HOST_NAME = str.split(FULL_HOST_NAME, '.')[0]
	# automatically setting RUN_MODE depending on the host name
	RUN_MODE = 'dev' if HOST_NAME.endswith('dev') else 'prod'
	DEV_MODE = RUN_MODE == 'dev'
	MODE_PROD = RUN_MODE == 'prod'
	PHARMA_MODE = False

	# Super User on breeze can Access all datas
	SU_ACCESS_OVERRIDE = True

	# contains everything else (including breeze generated content) than the breeze web source code and static files
	PROJECT_FOLDER = '/fs/projects/'
	# PROJECT_FOLDER = '/projects/'
	BREEZE_FOLDER = 'breeze' + ('-dev' if DEV_MODE else '') + '/'
	if HOST_NAME.endswith('ph'):
		BREEZE_FOLDER = 'breeze_new/'
		DEBUG = False
		VERBOSE = False
		SQL_DUMP = False
		PHARMA_MODE = True

	PROJECT_PATH = PROJECT_FOLDER + BREEZE_FOLDER
	PROD_PATH = PROJECT_FOLDER + 'breeze/'
	# R_HOME = "/projects/breeze/R/lib64/R"
	R_HOME = "%sR/lib64/R" % PROD_PATH
	R_ENGINE_SUB_PATH = 'R/bin/R ' # NOTE THERE IS A SPACE AT THIS END OF THIS VAR
	R_ENGINE_PATH = PROD_PATH + R_ENGINE_SUB_PATH
	if not os.path.isfile( R_ENGINE_PATH.strip()):
		PROJECT_FOLDER = '/projects/'
		PROJECT_PATH = PROJECT_FOLDER + BREEZE_FOLDER
		R_ENGINE_PATH = PROD_PATH + R_ENGINE_SUB_PATH

	PROJECT_FHRB_PM_PATH = '/projects/fhrb_pm/'
	JDBC_BRIDGE_PATH = PROJECT_FHRB_PM_PATH + 'bin/start-jdbc-bridge' # Every other path has a trailing /

	# root of the Breeze django project folder, includes 'venv', 'static' folder copy, isbio, logs
	SOURCE_ROOT = recur(3, os.path.dirname, os.path.realpath(__file__)) + '/'
	DJANGO_ROOT = recur(2, os.path.dirname, os.path.realpath(__file__)) + '/'

	# R_ENGINE_PATH = PROJECT_PATH + 'R/bin/R '
	TEMP_FOLDER = SOURCE_ROOT + 'tmp/' # /homes/dbychkov/dev/isbio/tmp/
	####
	# 'db' folder, containing : reports, scripts, jobs, datasets, pipelines, upload_temp
	####
	DATA_TEMPLATES_FN = 'mould/'

	RE_RUN_SH = SOURCE_ROOT + 're_run.sh'

	MEDIA_ROOT = PROJECT_PATH + 'db/'  # '/project/breeze[-dev]/db/'
	RORA_LIB = PROJECT_PATH + 'RORALib/'
	UPLOAD_FOLDER = MEDIA_ROOT + 'upload_temp/'
	DATASETS_FOLDER = MEDIA_ROOT + 'datasets/'
	STATIC_ROOT = SOURCE_ROOT + 'static/'
	# STATIC_ROOT = SOURCE_ROOT + 'static/'
	TEMPLATE_FOLDER = DJANGO_ROOT + 'templates/'
	MOULD_FOLDER = MEDIA_ROOT + DATA_TEMPLATES_FN
	NO_TAG_XML = TEMPLATE_FOLDER + 'notag.xml'
	GENERAL_SH_NAME = 'sgeconfig.sh'
	INCOMPLETE_RUN_FN = 'INCOMPLETE_RUN'
	# SGE_QUEUE_NAME = 'breeze.q'
	# SGE_QUEUE_NAME = 'breeze.q' # monitoring only



	##
	# Report config
	##
	NOZZLE_TEMPLATE_FOLDER = TEMPLATE_FOLDER + 'nozzle_templates/'
	TAGS_TEMPLATE_PATH = NOZZLE_TEMPLATE_FOLDER + 'tag.R'
	NOZZLE_REPORT_TEMPLATE_PATH = NOZZLE_TEMPLATE_FOLDER + 'report.R'
	NOZZLE_REPORT_FN = 'report'

	RSCRIPTS_FN = 'scripts/'
	RSCRIPTS_PATH = MEDIA_ROOT + RSCRIPTS_FN

	REPORT_TYPE_FN = 'pipelines/'
	REPORT_TYPE_PATH = MEDIA_ROOT + REPORT_TYPE_FN

	REPORTS_FN = 'reports/'
	REPORTS_PATH = '%s%s' % (MEDIA_ROOT, REPORTS_FN)
	REPORTS_SH = GENERAL_SH_NAME
	REPORTS_FM_FN = 'transfer_to_fm.txt'
	##
	# Jobs configs
	##
	SCRIPT_TEMPLATE_FOLDER = TEMPLATE_FOLDER + 'script_templates/'
	SCRIPT_TEMPLATE_PATH = SCRIPT_TEMPLATE_FOLDER + 'script.R'
	JOBS_FN = 'jobs/'
	JOBS_PATH = '%s%s' % (MEDIA_ROOT, JOBS_FN)
	JOBS_SH = '_config.sh'

	#
	# WATCHER RELATED CONFIG
	#
	WATCHER_DB_REFRESH = 2 # number of seconds to wait before refreshing reports from DB
	WATCHER_PROC_REFRESH = 2 # number of seconds to wait before refreshing processes

	#
	# SHINY RELATED CONFIG
	#
	# SHINY_APPS = MEDIA_ROOT + 'shinyApps/'
	SHINY_FN_REPORTS = 'shinyReports'
	SHINY_FN_TAGS = 'shinyTags'
	SHINY_FN_TEMPLATE = 'shiny_templates'
	SHINY_TAGS = '%s%s/' % (MEDIA_ROOT, SHINY_FN_TAGS)
	SHINY_REPORTS = '%s%s/' % (MEDIA_ROOT, SHINY_FN_REPORTS)
	SHINY_REPORT_TEMPLATE_PATH = '%s%s/' % (TEMPLATE_FOLDER, SHINY_FN_TEMPLATE)
	SHINY_ORIG_TARGET_URL = '%s/breeze/'
	SHINY_ORIG_STANDALONE_URL = '%s/apps/'
	SHINY_ORIG_LIBS_TARGET_URL = '%s/libs/'
	# local Shiny
	SHINY_LOCAL_ENABLE = True
	SHINY_LOCAL_IP = '127.0.0.1:3838'
	SHINY_LOCAL_TARGET_URL = 'http://' + SHINY_ORIG_TARGET_URL % SHINY_LOCAL_IP
	SHINY_LOCAL_LIBS_TARGET_URL = 'http://' + SHINY_ORIG_LIBS_TARGET_URL % SHINY_LOCAL_IP
	SHINY_LOCAL_LIBS_BREEZE_URL = '/libs/'
	SHINY_LOCAL_STANDALONE_BREEZE_URL = 'http://' + SHINY_ORIG_STANDALONE_URL % SHINY_LOCAL_IP
	# remote Shiny
	SHINY_REMOTE_ENABLE = True
	# SHINY_REMOTE_IP = 'vm0326.kaj.pouta.csc.fi'
	SHINY_REMOTE_IP = 'vm0326.kaj.pouta.csc.fi:3838'
	SHINY_REMOTE_LOCAL_PATH = '/shiny-csc/'
	SHINY_REMOTE_CSC_LOCAL_PATH = '/home/shiny/shiny/'
	SHINY_REMOTE_BREEZE_REPORTS_PATH = SHINY_REMOTE_LOCAL_PATH + REPORTS_FN
	SHINY_REMOTE_REPORTS = '%s%s/' % (SHINY_REMOTE_LOCAL_PATH, SHINY_FN_REPORTS)
	SHINY_REMOTE_REPORTS_INTERNAL = '%s%s/' % (SHINY_REMOTE_CSC_LOCAL_PATH, SHINY_FN_REPORTS)
	SHINY_REMOTE_TAGS = '%s%s/' % (SHINY_REMOTE_LOCAL_PATH, SHINY_FN_TAGS)
	SHINY_REMOTE_TAGS_INTERNAL = '%s%s/' % (SHINY_REMOTE_CSC_LOCAL_PATH, SHINY_FN_TAGS)
	# SHINY_REMOTE_PROTOCOL = 'https'
	SHINY_REMOTE_PROTOCOL = 'http'
	SHINY_REMOTE_TARGET_URL = '%s://' % SHINY_REMOTE_PROTOCOL + SHINY_ORIG_TARGET_URL % SHINY_REMOTE_IP
	SHINY_REMOTE_LIBS_TARGET_URL = '%s://' % SHINY_REMOTE_PROTOCOL + SHINY_ORIG_LIBS_TARGET_URL % SHINY_REMOTE_IP
	SHINY_REMOTE_LIBS_BREEZE_URL = '/libs/'

	# LEGACY ONLY (single Shiny old system)
	SHINY_MODE = 'local'

	SHINY_HEADER_FILE_NAME = 'header.R'
	SHINY_LOADER_FILE_NAME = 'loader.R'
	SHINY_GLOBAL_FILE_NAME = 'global.R'
	SHINY_UI_FILE_NAME = 'ui.R'
	SHINY_SERVER_FILE_NAME = 'server.R'
	SHINY_FILE_LIST = 'files.json'
	# SHINY_SERVER_FOLDER = 'scripts_server/'
	# SHINY_UI_FOLDER = 'scripts_body/'
	# SHINY_SERVER_FOLDER = 'scripts_server/'
	SHINY_RES_FOLDER = 'www/'
	# SHINY_DASH_UI_FILE = 'dash_ui.R'
	# HINY_DASH_SERVER_FILE = 'dashboard_serverside.R'
	# SHINY_DASH_UI_FN = SHINY_UI_FOLDER + SHINY_DASH_UI_FILE
	# SHINY_DASH_SERVER_FN = SHINY_SERVER_FOLDER + SHINY_DASH_SERVER_FILE
	SHINY_TAG_CANVAS_FN = 'shinyTagTemplate.zip'
	SHINY_TAG_CANVAS_PATH = MOULD_FOLDER + SHINY_TAG_CANVAS_FN
	SHINY_MIN_FILE_SIZE = 14 # library(shiny) is 14 byte long
	# NOZZLE_TARGET_URL = 'http://' + FULL_HOST_NAME + '/'
	# Install shiny library : install.packages('name of the lib', lib='/usr/local/lib/R/site-library', dependencies=TRUE)

	FOLDERS_LST = [TEMPLATE_FOLDER, SHINY_REPORT_TEMPLATE_PATH, SHINY_REPORTS, SHINY_TAGS,
		NOZZLE_TEMPLATE_FOLDER, SCRIPT_TEMPLATE_FOLDER, JOBS_PATH, REPORT_TYPE_PATH, REPORTS_PATH, RSCRIPTS_PATH, MEDIA_ROOT,
		PROJECT_FHRB_PM_PATH, RORA_LIB, STATIC_ROOT]


	##
	# System Autocheck config
	##
	# this is used to avoid 504 Gateway time-out from ngnix with is currently set to 600 sec = 10 min
	# LONG_POLL_TIME_OUT_REFRESH = 540 # 9 minutes
	# set to 50 sec to avoid time-out on breeze.fimm.fi
	LONG_POLL_TIME_OUT_REFRESH = 50
	SGE_MASTER_FILE = '/var/lib/gridengine/default/common/act_qmaster'
	SGE_MASTER_IP = '192.168.67.2'
	DOTM_SERVER_IP = '128.214.64.5'
	RORA_SERVER_IP = '192.168.0.219'
	FILE_SERVER_IP = '192.168.0.107'
	SPECIAL_CODE_FOLDER = PROJECT_PATH + 'code/'
	FS_SIG_FILE = PROJECT_PATH + 'fs_sig.md5'
	FS_LIST_FILE = PROJECT_PATH + 'fs_checksums.json'
	FOLDERS_TO_CHECK = [TEMPLATE_FOLDER, SHINY_TAGS, REPORT_TYPE_PATH, # SHINY_REPORTS,SPECIAL_CODE_FOLDER  ,
		RSCRIPTS_PATH, RORA_LIB, MOULD_FOLDER, STATIC_ROOT, DATASETS_FOLDER]

	# STATIC URL MAPPINGS
	SHINY_URL = '/shiny/rep/' # FIXME
	STATIC_URL = '/static/'
	MEDIA_URL = '/media/'
	MOULD_URL = MEDIA_URL + DATA_TEMPLATES_FN

	# number of seconds after witch a job that has not received a sgeid should be marked as aborted or re-run
	NO_SGEID_EXPIRY = 30

	# Additional locations of static files
	STATICFILES_DIRS = (
		"",
	)

	TMP_CSC_TAITO_MOUNT = '/mnt/csc-taito/'
	TMP_CSC_TAITO_REPORT_PATH = 'breeze/'

	# mail config
	EMAIL_HOST = 'smtp.gmail.com'
	EMAIL_HOST_USER = 'breeze.fimm@gmail.com'
	EMAIL_HOST_PASSWORD = 'mult24mult24'
	EMAIL_PORT = '587'
	EMAIL_SUBJECT_PREFIX = '[' + FULL_HOST_NAME + '] '
	EMAIL_USE_TLS = True

	#
	# END OF CONFIG
	# RUN-MODE SPECIFICS FOLLOWING
	# ** NO CONFIGURATION CONST BEYOND THIS POINT **
	#

	# if prod mode then auto disable DEBUG, for safety
	if MODE_PROD:
		SHINY_MODE = 'remote'
		SHINY_LOCAL_ENABLE = False
		DEBUG = False
		VERBOSE = False

	if DEBUG:
		import sys
		LOGGING = {
			'version': 1,
			'disable_existing_loggers': False,
			'formatters': {
				'verbose': {
					'datefmt': USUAL_DATE_FORMAT,
					'format': USUAL_LOG_FORMAT,
				},
				'standard': {
					'format': USUAL_LOG_FORMAT,
					'datefmt': USUAL_DATE_FORMAT,
				},
				'request_format': {
					'format': '%(remote_addr)s %(username)s "%(request_method)s '
							'%(path_info)s %(server_protocol)s" %(http_user_agent)s '
							'%(message)s %(asctime)s',
				},
			},
			'filters': {
				'request': {
					'()': 'django_requestlogging.logging_filters.RequestFilter',
				},
				'require_debug_false': {
					'()': 'django.utils.log.RequireDebugFalse'
				}
			},
			'handlers': {
				'default': {
					'level': 'DEBUG',
					'class': 'logging.handlers.RotatingFileHandler',
					'filename': LOG_PATH,
					'maxBytes': 1024 * 1024 * 5, # 5 MB
					'backupCount': 10,
					'formatter': 'standard',
				},
				'mail_admins': {
					'level': 'ERROR',
					'filters': ['require_debug_false'],
					'class': 'django.utils.log.AdminEmailHandler'
				},
				'console': {
					'level': 'INFO',
					'class': 'logging.StreamHandler',
					'stream': sys.stdout,
					'formatter': 'verbose',
				},
				'access_log': {
					'class': 'logging.handlers.RotatingFileHandler',
					'filename': LOG_HIT_PATH,
					'maxBytes': 1024 * 1024 * 10, # 5 MB
					'backupCount': 900,
					'filters': ['request'],
					'formatter': 'request_format',
				},
			},
			'loggers': {
				'isbio': {
					'handlers': ['console'],
					'level': 'DEBUG',
					'propagate': True,
				},
				'breeze': {
					'handlers': ['console', 'access_log'],
					'level': 'DEBUG',
					'propagate': True,
				},
				'breeze2': {
					'handlers': ['access_log'],
					'filters': ['request'],
				},
				'': {
					'handlers': ['default'],
					'level': logging.INFO,
					'propagate': True
				},
				'django.request': {
					'handlers': ['mail_admins'],
					'level': 'ERROR',
					'propagate': True,
				},
			}
		}
		import logging.config
		logging.config.dictConfig(LOGGING)

	else:
		VERBOSE = False


	try:
		import rollbar
		BASE_DIR = SOURCE_ROOT
		ROLLBAR = {
			'access_token': '00f2bf2c84ce40aa96842622c6ffe97d',
			'environment': 'development' if DEBUG else 'production',
			'root': BASE_DIR,
		}

		rollbar.init(**ROLLBAR)
	except Exception:
		logging.getLogger().error('Unable to init rollbar')
		pass

	if SHINY_MODE == 'remote':
		SHINY_TARGET_URL = SHINY_REMOTE_TARGET_URL
		SHINY_LIBS_TARGET_URL = SHINY_REMOTE_LIBS_TARGET_URL
		SHINY_LIBS_BREEZE_URL = SHINY_REMOTE_LIBS_BREEZE_URL
	else:
		SHINY_TARGET_URL = SHINY_LOCAL_TARGET_URL
		SHINY_LIBS_TARGET_URL = SHINY_LOCAL_LIBS_TARGET_URL
		SHINY_LIBS_BREEZE_URL = SHINY_LOCAL_LIBS_BREEZE_URL

if not BreezeSettings.SECRET_KEY:
	SECRET_KEY = getkey(DevSettings.SOURCE_ROOT)
	BreezeSettings.SECRET_KEY = SECRET_KEY


def make_run_file():
	f = open('running', 'w+')
	f.write(str(datetime.now().strftime(USUAL_DATE_FORMAT)))
	f.close()

if os.path.isfile('running'):
	# First time
	print '__breeze__started__'
	logging.info('__breeze__started__')

	os.remove('running')
else:
	make_run_file()
	# Second time
	time.sleep(1)
	print '__breeze__load/reload__'
	logging.info('__breeze__load/reload__')
	print 'source home : ' + DevSettings.SOURCE_ROOT
	logging.debug('source home : ' + DevSettings.SOURCE_ROOT)
	print 'project home : ' + DevSettings.PROJECT_PATH
	logging.debug('project home : ' + DevSettings.PROJECT_PATH)
	print 'Logging on %s\nSettings loaded. Running %s on %s' % \
		(Bcolors.bold(LOG_PATH), Bcolors.ok_blue(Bcolors.bold(DevSettings.RUN_MODE)), Bcolors.ok_blue(DevSettings.FULL_HOST_NAME))
	if DevSettings.PHARMA_MODE:
		print Bcolors.bold('RUNNING WITH PHARMA')
	logging.info('Settings loaded. Running %s on %s' % (DevSettings.RUN_MODE, DevSettings.FULL_HOST_NAME))
