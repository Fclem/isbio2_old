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

	def __init__(self, storage_backend):
		super(SGEInterface, self).__init__(storage_backend)

	# clem 16/03/2016
	def _write_log(self, txt):
		if str(txt).strip():
			if self.client:
				print '<sge%s>', txt
			else:
				print '<sge%s ?>', txt

	def send_job(self, job_folder=None, output_filename=None):
		pass

	# clem 21/04/2016
	def get_results(self, output_filename=None):
		pass


# clem 04/05/2016
def initiator(storage_module, config, *args):
	from breeze.models import ComputeTarget
	assert isinstance(config, ComputeTarget)
	return SGEInterface(storage_module)
