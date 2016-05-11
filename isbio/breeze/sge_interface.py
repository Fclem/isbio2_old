from compute_interface_module import * # has os, abc, function_name
from qstat import *
from django.conf import settings

# from utils import password_from_file, is_from_cli, get_file_md5, get_free_port # , new_thread

__version__ = '0.1'
__author__ = 'clem'
__date__ = '06/05/2016'


# clem 06/05/2016
class SGEInterface(ComputeInterface):
	run_id = ''
	client = None
	_compute_target = None
	DEFAULT_SHELL = '/bin/bash'
	DEFAULT_V_MEM = '15G'
	DEFAULT_H_CPU = '999:00:00'
	DEFAULT_H_RT = '999:00:00'

	def __init__(self, compute_target, storage_backend=None):
		super(SGEInterface, self).__init__(compute_target, storage_backend)

		self.apply_config()

	# clem 09/05/2016
	def write_config(self):
		""" Writes a custom config file for SGE to read from for config

		:return: success
		:rtype: bool
		"""
		assert isinstance(self._compute_target, ComputeTarget)
		a_dict = {
			'shell'	: self.DEFAULT_SHELL,
			'h_vmem': self.DEFAULT_V_MEM,
			'h_cpu'	: self.DEFAULT_H_CPU,
			'h_rt'	: self.DEFAULT_H_RT,
			'queue'	: settings.SGE_QUEUE,
		}
		return gen_file_from_template(settings.SGE_REQUEST_TEMPLATE, a_dict, '~/%s' % settings.SGE_REQUEST_FN)

	# clem 09/05/2016
	def apply_config(self):
		""" Applies the proper Django settings, and environement variables for SGE config

		:return: if succeeded
		:rtype: bool
		"""
		if self._compute_target:
			for (k, v) in self._compute_target.target_engine_conf:
				# print (k, v)
				settings.__setattr__(k.upper(), v)
				os.environ[k.upper()] = v
			return self.write_config()
		return False

	# clem 06/05/2016
	@property
	def _sge_obj(self): # TODO move it all here ( or not )
		return Qstat().job_info(self._runnable.sgeid)

	# clem 06/05/2016
	def status(self): # TODO move it all here
		return self._sge_obj.state

	# clem 16/03/2016
	def _write_log(self, txt):
		self.log.debug(txt)

	def send_job(self): # TODO move it all here
		# TODO fully switch to qsub, to get finally totally rid of DRMAA F*****G SHIT
		if self.apply_config:
			self._runnable.old_sge_run()
			return True
		return False

	# clem 06/05/2016
	def busy_waiting(self, *args): # TODO move it all here
		return self._runnable.old_sge_waiter(*args)

	# clem 09/05/2016
	def job_is_done(self):
		self.log.debug('done')

	# clem 06/05/2016
	def abort(self):
		if self._runnable.breeze_stat != JobStat.DONE:
			self._runnable.breeze_stat = JobStat.ABORT
			if not self._runnable.is_sgeid_empty:
				self._sge_obj.abort()
			else:
				self._runnable.breeze_stat = JobStat.ABORTED
			return True
		return False

	# clem 21/04/2016
	def get_results(self, output_filename=None):
		pass


# clem 04/05/2016
def initiator(compute_target, *args):
	assert isinstance(compute_target, ComputeTarget)
	return SGEInterface(compute_target)
