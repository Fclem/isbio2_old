# Django settings for isbio project.
from configurations import Settings
import logging
import os
import socket
from datetime import datetime

# TODO : redesign

def recur(nb, funct, args):
	while nb > 0:
		args = funct(args)
		nb -= 1
	return args


def recur_rec(nb, funct, args):
	if nb > 0:
		return recur_rec(nb-1, funct, funct(args))
	return args


USUAL_DATE_FORMAT = "%Y-%m-%d %H:%M:%S%z"
log_fname = 'breeze_%s.log' % datetime.now().strftime("%Y-%m-%d_%H-%M-%S%z")
LOG_PATH = '/var/log/breeze/%s' % log_fname

class BreezeSettings(Settings):
	global USUAL_DATE_FORMAT, LOG_PATH
	DEBUG = False
	TEMPLATE_DEBUG = DEBUG

	USUAL_DATE_FORMAT = USUAL_DATE_FORMAT
	LOG_PATH = LOG_PATH

	logging.basicConfig(level=logging.INFO,
						format='%(asctime)s %(funcName)s %(levelname)-8s %(message)s',
						datefmt=USUAL_DATE_FORMAT,
						# filename='/tmp/BREEZE.log', filemode='w')
						filename=LOG_PATH, filemode='w+')

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
			'OPTIONS': { "init_command": "SET foreign_key_checks = 0;", },
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
	TEMP_FOLDER = '/home/comrade/Projects/fimm/tmp/'
	# Path to R installation
	R_ENGINE_PATH = 'R '

	# Absolute filesystem path to the directory that will hold user-uploaded files.
	# Example: "/home/media/media.lawrence.com/media/"
	MEDIA_ROOT = '/home/comrade/Projects/fimm/db/'
	RORA_LIB = '/home/comrade/Projects/fimm/roralib/'

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
		"/home/comrade/Projects/fimm/isbio/breeze/",
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
	SECRET_KEY = 'ta(zaxdj#)wxg(g+7%f)^e6fu+l#0$y4@81t2g9jo%!i(82ue_'

	# List of callables that know how to import templates from various sources.
	TEMPLATE_LOADERS = (
		'django.template.loaders.filesystem.Loader',
		'django.template.loaders.app_directories.Loader',
		#     'django.template.loaders.eggs.Loader',
	)


	MIDDLEWARE_CLASSES = (
		'django.middleware.common.CommonMiddleware',
		'django.contrib.sessions.middleware.SessionMiddleware',
		'django.middleware.csrf.CsrfViewMiddleware',
		'django.contrib.auth.middleware.AuthenticationMiddleware',
		'django.contrib.messages.middleware.MessageMiddleware',
		'django.middleware.doc.XViewMiddleware',
		# 'breeze.middleware.Log',
		# Uncomment the next line for simple clickjacking protection:
		# 'django.middleware.clickjacking.XFrameOptionsMiddleware',
	)
	# from django_cas.backends import CASBackend
	AUTHENTICATION_BACKENDS = (
		'django.contrib.auth.backends.ModelBackend',
		'django_cas.backends.CASBackend',
	)

	CAS_SERVER_URL = 'https://192.168.0.218:8443/cas/'
	CAS_REDIRECT_URL = '/home/'

	ROOT_URLCONF = 'isbio.urls'

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
		'south',
		'gunicorn',
		# Uncomment the next line to enable the admin:
		'django.contrib.admin',
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
		'filters': {
			'require_debug_false': {
				'()': 'django.utils.log.RequireDebugFalse'
			}
		},
		'handlers': {
			'mail_admins': {
				'level': 'ERROR',
				'filters': ['require_debug_false'],
				'class': 'django.utils.log.AdminEmailHandler'
			}
		},
		'loggers': {
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
	global USUAL_DATE_FORMAT, LOG_PATH
	DEBUG = True
	VERBOSE = False
	SQL_DUMP = False

	ADMINS = (
	('Clement FIERE', 'clement.fiere@helsinki.fi'),  # ('Dmitrii Bychkov', 'piter.dmitry@gmail.com'),
	)

	MANAGERS = ADMINS

	sge_arch = "lx26-amd64";
	os.environ['SGE_ROOT'] = '/opt/gridengine'
	os.environ['QSTAT_BIN'] = os.environ['SGE_ROOT']+'/bin/'+sge_arch+'/qstat'
	os.environ['SGE_ARCH'] = 'UNSUPPORTED-lx3.2.0-40-generic-amd64'
	os.environ['LD_LIBRARY_PATH'] = os.environ['SGE_ROOT']+'/lib/' + os.environ['SGE_ARCH']

	os.environ['SGE_QMASTER_PORT'] = '536'
	os.environ['SGE_EXECD_PORT'] = '537'

	os.environ['SGE_CELL'] = 'default'
	os.environ['DRMAA_LIBRARY_PATH'] = os.environ['SGE_ROOT']+'/lib/'+sge_arch+'/libdrmaa.so'
	os.environ['MAIL'] = '/var/mail/dbychkov'

	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
			'NAME': 'breezedb',  # Or path to database file if using sqlite3.
			'USER': 'comrade',  # Not used with sqlite3.
			'PASSWORD': 'find!comrade',  # Not used with sqlite3.
			'HOST': '/var/run/mysqld/mysqld.sock',  # Set to empty string for localhost. Not used with sqlite3.
			'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
		}
	}
	# auto-sensing if running on dev or prod, for dynamic environment configuration
	FULL_HOST_NAME = socket.gethostname()
	HOST_NAME = str.split(FULL_HOST_NAME, '.')[0]
	# automatically setting RUN_MODE depending on the host name
	RUN_MODE = 'dev' if HOST_NAME.endswith('dev') else 'prod'
	DEV_MODE = RUN_MODE == 'dev'
	MODE_PROD = RUN_MODE == 'prod'
	PHARMA_MODE = False

	# contains everything else (including breeze generated content) than the breeze web source code and static files
	PROJECT_FOLDER = '/fs/projects/'
	# BREEZE_FOLDER = 'breeze-dev/' if DEV_MODE else 'breeze/'
	BREEZE_FOLDER = 'breeze' + ('-dev' if DEV_MODE else '') + '/'
	if HOST_NAME.endswith('ph'):
		BREEZE_FOLDER = 'breeze_new/'
		DEBUG = False
		VERBOSE = False
		SQL_DUMP = False
		PHARMA_MODE = True

	PROJECT_PATH = PROJECT_FOLDER + BREEZE_FOLDER
	if not os.path.isdir(PROJECT_PATH):
		PROJECT_FOLDER = '/projects/'
		PROJECT_PATH = PROJECT_FOLDER + BREEZE_FOLDER

	PROJECT_FHRB_PM_PATH = '/projects/fhrb_pm/'
	JDBC_BRIDGE_PATH = PROJECT_FHRB_PM_PATH + 'bin/start-jdbc-bridge' # Every other path has a trailing /

	# root of the Breeze django project folder, includes 'venv', 'static' folder copy, isbio, logs
	SOURCE_ROOT = recur(3, os.path.dirname, os.path.realpath(__file__)) + '/'

	R_ENGINE_PATH = PROJECT_PATH + 'R/bin/R '
	TEMP_FOLDER = SOURCE_ROOT + 'tmp/' # /homes/dbychkov/dev/isbio/tmp/

	# 'db' folder, containing : reports, scripts, jobs, datasets, pipelines, upload_temp
	MEDIA_ROOT = PROJECT_PATH + 'db/'  # '/project/breeze[-dev]/db/'
	RORA_LIB = PROJECT_PATH + 'RORALib/'
	REPORTS_PATH = MEDIA_ROOT + 'reports/'
	UPLOAD_FOLDER = MEDIA_ROOT + 'upload_temp/'
	STATIC_ROOT = SOURCE_ROOT + 'static/'
	# SHINY RELATED STUFF
	SHINY_APPS = MEDIA_ROOT + 'shinyApps/'
	SHINY_TAGS = MEDIA_ROOT + 'shinyTags/'
	SHINY_REPORTS = MEDIA_ROOT + 'shinyReports/'
	SHINY_REPORT_TEMPLATE_PATH = SOURCE_ROOT + 'isbio/shiny/report_template/'
	SHINY_TARGET_URL = 'http://127.0.0.1:3838/breeze/'
	SHINY_LIBS_TARGET_URL = 'http://127.0.0.1:3838/libs/'
	SHINY_LIBS_BREEZE_URL = '/shiny/libs/'
	SHINY_HEADER_FILE_NAME = 'header.R'
	SHINY_LOADER_FILE_NAME = 'loader.R'
	SHINY_GLOBAL_FILE_NAME = 'global.R'
	SHINY_UI_FILE_NAME = 'ui.R'
	SHINY_SERVER_FILE_NAME = 'server.R'
	SHINY_FILE_LIST = 'files.json'
	# SHINY_SERVER_FOLDER = 'scripts_server/'
	SHINY_UI_FOLDER = 'scripts_body/'
	SHINY_SERVER_FOLDER = 'scripts_server/'
	SHINY_RES_FOLDER = 'www/'
	SHINY_DASH_UI_FILE = 'dash_ui.R'
	SHINY_DASH_SERVER_FILE = 'dashboard_serverside.R'
	SHINY_DASH_UI_FN = SHINY_UI_FOLDER + SHINY_DASH_UI_FILE
	SHINY_DASH_SERVER_FN = SHINY_SERVER_FOLDER + SHINY_DASH_SERVER_FILE
	SHINY_TAG_CANVAS_FN = 'mould/shinyTagTemplate.zip'
	SHINY_TAG_CANVAS_PATH = MEDIA_ROOT + SHINY_TAG_CANVAS_FN
	SHINY_MIN_FILE_SIZE = 14 # library(shiny) is 14 byte long
	# NOZZLE_TARGET_URL = 'http://' + FULL_HOST_NAME + '/'
	# Install shiny library : install.packages('name of the lib', lib='/usr/local/lib/R/site-library', dependencies=TRUE)

	# STATIC URL MAPPINGS
	SHINY_URL = '/shiny/rep/'
	STATIC_URL = '/static/'
	MEDIA_URL = '/media/'

	# number of seconds after witch a job that has not received a sgeid should be marked as aborted
	NO_SGEID_EXPIRY = 60

	# Additional locations of static files
	STATICFILES_DIRS = (
		"",
	)

	logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)s %(funcName)s %(levelname)-8s %(message)s',
						datefmt=USUAL_DATE_FORMAT, # "%d/%b/%Y %H:%M:%S%z",
						filename='/var/log/breeze/breeze-dev.log', filemode='w+')

	# mail config
	EMAIL_HOST = 'smtp.gmail.com'
	EMAIL_HOST_USER = 'breeze.fimm@gmail.com'
	EMAIL_HOST_PASSWORD = 'mult24mult24'
	EMAIL_PORT = '587'
	EMAIL_SUBJECT_PREFIX = '[' + FULL_HOST_NAME + '] '
	EMAIL_USE_TLS = True

	if DEBUG:
		print 'source home : ' + SOURCE_ROOT
		logging.info('source home : ' + SOURCE_ROOT)
		print 'project home : ' + PROJECT_PATH
		logging.info('project home : ' + PROJECT_PATH)
	else:
		VERBOSE = False
	# if dev mode then auto disable DEBUG, for safety
	if MODE_PROD:
		DEBUG = False
		VERBOSE = False

	print 'Logging on %s\nSettings loaded. Running %s on %s' % (LOG_PATH, RUN_MODE, FULL_HOST_NAME)
	if PHARMA_MODE:
		print 'RUNNING WITH PHARMA'
	logging.info('Settings loaded. Running %s on %s' % (RUN_MODE, FULL_HOST_NAME))
