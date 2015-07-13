from symbol import argument

__author__ = 'clem'
import django.db
import os
from datetime import datetime
from multiprocessing import Process
from django.conf import settings
# import logging
from django.utils import timezone
from datetime import timedelta
from auxiliary import console_print as cp
import time
from exceptions import Exception
from breeze.models import Report, Jobs, JobStat
import drmaa
from utils import *

# logger = logging.getLogger(__name__)
DB_REFRESH = settings.WATCHER_DB_REFRESH
PROC_REFRESH = settings.WATCHER_PROC_REFRESH


def console_print(text, dbitem=None):
	sup = ''
	if dbitem is not None:
		sup = '%s%s ' % (dbitem.instance_type[0], dbitem.id)
	cp("PID%s : %s" % (os.getpid(), sup + text), settings.CONSOLE_DATE_F)


def with_drmaa(func):
	"""
	wrapper to use only one drmaa instance
	:param func:
	:type func:
	:return:
	:rtype:
	"""
	def inner(*args, **kwargs):
		self = args[0]
		self.s = drmaa.Session()
		self.s.initialize()
		func(*args, **kwargs)
		self.s.exit()

	return inner

class Watcher:
	def __init__(self):
		if settings.HOST_NAME.startswith('breeze'):

			self.s = None

			self.jobs_lst = dict()
			self.report_lst = list()
			self.proc_lst = dict()

	@staticmethod
	def get_fresh_obj(dbitem):
		assert isinstance(dbitem, Report) or isinstance(dbitem, Jobs)
		if dbitem.is_job:
			return Jobs.objects.get(pk=dbitem.id)
		elif dbitem.is_report:
			return Report.objects.get(pk=dbitem.id)

	def refresh_db(self):
		"""
		Scan the db for new reports tu be run or updated
		:return: if any changed occured
		:rtype: bool
		"""
		changed = False
		django.db.close_connection()

		lst = Report.objects.get_active()
		for item in lst:
			self.refresh_drmaa(item)

		lst = Report.objects.get_run_wait()
		for item in lst:
			self._spawn_the_job(item)
			changed = True
		# TODO merge this
		lst = Jobs.objects.get_active()
		for item in lst:
			self.refresh_drmaa(item)

		lst = Jobs.objects.get_run_wait()
		for item in lst:
			self._spawn_the_job(item)
			changed = True

		return changed

	def refresh_proc(self):
		"""
		Ping each running process that waits against an DRMAA job to end
		"""
		for each in self.proc_lst.keys():
			dbitem = self.proc_lst[each][1]
			proc = self.proc_lst[each][0]
			assert isinstance(proc, Process)
			assert isinstance(dbitem, Report) or isinstance(dbitem, Jobs)
			if not proc.is_alive():
				exit_c = proc.exitcode
				console_print('PID%s exited with code : %s' % (proc.pid, exit_c), dbitem)
				proc.terminate()
				console_print('%s : %s dbitem says : %s' % (each, proc, dbitem.status), dbitem)
				del self.proc_lst[each]
				# at that point, either the run was successful and the process saved that state,
				# or we have to deal with a uncompleted run
				if not dbitem.is_done and dbitem.status != JobStat.ABORTED:
					console_print('the job has apparently failed', dbitem)
					dbitem.breeze_stat = JobStat.FAILED
			else:
				self.refresh_drmaa(self.proc_lst[each][1])

	@with_drmaa
	def refresh_drmaa(self, dbitem):
		"""
		Update the status of one Report
		Can trigger job abortion if instructed to
		:param dbitem: a Runnable subclass
		:type dbitem: Report | Jobs
		"""
		assert isinstance(dbitem, Report) or isinstance(dbitem, Jobs)
		dbitem = self.get_fresh_obj(dbitem)
		log = get_logger()
		i_type = dbitem.instance_type[0]
		log_data = (i_type, dbitem.id)
		if self.s is None:
			console_print('NO DRMAA instance available', dbitem)
			log.error('NO DRMAA instance available' % log_data)
			return

		status = None
		if dbitem.breeze_stat == JobStat.ABORT:
			dbitem.breeze_stat = JobStat.ABORTED
			if dbitem.sgeid is not None and dbitem.sgeid != '' and dbitem.sgeid > 0:
				self.s.control(dbitem.sgeid, drmaa.JobControlAction.TERMINATE)
		elif dbitem.sgeid is not None and dbitem.sgeid != '' and int(dbitem.sgeid) > 0:
			if not dbitem.is_done:
				try:
					status = str(self.s.jobStatus(dbitem.sgeid))
					log.info('%s%s : drmaa says %s' % (i_type, dbitem.id, status) )
				except drmaa.InvalidArgumentException:
					log.exception('%s%s : drmaa InvalidArgumentException' % log_data)
					if settings.DEBUG: console_print("InvalidArgumentException", dbitem)
				except drmaa.InvalidJobException:
					log.warning('%s%s : drmaa InvalidJobException' % log_data)
					if settings.DEBUG: console_print("InvalidJobException", dbitem)
					if dbitem.is_done:
						status = JobStat.SUCCEED
					else: # The following has no effect. Good or Bad ? TODO Fix or delete ?
						status = JobStat.ABORTED
				except drmaa.AlreadyActiveSessionException:
					if settings.DEBUG: console_print("AlreadyActiveSessionException", dbitem)
					log.error('%s%s : drmaa AlreadyActiveSessionException' % log_data)

				if status != dbitem.status:
					dbitem.breeze_stat = status
		else:
			now_t = timezone.now()  # .time()
			crea = dbitem.created
			tdelta = now_t - crea
			assert isinstance(tdelta, timedelta)
			log.warning('%s%s : sgeid has been empty for %s sec' % (i_type, dbitem.id, tdelta.seconds))
			if settings.DEBUG: console_print('sgeid has been empty for ' + str(tdelta.seconds) + ' sec', dbitem)
			if tdelta > timedelta(seconds=settings.NO_SGEID_EXPIRY):
				log.warning('%s%s : resetting job status' % log_data)
				if settings.DEBUG: console_print('resetting job status', dbitem)
				# TODO : move this to _set_status
				dbitem.created = datetime.now().strftime(settings.USUAL_DATE_FORMAT)
				# reset job status to RUN_WAIT which will trigger job.run
				dbitem.breeze_stat = JobStat.RUN_WAIT

		# s.exit()

	def _spawn_the_job(self, dbitem):
		log = get_logger()
		assert isinstance(dbitem, Report) or isinstance(dbitem, Jobs)
		dbitem = self.get_fresh_obj(dbitem)
		i_type = dbitem.instance_type[0]
		try:
			p = Process(target=dbitem.run)
			p.start()
			self.proc_lst.update({ (p.pid, dbitem.id): (p, dbitem) })

			console_print('running job in PID%s' % p.pid, dbitem)
			log.info('%s%s : running job in PID%s' % (i_type, dbitem.id, p.pid))
		except Exception as e:
			log.exception('%s%s : unhandled exception in _spawn_the_job : %s' % (i_type, dbitem.id, e))
			return False

# TO BE RUN ONLY_ONCE IN A SEPARATE BACKGROUND PROCESS
def runner():
	"""
	Worker that post the jobs, and update their status
	Run until killed or crashed
	TO BE RUN ONLY_ONCE IN A SEPARATE BACKGROUND PROCESS
	"""
	console_print("Running watcher")
	watching = Watcher()

	i = 0
	j = 0
	sleep_time = min(DB_REFRESH, PROC_REFRESH)
	while True:
		i += 1 # DB refresh time counter
		j += 1 # PROC refresh time counter
		if i == (DB_REFRESH / sleep_time):
			# console_print('db_refresh')
			i = 0
			watching.refresh_db()
		if j == (PROC_REFRESH / sleep_time):
			# console_print('proc_refresh')
			j = 0
			watching.refresh_proc()

		time.sleep(sleep_time)
