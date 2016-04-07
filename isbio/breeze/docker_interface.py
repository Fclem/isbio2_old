from docker_client import *
from paramiko.pkey import PKey
from utils import password_from_file, new_thread
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
SSH_PORT = 22
SSH_HOST_KEY = 'AAAAB3NzaC1yc2EAAAADAQABAAABAQC/RWm8040HWNOr/B0CfXgr3ZxXZPbwhrpxumvUskut' \
				'/003gNFAEne2TmZGxAZ1Y4knLM81FfIbkxjmMWI+Oz' \
				'+VQ1hA3XEz0yRPJMFBzchOviF2g0MFMjpADc9ovuILrjpDtD7BzAv40rQRZugLo7Pz6M1JJeL7lFe' \
				'+hMFVKlglEafAxiG1IlRLtcJKa5efcvVTBstmXkIHq5N3L1Fb1LQY+GDY/EiZApNlaf++f5UzyyfCCQzcV/J9eWyUxrL2ak1hxnX' \
				'/404tWvrJSuASr4+gja9ZfjOi9oOhNgoHURf9tWGHjzpepb8I2q6d+mXNJhcPDxNT85DXbin7i1VuCM97'
# SSH_HOST_KEY = PKey(data=SSH_HOST_KEY)
SSH_PUB_KEY = 'AAAAB3NzaC1yc2EAAAADAQABAAABAQDG2LHqXF2zDOkWEj7upYHMLJuhFuv3VKh/xz+cqmb0gY7Rb6Y96vCpzf+7PE0uc' \
				'/4XFrtHuZ6XM9JcistOWBbv/OoH3XaXlpeO0zXYUzhshDqlQgspCOMVq4Oc5YX7ZZG1bgti7xljYblPKnziFxwrzWsqsiU5' \
				'+wi7foT0Tb5PGKFyYmWeAxvjJdHh8PE0Bw2EtJFxObtV9830K+etcEOdfV+/1DOz4EWkvl4bL12JUhvJJTgwEeXmV2aX5iZJ7' \
				'+rpjn5TIHNVxxAcb4oI8IeOCq5t72har30S2CAssO1/1nEBB10VDgDQ+SPIXRQs6z3Sp6M8DQHSqWpWDMsXEVnB ' \
				'dbychkov@breeze-dev'
SSH_PUB_KEY = PKey(data=SSH_PUB_KEY)
SSH_USER_NAME = os.getlogin()
SSH_PRIVATE_KEY = os.path.expanduser('~/.ssh/id_rsa')
SSH_REMOTE_BIND = DOCKER_BIND_ADDR
SSH_PASSWORD = password_from_file('~/code/azure_pwd') # FIXME
# FIXME
SSH_CMD = ['ssh', '-CfNnL', '%s:%s:%s' % (DOCKER_REMOTE_PORT, DOCKER_REMOTE_HOST, DOCKER_REMOTE_PORT), SSH_HOST]
SSH_BASH_KILL = 'ps aux | grep "%s"' % ' '.join(SSH_CMD) + " | awk '{ print $2 }' | tr '\\n' ' '"


# clem 06/04/2016
class SSHTunnel:
	server = None

	def __init__(self, host, port, username, remote_bind_address, host_key=None, private_key=None, password=None):
		if private_key and isinstance(private_key, str) and not os.path.exists(private_key):
			# private_key = PKey(data=open(private_key).read())
			private_key = open(private_key).read()
		# print 'pk:', private_key
		print 'passwd:', password

		from sshtunnel import SSHTunnelForwarder

		self.server = SSHTunnelForwarder(
			(host, port),
			ssh_host_key=host_key,
			ssh_username=username,
			ssh_password=password,
			# ssh_private_key=private_key,
			remote_bind_address=remote_bind_address,
			) # local_bind_address=('', remote_bind_address[1])

		self.server.start()

		print(self.server.local_bind_port)
		# work with `SECRET SERVICE` through `server.local_bind_port`.

		print "LOCAL PORT:", self.server.local_bind_port

	def __delete__(self, *_):
		self.server.stop()

	def __exit__(self, *_):
		self.server.stop()


# clem 15/03/2016
class Docker:
	ssh_tunnel = None
	proc = None
	client = None
	_lock = None
	volumes = {
		'test': DockerVolume('/home/breeze/data/', '/breeze', 'rw')
	}
	runs = {
		'op': DockerRun('fimm/r-light:op', './run.sh', volumes['test']),
		'flat': DockerRun('fimm/r-light:flat', '/home/breeze/data/run.sh', volumes['test']),
	}
	container = None
	cat = DockerEventCategories
	MY_DOCKER_HUB = DockerRepo(REPO_LOGIN, REPO_PWD, email=REPO_EMAIL)

	def __init__(self):
		from time import sleep
		# self.client = DockerClient(self.MY_DOCKER_HUB, AZURE_REMOTE_URL)
		# self.ssh_tunnel = SSHTunnel(SSH_HOST, SSH_PORT, SSH_USER_NAME, SSH_REMOTE_BIND, private_key=SSH_PRIVATE_KEY)
		# self.ssh_tunnel = SSHTunnel(SSH_HOST, SSH_PORT, SSH_USER_NAME, SSH_REMOTE_BIND, password=SSH_PASSWORD)
		# self.get_ssh()
		from threading import Lock
		# while not self.ssh_tunnel:
		# self.proc = Process(target=self.get_ssh, args=())
		# self.proc.start()
		# self._lock = Lock()
		print 'Establishing ssh tunnel...'
		self.get_ssh()
		print 'pid:', self.ssh_tunnel.pid
		self.connect()

	# clem 07/04/2016
	def connect(self):
		self.client = DockerClient(DOCKER_DAEMON_URL, self.MY_DOCKER_HUB, False)
		self.attach_all_event_manager()

	# clem 06/04/2016
	# @new_thread
	def get_ssh(self):

		# from forward import connect
		# self.ssh_tunnel = connect(SSH_HOST, SSH_PORT, SSH_USER_NAME, SSH_REMOTE_BIND, password=SSH_PASSWORD)
		# self.ssh_tunnel = connect(SSH_HOST, SSH_PORT, SSH_USER_NAME, SSH_REMOTE_BIND, private_key=SSH_PRIVATE_KEY)
		# from subprocess import call, Popen
		import subprocess
		# import sys
		# dev_null = open('/dev/null', 'w+')
		# Popen(os.path.expanduser("~/code/azure_port_forward.sh"), stdin=dev_null, stdout=sys.stdout, stderr=dev_null)
		# sub_cmd = os.path.expanduser("~/code/azure_port_forward.sh")
		# sub_cmd = 'ssh -CfNnL %s:%s:%s %s' % (DOCKER_REMOTE_PORT, DOCKER_REMOTE_HOST, DOCKER_REMOTE_PORT, SSH_HOST)
		print 'running', SSH_CMD, '...',
		self.ssh_tunnel = subprocess.Popen(SSH_CMD)
		print 'done'
		stat = self.ssh_tunnel.poll()
		while stat is None:
			stat = self.ssh_tunnel.poll()
		print "ssh in background"

	def attach_all_event_manager(self):
		for name, run_object in self.runs.iteritems():
			self.runs[name] = self.attach_event_manager(run_object)

	def attach_event_manager(self, run):
		assert isinstance(run, DockerRun)
		run.event_listener = self.event_manager_wrapper()
		return run

	# clem 16/03/2016
	def write_log(self, txt):
		if self.client:
			# print '<docker>', txt
			self.client.write_log_entry(txt)
		else:
			print '<docker>', txt

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

	def run(self, run):
		if not run:
			run = self.runs['op']
		self.container = self.client.run(run)
		self.write_log('Got %s' % repr(self.container))

	def custom_run(self, name=''):
		if not name:
			print 'Available run :'
			advanced_pretty_print(self.runs)
		else:
			run = self.runs.get(name, None)
			if not run:
				self.write_log('No run named "%s", running default one' % name)
			self.run(run)

	def event_manager_wrapper(self):
		def my_event_manager(event):
			assert isinstance(event, DockerEvent)
			if event.description == DockerEventCategories.DIE:
				# self.write_log('%s died event managed' % event.container.name)
				self.write_log(event.container.logs)
			else:
				# self.write_log(event)
				print '#'
				# self.client._event_log(event)

		return my_event_manager

	# clem 07/04/2016
	@atexit.register # TODO FIXME
	def __cleanup__(self):
		try:
			self.ssh_tunnel.kill()
		except Exception as e:
			print e
			pass

		bash_command = 'ps aux | grep "%s"' % ' '.join(SSH_CMD) + " | awk '{ print $2 }' | tr '\\n' ' '"
		# print "$ %s" % bash_command
		import commands
		try:
			bash_command = 'kill -15 %s' % commands.getstatusoutput(bash_command)[1]
			print "$ %s" % bash_command
			print 'killing: %s' % str(commands.getstatusoutput(bash_command))
		except Exception as e:
			print e

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.__cleanup__()

	def __delete__(self, instance):
		self.__cleanup__()
