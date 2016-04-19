#!/usr/bin/python
from azure.storage.blob import BlockBlobService
from azure.common import AzureMissingResourceHttpError
import os


# clem 06/04/2016
def password_from_file(path):
	from os.path import exists, expanduser
	if not exists(path):
		temp = expanduser(path)
		if exists(temp):
			path = temp
		else:
			return False
	return open(path).read().replace('\n', '')

AZURE_ACCOUNT = 'breezedata'
azure_file_name = 'azure_pwd_%s' % AZURE_ACCOUNT
AZURE_KEY = password_from_file('~/code/%s' % azure_file_name) or password_from_file('./%s' % azure_file_name)
AZURE_CONTAINERS_NAME = ['dockertest']
AZURE_BLOB_BASE_URL = 'https://%s.blob.core.windows.net/%s/'
__DEV__ = True
RESULT_FILE = 'job.tar.xz'
JOB_FILE = 'in.tar.xz'


# clem 14/04/2016
class AzureStorage:
	_blob_service = None
	container = None
	ACCOUNT_LOGIN = ''
	ACCOUNT_KEY = ''

	def __init__(self, login, key, container):
		assert isinstance(login, basestring)
		assert isinstance(key, basestring)
		assert isinstance(container, basestring)
		self.ACCOUNT_LOGIN = login
		self.ACCOUNT_KEY = key
		self.container = container

	@property
	def blob_service(self):
		"""
		:rtype: BlobService
		"""
		if not self._blob_service:
			self._blob_service = BlockBlobService(account_name=self.ACCOUNT_LOGIN, account_key=self.ACCOUNT_KEY)
			if __DEV__:
				for each in AZURE_CONTAINERS_NAME:
					self._list_blobs(each)
		return self._blob_service

	def container_url(self):
		return self._container_url(self.container)

	def _container_url(self, container):
		return AZURE_BLOB_BASE_URL % (self.ACCOUNT_LOGIN, container)

	def list_blobs(self):
		return self._list_blobs(self.container)

	def _list_blobs(self, container):
		generator = self.blob_service.list_blobs(container)
		print 'Azure container %s :' % container
		for blob in generator:
			print blob.name

	def blob_info(self, blob_name):
		return self._blob_info(self.container, blob_name)

	def _blob_info(self, cont_name, blob_name):
		return self.blob_service.get_blob_properties(cont_name, blob_name)

	# clem 15/04/2016
	def upload(self, blob_name, file_path):
		if os.path.exists(file_path):
			cont_name = AZURE_CONTAINERS_NAME[0]
			self.blob_service.create_container(cont_name)
			print "create_blob_from_path(%s, %s, %s)" % (cont_name, blob_name, file_path)
			self.blob_service.create_blob_from_path(cont_name, blob_name, file_path)
		else:
			raise NotImplementedError('File %s not found in %s !' % (file_path, os.path.curdir))
		return self.blob_service.get_blob_properties(cont_name, blob_name)

	# clem 15/04/2016
	def download(self, blob_name, file_path):
		try:
			print "get_blob_to_path(%s, %s, %s)" % (self.container, blob_name, file_path)
			self.blob_service.get_blob_to_path(self.container, blob_name, file_path)
		except AzureMissingResourceHttpError as e: # FIXME HAS NO EFFECT
			raise e

		return True


if __name__ == '__main__':
	import sys
	import os
	DOCK_HOME = os.environ.get('DOCK_HOME', '.')

	print 'Argument List:', str(sys.argv)

	assert len(sys.argv) >= 3

	action = str(sys.argv[1])
	obj_id = str(sys.argv[2])

	print action, obj_id

	assert isinstance(action, basestring) and action in ('load', 'save')
	assert isinstance(obj_id, basestring) and len(obj_id) >= 12

	__DEV__ = False
	try:
		storage = AzureStorage(AZURE_ACCOUNT, AZURE_KEY, AZURE_CONTAINERS_NAME[0])
		if action == 'load':
			path = DOCK_HOME + '/' + JOB_FILE
			storage.download(obj_id, path)
		elif action == 'save':
			path = DOCK_HOME + '/' + RESULT_FILE
			storage.upload(obj_id, path)
	except Exception as e:
		raise e
