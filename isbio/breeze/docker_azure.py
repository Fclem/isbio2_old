from docker_interface import *
import azure_storage

__version__ = '0.1'
__author__ = 'clem'
__date__ = '29/04/2016'


# clem 29/04/2016
class DockerAzure(DockerInterface):
	def __init__(self):
		super(DockerAzure, self).__init__(azure_storage, 'breeze.northeurope.cloudapp.azure.com', 'az')
