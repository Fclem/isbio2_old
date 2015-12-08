__author__ = 'clem'
# import drmaa
from breeze.b_exceptions import NoSuchJob, InvalidArgument
from breeze.models import _JOB_PS as job_ps
from breeze.utils import get_logger
from django.conf import settings


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
		from breeze.models import Runnable
		init = output.strip().replace('\n', '').replace('     ', ' ')
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
		self.queue = a_list[7] if len(a_list) > 7 else ''
		self.slot = a_list[8] if len(a_list) > 8 else ''
		self.runnable = Runnable.find_sge_instance(self.id)
		if self.runnable:
			self.user = str(self.runnable.author)
			self.full_user = self.runnable.author.get_full_name()
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
		return subprocess.Popen('%s %s' % (settings.QDEL_BIN, self.id), shell=True, stdout=subprocess.PIPE).stdout

	def __repr__(self):
		return '<SgeJob %s>' % self.name

	def __str__(self):
		return '\t'.join(
			[str(self.id), self.name, self.user, self.state, self.start_d, self.start_t, self.queue, self.slot])


# clem on 25/08/2015
class Qstat(object): # would need some proper error management if SGE is not set up properly
	def __init__(self):
		try:
			self._job_list = dict()
			self.qstat = settings.QSTAT_BIN
			self._refresh_qstat()
		except Exception as e:
			pass

	def __sub_proc(self, arg):
		import subprocess
		return subprocess.Popen('%s|grep %s' % (self.qstat, str(arg)), shell=True, stdout=subprocess.PIPE).stdout

	# clem 12/10/2015
	@property
	def queue_stat(self, queue_name=settings.SGE_QUEUE_NAME):
		import subprocess
		from collections import namedtuple
		try:
			p = subprocess.Popen('%s -g c|grep %s' % (self.qstat, str(queue_name)), shell=True, stdout=subprocess.PIPE)
			output, err = p.communicate()
			server_info = dict()
			for each in output.splitlines():
				if queue_name in each.split():
					server_info['s_name'] = str(each.split()[0])
					server_info['cqload'] = str(float(each.split()[1]) * 100)
					server_info['used'] = str(each.split()[2])
					server_info['avail'] = str(each.split()[4])
					server_info['total'] = str(each.split()[5])
					server_info['cdsuE'] = str(each.split()[7])
					server_info['cdsuE'] = str(each.split()[7])
					break

			return namedtuple('Struct', server_info.keys())(*server_info.values())
		except Exception:
			from b_exceptions import SGEError
			raise SGEError('SGE seems to be not properly configured')

	# clem 12/10/2015
	@property
	def queue_stat_int(self):
		q = self.queue_stat
		for each in q.__dict__:
			if each != 's_name':
				q.__dict__[each] = 0 + int(float(q.__dict__[each]))
		return q

	# clem 12/10/2015
	@property
	def is_queue_full(self):
		try:
			return not self.queue_stat_int.avail
		except AttributeError:
			return True

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
		# if len(lines) == 0:
			# get_logger().debug('qstat says : No jobs running')
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

	# Clem 22/09/2015
	@property
	def html(self):
		"""
		Format job_list as an smart HTML output
		replace default sge user, by job owner, and owner fullname as tooltip
		and add the job full name as tooltip
		:rtype: str
		"""
		q = self.job_list

		result = ''
		for each in q:
			assert isinstance(each, SgeJob)
			tab = each.raw_out_tab
			tab[2] = "<span title='%s'>%s</span>" % (each.full_name, each.name)
			tab[3] = "<span title='%s'>%s</span>" % (each.full_user, each.user)
			sup = ''
			if each.runnable is None:
				sup = ' &lt;ext&gt; '
			result += '<code>%s%s%s</code><br />' % (sup, '\t'.join(tab), sup)

		if result == '':
			result = 'There is no SGE jobs running at the moment.<br />'

		return result

	# Clem 22/09/2015
	@property
	def md5(self):
		"""
		Return the md5 of the current qstat full output
		Used for long_poll refresh :
		Client check his last known status md5 against this,
		and only get a reply when this output changes compared to his md5
		:return:
		:rtype: str
		"""
		from utils import get_md5
		# from hashlib import md5
		# m = md5()
		# m.update(str(self.html))
		# return m.hexdigest()
		return get_md5(str(self.html))
