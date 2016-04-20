from docker_client import *
from utils import password_from_file, function_name, is_from_cli # , new_thread
import os
import atexit

REPO_PWD = password_from_file('~/code/docker_repo') # FIXME
REPO_LOGIN = 'fimm'
REPO_EMAIL = 'clement.fiere@fimm.fi'
DOCKER_REMOTE_HOST = '127.0.0.1'
DOCKER_REMOTE_PORT = 4243
DOCKER_BIND_ADDR = (DOCKER_REMOTE_HOST, DOCKER_REMOTE_PORT)
DOCKER_DAEMON_URL = 'tcp://%s:%s' % DOCKER_BIND_ADDR
SSH_HOST = 'breeze.northeurope.cloudapp.azure.com'
# FIXME
SSH_CMD = ['ssh', '-CfNnL', '%s:%s:%s' % (DOCKER_REMOTE_PORT, DOCKER_REMOTE_HOST, DOCKER_REMOTE_PORT), SSH_HOST]
SSH_BASH_KILL = 'ps aux | grep "%s"' % ' '.join(SSH_CMD) + " | awk '{ print $2 }' | tr '\\n' ' '"

NORMAL_ENDING = ['Running R script... done !', 'Success !', 'done']


# clem 15/03/2016
class Docker:
	ssh_tunnel = None
	auto_remove = True
	_storage = None
	proc = None
	client = None
	_lock = None
	volumes = {
		'test': DockerVolume('/home/breeze/data/', '/breeze', 'rw'),
		'final': DockerVolume('/home/breeze/data/', '/breeze', 'rw')
	}
	runs = {
		'op': DockerRun('fimm/r-light:op', './run.sh', volumes['test']),
		'rtest': DockerRun('fimm/r-security-blanket:new', './run.sh', volumes['test']),
		'flat': DockerRun('fimm/r-light:flat', '/breeze/run.sh', volumes['test']),
		'final': DockerRun('fimm/r-light:latest', '/run.sh', volumes['final']),
	}
	container = None
	cat = DockerEventCategories
	MY_DOCKER_HUB = DockerRepo(REPO_LOGIN, REPO_PWD, email=REPO_EMAIL)

	def __init__(self):
		if not self.test_connection(DOCKER_BIND_ADDR):
			self.write_log('No connection to daemon, trying ssh tunnel')
			self.get_ssh()
			if self.test_connection(DOCKER_BIND_ADDR):
				self.connect()
		else:
			self.connect()

	# clem 08/09/2016
	def test_connection(self, target):
		import socket
		s = socket.socket() # socket.AF_INET, socket.SOCK_STREAM
		try:
			s.settimeout(2)
			self.write_log('testing connection to %s Tout: %s sec' % (str(target), s.gettimeout()))
			s.connect(target)
			self.write_log('success')
			return True
		except socket.timeout:
			self.write_log('connect %s: Time-out' % str(target))
		except Exception as e:
			self.write_log('connect %s' % str((type(e), e)))
		finally:
			s.close()

		return False

	# clem 07/04/2016
	def connect(self):
		self.client = DockerClient(DOCKER_DAEMON_URL, self.MY_DOCKER_HUB, False)
		self.attach_all_event_manager()

	# clem 06/04/2016 # FIXME change print to log
	def get_ssh(self):
		import subprocess
		print 'Establishing ssh tunnel, running', SSH_CMD, '...',
		self.ssh_tunnel = subprocess.Popen(SSH_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
		print 'done,',
		stat = self.ssh_tunnel.poll()
		while stat is None:
			stat = self.ssh_tunnel.poll()
		print 'bg PID :', self.ssh_tunnel.pid

	def attach_all_event_manager(self):
		for name, run_object in self.runs.iteritems():
			self.runs[name] = self.attach_event_manager(run_object)

	def attach_event_manager(self, run):
		assert isinstance(run, DockerRun)
		run.event_listener = self.event_manager_wrapper()
		return run

	# clem 16/03/2016
	def write_log(self, txt):
		if str(txt).strip():
			if self.client:
				print '<docker>', txt
				# self.client.write_log_entry(txt)
			else:
				print '<docker?>', txt

	def self_test(self):
		self.test(self.client.get_container, '12')
		self.test(self.client.get_container, '153565748415')
		self.test(self.client.img_run, 'fimm/r-light:op', 'echo "test"')
		self.test(self.client.img_run, 'fimm/r-light:op', '/run.sh')
		self.test(self.client.img_run, 'fimm/r-light:candidate', 'echo "test"')
		self.test(self.client.img_run, 'fimm/r-light:candidate', '/run.sh')
		self.test(self.client.images_list[0].pretty_print)

	def test(self, func, *args):
		self.write_log('>>%s%s' % (func.im_func.func_name, args))
		return func(*args)

	def run(self, run=None):
		if not run:
			run = self.runs['op']
		self.container = self.client.run(run)
		self.write_log('Got %s' % repr(self.container))

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
				self.write_log('No run named "%s", running default one' % name)
			self.run(run)

	# clem 08/04/2016
	def call_test(self):
		return self.custom_run()

	def event_manager_wrapper(self):
		def my_event_manager(event):
			assert isinstance(event, DockerEvent)
			# self.write_log(event)
			if event.description == DockerEventCategories.DIE:
				cont = event.container
				log = str(cont.logs)
				assert isinstance(cont, DockerContainer)
				# self.write_log('%s died event managed' % event.container.name)
				self.write_log('Died code %s. Total execution time : %s' % (cont.status.ExitCode,
					cont.delta_display))
				if cont.status.ExitCode > 0:
					self.write_log('Failure (container won\t be deleted) ! Run log :\n%s' % log)
				else:
					self.write_log('Success !')
					the_end = log.split('\n')[-5:-1] # copy the last 4 lines
					arch = the_end[-2] # copy the line about the archive
					del the_end[-2] # remove the second last which should be about the archive
					if the_end != NORMAL_ENDING:
						self.write_log('It seems there was some errors, run log :\n%s' % log)
					if self.auto_remove:
						cont.remove_container()
			elif event.description == DockerEventCategories.START:
				self.write_log('%s started' % event.container.name)

		return my_event_manager

	# clem 07/04/2016
	@atexit.register # TODO FIXME
	def __cleanup__(self):
		try:
			self.ssh_tunnel.terminate()
			self.ssh_tunnel.kill()
		except Exception as e:
			print e
			pass

		import commands
		import signal

		pid_list = commands.getstatusoutput(SSH_BASH_KILL)[1].strip().split(' ')
		for each in pid_list:
			try:
				print 'pid', each, os.kill(int(each), signal.SIGTERM)
			except Exception as e:
				print e

	def __exit__(self, *_):
		self.__cleanup__()

	def __delete__(self, *_):
		self.__cleanup__()

	# clem 20/04/2016
	@property
	def storage(self):
		if not self._storage:
			from azure_storage import AzureStorage, AZURE_ACCOUNT, AZURE_KEY, AZURE_CONTAINERS_NAME
			self._storage = AzureStorage(AZURE_ACCOUNT, AZURE_KEY, AZURE_CONTAINERS_NAME[0])
		return self._storage

	def azure_test(self):
		from azure_storage import IN_FILE
		DOCK_HOME = os.environ.get('DOCK_HOME', '/homes/breeze/code/isbio/breeze')

		path = DOCK_HOME + '/' + IN_FILE
		return self.storage.upload(IN_FILE, path)
