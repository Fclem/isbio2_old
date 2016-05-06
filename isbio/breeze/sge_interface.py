from compute_interface_module import * # has os, abc, function_name
from qstat import *
# from utils import password_from_file, is_from_cli, get_file_md5, get_free_port # , new_thread

__version__ = '0.1'
__author__ = 'clem'
__date__ = '06/05/2016'


# clem 06/05/2016
class SGEInterface(ComputeInterface):
	run_id = ''
	client = None
	_compute_target = ComputeTarget

	def __init__(self, compute_target, storage_backend=None):
		super(SGEInterface, self).__init__(compute_target, storage_backend)

	# clem 06/05/2016
	@property
	def _sge_obj(self): # TODO move it all here ( or not )
		return Qstat().job_info(self._runnable.sgeid)

	# clem 06/05/2016
	def status(self): # TODO move it all here
		return self._sge_obj.state

	# clem 16/03/2016
	def _write_log(self, txt):
		if str(txt).strip():
			if self.client:
				print '<sge%s>', txt
			else:
				print '<sge%s ?>', txt

	def send_job(self): # TODO move it all here
		self._runnable.old_sge_run()

	# clem 06/05/2016
	def busy_waiting(self, *args): # TODO move it all here
		return self._runnable.old_sge_waiter(*args)

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
	from breeze.models import ComputeTarget
	assert isinstance(compute_target, ComputeTarget)
	return SGEInterface(compute_target)
