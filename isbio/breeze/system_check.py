from django.contrib.auth.models import User
from breeze import utils
from breeze.auxiliary import proxy_to
from isbio import settings
from breeze.b_exceptions import *
from django.http import HttpRequest
# from _ctypes_test import func
# import breeze.auxiliary as aux


DEBUG = True
SKIP_SYSTEM_CHECK = False
FAIL_ON_CRITICAL_MISSING = True
RAISE_EXCEPTION = False

if DEBUG:
	# quick fix to solve PyCharm Django console environment issue
	from breeze.process import Process
else:
	from multiprocessing import Process


class Bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

	@staticmethod
	def ok_blue(text):
		return Bcolors.OKBLUE + text + Bcolors.ENDC

	@staticmethod
	def ok_green(text):
		return Bcolors.OKGREEN + text + Bcolors.ENDC

	@staticmethod
	def fail(text):
		return Bcolors.FAIL + text + Bcolors.ENDC

	@staticmethod
	def warning(text):
		return Bcolors.WARNING + text + Bcolors.ENDC

	@staticmethod
	def header(text):
		return Bcolors.HEADER + text + Bcolors.ENDC

	@staticmethod
	def bold(text):
		return Bcolors.BOLD + text + Bcolors.ENDC

	@staticmethod
	def underlined(text):
		return Bcolors.UNDERLINE + text + Bcolors.ENDC


OK = '[' + Bcolors.ok_green('OK') + ']'
BAD = '[' + Bcolors.fail('NO') + ']'
WARN = '[' + Bcolors.warning('NO') + ']'

# Manage checks process for rendez-vous
proc_lst = list()


# clem 10/09/2015
def gen_test_report(the_user, gen_number=10, job_duration=30, time_break=1):
	from breeze.views import report_overview
	import time

	posted = dict()
	posted["project"] = 1
	posted["Section_dbID_9"] = 0
	posted["9_opened"] = 'False'
	posted["Dropdown"] = 'Enter'
	posted["Textarea"] = ''
	posted["Section_dbID_81"] = 0
	posted["81_opened"] = 'False'
	posted["Section_dbID_118"] = '1'
	posted["118_opened"] = 'True'
	posted["sleep duration"] = str(job_duration)
	posted["sleep_duration"] = str(job_duration)
	posted["wait_time"] = str(job_duration)
	posted["Groups"] = ''
	posted["Individuals"] = ''

	rq = HttpRequest()
	# del rq.POST
	rq.POST = posted
	rq.user = the_user
	rq.method = 'POST'

	for i in range(1, gen_number+1):
		name = 'SelfTest%s' % i
		print name
		report_overview(rq, 'TestPipe', name, '00000')
		time.sleep(time_break)

	print 'done.'


# clem 08/09/2015
class RunType:
	@staticmethod
	@property
	def runtime():
		pass

	@staticmethod
	@property
	def boot_time():
		pass

	@staticmethod
	@property
	def both():
		pass


# clem 08/09/2015
class SysCheckUnit:
	def __init__(self, funct, url, legend, msg, type, t_out=0, arg=None, supl=None, ex=SystemCheckFailed, mandatory=False):
		if type is RunType.runtime or callable(funct):
			self.checker_function = funct
			self.url = url
			self.legend = legend
			self._msg = msg
			self.t_out = int(t_out)
			self.arg = arg
			self.type = type
			self.supl = supl
			self.mandatory = mandatory
			self.ex = ex
		else:
			raise InvalidArgument(Bcolors.fail('Argument function must be a callable object'))

	def s_check(self):
		if (self.type is RunType.boot_time or self.type is RunType.both) and callable(self.checker_function):
			self.split_run()
			return True
		return False

	# clem 08/09/2015
	def split_run(self, from_ui=False):
		"""
		Runs each checker function in a separate process for
			_ concurrency and speed (from console)
			_ process isolation, and main thread segfault avoidance (from UI)
		"""
		p = Process(target=self.split_runner, args=(from_ui, ))
		p.start()
		if not from_ui:
			proc_lst.append({ 'proc': p, 'chk': self }) # add process to the rendez-vous list
		else:
			p.join() # wait for process to finish
			p.terminate()
			return p.exitcode == 0

	# clem 08/09/2015
	def split_runner(self, from_ui=False):
		"""
		Checker function runner.
		Call the function, display console message and exception if appropriate
		"""
		res = False
		if callable(self.checker_function):
			if self.arg is not None:
				res = self.checker_function(self.arg)
			else:
				res = self.checker_function()
		else:
			raise InvalidArgument(Bcolors.fail('Argument function must be a callable object'))

		sup = ''
		sup2 = ''

		if not res:
			if self.mandatory:
				sup2 = Bcolors.warning('required and critical !')
			else:
				sup2 = Bcolors.warning('NOT critical')

		if not from_ui:
			print self.msg,
			if self.supl is not None and callable(self.supl):
				sup = self.supl()
			print OK if res else BAD if self.mandatory else WARN, sup, sup2

		if not res:
			if RAISE_EXCEPTION:
				raise self.ex
			if from_ui or self.mandatory:
				import sys
				sys.exit(1)
		# implicit exit(0)

	@property
	def msg(self):
		return Bcolors.ok_blue(self._msg)


# clem 08/09/2015
def check_rdv(): # Rendez-vous for processes
	"""
	New version, replaces the 25/08/2015 one, use rendez-vous instead of busy-waiting
	"""
	for each in proc_lst:
		proc = each['proc']
		chk = each['chk']
		assert isinstance(proc, Process) and isinstance(chk, SysCheckUnit)
		proc.join()
		if FAIL_ON_CRITICAL_MISSING and proc.exitcode != 0 and chk.mandatory:
			print Bcolors.fail('BREEZE INIT FAILED')
			raise chk.ex()
		proc.terminate()

	print Bcolors.ok_green('All checks done, system is up and running !')

# split_run(message, function, arg=None, supl=None): DELETED on 08/09/2015
# split_runner(message, function, arg=None, supl=None): DELETED on 08/09/2015


# clem 08/09/2015
def run_system_test():
	"""
	NEW ONE 08/09/2015
	replacing old version from 31/08/2015
	"""
	from breeze.middlewares import is_on
	global SKIP_SYSTEM_CHECK
	if not SKIP_SYSTEM_CHECK and is_on():
		print Bcolors.ok_blue('Running Breeze system integrity checks ......')
		if fs_mount.checker_function():
			print fs_mount.msg + OK
			for each in check_list:
				each.s_check()

			check_rdv()
		else:
			print 'FS\t\t' + BAD
			raise FileSystemNotMounted
	else:
		print Bcolors.ok_blue('Skipping Breeze system integrity checks ......')

##
# Special file system snapshot systems
##


# clem on 21/08/2015
def generate_file_index(root_dir, exclude=list()):
	"""
	Generate a dict with md5 checksums of every files within rootDir
	:param root_dir: path to scan
	:type root_dir: str
	:param exclude: list of folder within rootDir to exclude
	:type exclude: list
	:rtype: dict
	"""
	# import os.path, time
	md5s = dict()

	def short(dirName):
		if dirName != root_dir:
			return dirName.replace(root_dir, '') # if rootDir != dirName else './'
		else:
			return '/'

	import os

	for dirName, subdirList, fileList in os.walk(root_dir):
		s_dirName = short(dirName)
		if dirName not in exclude and not '/.' in s_dirName and not s_dirName.startswith('.'):
			for fname in fileList:
				md = utils.get_file_md5(os.path.join(dirName, fname))
				try:
					# mod_time = time.ctime(os.path.getmtime(os.path.join(dirName, fname)))
					mod_time = os.path.getmtime(os.path.join(dirName, fname))
				except OSError:
					mod_time = ''
				md5s[os.path.join(short(dirName), fname)] = [md, mod_time]

	return md5s


# clem on 21/08/2015
def save_file_index():
	"""
	Save the FS signature in file settings.FS_SIG_FILE
	and a file system checksum index json object in file settings.FS_LIST_FILE
	:return: True
	:rtype: bool
	"""
	from django.utils import simplejson

	fs_sig, save_obj = file_system_check()

	f = open(settings.FS_SIG_FILE, 'w')
	f.write(fs_sig)
	f.close()
	f = open(settings.FS_LIST_FILE, 'w')
	simplejson.dump(save_obj, f)
	f.close()
	return True


# clem on 21/08/2015
def file_system_check(verbose=False):
	"""
	Generate MD5 for files of every folders listed under settings.FOLDERS_TO_CHECK
	:param verbose: display info
	:type verbose: bool
	:return: file system signature, file system index dict
	:rtype: str, dict
	"""
	from django.utils import simplejson
	total = ''
	save_obj = dict()
	for each in settings.FOLDERS_TO_CHECK:
		md5s = generate_file_index(each, ['__MACOSX', ])
		json = simplejson.dumps(md5s)
		# save_obj[each] = (utils.get_md5(json), md5s)
		save_obj[each] = md5s
		total += json
	# print '(' + str(len(md5s)), 'files)', fs_state[each]
	if verbose:
		for el in save_obj:
			print save_obj[el], el

	return utils.get_md5(total), save_obj


# clem on 21/08/2015
def saved_fs_sig():
	f = open(settings.FS_SIG_FILE)
	txt = f.readline()
	f.close()
	return txt


##
# Checkers functions, called on boot and/or runtime
##


# clem on 21/08/2015
def check_is_file_system_unchanged():
	"""
	Check if the FS (as listed in settings.FOLDERS_TO_CHECK) remains unchanged
	:rtype: bool
	"""
	if file_system_check()[0] == saved_fs_sig():
		return True, True, 0
	else: # if both fs_sig don't match, review the whole fs. For example Newer or Added files don't count
		changed, broken, _, _, errors = deep_fs_check()
		return not changed, not broken, errors


# clem 25/08/2015
def deep_fs_check(): # TODO optimize (too slow)
	"""
	Return flag_changed, flag_invalid, files_state, folders_state
	:return: flag_changed, flag_invalid, files_state, folders_state
	:rtype:
	"""
	from django.utils import simplejson
	from hurry.filesize import size, si
	files_state = list()

	folders_state = list()
	current_state = file_system_check()[1]
	f = open(settings.FS_LIST_FILE)
	saved_state = simplejson.load(f)
	f.close()
	flag_changed = False
	flag_invalid = False
	errors = 0

	def getFolderSize(folder):
		import os
		total_size = os.path.getsize(folder)
		for item in os.listdir(folder):
			itempath = os.path.join(folder, item)
			if os.path.isfile(itempath):
				total_size += os.path.getsize(itempath)
			elif os.path.isdir(itempath):
				total_size += getFolderSize(itempath)
		return total_size

	folder = dict()

	for each in saved_state:
		status = dict()
		status['name'] = each
		status['size'] = 0
		if each not in current_state:
			status['status'] = 'MISSING'
			flag_changed = True
			errors += len(saved_state[each])
		else:
			folder_count = len(saved_state[each])
			folder_size = size(getFolderSize(each), system=si)
			folder[each] = { 'count': folder_count, 'size': folder_size}
			status['count'] = folder_count
			status['size'] = folder_size
			if saved_state[each] == current_state[each]:
				status['status'] = 'OK'
			else:
				status['status'] = 'CHANGED'
				flag_changed = True
			# del current_state[each]
		folders_state.append(status)

	for each in saved_state:
		files_tmp = list()
		ss = saved_state[each]
		cs = current_state[each]
		for file_n in ss:
			status = dict()
			# status['name'] = os.path.join(each, file_n)
			status['name'] = file_n
			if file_n not in cs:
				status['status'] = 'MISSING'
				errors += 1
				flag_changed = True
			else:
				if ss[file_n] == cs[file_n]:
					status['status'] = 'OK'
				else:
					flag_changed = True
					if ss[file_n][1] > cs[file_n][1]:
						status['status'] = 'OLDER'
						errors += 1
					elif ss[file_n][1] < cs[file_n][1]:
						status['status'] = 'NEWER'
					else: # same time, different checksum (is that even possible ?)
						status['status'] = 'EQT_DIFF'
						errors += 1
				del cs[file_n]
			files_tmp.append(status)
		# at this point cs should be empty
		for file_n in cs:
			flag_changed = True
			files_tmp.append({ 'name': file_n, 'status': 'ADDED' })
		files_state.append({ 'name': each, 'size': folder[each]['size'], 'count': len(files_tmp), 'list': files_tmp })

	if errors > 0:
		flag_invalid = True

	return flag_changed, flag_invalid, files_state, folders_state, errors


# clem on 20/08/2015
def check_rora():
	"""
	Check if RORA db host is online and RORA db connection is successful
	:rtype: bool
	"""
	try:
		if utils.is_host_online(settings.RORA_SERVER_IP, '2'):
			from breeze import rora
			return rora.test_rora_connect()
	except Exception as e:
		print e
	return False


# clem on 20/08/2015
def check_dotm():
	"""
	Check if Dotmatix db host is online and Dotmatix db connection is successful
	:rtype: bool
	"""
	# return status_button(rora.test_dotm_connect())
	if utils.is_host_online(settings.DOTM_SERVER_IP, '2'):
		from breeze import rora
		return rora.test_dotm_connect()
	return False


# clem on 21/08/2015
def check_file_server():
	"""
	Check if file server host is online
	:rtype: bool
	"""
	return utils.is_host_online(settings.FILE_SERVER_IP, '2')


# clem on 21/08/2015
def check_file_system_mounted():
	"""
	Check if file server host is online, and project folder is mounted
	:rtype: bool
	"""
	from utils import exists
	return check_file_server() and exists(settings.MEDIA_ROOT)


# clem on 20/08/2015
def check_shiny(request):
	"""
	Check if Shiny server is responding
	:rtype: bool
	"""
	try:
		r = proxy_to(request, '', settings.SHINY_TARGET_URL, silent=True)
		if r.status_code == 200:
			return True
	except Exception:
		pass
	return False


# clem on 09/09/2015
def check_watcher():
	from breeze.middlewares import JobKeeper
	return JobKeeper.p.is_alive()


# clem on 20/08/2015
def check_sge():
	"""
	Check if SGE queue master server host is online, and drmaa can initiate a valid session
	:rtype: bool
	"""
	if utils.is_host_online(settings.SGE_MASTER_IP, '2'):
		import drmaa
		try:
			s = drmaa.Session()
			s.initialize()
			s.exit()
			return True
		except Exception:
			pass
	return False


# clem 08/09/2015
def check_cas(request):
	"""
	Check if CAS server is responding
	:rtype: bool
	"""
	if utils.is_host_online(settings.CAS_SERVER_IP, '2'):
		try:
			r = proxy_to(request, '', settings.CAS_SERVER_URL, silent=True)
			if r.status_code == 200:
				return True
		except Exception:
			pass
	return False


# clem 09/09/2015
def ui_checker_proxy(what):
	# from breeze import views
	# return views.custom_404_view(HttpRequest())
	if what not in check_dict:
		from breeze import auxiliary as aux
		return aux.fail_with404(HttpRequest(), 'NOT FOUND')
	obj = check_dict[what]
	assert isinstance(obj, SysCheckUnit)

	if what == 'watcher':
		return check_watcher()
	else:
		return obj.split_run(from_ui=True)

check_list = list()

# Collection of system checks that is used to run all the test automatically, and display run-time status
check_list.append( SysCheckUnit(save_file_index, 'fs_ok', 'File System', 'saving file index...\t',
								RunType.both, 10000, supl=saved_fs_sig, ex=FileSystemNotMounted, mandatory=True))
fs_mount = SysCheckUnit(check_file_system_mounted, 'fs_mount', 'File server', 'FILE SYSTEM\t\t ',
								RunType.runtime, ex=FileSystemNotMounted, mandatory=True)
check_list.append(fs_mount)
check_list.append( SysCheckUnit(check_cas, 'cas', 'CAS server', 'CAS SERVER\t\t',
								RunType.both, arg=HttpRequest(), ex=CASUnreachable, mandatory=True))
check_list.append( SysCheckUnit(check_rora, 'rora', 'RORA db', 'RORA DB\t\t\t', RunType.both, ex=RORAUnreachable))
check_list.append( SysCheckUnit(check_sge, 'sge', 'SGE DRMAA', 'SGE MASTER\t\t',
								RunType.both, ex=SGEUnreachable, mandatory=True))
check_list.append( SysCheckUnit(check_dotm, 'dotm', 'DotMatics server', 'DOTM DB\t\t\t',
								RunType.both, ex=DOTMUnreachable))
check_list.append( SysCheckUnit(check_shiny, 'shiny', 'Shiny server', 'SHINY HTTP\t\t',
								RunType.both, arg=HttpRequest(), ex=ShinyUnreachable))
check_list.append(SysCheckUnit(check_watcher, 'watcher', 'JobKeeper', 'JOB_KEEPER\t\t',
								RunType.runtime, ex=WatcherIsNotRunning))

check_dict = dict()
for each in check_list:
	check_dict.update({ each.url: each })


# clem 08/09/2015
def get_template_check_list():
	res = list()
	for each in check_list:
		res.append({ 'url': '/status/%s/' % each.url, 'legend': each.legend, 'id': each.url, 't_out': each.t_out })
	return res
