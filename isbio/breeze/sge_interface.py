from compute_interface_module import * # has os, abc, JobStat, Runnable, ComputeTarget and utilities.*
from breeze.b_exceptions import NoSuchJob, SGEError # , InvalidArgument
import StringIO


__version__ = '0.1'
__author__ = 'clem'
__date__ = '06/05/2016'


class ConfigNames(enumerate):
	q_master = 'SGE_MASTER_HOST'
	q_master_port = 'SGE_QMASTER_PORT'
	exec_port = 'SGE_EXECD_PORT'
	queue = 'SGE_QUEUE'
	r_home = 'R_HOME'
	shell_path = 'DEFAULT_SHELL'
	engine_section = 'sge'
	q_bin_folder_path = 'Q_BIN'
	qstat_bin_path = 'QSTAT_BIN'
	qdel_bin_path = 'QDEL_BIN'


# clem 06/05/2016
class SGEInterface(ComputeInterface):
	from django.conf import settings
	DEFAULT_V_MEM = '15G'
	DEFAULT_H_CPU = '999:00:00'
	DEFAULT_H_RT = '999:00:00'
	SGE_RQ_TEMPLATE = settings.SGE_REQUEST_TEMPLATE
	SGE_REQUEST_FN = settings.SGE_REQUEST_FN

	def __init__(self, compute_target, storage_backend=None):
		super(SGEInterface, self).__init__(compute_target, storage_backend)

	# clem 09/05/2016
	def write_config(self):
		""" Writes a custom config file for SGE to read from for config

		:return: success
		:rtype: bool
		"""
		assert isinstance(self.target_obj, ComputeTarget)
		a_dict = {
			'shell'	: self.config_shell_path,
			'h_vmem': self.DEFAULT_V_MEM,
			'h_cpu'	: self.DEFAULT_H_CPU,
			'h_rt'	: self.DEFAULT_H_RT,
			'queue'	: self.config_queue_name,
		}
		return gen_file_from_template(self.SGE_RQ_TEMPLATE, a_dict, '~/%s' % self.SGE_REQUEST_FN)

	# clem 09/05/2016
	def apply_config(self):
		""" Applies the proper Django settings, and environement variables for SGE config

		:return: if succeeded
		:rtype: bool
		"""
		if self.target_obj:
			self.engine_obj.set_local_env()
			self.execut_obj.set_local_env()
			# self.target_obj.set_local_env()
			self.target_obj.set_local_env(self.target_obj.engine_section)
			self.engine_obj.set_local_env()

			return self.write_config()
		return False

	# clem 06/05/2016
	@property
	def _sge_obj(self): # TODO move it all here ( or not )
		return Qstat(self).job_info()

	# clem 06/05/2016
	def status(self): # TODO move it all here
		return self._sge_obj.state

	# clem 16/03/2016
	def _write_log(self, txt):
		self.log.debug(txt)

	def send_job(self): # TODO move it all here
		# TODO fully switch to qsub, to get finally totally rid of DRMAA F*****G SHIT
		if self.apply_config():
			self._runnable.old_sge_run()
			return True
		return False

	# clem 06/05/2016 # FIXME
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

	# clem 17/05/2016
	@property  # writing shortcut
	def config_qstat_bin_path(self):
		if self.engine_obj:
			return self.engine_obj.get(ConfigNames.qstat_bin_path)
		return ''

	# clem 17/05/2016
	@property  # writing shortcut
	def config_qdel_bin_path(self):
		if self.engine_obj:
			return self.engine_obj.get(ConfigNames.qdel_bin_path)
		return ''

	# clem 17/05/2016
	@property  # writing shortcut
	def config_shell_path(self):
		if self.engine_obj:
			return self.engine_obj.get(ConfigNames.shell_path)
		return ''

	# clem 17/05/2016
	@property  # writing shortcut
	def config_queue_name(self):
		if self.target_obj:
			return self.target_obj.get(ConfigNames.queue, ConfigNames.engine_section)
		return ''


# clem 04/05/2016
def initiator(compute_target, *_):
	"""

	:type compute_target: ComputeTarget
	:type _: object
	"""
	assert isinstance(compute_target, ComputeTarget)
	return SGEInterface(compute_target)

# moved here on 17/05/2016


# clem 17/06/2016
def sub_proc(cmd, shell=True):
	""" Shortcut for subprocess.Popen()

	:param cmd: the command to run
	:type cmd: basestring
	:param shell: shell param of Popen, default to True
	:type shell: bool
	:return: process object
	:rtype: subprocess.Popen
	"""
	assert isinstance(cmd, basestring)
	assert isinstance(shell, bool)
	from subprocess import Popen, PIPE
	return Popen(cmd, shell=shell, stdout=PIPE)


# clem on 20/08/2015
def sys_user_name():
	""" Return current system user name

	:rtype: str
	"""
	return sub_proc('whoami').stdout.readline().replace('\n', '')


class SgeJob(object):
	"""
	Represents a SGE job from qstat output
	"""

	runnable = None
	id = 0
	prior = ''
	name = ''
	full_name = ''
	user = ''
	full_user = ''
	_state = ''
	start_d = ''
	start_t = ''
	queue = ''
	slot = ''
	qstat = None

	def __init__(self, output, qstat=None):
		""" Parse one qstat line output, as one SgeJob obj

		:type output: str
		:rtype: None
		"""
		assert not qstat or isinstance(qstat, Qstat)
		init = output.strip().replace('\n', '').replace('     ', ' ')
		while init != init.replace('  ', ' '):
			init = init.replace('  ', ' ')
		a_list = init.split(' ')
		self.id = int(a_list[0]) # SgeId
		self.prior = a_list[1]
		self.name = a_list[2]
		# self.full_name = ''
		self.user = a_list[3]
		# self.full_user = ''
		self._state = a_list[4]
		self.start_d = a_list[5]
		self.start_t = a_list[6]
		self.queue = a_list[7] if len(a_list) > 7 else ''
		self.slot = a_list[8] if len(a_list) > 8 else ''
		self.qstat = qstat
		if self.qstat and self.qstat.runnable:
			self.runnable = self.qstat.runnable # Runnable.find_sge_instance(self.id)
		else:
			self.runnable = Runnable.find_sge_instance(self.id)
		if self.runnable:
			self.user = str(self.runnable.author)
			self.full_user = self.runnable.author.get_full_name()
			self.full_name = self.runnable.sge_job_name

	@property
	def state(self):
		"""

		:return: the SgeJob state as a JobStat parameter
		:rtype: str
		"""
		jps = self.runnable.compute_if.js.job_ps
		if self._state in jps:
			return jps[self._state]
		else:
			return str(self._state)

	@property
	def raw_out(self):
		"""

		:return: text line output similar to qstat output
		:rtype: str
		"""
		return '\t'.join(self.raw_out_tab)

	@property
	def raw_out_tab(self):
		"""

		:return: text line output similar to qstat output
		:rtype: list[a, b]
		"""
		return [str(self.id), self.prior, self.name, self.user, self.state, self.start_d, self.start_t, self.queue,
			self.slot]

	def abort(self):
		""" Abort a job using command line

		"""
		if self.qstat.qdel_bin_path:
			return sub_proc('%s %s' % (self.qstat.qdel_bin_path, self.id)).stdout
		return StringIO.StringIO()

	def __repr__(self):
		return '<SgeJob %s>' % self.name

	def __str__(self):
		return '\t'.join(
			[str(self.id), self.name, self.user, self.state, self.start_d, self.start_t, self.queue, self.slot])


# TODO : Split this object in two : one general and one runnable / config related
# clem on 25/08/2015
class Qstat(object): # would need some proper error management if SGE is not set up properly
	runnable = None
	sge_if = None
	target_obj = None
	qstat_bin_path = ''
	qdel_bin_path = ''
	queue_name = ''

	def __init__(self, sge_interface):
		assert isinstance(sge_interface, SGEInterface)
		try:
			self.sge_if = sge_interface
			self.target_obj = self.sge_if.target_obj
			self.runnable = self.target_obj.runnable
			self._job_list = dict()
			self.qstat_bin_path = self.sge_if.config_qstat_bin_path
			self.qdel_bin_path = self.sge_if.config_qdel_bin_path
			self.queue_name = self.sge_if.config_queue_name
			self._refresh_qstat()
		except Exception as e:
			self.sge_if.log.warning('Qstat : %s' % str(e))
			pass

	def __sub_proc(self, arg):
		if self.qstat_bin_path:
			return sub_proc('%s|grep %s' % (self.qstat_bin_path, str(arg))).stdout
		return StringIO.StringIO()

	# clem 12/10/2015
	@property
	def queue_stat(self, _=''):
		from collections import namedtuple
		if self.qstat_bin_path and self.queue_name:
			try:
				p = sub_proc('%s -g c|grep %s' % (self.qstat_bin_path, str(self.queue_name)))
				output, err = p.communicate()
				server_info = dict()
				for each in output.splitlines():
					if self.queue_name in each.split():
						server_info['s_name'] = str(each.split()[0])
						server_info['cqload'] = str(float(each.split()[1]) * 100)
						server_info['used'] = str(each.split()[2])
						server_info['avail'] = str(each.split()[4])
						server_info['total'] = str(each.split()[5])
						server_info['cdsuE'] = str(each.split()[7])
						server_info['cdsuE'] = str(each.split()[7])
						break

				return namedtuple('Struct', server_info.keys())(*server_info.values())
			except Exception as e:
				raise SGEError('SGE seems to be not properly configured : %s' % str(e))
		else:
			return namedtuple('Struct', [])(*[])

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
		return False

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
			j = SgeJob(e, self)
			self._job_list[j.id] = j
		return len(lines)

	def job_info(self, jid=None):
		"""
		:type jid: int
		:rtype: SgeJob | NoSuchJob
		"""
		if not jid and self.runnable:
			jid = self.runnable.sgeid
		if jid is not None:
			if type(jid) == unicode:
				jid = int(jid)
			self._refresh_qstat()
			if jid in self._job_list:
				return self._job_list[jid]
			else:
				raise NoSuchJob('%s was not found. It usually mean the SgeJob run was completed.' % jid)

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
			if each.runnable is None:
				sup = ' &lt;ext&gt; '
			else:
				sup = ' &lt;%s&gt; ' % each.runnable.short_id
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
		return get_md5(str(self.html))
