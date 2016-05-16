from compute_interface_module import * # has os, abc, JobStat, Runnable, ComputeTarget and utilities.*
from docker_client import *
a_lock = Lock()

__version__ = '0.2'
__author__ = 'clem'
__date__ = '15/03/2016'


# clem 15/03/2016
class DockerInterface(ComputeInterface):
	ssh_tunnel = None
	auto_remove = True
	__docker_storage = None
	_data_storage = None
	_jobs_storage = None
	run_id = '' # stores the md5 of the sent archive ie. the job id
	proc = None
	client = None
	_lock = None
	_label = ''
	my_volume = DockerVolume('/home/breeze/data/', '/breeze')
	my_run = None
	_container = None
	cat = DockerEventCategories

	# DOCKER HUB RELATED CONF
	REPO_PWD = password_from_file('~/code/docker_repo')
	REPO_LOGIN = 'fimm'
	REPO_EMAIL = 'clement.fiere@fimm.fi'
	# TARGET DOCKER DAEMON CONF
	DOCKER_REMOTE_HOST = '127.0.0.1'
	DOCKER_REMOTE_PORT = 4243
	DOCKER_LOCAL_PORT = 0
	DOCKER_REMOTE_BIND_ADDR = (DOCKER_REMOTE_HOST, DOCKER_REMOTE_PORT)
	DOCKER_LOCAL_BIND_ADDR = None
	DOCKER_REMOTE_DAEMON_URL = 'tcp://%s:%s' % DOCKER_REMOTE_BIND_ADDR
	DOCKER_LOCAL_DAEMON_URL = ''
	# SSH TUNNEL CONFIG
	SSH_HOST = None
	SSH_CMD_BASE = ['ssh', '-CfNnL', '%s:%s:%s']
	# SSH_CMD_BASE = ['ssh', '-CfNnL', '%s:%s:%s' % (DOCKER_LOCAL_PORT, DOCKER_REMOTE_HOST, DOCKER_REMOTE_PORT)]
	SSH_BASH_KILL_BASE = 'ps aux | grep "%s"' + " | awk '{ print $2 }' | tr '\\n' ' '"
	# CONTAINER SPECIFIC
	NORMAL_ENDING = ['Running R script... done !', 'Success !', 'done']

	MY_DOCKER_HUB = DockerRepo(REPO_LOGIN, REPO_PWD, email=REPO_EMAIL)
	LINE3 = '\x1b[34mCreating archive /root/out.tar.xz'
	LINE2 = '\x1b[1mcreate_blob_from_path\x1b[0m(' # FIXME NOT ABSTRACT
	LINES = dict([(-3, LINE3), (-2, LINE2)])

	_status = JobStat.INIT

	def __init__(self, compute_target, storage_backend=None):
		"""

		:type storage_backend: module
		"""
		super(DockerInterface, self).__init__(compute_target, storage_backend)

		self.SSH_HOST = compute_target.tunnel_host
		# TODO changes these to factory
		self.DOCKER_LOCAL_PORT = self.get_a_port()
		self.DOCKER_LOCAL_BIND_ADDR = ('127.0.0.1', self.DOCKER_LOCAL_PORT)
		self.DOCKER_LOCAL_DAEMON_URL = 'tcp://%s:%s' % self.DOCKER_LOCAL_BIND_ADDR
		self.SSH_CMD = ['ssh', '-CfNnL', '%s:%s:%s' % (self.DOCKER_LOCAL_PORT, self.DOCKER_REMOTE_HOST,
		self.DOCKER_REMOTE_PORT), self.SSH_HOST]
		self._label = compute_target.tunnel_host[0:2]

		res = False
		if not self._test_connection(self.DOCKER_LOCAL_BIND_ADDR):
			self.log.debug('No connection to daemon, trying ssh tunnel')
			self._get_ssh()
			if self._test_connection(self.DOCKER_LOCAL_BIND_ADDR):
				res = self._connect()
		else:
			res = self._connect()
		if not res:
			self.log.error('FAILURE connecting to docker daemon, cannot proceed')
			self._set_status(JobStat.FAILED)
			self._runnable.manage_run_failed(1, 99)
			raise DaemonNotConnected

	# clem 10/05/2016
	def get_a_port(self):
		""" Give the port number of an existing ssh tunnel, or return a free port if no (or more than 1) tunnel exists

		:return: a TCP port number
		:rtype: int
		"""
		import subprocess
		lookup = ' '.join(self.SSH_CMD_BASE + [self.SSH_HOST]) %\
			('.*', self.DOCKER_REMOTE_HOST, self.DOCKER_REMOTE_PORT)
		full_string = 'ps aux|grep "%s"|grep -v grep' % lookup
		tmp = subprocess.Popen(full_string, shell=True, stdout=subprocess.PIPE).stdout
		lines = []
		for line in tmp.readlines():
			try:
				lines.append(line.split(' ')[-2].split(':')[0])
			except Exception:
				pass
		if len(lines) > 0:
			if len(lines) == 1:
				self.log.debug('Found pre-existing active ssh tunnel, gonna re-use it')
				return int(lines[0])
			else:
				self.log.warning('Found %s active ssh tunnels, killing them all...' % len(lines))
				subprocess.Popen('killall ssh && killall ssh', shell=True, stdout=subprocess.PIPE)
		return int(get_free_port())

	# TODO externalize
	# clem 08/09/2016
	def _test_connection(self, target):
		import socket
		s = socket.socket() # socket.AF_INET, socket.SOCK_STREAM
		try:
			s.settimeout(2)
			self.log.debug('testing connection to %s Tout: %s sec' % (str(target), s.gettimeout()))
			s.connect(target)
			self.log.debug('success')
			return True
		except socket.timeout:
			self.log.exception('connect %s: Time-out' % str(target))
		except socket.error as e:
			self.log.exception('connect %s: %s' % (str(target), e[1]))
		except Exception as e:
			self.log.error('connect %s' % str((type(e), e)))
		finally:
			s.close()

		return False

	# clem 07/04/2016
	def _connect(self):
		# self.client = DockerClient(self.DOCKER_LOCAL_DAEMON_URL, self.MY_DOCKER_HUB, False)
		self.client = get_docker_client(self.DOCKER_LOCAL_DAEMON_URL, self.MY_DOCKER_HUB, False)
		return self.client

	# TODO externalize
	# clem 06/04/2016 # FIXME change print to log
	def _get_ssh(self):
		if self.SSH_HOST:
			import subprocess
			print 'Establishing ssh tunnel, running', self._ssh_cmd_list, '...',
			self.ssh_tunnel = subprocess.Popen(self._ssh_cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
				preexec_fn=os.setsid)
			print 'done,',
			stat = self.ssh_tunnel.poll()
			while stat is None:
				stat = self.ssh_tunnel.poll()
			print 'bg PID :', self.ssh_tunnel.pid
		else:
			raise AttributeError('Cannot establish ssh tunnel since no ssh_host provided during init')

	def _attach_event_manager(self):
		if self.my_run and isinstance(self.my_run, DockerRun):
			self.my_run.event_listener = self._event_manager_wrapper()
			self.log.debug('Attached event listener')
		return True

	# clem 11/05/2016
	@property
	def label(self):
		return '<docker%s%s>' % ('_' + self._label, '' if self.client else ' ?')

	# clem 11/05/2016
	@property
	def log(self):
		log_obj = logging.LoggerAdapter(self._compute_target.runnable.log_custom(1), dict())
		bridge = log_obj.process
		log_obj.process = lambda msg, kwargs: bridge(self.label + ' ' + str(msg), kwargs)
		return log_obj

	# clem 12/05/2016
	@property
	def container(self):
		if not self._container and self.client and self._runnable.sgeid:
			self._container = self.client.get_container(self._runnable.sgeid)
			self.log.debug('Found container %s' % self._container.name)
			if self._container.is_running:
				self._set_global_status(JobStat.RUNNING)
			else:
				self._set_global_status(JobStat.SUBMITTED)
		return self._container

	def _run(self):
		self._container = self.client.run(self.my_run)
		self.log.debug('Got %s' % repr(self.container))
		return self.container

	def _event_manager_wrapper(self):
		def my_event_manager(event):
			assert isinstance(event, DockerEvent)
			# self.write_log(event)
			if event.description in (DockerEventCategories.DIE, DockerEventCategories.KILL):
				self.job_is_done()
			elif event.description == DockerEventCategories.START:
				self.log.debug('%s started' % event.container.name)
				self._set_global_status(JobStat.RUNNING)

		return my_event_manager

	# clem 29/04/2016
	@property
	def _ssh_cmd_list(self):
		assert isinstance(self.SSH_HOST, basestring)
		return self.SSH_CMD

	# clem 20/04/2016
	@property
	def _job_storage(self):
		if not self._jobs_storage:
			self._jobs_storage = self._get_storage(self.storage_backend.jobs_container())
		return self._jobs_storage

	# clem 21/04/2016
	@property
	def _result_storage(self):
		if not self._data_storage:
			self._data_storage = self._get_storage(self.storage_backend.data_container())
		return self._data_storage

	# clem 21/04/2016
	@property
	def _docker_storage(self):
		if not self.__docker_storage:
			self.__docker_storage = self._get_storage(self.storage_backend.management_container())
		return self.__docker_storage

	def send_job(self):
		self._set_global_status(JobStat.PREPARE_RUN)
		# FIXME : still on test design (using a pre-assembled report job)
		job_folder = None
		output_filename = None
		if not job_folder:
			job_folder = '/projects/breeze-dev/db/testing/in/'
		if not output_filename:
			output_filename = '/projects/breeze-dev/db/testing/temp.tar.bz2'

		# real implementation
		if self.make_tarfile(output_filename, job_folder):
			self._docker_storage.upload_self() # update the cloud version of azure_storage.py
			self.run_id = get_file_md5(output_filename)
			b = self._job_storage.upload(self.run_id, output_filename)
			if b:
				os.remove(output_filename)
				self.my_run = DockerRun('fimm/r-light:latest', '/run.sh %s' % self.run_id, self.my_volume)
				# self.my_run = my_run
				self._attach_event_manager()
				if self._run():
					self._runnable.sgeid = self.container.short_id
					self._set_global_status(JobStat.SUBMITTED)
					return True
		else:
			print 'failed'
		self._set_status(JobStat.FAILED)
		self._runnable.manage_run_failed(1, 88)
		return False

	# clem 10/05/2016
	def _set_status(self, status):
		""" Set status of local object for state tracking

		:param status: status
		:type status: JobStat
		"""
		self._status = status

	# clem 10/05/2016
	def _set_global_status(self, status):
		""" Set status of both local and runnable object for state tracking

		:param status: status
		:type status: JobStat
		"""
		self._set_status(status)
		self._runnable.breeze_stat = status

	# clem 21/04/2016
	def get_results(self, output_filename=None):
		if not output_filename:
			output_filename = '/projects/breeze-dev/db/testing/results_%s.tar.xz' % self.run_id
		try:
			e = self._result_storage.download(self.run_id, output_filename)

			# if e:
			# 	self.result_storage.erase(self.run_id)
			self._set_status(JobStat.SUCCEED)
			self._runnable.manage_run_success(0)
			# TODO extract in original path
			return e
		except self._missing_exception:
			self.log.error('No result found for job %s' % self.run_id)
			self._set_status(JobStat.FAILED)
			self._runnable.manage_run_failed(1, 92)
			raise

	# clem 06/05/2016
	def abort(self):
		if self._runnable.breeze_stat != JobStat.DONE:
			self._set_global_status(JobStat.ABORT)
			if self.container:
				try:
					self.container.stop()
				except Exception as e:
					self.log.exception('Stopping container failed : %s' % str(e))
				try:
					self.container.kill()
				except Exception as e:
					self.log.exception('Killing container failed : %s' % str(e))
				try:
					self.container.remove_container()
				except Exception as e:
					self.log.exception('Removing container failed : %s' % str(e))
			self._set_status(JobStat.ABORTED)
			self._runnable.manage_run_aborted(1, 95)
			return True
		return False

	# clem 06/05/2016
	def busy_waiting(self, *args):
		if not self.container:
			return False
		while self.container.is_running and not self._runnable.aborting:
			time.sleep(1)
		return True

	# clem 06/05/2016
	def status(self): # TODO
		return self._status

	# clem 06/05/2016
	def job_is_done(self):
		cont = self.container
		log = str(cont.logs)
		assert isinstance(cont, DockerContainer)
		self._set_global_status(JobStat.GETTING_RESULTS)
		self.log.info('Died code %s. Total execution time : %s' % (cont.status.ExitCode,
		cont.delta_display))
		if cont.status.ExitCode > 0:
			self._set_status(JobStat.FAILED)
			self._runnable.manage_run_failed(1, cont.status.ExitCode)
			self._set_global_status(JobStat.FAILED)
			self.log.warning('Failure (container will not be deleted) ! Run log :\n%s' % log)
		else:
			self.log.info('Success !')
			# filter the end of the log to match it to a specific pattern, to ensure no unexpected event
			# happened
			the_end = log.split('\n')[-6:-1] # copy the last 5 lines
			for (k, v) in self.LINES.iteritems():
				if the_end[k].startswith(v):
					del the_end[k]
			if the_end != self.NORMAL_ENDING:
				self.log.warning('It seems there was some errors, run log :\n%s\nEND OF RUN LOGS !! '
								'##########################' % log)
			if self.auto_remove:
				cont.remove_container()
			self.get_results() #


use_caching = True
expire_after = 30 * 60 # 30 minutes


# clem 04/05/2016
def initiator(compute_target, *_):
	assert isinstance(compute_target, ComputeTarget)

	def new_if():
		return DockerInterface(compute_target)

	with a_lock:
		if use_caching:
			key = '%s:%s' % ('DockerInterface', compute_target.runnable.short_id)
			cached = ObjectCache.get(key)
			if not cached:
				ObjectCache.add(new_if(), key, expire_after)
			return ObjectCache.get(key)
		return new_if()


# clem 15/03/2016
class DockerIfTest(DockerInterface): # TEST CLASS
	volumes = {
		'test'	: DockerVolume('/home/breeze/data/', '/breeze', 'rw'),
		'final'	: DockerVolume('/home/breeze/data/', '/breeze', 'rw')
	}
	runs = {
		'op'	: DockerRun('fimm/r-light:op', './run.sh', volumes['test']),
		'rtest'	: DockerRun('fimm/r-security-blanket:new', './run.sh', volumes['test']),
		'flat'	: DockerRun('fimm/r-light:flat', '/breeze/run.sh', volumes['test']),
		'final'	: DockerRun('fimm/r-light:latest', '/run.sh', volumes['final']),
	}

	def _attach_event_manager(self, run=None):
		if run and isinstance(run, DockerRun):
			run.event_listener = self._event_manager_wrapper()
		return run

	def _attach_all_event_manager(self):
		for name, run_object in self.runs.iteritems():
			self.runs[name] = self._attach_event_manager(run_object)
		return True

	def _run(self, run=None):
		self._container = self.client.run(run)
		self.log.debug('Got %s' % repr(self.container))
		return self.container

	# clem 06/04/2016
	def custom_run(self, name=''):
		if not is_from_cli():
			assert name in self.runs.keys()
		if not name:
			self_name = function_name()
			print 'Available run :'
			advanced_pretty_print(self.runs)
			print 'usage:\t%s(RUN_NAME)\ni.e.\t%s(\'%s\')' % (self_name, self_name, self.runs.items()[0][0])
		else:
			run = self.runs.get(name, None)
			if not run:
				self.log.debug('No run named "%s", running default one' % name)
			self._run(run)

	# noinspection PyTypeChecker
	def self_test(self): # FIXME Obsolete
		self.test(self.client.get_container, '12')
		self.test(self.client.get_container, '153565748415')
		self.test(self.client.img_run, 'fimm/r-light:op', 'echo "test"')
		self.test(self.client.img_run, 'fimm/r-light:op', '/run.sh')
		self.test(self.client.img_run, 'fimm/r-light:candidate', 'echo "test"')
		self.test(self.client.img_run, 'fimm/r-light:candidate', '/run.sh')
		self.test(self.client.images_list[0].pretty_print)

	def test(self, func, *args): # FIXME Obsolete
		self.log.debug('>>%s%s' % (func.im_func.func_name, args))
		return func(*args)
