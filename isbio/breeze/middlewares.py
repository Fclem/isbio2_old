# -*- coding: latin-1 -*-
from multiprocessing import Process
from breeze.watcher import runner
import logging
from breeze.models import UserProfile
from breeze import views

logger = logging.getLogger(__name__)


class JobKeeper:
	p = Process()

	def __init__(self):
		# from breeze.watcher import runner
		JobKeeper.p = Process(target=runner)
		JobKeeper.p.start()
		# print JobKeeper.p.pid

	def process_request(self, request):
		if not JobKeeper.p.is_alive():
			JobKeeper.p.terminate()
			log = logger.getChild('watcher_guard')
			log.warning('watcher was down, restarting...')
			self.__init__()


class CheckUserProfile(object):
	@staticmethod
	def process_exception(request, exception):
		if isinstance(exception, UserProfile.DoesNotExist):
			return views.home(request)

