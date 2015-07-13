# -*- coding: latin-1 -*-
from multiprocessing import Process
from breeze.watcher import runner
import logging
from breeze.models import UserProfile
from breeze import views

logger = logging.getLogger(__name__)

class JobKeeper:
	def __init__(self):
		self.p = Process(target=runner)
		self.p.start()

	def process_request(self, request):
		if not self.p.is_alive():
			self.p.terminate()
			log = logger.getChild('init.watcher_guard')
			log.warning('watcher was down, restarting...')
			self.__init__()


class CheckUserProfile(object):
	@staticmethod
	def process_exception(request, exception):
		if isinstance(exception, UserProfile.DoesNotExist):
			return views.home(request)

