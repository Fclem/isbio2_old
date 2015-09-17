__author__ = 'clem'
# import drmaa
from breeze.b_exceptions import NoSuchJob, InvalidArgument
from breeze.models import _JOB_PS as job_ps
from breeze.utils import get_logger


# clem on 20/08/2015
def sys_user_name():
	"""
	Return current system user name
	:rtype: str
	"""
	import subprocess
	return subprocess.Popen('whoami', shell=True, stdout=subprocess.PIPE).stdout.readline().replace('\n', '')


class SgeJob(object):
	"""
	Represents a SGE job from qstat output
	"""
	def __init__(self, output):
		"""
		Parse one qstat line output, as one SgeJob obj
		:type output: str
		:rtype: None
		"""
		from breeze.models import Runnable, Report, Jobs
		init = output.replace('\n', '').replace('     ', ' ')
		while init != init.replace('  ', ' '):
			init = init.replace('  ', ' ')
		a_list = init.split(' ')
		self.id = int(a_list[0]) # SgeId
		self.prior = a_list[1]
		self.name = a_list[2]
		self.full_name = ''
		self.user = a_list[3]
		self.full_user = ''
		self._state = a_list[4]
		self.start_d = a_list[5]
		self.start_t = a_list[6]
		self.queue = a_list[7]
		self.slot = a_list[8]
		self.runnable = Runnable.find_sge_instance(self.id)
		if self.runnable:
			self.user = str(self.runnable._author)
			self.full_user = self.runnable._author.get_full_name()
			self.full_name = self.runnable.sge_job_name


	@property
	def state(self):
		"""
		Returns the SgeJob state as a JobStat parameter
		:return:
		:rtype:
		"""
		if self._state in job_ps:
			return job_ps[self._state]
		else:
			return job_ps['']

	@property
	def raw_out(self):
		"""
		displays text line output similar to qstat output
		:rtype: str
		"""
		return '\t'.join(self.raw_out_tab)

	@property
	def raw_out_tab(self):
		"""
		displays text line output similar to qstat output
		:rtype: str
		"""
		return [str(self.id), self.prior, self.name, self.user, self.state, self.start_d, self.start_t, self.queue, self.slot]

	def abort(self):
		"""
		Abort a job using command line
		:return:
		:rtype:
		"""
		import subprocess
		return subprocess.Popen('qdel %s' % self.id, shell=True, stdout=subprocess.PIPE).stdout

	def __repr__(self):
		return '<SgeJob %s>' % self.name

	def __str__(self):
		return '\t'.join(
			[str(self.id), self.name, self.user, self.state, self.start_d, self.start_t, self.queue, self.slot])


# clem on 25/08/2015
class Qstat(object):
	def __init__(self):
		import os
		if 'QSTAT_BIN' in os.environ:
			self.qstat = os.environ['QSTAT_BIN']
		else:
			self.qstat = 'qstat'

		self._job_list = dict()
		self._refresh_qstat()

	def __sub_proc(self, arg):
		import subprocess
		return subprocess.Popen('%s|grep %s' % (self.qstat, str(arg)), shell=True, stdout=subprocess.PIPE).stdout

	@property
	def job_dict(self):
		"""
		:rtype: dict()
		"""
		self._refresh_qstat()
		return self._job_list

	@property
	def job_list(self):
		"""
		:rtype: dict()
		"""
		l = list()
		self._refresh_qstat()
		for each in self._job_list:
			l.append(self._job_list[each])
		return l

	# clem on 25/08/2015
	def _refresh_qstat(self):
		"""
		:return:
		:rtype: int
		"""
		self._job_list = dict()
		lines = self.__sub_proc(sys_user_name()).readlines()
		for e in lines:
			j = SgeJob(e)
			self._job_list[j.id] = j
		if len(lines) == 0:
			get_logger().debug('qstat says : No jobs running')
		return len(lines)

	def job_info(self, jid=None):
		"""
		:type jid: int
		:rtype: SgeJob | NoSuchJob
		"""
		if jid is not None:
			if type(jid) == unicode:
				jid = int(jid)
			self._refresh_qstat()
			if jid in self._job_list:
				return self._job_list[jid]
			else:
				raise NoSuchJob('%s was not found. SgeJob run was completed or SgeJob never existed.' % jid)
				# return None, self.job_list[jid]
