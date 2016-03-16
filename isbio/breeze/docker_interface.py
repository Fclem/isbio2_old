from .docker_client import *

REPO_PWD = '.VaQOap_U"@%+D.YQZ[%\')7^}.#Heh?Dq'
REPO_LOGIN = 'fimm'
REPO_EMAIL = 'clement.fiere@fimm.fi'
AZURE_REMOTE_URL = 'tcp://127.0.0.1:4243'


# clem 15/03/2016
class Docker:
	client = None
	cat = DockerEventCategories
	MY_DOCKER_HUB = DockerRepo(REPO_LOGIN, REPO_PWD, email=REPO_EMAIL)

	def __init__(self):
		fimm_test_volume = DockerVolume('/home/breeze/data/', '/breeze', 'rw')
		fimm_test_run = DockerRun('fimm/r-light:op', './run.sh', fimm_test_volume, self.event_manager_wrapper())
		self.client = DockerClient(self.MY_DOCKER_HUB, AZURE_REMOTE_URL, fimm_test_run)

	def run(self):
		return self.client.run_default()

	def event_manager_wrapper(self):
		def my_event_manager(event):
			assert isinstance(event, DockerEvent)
			self.client.event_log(event)
			if event.description == DockerEventCategories.DIE:
				print 'Container died'
				print event.container

		return my_event_manager

