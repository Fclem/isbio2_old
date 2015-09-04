__author__ = 'clem'

# from _ctypes_test import func
# import breeze.auxiliary as aux
from breeze import utils
from breeze.auxiliary import proxy_to
from isbio import settings
# from breeze.b_exceptions import InvalidArgument, FileSystemNotMounted
from django.http import HttpRequest

DEBUG = False
SKIP_SYSTEM_CHECK = False

if DEBUG:
	# quick fix to solve PyCharm Django console environnement issue
	from breeze.process import Process
else:
	from multiprocessing import Process

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'


OK = '[' + bcolors.OKGREEN + 'OK' + bcolors.ENDC + ']'
BAD = '[' + bcolors.FAIL + 'NO' + bcolors.ENDC + ']'

# Manage checks process for rendez-vous
proc_lst = list()


# clem 25/08/2015
def refresh_proc(): # Rendez-vous for processes
	while len(proc_lst) > 0:
		for proc in proc_lst:
			assert isinstance(proc, Process)
			if not proc.is_alive():
				proc_lst.remove(proc)
				del proc

	print 'All checks done, system is up and running !'


# clem 25/08/2015
def split_run(message, function, arg=None, supl=None):
	p = Process(target=split_runner, args=(message, function, arg, supl,))
	p.start()
	proc_lst.append(p) # add process to the rendez-vous list


# clem 25/08/2015
def split_runner(message, function, arg=None, supl=None):
	res = None
	if callable(function):
		if arg is not None:
			res = function(arg)
		else:
			res = function()
	else:
		raise InvalidArgument('Argument function must be a callable object')

	sup = ''
	if supl is not None and callable(supl):
		sup = supl()

	print message, OK if res else BAD, sup


# clem 31/08/2015
def run_system_test():
	global SKIP_SYSTEM_CHECK
	if not SKIP_SYSTEM_CHECK:
		print 'Running Breeze system integrity checks ......'
		if check_file_system_mounted():
			print 'FILE SYSTEM\t\t' + OK
			split_run('saving file index...\t', save_file_index, None, supl=saved_fs_sig)
			split_run('RORA DB\t\t\t', check_rora)
			split_run('SGE MASTER\t\t', check_sge)
			split_run('DOTM DB\t\t\t', check_dotm)
			split_run('SHINY HTTP\t\t', check_shiny, HttpRequest())

			refresh_proc()
		else:
			print 'FS\t\t' + BAD
			raise FileSystemNotMounted
	else:
		print 'Skipping Breeze system integrity checks ......'


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

	open(settings.FS_SIG_FILE, 'w').write(fs_sig)
	simplejson.dump(save_obj, open(settings.FS_LIST_FILE, 'w'))
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
	return open(settings.FS_SIG_FILE).readline()


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
def deep_fs_check():
	"""
	Return flag_changed, flag_invalid, files_state, folders_state
	:return: flag_changed, flag_invalid, files_state, folders_state
	:rtype:
	"""
	from django.utils import simplejson
	files_state = list()

	folders_state = list()
	current_state = file_system_check()[1]
	saved_state = simplejson.load(open(settings.FS_LIST_FILE))
	flag_changed = False
	flag_invalid = False
	errors = 0

	for each in saved_state:
		status = dict()
		status['name'] = each
		if each not in current_state:
			status['status'] = 'MISSING'
			flag_changed = True
			errors += len(saved_state[each])
		else:
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
		files_state.append({ 'name': each, 'list': files_tmp, 'count': len(files_tmp) })

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
