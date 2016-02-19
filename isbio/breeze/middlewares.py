# -*- coding: latin-1 -*-
from multiprocessing import Process
from breeze.watcher import runner
import logging
import os
import datetime
import sys
from breeze.models import UserProfile
from breeze import views
from breeze.utils import Bcolors
from django.conf import settings

logger = logging.getLogger(__name__)
check_file_dt = ''
check_file_state = ''


# experimental site-disabling
# clem 14/09/2015
def modification_date(filename, formatted=False):
	t = os.path.getmtime(filename)
	return datetime.datetime.fromtimestamp(t) if formatted else t


def creation_date(filename, formatted=False):
	t = os.path.getctime(filename)
	return datetime.datetime.fromtimestamp(t) if formatted else t


def get_state():
	return open('./breeze').read().lower().replace('\n', '').replace('\r', '').replace('\f', '').replace(' ', '')


def update_state():
	global check_file_dt, check_file_state
	check_file_dt = modification_date('./breeze')
	check_file_state = get_state()


def is_on():
	global check_file_state
	if check_file_state == '':
		update_state()
	return check_file_state == 'up' or check_file_state == 'enabled' or check_file_state == 'on'


def reload_urlconf(urlconf=None):
	print Bcolors.warning('State changed') + ', ' + Bcolors.ok_blue('Reloading urls...')
	if urlconf is None:
		urlconf = settings.ROOT_URLCONF
	if urlconf in sys.modules:
		reload(sys.modules[urlconf])


def check_state():
	global check_file_dt, check_file_state
	if modification_date('./breeze') != check_file_dt:
		new_state = get_state()
		old_state = check_file_state
		update_state()
		if new_state != old_state:
			reload_urlconf()
# END


class JobKeeper:
	p = Process()

	def __init__(self):
		JobKeeper.p = Process(target=runner)
		JobKeeper.p.start()

	def process_request(self, request):
		if not JobKeeper.p.is_alive():
			JobKeeper.p.terminate()
			log = logger.getChild('watcher_guard')
			log.warning('watcher was down, restarting...')
			self.__init__()


class BreezeAwake:
	def __init__(self):
		update_state()

	@staticmethod
	def process_request(request):
		check_state()

if settings.ENABLE_DATADOG:
	from datadog import statsd


	class DataDog:
		def __init__(self):
			# Increment a counter.
			statsd.increment('python.breeze.reload')
			statsd.event('Breeze reload', '', 'info', hostname=settings.HOST_NAME)

		@staticmethod
		def process_request(request):
			statsd.increment('python.breeze.request')

		@staticmethod
		def process_view(request, view_func, view_args, view_kwargs):
			statsd.increment('python.breeze.page.views')
			statsd.increment('python.breeze.page.view.' + str(view_func.__name__))
			if request.user:
				statsd.increment('python.breeze.page.auth_views')

		@staticmethod
		def process_exception(exception, e):
			statsd.event('Python Exception', str(e), 'warning', hostname=settings.HOST_NAME)
			statsd.increment('python.breeze.exception')


class CheckUserProfile(object):
	@staticmethod
	def process_exception(request, exception):
		if isinstance(exception, UserProfile.DoesNotExist):
			return views.home(request)


class RemoteFW:
	@staticmethod
	def process_request(request):
		print type(request), request


class Empty:
	pass
