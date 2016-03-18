from .docker_client import *

REPO_PWD = '.VaQOap_U"@%+D.YQZ[%\')7^}.#Heh?Dq'
REPO_LOGIN = 'fimm'
REPO_EMAIL = 'clement.fiere@fimm.fi'
AZURE_REMOTE_URL = 'tcp://127.0.0.1:4243'


# clem 15/03/2016
class Docker:
	client = None
	fimm_test_run = None
	container = None
	cat = DockerEventCategories
	MY_DOCKER_HUB = DockerRepo(REPO_LOGIN, REPO_PWD, email=REPO_EMAIL)

	def __init__(self):
		fimm_test_volume = DockerVolume('/home/breeze/data/', '/breeze', 'rw')
		self.fimm_test_run = DockerRun('fimm/r-light:op', './run.sh', fimm_test_volume, self.event_manager_wrapper())
		self.client = DockerClient(self.MY_DOCKER_HUB, AZURE_REMOTE_URL)

	# clem 16/03/2016
	def write_log(self, txt):
		if self.client:
			self.client._log(txt)
		else:
			print txt

	def self_test(self):
		self.test(self.client.get_container, '12')
		self.test(self.client.get_container, '153565748415')
		self.test(self.client.img_run, 'fimm/r-light:op', 'echo "test"')
		self.test(self.client.img_run, 'fimm/r-light:op', '/run.sh')
		self.test(self.client.img_run, 'fimm/r-light:candidate', 'echo "test"')
		self.test(self.client.img_run, 'fimm/r-light:candidate', '/run.sh')
		self.test(self.client.images_list[0].pretty_print)
		self.test(self.client.run_default)

	def test(self, func, *args):
		self.write_log('>>%s%s' % (func.func_name, args))
		return func(*args)

	def run(self):
		self.container = self.client.run(self.fimm_test_run)
		self.write_log('Got %s' % repr(self.container))

	def event_manager_wrapper(self):
		def my_event_manager(event):
			assert isinstance(event, DockerEvent)
			if event.description == DockerEventCategories.DIE:
				# self.write_log('%s died event managed' % event.container.name)
				self.write_log(event.container.logs)
			else:
				self.client._event_log(event)

		return my_event_manager

