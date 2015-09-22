import django.db
import os
from multiprocessing import Process
from utils import console_print as cp
import time
from breeze.models import Report, Jobs, JobStat
import drmaa
from utils import *
from b_exceptions import *
from django.conf import settings

# from exceptions import Exception
# import logging
# logger = logging.getLogger(__name__)
DB_REFRESH = settings.WATCHER_DB_REFRESH
PROC_REFRESH = settings.WATCHER_PROC_REFRESH

if settings.HOST_NAME.startswith('breeze'):
	s = None
	proc_lst = dict()


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
		global s
		# self = args[0]
		s = drmaa.Session()
		s.initialize()
		func(*args, **kwargs)
		s.exit()

	return inner


class ProcItem(object):
	def __init__(self, proc, dbitem):
		assert isinstance(proc, Process) or proc is None
		assert isinstance(dbitem, Report) or isinstance(dbitem, Jobs)
		self.process = proc
		self._db_item_id = dbitem.id
		self._inst_type = dbitem.instance_of

	@property
	def db_item(self):
		return self._inst_type.objects.get(pk=self._db_item_id)


def refresh_db():
	"""
	Scan the db for new reports to be run or updated
	"""
	# django.db.close_connection()
	lst_r = Report.objects.f.get_run_wait()
	lst_j = Jobs.objects.f.get_run_wait()
	for item in lst_r:
		_spawn_the_job(item)
	for item in lst_j:
		_spawn_the_job(item)

	lst_r = Report.objects.f.get_active()
	lst_j = Jobs.objects.f.get_active()
	for item in lst_r:
		if item.id not in proc_lst.keys():
			_reattach_the_job(item)
	for item in lst_j:
		if item.id not in proc_lst.keys():
			_reattach_the_job(item)


def end_tracking(proc_item): # proc_item):
	"""
	:param proc_item:
	:type proc_item: ProcItem
	"""
	# TODO check that
	# proc_item.db_item.breeze_stat = JobStat.DONE
	get_logger().debug('%s%s : ending tracking' % proc_item.db_item.short_id)
	a = proc_item.db_item.is_r_successful
	# proc_item.process.terminate()
	del proc_lst[proc_item.db_item.id]


def refresh_proc():
	"""
		Checks each running process that waits against an DRMAA job to end
		There might also be jobs on the list that have no process :
		i.e. if the waiter crashed, server restarted etc
	"""
	for each in proc_lst.keys():
		proc_item = proc_lst[each]
		assert isinstance(proc_item, ProcItem)
		dbitem = proc_item.db_item
		proc = proc_item.process

		if not proc.is_alive(): # process finished
			exit_c = proc.exitcode
			end_tracking(proc_item)
			msg = '%s%s : waiting process ended with code %s' % (dbitem.short_id + (exit_c,))
			if exit_c != 0:
				get_logger().error(msg)
				# drmaa waiter failed on first wait run
				dbitem.breeze_stat = JobStat.FAILED
				# relunch wait to check out
				_reattach_the_job(dbitem)
			else:
				get_logger().debug(msg)
			# else : clean exit, success assessment code is managed by waiter
		else:
			refresh_qstat(proc_item)


def refresh_qstat(proc_item):
	"""
	Update the status of one Report
	Can trigger job abortion if instructed to
	:param proc_item: a ProcItem object
	:type proc_item: ProcItem
	"""
	# from qstat import Qstat
	assert isinstance(proc_item, ProcItem)
	dbitem = proc_item.db_item
	assert isinstance(dbitem, Report) or isinstance(dbitem, Jobs)
	log = get_logger()

	status = None
	if not dbitem.is_sgeid_empty:
		if not dbitem.is_done:
			try:
				status = dbitem.qstat_stat()
				# log.debug('%s%s : qstat says %s' % (dbitem.short_id + (status,)) )
			except NoSuchJob as e:
				log.warning('%s%s : qstat InvalidJobException (%s)' % (dbitem.short_id + (e,)))
				end_tracking(proc_item)
			if status is not None and status != dbitem.status and not dbitem.aborting:
				dbitem.breeze_stat = status
	elif dbitem.is_sgeid_timeout: # and not dbitem.is_done:
		log.warning('%s%s : SgeId timeout !' % dbitem.short_id)
		end_tracking(proc_item)
		dbitem.re_submit_to_cluster()


@with_drmaa
def _reattach_the_job(dbitem):
	"""
	:param dbitem:
	:type dbitem: Report | Jobs
	"""
	log = get_logger()
	assert isinstance(dbitem, Report) or isinstance(dbitem, Jobs)
	#if not dbitem.aborting:
	try:
		p = Process(target=dbitem.waiter, args=(s, ))
		p.start()
		proc_lst.update({ dbitem.id: ProcItem(p, dbitem) })

		log.debug('%s%s : reattaching job.waiter in PID%s' % (dbitem.short_id + (p.pid,)))
	except Exception as e:
		log.exception('%s%s : unhandled exception : %s' % (dbitem.short_id + (e,)))
		return False


def _spawn_the_job(dbitem):
	"""
	:param dbitem:
	:type dbitem: Report | Jobs
	"""
	log = get_logger()
	assert isinstance(dbitem, Report) or isinstance(dbitem, Jobs)
	if not dbitem.aborting:
		try:
			p = Process(target=dbitem.run)
			p.start()
			# proc_lst.update({ dbitem.id: (p, dbitem) })
			proc_lst.update({ dbitem.id: ProcItem(p, dbitem) })

			log.debug('%s%s : spawning job.run in PID%s' % (dbitem.short_id + (p.pid,)))
		except Exception as e:
			log.exception('%s%s : unhandled exception : %s' % (dbitem.short_id + (e,)))
			return False
	else:
		# abort_sub(ProcItem(None, dbitem), s)
		dbitem.breeze_stat = JobStat.ABORTED


def runner():
	"""
	Worker that post the jobs, and update their status
	Run until killed or crashed
	TO BE RUN ONLY_ONCE IN A SEPARATE BACKGROUND PROCESS
	"""
	get_logger().info('now running')
	# watching = Watcher()

	i = 0
	j = 0
	sleep_time = min(DB_REFRESH, PROC_REFRESH)
	while True:
		i += 1 # DB refresh time counter
		j += 1 # PROC refresh time counter
		if i == (DB_REFRESH / sleep_time):
			# console_print('db_refresh')
			i = 0
			# Process(target=refresh_db).start()
			refresh_db()

		if j == (PROC_REFRESH / sleep_time):
			# console_print('proc_refresh')
			j = 0
			# Process(target=refresh_proc).start()
			refresh_proc()

		time.sleep(sleep_time)
