#!/usr/bin/python
from azure.storage.blob import BlockBlobService
from azure.common import AzureMissingResourceHttpError
import os
import sys


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


# general config
__DEV__ = True
AZURE_ACCOUNT = 'breezedata'
AZURE_PWD_FILE = 'azure_pwd_%s' % AZURE_ACCOUNT
AZURE_KEY = password_from_file('~/code/%s' % AZURE_PWD_FILE) or password_from_file('./%s' % AZURE_PWD_FILE)
AZURE_CONTAINERS_NAME = ['dockertest', 'mycontainer']
AZURE_DEFAULT_CONTAINER = AZURE_CONTAINERS_NAME[0]
AZURE_SELF_UPDATE_CONTAINER = AZURE_CONTAINERS_NAME[1]
AZURE_BLOB_BASE_URL = 'https://%s.blob.core.windows.net/%s/'
# command line config
OUT_FILE = 'out.tar.xz'
IN_FILE = 'in.tar.xz'
ENV_DOCK_HOME = ('DOCK_HOME', '/breeze')
ENV_HOME = ('HOME', '/root')
ENV_JOB_ID = ('JOB_ID', '')
ENV_HOSTNAME = ('HOSTNAME', '')
# command line CONSTs
DOCK_HOME = os.environ.get(*ENV_DOCK_HOME)
HOME = os.environ.get(*ENV_HOME)
ACTION_LIST = ('load', 'save', 'upload', 'upgrade') # DO NOT change item order


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
		""" the Azure storage interface to self.ACCOUNT_LOGIN\n
		if not connected yet, establish the link and save it

		:return: Azure storage interface
		:rtype: BlockBlobService
		:raise: Exception
		"""
		if not self._blob_service:
			self._blob_service = BlockBlobService(account_name=self.ACCOUNT_LOGIN, account_key=self.ACCOUNT_KEY)
		return self._blob_service

	def container_url(self):
		""" The public url to self.container\n
		(the container might not be public, thus this url would be useless)

		:return: the url to access self.container
		:rtype: str
		"""
		return self._container_url(self.container)

	# clem 19/04/2016
	def _container_url(self, container):
		return AZURE_BLOB_BASE_URL % (self.ACCOUNT_LOGIN, container)

	# clem 20/04/2016
	def list_containers(self, do_print=False):
		""" The list of container in the current Azure storage account

		:param do_print: print the resulting list ? (default to False)
		:type do_print: bool
		:return: generator of the list of containers in self.ACCOUNT_LOGIN storage account
		:rtype: azure.storage.models.ListGenerator
		"""
		generator = self.blob_service.list_containers()
		if do_print:
			print 'Azure account \'%s\' containers list :' % self.ACCOUNT_LOGIN
			for container in generator:
				print container.name
		return generator

	def list_blobs(self, do_print=False):
		""" The list of blob in self.container

		:param do_print: print the resulting list ? (default to False)
		:type do_print: bool
		:return: generator of the list of blob in self.container
		:rtype: azure.storage.models.ListGenerator
		"""
		return self._list_blobs(self.container, do_print)

	# clem 19/04/2016
	def _list_blobs(self, container, do_print=False):
		"""
		:param container: name of the container to list content from
		:type container: str
		:param do_print: print the resulting list ? (default to False)
		:type do_print: bool
		:rtype: azure.storage.models.ListGenerator
		"""
		generator = self.blob_service.list_blobs(container)
		if do_print:
			print 'Azure container \'%s\' content :' % container
			for blob in generator:
				print blob.name
		return generator

	def blob_info(self, blob_name):
		"""
		:param blob_name: a blob existing in self.container to get info about
		:type blob_name: str
		:return: info object of specified blob
		:rtype: Blob
		"""
		return self._blob_info(self.container, blob_name)

	# clem 19/04/2016
	def _blob_info(self, cont_name, blob_name):
		return self.blob_service.get_blob_properties(cont_name, blob_name)

	# clem 20/04/2016
	def upload_self(self, container=None):
		""" Upload this script to azure blob storage

		:param container: target container (default to AZURE_SELF_UPDATE_CONTAINER)
		:type container: str|None
		:return: Info on the created blob as a Blob object
		:rtype: Blob
		"""
		if not container:
			container = AZURE_SELF_UPDATE_CONTAINER
		return self.upload(os.path.basename(__file__), __file__, container)

	# clem 20/04/2016
	def update_self(self, container=None):
		""" Download a possibly updated version of this script from azure blob storage
		Will only work from command line.

		:param container: target container (default to AZURE_SELF_UPDATE_CONTAINER)
		:type container: str|None
		:return: success ?
		:rtype: bool
		:raise: AssertionError
		"""
		assert __name__ == '__main__' # restrict access
		if not container:
			container = AZURE_SELF_UPDATE_CONTAINER
		return self.download(os.path.basename(__file__), __file__, container)

	# clem 15/04/2016
	def upload(self, blob_name, file_path, container=None, verbose=True):
		""" Upload wrapper (around BlockBlobService().blob_service.get_blob_properties) for Azure block blob storage :\n
		upload a local file to the default container or a specified one on Azure storage
		if the container does not exists, it will be created using BlockBlobService().blob_service.create_container

		:param blob_name: Name of the blob as to be stored in Azure storage
		:type blob_name: str
		:param file_path: Path of the local file to upload
		:type file_path: str
		:param container: Name of the container to use to store the blob (default to self.container)
		:type container: str or None
		:param verbose: Print actions (default to True)
		:type verbose: bool or None
		:return: object corresponding to the created blob
		:rtype: Blob
		:raise: IOError or FileNotFoundError
		"""
		if not container:
			container = self.container
		if os.path.exists(file_path):
			if not self.blob_service.exists(container):
				# if container does not exist yet, we create it
				if verbose:
					print "create_container(\'%s\')" % container
				self.blob_service.create_container(container)
			if verbose:
				print "create_blob_from_path(\'%s\', \'%s\', \'%s\')" % (container, blob_name, file_path)
			self.blob_service.create_blob_from_path(container, blob_name, file_path)
		else:
			err = getattr(__builtins__, 'FileNotFoundError', IOError)
			raise err('File \'%s\' not found in \'%s\' !' % (os.path.basename(file_path),
				os.path.dirname(file_path)))
		return self.blob_service.get_blob_properties(container, blob_name)

	# clem 15/04/2016
	def download(self, blob_name, file_path, container=None, verbose=True):
		""" Download wrapper (around BlockBlobService().blob_service.get_blob_to_path) for Azure block blob storage :\n
		download a blob from the default container (or a specified one) from azure storage and save it as a local file
		if the container does not exists, the operation will fail

		:param blob_name: Name of the blob to retrieve from Azure storage
		:type blob_name: str
		:param file_path: Path of the local file to save the downloaded blob
		:type file_path: str
		:param container: Name of the container to use to store the blob (default to self.container)
		:type container: str or None
		:param verbose: Print actions (default to True)
		:type verbose: bool or None
		:return: success?
		:rtype: bool
		:raise: AzureMissingResourceHttpError
		"""
		if not container:
			container = self.container
		if self.blob_service.exists(container):
			try:
				if verbose:
					print "get_blob_to_path(\'%s\', \'%s\', \'%s\')" % (container, blob_name, file_path)
				self.blob_service.get_blob_to_path(container, blob_name, file_path)
			except AzureMissingResourceHttpError as e: # FIXME HAS NO EFFECT
				raise e
			return True
		return False


# clem on 21/08/2015
def get_md5(content):
	""" compute the md5 checksum of the content argument

	:param content: the content to be hashed
	:type content: list or str
	:return: md5 checksum of the provided content
	:rtype: str
	"""
	import hashlib
	m = hashlib.md5()
	if type(content) == list:
		for eachLine in content:
			m.update(eachLine)
	else:
		m.update(content)
	return m.hexdigest()


# clem on 21/08/2015
def get_file_md5(file_path):
	""" compute the md5 checksum of a file

	:param file_path: path of the local file to hash
	:type file_path: str
	:return: md5 checksum of file
	:rtype: str
	"""
	content = list()
	try:
		fd = open(file_path, "rb")
		content = fd.readlines()
		fd.close()
	except IOError:
		return ''

	return get_md5(content)


if __name__ == '__main__':
	assert len(sys.argv) >= 2

	action = str(sys.argv[1])
	obj_id = '' if len(sys.argv) <= 2 else str(sys.argv[2])
	file_n = '' if len(sys.argv) <= 3 else str(sys.argv[3])

	print 'args :', sys.argv

	assert isinstance(action, basestring) and action in ACTION_LIST

	__DEV__ = False
	try:
		storage = AzureStorage(AZURE_ACCOUNT, AZURE_KEY, AZURE_CONTAINERS_NAME[0])
		if action == ACTION_LIST[0]: # download the job archive from azure blob storage
			if not obj_id:
				obj_id = os.environ.get(*ENV_JOB_ID)
			path = HOME + '/' + IN_FILE
			storage.download(obj_id, path)
		elif action == ACTION_LIST[1]: # uploads the job resulting archive to azure blob storage
			path = HOME + '/' + OUT_FILE
			if not obj_id:
				obj_id = os.environ.get(ENV_JOB_ID[0], os.environ.get(ENV_HOSTNAME[0], get_file_md5(path)))
			storage.upload(obj_id, path)
		elif action == ACTION_LIST[2]: # uploads an arbitrary file to azure blob storage
			assert file_n and len(file_n) > 3
			assert obj_id and len(obj_id) > 4
			path = HOME + '/' + file_n
			storage.upload(obj_id, path)
		elif action == ACTION_LIST[3]: # self update
			print storage.update_self()
	except Exception as e:
		raise e
