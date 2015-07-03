from symbol import argument

__author__ = 'clem'
import django.db
from django.template.defaulttags import now
import os, shutil, re, stat, copy
from datetime import datetime
from multiprocessing import Process
from Bio import Entrez
from django.template.defaultfilters import slugify
from django.conf import settings
import auxiliary as aux
import logging
import pickle, json
import hashlib
from django.utils import timezone
from datetime import timedelta
from auxiliary import console_print as cp
import time
from exceptions import Exception
from breeze.models import Report, Jobs, JobStat
from breeze import shell
import drmaa

logger = logging.getLogger(__name__)
DB_REFRESH = settings.WATCHER_DB_REFRESH
PROC_REFRESH = settings.WATCHER_PROC_REFRESH


def console_print(text, report=None):
	sup = ''
	if report is not None:
		sup = ' report %s, ' % report
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
	truc = 'machin'

	def __init__(self):
		if settings.HOST_NAME.startswith('breeze'):

			self.s = None

			self.jobs_lst = dict()
			self.report_lst = list()
			self.report_p = dict()

	@staticmethod
	def report(id):
		django.db.close_connection()
		return Report.objects.get(id=id)

	def refresh_db(self):
		"""
		Scan the db for new reports tu be run or updated
		:return: if any changed occured
		:rtype: bool
		"""
		changed = False
		django.db.close_connection()
		# lst = Report.objects.filter(breeze_stat='run_wait')
		lst = Report.objects.all().exclude(breeze_stat=JobStat.DONE).exclude(status=JobStat.SCHEDULED)
		for item in lst:
			# self.report_lst.update({ item.id: item })
			if item.breeze_stat == JobStat.RUN_WAIT:
				self._run_report(item)
				changed = True
			elif item.breeze_stat != JobStat.DONE:
				self.refresh_drmaa(item.id)

		return changed

	def refresh_proc(self):
		"""
		Ping each running process that waits against an DRMAA job to end
		"""
		for each in self.report_p.keys():
			report = self.report(each[1])
			proc = self.report_p[each]
			assert isinstance(proc, Process)
			if not proc.is_alive():
				exit_c = proc.exitcode
				console_print('exited with code : %s' % exit_c, report.id)
				proc.terminate()
				console_print('%s : %s report says : %s' % (each, proc, report.status), report.id)
				del self.report_p[each]
				# at that point, ether the run was successful and the proccess saed that state,
				# or we have to deal with a uncompleted run
				if report.status != JobStat.SUCCEED and report.breeze_stat != JobStat.ABORT \
					and report.status != JobStat.ABORTED:
					console_print('failing job', report.id)
					report.set_status(JobStat.FAILED)
			else:
				self.refresh_drmaa(each[1])

	@with_drmaa
	def refresh_drmaa(self, rid):
		"""
		Update the status of one Report
		Can trigger job abortion if instructed to
		:param rid: a Report id
		:type rid: int
		"""
		s = self.s
		if s is None:
			console_print('NO DRMAA instance availiable', rid)
			return

		log = logger.getChild('watcher.refresh_drmaa')
		job = self.report(rid)
		type = 'r'
		status = None
		if job.breeze_stat == JobStat.ABORT:
			job.set_status(JobStat.ABORTED)
			if job.sgeid is not None and job.sgeid != '' and job.sgeid > 0:
				s.control(job.sgeid, drmaa.JobControlAction.TERMINATE)
		elif job.sgeid is not None and job.sgeid != '' and int(job.sgeid) > 0:
			try:
				status = str(s.jobStatus(job.sgeid))
				log.info('%s%s : drmaa says %s' % (type, job.id, status) )
			except drmaa.InvalidArgumentException:
				log.exception('%s%s : drmaa InvalidArgumentException' % (type, job.id))
				# if settings.DEBUG: console_print("InvalidArgumentException", rid)
			except drmaa.InvalidJobException:
				log.warning('%s%s : drmaa InvalidJobException' % (type, job.id))
				# if settings.DEBUG: console_print("InvalidJobException", rid)
				if job.is_done():
					status = JobStat.SUCCEED
				else:
					status = JobStat.ABORTED
			except drmaa.AlreadyActiveSessionException:
				if settings.DEBUG: console_print("AlreadyActiveSessionException", rid)
				log.error('%s%s : drmaa AlreadyActiveSessionException' % (type, job.id))

			if status != job.status:
				job.set_status(status)
				# No need to save, set_status take care of that
		else:
			now_t = timezone.now()  # .time()
			crea = job.created
			tdelta = now_t - crea
			assert isinstance(tdelta, timedelta)
			log.warning('%s%s : sgeid has been empty for %s sec' % (type, job.id, tdelta.seconds))
			if settings.DEBUG: console_print('sgeid has been empty for ' + str(tdelta.seconds) + ' sec', rid)
			if tdelta > timedelta(seconds=settings.NO_SGEID_EXPIRY):
				log.warning('%s%s : trying to resubmit the report' % (type, job.id))
				if settings.DEBUG: console_print('trying to resubmit the report', rid)
				# TODO : move this to set_status
				job.created = datetime.now().strftime(settings.USUAL_DATE_FORMAT)
				# reset job status to RUN_WAIT which will trigger job.run
				job.set_status(JobStat.RUN_WAIT)

		# s.exit()

	def _run_report(self, dbitem):
		log = logger.getChild('watcher.run_report')
		assert isinstance(log, logging.getLoggerClass())
		assert isinstance(dbitem, Report)
		try:
			# submit r-code

			p = Process(target=dbitem.run)
			p.start()
			self.report_p.update({ (p.pid, dbitem.id): p })

			console_print('running report in blocking process %s', (dbitem.id, p.pid))
			log.info('r%s : running report in blocking process %s' % (p.pid, dbitem.id))
		except Exception as e:
			log.exception('r%s : unhandled error while starting run_process thread : %s' % (dbitem.id, e))
			return False


class Watched:
	type = None

	def __unicode__(self):
		return self.type

	class Meta:
		abstract = True


class WatchedJob(Watched):
	type = Jobs

	@property
	def status(self):
		return self.type


class WatchedReport():
	type = Report

	@property
	def status(self):
		return self.type


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
