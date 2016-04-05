from docker_client import *

REPO_PWD = '.VaQOap_U"@%+D.YQZ[%\')7^}.#Heh?Dq'
REPO_LOGIN = 'fimm'
REPO_EMAIL = 'clement.fiere@fimm.fi'
AZURE_REMOTE_URL = 'tcp://127.0.0.1:4243'


# clem 15/03/2016
class Docker:
	client = None
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
		# self.client = DockerClient(self.MY_DOCKER_HUB, AZURE_REMOTE_URL)
		self.client = DockerClient(AZURE_REMOTE_URL, self.MY_DOCKER_HUB, False)
		self.attach_all_event_manager()

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

