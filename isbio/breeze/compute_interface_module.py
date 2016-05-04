from utils import function_name
import os
import abc

__version__ = '0.1'
__author__ = 'clem'
__date__ = '04/05/2016'


# clem 04/05/2016
class ComputeInterface:
	__metaclass__ = abc.ABCMeta
	_not = "Class %s doesn't implement %s()"
	storage_backend = None
	_missing_exception = None

	def __init__(self, storage_backend): # TODO call from child-class, as the first instruction
		assert hasattr(storage_backend, 'MissingResException')
		self.storage_backend = storage_backend
		self._missing_exception = self.storage_backend.MissingResException

	@abc.abstractmethod
	def _write_log(self, txt):
		raise NotImplementedError(self._not % (self.__class__.__name__, function_name()))

	@abc.abstractmethod
	def send_job(self, job_folder=None, output_filename=None):
		raise NotImplementedError(self._not % (self.__class__.__name__, function_name()))

	@abc.abstractmethod
	def get_results(self, output_filename=None):
		raise NotImplementedError(self._not % (self.__class__.__name__, function_name()))

	def _get_storage(self, container=None):
		return self.storage_backend.back_end_initiator(container)

	# clem 20/04/2016
	def make_tarfile(self, output_filename, source_dir):
		import tarfile
		with tarfile.open(output_filename, "w:bz2") as tar:
			tar.add(source_dir, arcname=os.path.basename(source_dir))
		return True


# clem 04/05/2016
def initiator(storage_backend, *args): # TODO override in implementation
	return ComputeInterface(storage_backend, *args)
