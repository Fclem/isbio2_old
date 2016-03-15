from .docker_client import *


class Docker:
	client = None

	def __init__(self):
		fimm_docker_hub = DockerRepo('fimm', PWD, email='clement.fiere@fimm.fi')
		fimm_test_volume = DockerVolume('/home/breeze/data/', '/breeze', 'rw')
		fimm_test_run = DockerRun('fimm/r-light:op', './run.sh', fimm_test_volume, self.event_manager_wrapper())
		self.client = DockerClient(fimm_docker_hub, AZURE_REMOTE_URL, fimm_test_run)

	# clem 15/03/2016
	def event_manager_wrapper(self):
		# clem 15/03/2016
		def my_event_manager(event):
			assert isinstance(event, DockerEvent)
			self.client.event_log(event)
			# print 'manager :', event
		return my_event_manager

