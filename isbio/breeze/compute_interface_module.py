from utils import function_name, gen_file_from_template, get_logger, logging
from breeze.models import JobStat, Runnable, ComputeTarget
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
	_compute_target = None
	_runnable = None

	def __init__(self, compute_target, storage_backend=None): # TODO call from child-class, as the first instruction
		assert isinstance(compute_target, ComputeTarget)
		self._compute_target = compute_target
		self._runnable = self._compute_target.runnable
		assert isinstance(self._runnable, Runnable)

		self.storage_backend = storage_backend
		if not self.storage_backend:
			self.storage_backend = self._compute_target.storage_module
		assert hasattr(self.storage_backend, 'MissingResException')

		self._missing_exception = self.storage_backend.MissingResException

	# clem 11/05/2016
	@property
	def log(self):
		log_obj = logging.LoggerAdapter(self._compute_target.runnable.log_custom(1), dict())
		bridge = log_obj.process
		log_obj.process = lambda msg, kwargs: bridge('<%s> %s' % (self._compute_target, str(msg)), kwargs)
		return log_obj

	@abc.abstractmethod
	def send_job(self):
		raise NotImplementedError(self._not % (self.__class__.__name__, function_name()))

	@abc.abstractmethod
	def get_results(self, output_filename=None):
		raise NotImplementedError(self._not % (self.__class__.__name__, function_name()))

	# clem 06/05/2016
	@abc.abstractmethod
	def abort(self):
		raise NotImplementedError(self._not % (self.__class__.__name__, function_name()))

	# clem 06/05/2016
	@abc.abstractmethod
	def status(self):
		raise NotImplementedError(self._not % (self.__class__.__name__, function_name()))

	# clem 06/05/2016
	@abc.abstractmethod
	def busy_waiting(self, *args):
		raise NotImplementedError(self._not % (self.__class__.__name__, function_name()))

	# clem 06/05/2016
	@abc.abstractmethod
	def job_is_done(self):
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
def initiator(compute_target, *args): # TODO override in implementation
	assert isinstance(compute_target, ComputeTarget)
	# Replace compute_target.storage_module with another module.
	# Note : compute_target.storage_module is also the default
	return ComputeInterface(compute_target, compute_target.storage_module)
