from utilities import *
from breeze.models import JobStat, Runnable, ComputeTarget
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

	# clem 17/05/2016
	@property
	def js(self):
		return JobStat

	# clem 11/05/2016
	@property
	def log(self):
		log_obj = LoggerAdapter(self._compute_target.runnable.log_custom(1), dict())
		bridge = log_obj.process
		log_obj.process = lambda msg, kwargs: bridge('<%s> %s' % (self._compute_target, str(msg)), kwargs)
		return log_obj

	# clem 14/05/2016
	@property
	def target_obj(self):
		"""

		:return:
		:rtype: ComputeTarget
		"""
		return self._compute_target

	# clem 17/05/2016
	@property # writing shortcut
	def engine_obj(self):
		if self.target_obj and self.target_obj.engine_obj:
			return self.target_obj.engine_obj
		return None

	# clem 17/05/2016
	@property  # writing shortcut
	def execut_obj(self):
		if self.target_obj and self.target_obj.exec_obj:
			return self.target_obj.exec_obj
		return None

	# clem 23/05/2016
	@abc.abstractmethod
	def assemble_job(self):
		""" This function should implement whatever assembling of the source / files / dependencies are necessary
		for the job to be ready for submission and run

		It is advised to return a bool indicating success or failure
		"""
		raise NotImplementedError(self._not % (self.__class__.__name__, this_function_name()))

	@abc.abstractmethod
	def send_job(self):
		""" This function should implement the submission and triggering of the job's run

		It is advised to return a bool indicating success or failure
		"""
		raise NotImplementedError(self._not % (self.__class__.__name__, this_function_name()))

	@abc.abstractmethod
	def get_results(self):
		""" This function should implement the transfer and extraction of the results files from the storage backend
		to the local report folder in Breeze tree structure

		It is advised to return a bool indicating success or failure
		"""
		raise NotImplementedError(self._not % (self.__class__.__name__, this_function_name()))

	# clem 06/05/2016
	@abc.abstractmethod
	def abort(self):
		""" This function should implement the abortion of the job

		It is advised to return a bool indicating success or failure
		"""
		raise NotImplementedError(self._not % (self.__class__.__name__, this_function_name()))

	# clem 06/05/2016
	@abc.abstractmethod
	def status(self):
		""" This function should implement a status interface for the job.

		:rtype: str
		"""
		raise NotImplementedError(self._not % (self.__class__.__name__, this_function_name()))

	# clem 06/05/2016
	@abc.abstractmethod
	def busy_waiting(self, *args):
		""" This function should implement an active busy waiting system, that waits until job competition.

		This method will be run on another Thread, so you do not need to worry about blocking execution.
		However it is advised to use time.sleep() with increments of 1 second, to reduce CPU usage of the server.
		Also you are not required to use busy waiting, and can simply return True early on, this will not affect the
		job status, and implement instead a event driven status system.

		It is advised to return a bool indicating success or failure
		"""
		raise NotImplementedError(self._not % (self.__class__.__name__, this_function_name()))

	# clem 06/05/2016
	@abc.abstractmethod
	def job_is_done(self):
		""" This function should implement the necessary action to take upon job completion.

		It will not be called from Breeze, it is for you to trigger it.
		This function should also access the final status of the job, and call the appropriated method from runnable
		Runnable.manage_run_*()

		It is advised to return a bool indicating success or failure
		"""
		raise NotImplementedError(self._not % (self.__class__.__name__, this_function_name()))

	def _get_storage(self, container=None):
		return self.storage_backend.back_end_initiator(container)

	# clem 20/04/2016
	def make_tarfile(self, output_filename, source_dir):
		""" makes a tar.bz2 archive from source_dir, and stores it in output_filename

		:param output_filename: the name/path of the resulting archive
		:type output_filename: basestring
		:param source_dir: the path of the source folder
		:type source_dir: basestring
		:return: if success
		:rtype: bool
		"""
		try:
			return make_tarfile(output_filename, source_dir)
		except Exception as e:
			self.log.exception('Error creating %s : %s' % (output_filename, str(e)))
		return False

	# clem 23/05/2016
	def extract_tarfile(self, input_filename, destination_dir):
		""" extract an tar.* to a destination folder

		:param input_filename: the name/path of the source archive
		:type input_filename: basestring
		:param destination_dir: the path of the destination folder
		:type destination_dir: basestring
		:return: if success
		:rtype: bool
		"""
		try:
			return extract_tarfile(input_filename, destination_dir)
		except Exception as e:
			self.log.exception('Error extracting %s : %s' % (input_filename, str(e)))
		return False

	# clem 16/05/2016
	def __repr__(self):
		return '<%s@%s>' % (self.__class__.__name__, hex(id(self)))


# clem 04/05/2016 EXAMPLE function
# TODO override in implementation
def initiator(compute_target, *_):
	# It is probably a good idea to cache the object you are going to create here.
	# Also a good idea is to use module-wide Thread.Lock() to avoid cache-miss due to concurrency
	assert isinstance(compute_target, ComputeTarget)
	# Replace compute_target.storage_module with another module.
	# Note : compute_target.storage_module is also the default
	return ComputeInterface(compute_target, compute_target.storage_module)
