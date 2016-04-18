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

AZURE_ACCOUNT = 'breeze5496'
AZURE_KEY = password_from_file('~/code/azure_blob_pwd') or password_from_file('./azure_blob_pwd')
AZURE_CONTAINERS_NAME = ['dockertest', 'vhds']
AZURE_BLOB_BASE_URL = 'https://%s.blob.core.windows.net/%s/'
__DEV__ = True
RESULT_FILE = 'job.tar.xz'
JOB_FILE = 'in.tar.xz'


# clem 14/04/2016
class AzureStorage:
	_blob_service = None
	ACCOUNT_LOGIN = ''
	ACCOUNT_KEY = ''

	def __init__(self, login, key):
		assert isinstance(login, basestring)
		assert isinstance(key, basestring)
		self.ACCOUNT_LOGIN = login
		self.ACCOUNT_KEY = key

	@property
	def blob_service(self):
		"""
		:rtype: BlobService
		"""
		if not self._blob_service:
			self._blob_service = BlockBlobService(account_name=self.ACCOUNT_LOGIN, account_key=self.ACCOUNT_KEY)
			if __DEV__:
				for each in AZURE_CONTAINERS_NAME:
					self.list_blobs(each)
		return self._blob_service

	def container_url(self, container):
		return AZURE_BLOB_BASE_URL % (self.ACCOUNT_LOGIN, container)

	def list_blobs(self, blob_name):
		generator = self.blob_service.list_blobs(blob_name)
		print 'Azure container %s :' % blob_name
		for blob in generator:
			print blob.name

	# clem 15/04/2016
	def upload(self, blob_name, file_path):
		if os.path.exists(file_path):
			cont_name = 'mycontainer'
			self.blob_service.create_container(cont_name)
			print "create_blob_from_path(%s, %s, %s)" % (cont_name, blob_name, file_path)
			# self.blob_service.put_block_blob_from_path(cont_name, blob_name, file_path)
			self.blob_service.create_blob_from_path(cont_name, blob_name, file_path)
		else:
			raise NotImplementedError('File %s not found in %s !' % (file_path, os.path.curdir))
		return True

	# clem 15/04/2016
	def download(self, blob_name, file_path):
		try:
			print "get_blob_to_path(%s, %s, %s)" % (AZURE_CONTAINERS_NAME[0], blob_name, file_path)
			self.blob_service.get_blob_to_path(AZURE_CONTAINERS_NAME[0], blob_name, file_path)
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
		storage = AzureStorage(AZURE_ACCOUNT, AZURE_KEY)
		if action == 'load':
			path = DOCK_HOME + '/' + JOB_FILE
			storage.download(obj_id, path)
		elif action == 'save':
			path = DOCK_HOME + '/' + RESULT_FILE
			storage.upload(obj_id, path)
	except Exception as e:
		raise e
