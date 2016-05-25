import logging
import hashlib
import time
from sys import stdout, _getframe as get_frame
from multipledispatch import dispatch # enables method overloading
from filesize import UnitSystem, file_size2human
from os.path import isfile, isdir, islink, exists, getsize, join, basename
from os import symlink, readlink, listdir, makedirs, access, R_OK, chmod
from subprocess import call, Popen, PIPE
from threading import Thread, Lock

# DO NOT HAVE ANY BREEZE NOR DJANGO RELATED CODE IN THIS MODULE
# this module is intended to have utilities function used in breeze, but must remain self-contained
# i.e. NO Breeze related code, no Django-specific code, no imports from Breeze nor Django


logger = logging.getLogger(__name__)
GENERAL_CACHE_TIME_OUT = 60 * 60 # 60 minutes


# clem 16/05/2016
class ExpiredCacheObject(RuntimeWarning):
	pass


# clem 16/05/2016
class IdleExpiredCacheObject(ExpiredCacheObject):
	pass


class ACL(enumerate):
	__R = 4
	__RX = 5
	__W = 6
	__X = 7
	__OTHER = 1
	__GROUP = 10
	__OWNER = 100

	R__ = 0400
	RW__ = 0600
	RWX__ = 0700
	RW_RW_R = 0664
	RW_RW_ = 0660
	RW_R_ = 0640
	R_R_ = 0440
	RWX_RWX_R = 0774
	RWX_RWX_ = 0770
	RWX_RX_ = 0750
	RX_RX_ = 0550


class TermColoring(enumerate):
	HEADER = '\033[95m'
	OK_BLUE = '\033[94m'
	OK_GREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	END_C = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

	@classmethod
	def ok_blue(cls, text):
		return cls.OK_BLUE + text + cls.END_C

	@classmethod
	def ok_green(cls, text):
		return cls.OK_GREEN + text + cls.END_C

	@classmethod
	def fail(cls, text):
		return cls.FAIL + text + cls.END_C

	@classmethod
	def warning(cls, text):
		return cls.WARNING + text + cls.END_C

	@classmethod
	def header(cls, text):
		return cls.HEADER + text + cls.END_C

	@classmethod
	def bold(cls, text):
		return cls.BOLD + text + cls.END_C

	@classmethod
	def underlined(cls, text):
		return cls.UNDERLINE + text + cls.END_C


# clem on 20/08/2015
def is_host_online(host, deadline=5):
	""" Check if given host is online (whether it respond to ping)

	:param host: the IP address to test
	:type host: str
	:param deadline: the maximum time to wait in second (text format)
	:type deadline: str | int
	:rtype: bool
	"""
	res = call(['ping', '-c', '3', '-i', '0.2', '-W', '0.1', '-w', str(deadline), host], stdout=PIPE)
	return res == 0


# clem 08/09/2016 moved here on 25/05/2016
def test_tcp_connect(host, port, timeout=2):
	""" Test if TCP can connect to target host on specified port

	:param host: ip address or FQDN of the target host
	:type host: str
	:param port: TCP port number to attempt connection to
	:type port: str
	:param timeout: connection timeout time in seconds
	:type timeout: int
	:return: if TCP connect is successful
	:rtype: bool
	:raises: socket.error or Exception
	"""
	try:
		import socket
		s = socket.socket()
		try:
			s.settimeout(timeout)
			s.connect((host, port))
			return True
		finally:
			s.close()
	except Exception:
		raise


# clem on 21/08/2015
def get_md5(content):
	""" Return md5 checksum of content argument

	:type content: list|str
	:rtype: str
	"""
	m = hashlib.md5()
	if type(content) == list:
		for eachLine in content:
			m.update(eachLine)
	else:
		m.update(content)
	return m.hexdigest()


# clem on 21/08/2015
def get_file_md5(file_path):
	""" Return md5 checksum of file

	:param file_path: location of the file
	:type file_path: str
	:rtype: str
	"""
	try:
		fd = open(file_path, "rb")
		content = fd.readlines()
		fd.close()
		return get_md5(content)
	except IOError:
		return ''


def get_logger(name=None, level=0):
	if name is None:
		# name = sys._getframe(level + 1).f_code.co_name
		name = this_function_name(level)
	log_obj = logger.getChild(name)
	assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only
	return log_obj


# Shortcut for handling path ( TEST DESIGN )
class Path(object):
	import os
	SEP = os.path.sep

	def __init__(self, path_str):
		""" Path object always return the path string with a trailing slash ( / ) for folders

		:param path_str: the path to use
		:type path_str: str
		"""
		self.__path_str = ''
		self.set_path(path_str)

	def get_path(self):
		return self.__path_str

	def set_path(self, path_str):
		if path_str is not None and path_str != '':
			if path_str[-1] != self.SEP and isdir(path_str + self.SEP):
				path_str += self.SEP
		self.__path_str = path_str

	path_str = property(get_path, set_path)

	def __str__(self): # Python 3: def __str__(self):
		return '%s' % self.path_str

	def is_dir(self):
		return isdir(self.path_str)

	def is_file(self):
		return isfile(self.path_str)

	def is_link(self):
		return islink(self.path_str)

	def exists(self):
		return exists(self.path_str)

	def get_size(self):
		return getsize(self.path_str)

	def is_non_empty_file(self):
		"""
		Return if the path is pointing to an non empty file
		:return: is path pointing to an non empty file
		:rtype: bool
		"""
		return isfile(self.path_str) and getsize(self.path_str) > 0

	def remove_file_safe(self):
		"""
		Remove a file or link if it exists
		:return: True or False
		:rtype: bool
		"""
		from os import remove
		try:
			if isfile(self.path_str) or islink(self.path_str):
				get_logger().info("removing %s" % self.path_str)
				set_file_acl(self.path_str, ACL.RW_RW_, True)
				remove(self.path_str)
				return True
		except OSError:
			return self.remove_lnk_safe()
		return False

	def remove_lnk_safe(self):
		"""
		Remove a link file or a dir and all sub content (to use for links only)
		"""
		from os import unlink

		path = self.path_str
		if self.is_dir() and self.path_str.endswith(self.SEP):
			path = path[:-1]

		try:
			get_logger().debug("unlinking %s" % path)
			unlink(path)
			return True
		except OSError as e:
			get_logger().debug("unable to unlink : %s" % e)
		return False

	def auto_symlink(self, holder):
		"""
		Make a soft-link and overwrite any previously existing file (be careful !) or link with the same name
		:param holder: path of the link holder
		:type holder: str
		"""
		log_obj = get_logger()
		Path(holder).remove_lnk_safe()

		log_obj.debug("symlink to %s @ %s" % (self.path_str, holder))
		symlink(self.path_str, holder)
		return True


def custom_copytree(src, dst, symlinks=False, ignore=None, verbose=True, sub=False):
	from shutil import copy2, Error, copystat, WindowsError

	if not sub and verbose:
		print 'copy %s => %s' % (src, dst)
	files_count, folders_count = 0, 0

	names = listdir(src)
	if ignore is not None:
		ignored_names = ignore(src, names)
	else:
		ignored_names = set()

	def dot():
		stdout.write('.')
		stdout.flush()

	try:
		makedirs(dst)
	except OSError:
		pass

	errors = []
	for name in names:
		if name in ignored_names:
			continue
		src_name = join(src, name)
		dst_name = join(dst, name)
		try:
			if symlinks and islink(src_name):
				linkto = readlink(src_name)
				symlink(linkto, dst_name)
				if verbose:
					if isdir(linkto):
						folders_count += 1
					elif isfile(linkto):
						files_count += 1
					dot()
			elif isdir(src_name):
				c1, c2 = custom_copytree(src_name, dst_name, symlinks, ignore, verbose=verbose, sub=True)
				files_count += c1
				folders_count += c2 + 1
			else:
				# Will raise a SpecialFileError for unsupported file types
				copy2(src_name, dst_name)
				if verbose:
					dot()
					files_count += 1

		# catch the Error from the recursive copytree so that we can
		# continue with other files
		except Error, err:
			errors.extend(err.args[0])
		except EnvironmentError, why:
			errors.append((src_name, dst_name, str(why)))
	try:
		copystat(src, dst)
	except OSError, why:
		if WindowsError is not None and isinstance(why, WindowsError):
			# Copying file access times may fail on Windows
			pass
		else:
			errors.extend((src, dst, str(why)))
	if errors:
		raise Error(errors)
	if not sub and verbose:
		print 'done (%s files and %s folders)' % (files_count, folders_count)
	return files_count, folders_count


def is_non_empty_file(file_path):
	return Path(file_path).is_non_empty_file()


def remove_file_safe(fname):
	""" Remove a file or link if it exists

	:param fname: the path of the file/link to delete
	:type fname: str
	:return: True or False
	:rtype: bool
	"""
	return Path(fname).remove_file_safe()


def auto_symlink(target, holder):
	""" Make a soft-link and overwrite any previously existing file (be careful !) or link with the same name

	:param target: target path of the link
	:type target: str
	:param holder: path of the link holder
	:type holder: str
	"""
	return Path(target).auto_symlink(holder)


# clem 29/09/2015
# from [fr] http://saladtomatonion.com/blog/2014/12/16/mesurer-le-temps-dexecution-de-code-en-python/
class Timer(object):
	def __init__(self):
		self.interval = None
		self.start_time = None

	def __enter__(self):
		self.start()
		# __enter__ must return an instance bound with the "as" keyword
		return self

	# There are other arguments to __exit__ but we don't care here
	def __exit__(self, *_):
		self.function_timer()

	def start(self):
		if hasattr(self, 'interval'):
			del self.interval
		self.start_time = time.time()

	def function_timer(self):
		if hasattr(self, 'start_time'):
			self.interval = time.time() - self.start_time
			del self.start_time # Force timer reinit


# clem 29/09/2015
# from [fr] http://saladtomatonion.com/blog/2014/12/16/mesurer-le-temps-dexecution-de-code-en-python/
# use as decorator like so : @LoggerTimer('prefix message', logger.debug)
class LoggerTimer(Timer):
	@staticmethod
	def default_logger(msg):
		print msg

	def __init__(self, prefix=None, func=None):
		super(LoggerTimer, self).__init__() # not sure about that, TODO check
		# Use func if not None else the default one
		self.f = func or LoggerTimer.default_logger
		# Format the prefix if not None or empty, else use empty string
		self.prefix = prefix or '' # getmembers(func, '__name__')

	def function_timer(self):
		# Call the parent method
		super(LoggerTimer, self).function_timer()
		# Call the logging function with the message
		self.f('{0}{1}{2}'.format(self.prefix, self.interval, ' sec'))

	def __call__(self, func):
		# Use self as context manager in a decorated function
		def decorated_func(*args, **kwargs):
			self.prefix = '{0} : '.format(self.prefix or func.__name__ if func else '')
			with self:
				return func(*args, **kwargs)

		return decorated_func


# clem 29/09/2015 writing shortcut
def logger_timer(function):
	a = LoggerTimer(func=get_logger('timing').debug)
	return a(function)


def get_folder_size(folder):
	""" Return the total size of a folder located at <i>folder</i>, recursively
	:type folder: str
	:rtype: int
	"""
	total_size = getsize(folder)
	for item in listdir(folder):
		item_path = join(folder, item)
		if not islink(item_path):
			if isfile(item_path):
				total_size += getsize(item_path)
			elif isdir(item_path):
				total_size += get_folder_size(item_path)
	return total_size


# clem 09/10/2015
def human_readable_byte_size(size_value, unit=None, digit=2):
	""" Human-readable file size.
	:type size_value: int
	:type unit: filesize.UnitSystem
	:type digit: int
	:rtype: str
	"""
	return file_size2human(size_value, system=UnitSystem.traditional if not unit else unit, digit=digit)


# clem 07/10/2015
def is_readable(file_path):
	""" Return if a file located at <i>file_path</i> is readable
	:type file_path: str
	:rtype: bool
	"""
	return access(file_path, R_OK)


# clem 09/10/2015
def set_file_acl(path, perm=ACL.RW_R_, silent_fail=False):
	""" Change file permission to <i>perm</i> (default is RW_R_)
	:type path: str
	:type perm: int
	:type silent_fail: bool
	:rtype: bool
	"""
	if not is_readable(path):
		try:
			chmod(path, perm)
			get_logger().info('changed {0} to {1:#o}'.format(path, perm))
			return True
		except OSError as e:
			get_logger().exception(str(e))
			if not silent_fail:
				raise OSError(e)
	return False


# clem 19/02/2016
def do_restart():
	try:
		Popen('sleep 1 && killall python', shell=True, stdout=PIPE) # relies on autorun.sh
	except Exception as e:
		raise e
	return True


# clem 19/02/2016
def do_reboot():
	try:
		Popen('sleep 1 && sudo reboot -n', shell=True, stdout=PIPE)
	except Exception as e:
		raise e
	return True


# TODO rewrite, as a class maybe ?
# clem 09/03/2016 contains code from from http://stackoverflow.com/a/3229493/5094389
def advanced_pretty_print(d, indent=0, open_obj=False, get_output=False):
	""" Prints a tree from a nested dict
	:type d: dict | list | basestring
	:type indent: int
	:type open_obj: bool
	:type get_output: bool
	:rtype: None | basestring
	"""

	buff = ''

	# clem 10/03/2016
	def get_iter(obj):
		if isinstance(obj, basestring):
			return obj
		if type(obj) in [dict, list] or hasattr(obj, 'iteritems') or hasattr(obj, '__iter__'):
			return obj
		if hasattr(obj, '__dict__'):
			if open_obj:
				return obj.__dict__
			else:
				return repr(obj)
		return list()

	# clem 10/03/2016
	def get_type(obj):
		res = str(type(obj)).partition("'")[2].partition("'")[0]
		return res if not res == 'instance' else ''

	# clem 10/03/2016
	def get_size(obj):
		try:
			return len(obj)
		except (TypeError, AttributeError):
			if hasattr(obj, 'bit_length'):
				return obj.bit_length()
		return '?'

	# clem 10/03/2016
	def extra_info(obj):
		a_type = get_type(obj)
		return ' <%s:%s>' % (a_type, get_size(obj)) if a_type else ''

	# clem 14/03/2016
	def out(content):
		if get_output:
			return content
		else:
			print content
			return ''

	def multi_line_ident(txt):
		return txt.replace('\n', '\n' + '\t' * (indent + 1))

	iterable = get_iter(d)

	if type(d) is list: # source element is a list, that may contain dicts
		i = 0
		for el in iterable:
			buff += out('\t' * indent + '_#%s :' % i)
			buff += str(advanced_pretty_print(el, indent + 1, open_obj, get_output))
			i += 1
	elif type(d) is dict or type(iterable) is dict:
		for key, value in iterable.iteritems():
			buff += out('\t' * indent + str(key) + extra_info(value))
			if isinstance(value, (dict, list)):
				buff += str(advanced_pretty_print(value, indent + 1, open_obj, get_output))
			else:
				buff += out('\t' * (indent + 1) + multi_line_ident(str(repr(value))))
	else:
		buff += out('\t' * (indent + 1) + multi_line_ident(str(iterable)))

	# if get_output:
	return buff


# clem 01/04/2016
def pp(data, unfold_objects=False, return_output=False):
	return advanced_pretty_print(data, open_obj=unfold_objects, get_output=return_output)


# clem 05/04/2016
def new_thread(func):
	"""
	Wrapper to run functions in a new Thread

	:type func:
	:rtype:
	"""
	# assert callable(func)

	def decorated(*args):
		Thread(target=func, args=args).start()

	return None if not func else decorated


# clem 06/04/2016
def password_from_file(path):
	from os.path import exists, expanduser
	if not exists(path):
		temp = expanduser(path)
		if exists(temp):
			path = temp
	return open(path).read().replace('\n', '')


# clem 08/04/2016
def this_function_name(delta=0):
	return this_function_caller_name(delta)


# clem 08/04/2016
def this_function_caller_name(delta=0):
	return get_frame(2 + delta).f_code.co_name


# clem 08/04/2016
def is_from_cli():
	""" Tells if the caller was called from command line or not
	:rtype: bool
	"""
	return this_function_caller_name(1) == '<module>'


# clem 08/04/2016
def get_named_tuple(class_name, a_dict):
	assert isinstance(class_name, basestring) and isinstance(a_dict, dict)
	from collections import namedtuple
	return namedtuple(class_name, ' '.join(a_dict.keys()))(**a_dict)


# clem 18/04/2016
def get_term_cmd_stdout(cmd_list_with_args):
	assert isinstance(cmd_list_with_args, list)
	ret = ''
	a = Popen(cmd_list_with_args, stdout=PIPE)
	b = a.communicate()
	if b:
		s = b[0].split('\n')
		return s
	return ret


# clem 18/04/2016
def git_get_branch():
	ret = ''
	s = get_term_cmd_stdout(["git", "branch"])
	if s:
		for line in s:
			if line.startswith('*'):
				ret = line.replace('*', '').strip()
	return ret


# clem 18/04/2016
def git_get_status():
	ret = ''
	s = get_term_cmd_stdout(["git", "status"])
	if s:
		ret = '%s / %s\n%s' % (s[0].strip(), git_get_commit_line(), s[1].strip())
	return ret


# clem 18/04/2016
def git_get_commit_line(full=False, hash_only=False): # FIXME : too much of an HACK
	ret = ''
	try:
		s = get_term_cmd_stdout(["git", "show"])
		if s:
			commit = s[0].strip()[:14] if not full else s[0].strip()
			if hash_only:
				return commit
			ret = '%s on %s' % (commit, s[2].replace('Date:   ', '').strip())
	finally:
		return ret


# clem 18/04/2016
def git_get_commit(full=False):
	return git_get_commit_line(full, True).replace('commit', '').strip()


# clem 18/04/2016
def git_get_head(folder=''):
	try:
		return open('%s.git/FETCH_HEAD' % folder).readline().replace('\n', '')
	except IOError:
		return ''


# clem 29/04/2016
def get_free_port():
	"""
	:return: the number of a free TCP port on the local machine
	"""
	from socket import socket
	sock = socket()
	sock.bind(('', 0))
	return sock.getsockname()[1]


# clem 06/05/2016, moved here on 16/05/2016
def gen_file_from_template(template_path, sub_dict, output_path=None, safe=True):
	"""
	generate a content from a template

	:param template_path: the path of the template file to use
		(c.f. https://docs.python.org/2.7/library/string.html#string.Template )
	:type template_path: str or unicode
	:param sub_dict: the substitution dictionary to use. Keys are used to match the $-var in the template
	:type sub_dict: dict
	:param output_path: the full path (including file name) where to save the output to. If None, then the
		result is returned
	:type output_path: basestring or None
	:param safe: If True, the sub-engine will not raise error for non-matched $-keys
	:type safe: bool
	:return: Either a success flag is output_path was provided, or the result of the replacement if successful,
	or False
	:rtype: bool or basestring
	"""
	from os.path import exists, expanduser
	assert isinstance(template_path, (str, unicode))
	assert exists(template_path)
	assert output_path is None or isinstance(output_path, (str, unicode))
	assert isinstance(sub_dict, dict)

	from string import Template

	# load the template
	with open(template_path) as template_fd:
		src = Template(template_fd.read())

	# do the substitution
	result = src.safe_substitute(sub_dict) if safe else src.substitute(sub_dict)

	if output_path:
		output_path = expanduser(output_path)
		with open(output_path, 'w') as output_fd:
			# writes the result to the output file
			while output_fd.write(result):
				pass
		return True
	return result


# clem 16/05/2016
class CachedObject:
	__created = 0.
	__last_access = 0.
	access_counter = 0
	__stored_object = None
	__time_out = -1
	__idle_time_out = -1

	def __init__(self, an_object, invalidate_after=GENERAL_CACHE_TIME_OUT, idle_expiry=0):
		""" This class is a caching mechanism to store an object, managing expiration, and idle expiration.
		if no invalidate_after is provided, it will be assigned default_time_out (120 sec).
		if no idle_expiry is provided, it will be disabled.

		:param an_object: The object to store
		:type an_object: object
		:param invalidate_after: number of second after which the object will be deleted (0 to disable)
		:type invalidate_after: int | float
		:param idle_expiry: number of second since last access after which the object will be deleted (0 to disable)
		:type idle_expiry: int | float
		"""
		self.__stored_object = an_object
		self.__created = time.time()
		self.__last_access = time.time()
		self.__time_out = invalidate_after
		self.__idle_time_out = idle_expiry

	@property
	def is_expired(self):
		""" returns whether or not this object has expired

		:rtype: bool
		"""
		if self.__time_out and self.age >= self.__time_out:
			return True
		return False

	@property
	def is_idle_time_out(self):
		""" returns whether or not this object has exceeded its idle time-out

		:rtype: bool
		"""
		if self.__idle_time_out and self.idle_time >= self.__idle_time_out:
			return True
		return False

	def __accessed(self):
		""" Updates the last access time of the object, and the access counter. Also manages expiration.

		:raise: IdleExpiredCacheObject | ExpiredCacheObject
		:rtype: None
		"""
		if self.is_expired or self.is_idle_time_out:
			self.__stored_object = None
			raise IdleExpiredCacheObject if self.is_idle_time_out else ExpiredCacheObject
		self.__last_access = time.time()
		self.access_counter += 1

	def get_object(self):
		""" Returns the stored object. will update the last access time, and thus reset the idle_time."""
		self.__accessed()
		return self.__stored_object

	@property
	def age(self):
		""" return the number of seconds since this object was created

		:rtype: float
		"""
		return time.time() - self.__created

	@property
	def idle_time(self):
		""" return the number of seconds since this object was last accessed directly

		:rtype: float
		"""
		return time.time() - self.__last_access

	@property
	def last_access(self):
		""" return the time stamp (i.e. as time.time() ) of the last direct access to the stored object

		:rtype: float
		"""
		return self.__last_access

	@property
	def object(self):
		""" Returns the stored object. will update the last access time, and thus reset the idle_time alias
			of get_object().

		:raise: IdleExpiredCacheObject | ExpiredCacheObject
		"""
		return self.get_object()

	def __str__(self):
		return '<cached %s (idle %s sec / %s sec old)>' % (
			repr(self.__stored_object), int(self.idle_time), int(self.age))

	def __repr__(self):
		return '<cached %s>' % repr(self.__stored_object)


# clem 16/05/2016
class ObjectCache(object):
	_cache = dict()
	data_mutex = Lock()

	@classmethod
	def get_cached(cls, key, default=None):
		""" Retrieves the CachedObject containing the object if it exists

		:param key: the key to identify the object
		:type key: Any
		:param default: default object to return if object is not found in the cache
		:type default: Any
		:return: The corresponding CacheObject or None
		:rtype: CachedObject | None
		"""
		with cls.data_mutex:
			val = cls._cache.get(key, default)
		return val

	@classmethod
	def get(cls, key, default=None):
		""" Retrieves the stored object if it exists

		:param key: the key to identify the object
		:type key: Any
		:param default: default object to return if object is not found in the cache
		:type default: Any
		:return: The stored object or None
		"""
		cached = cls.get_cached(key, default)
		if cached:
			text = str(cached)
			try:
				return cached.object
			except ExpiredCacheObject as e:
				cls.expire(key, text, str(e.__class__.__name__))
		return default

	@classmethod
	@new_thread
	def expire(cls, key, text, exception_txt):
		try:
			with cls.data_mutex:
				del cls._cache[key]
			get_logger().debug('Cache : removed %s:%s : %s' % (key, text, exception_txt))
			return True
		except KeyError:
			return False

	@classmethod
	def add(cls, some_object, key, invalidate_after=GENERAL_CACHE_TIME_OUT, idle_expiry=0):
		if not cls.get_cached(key):
			with cls.data_mutex:
				cls._cache[key] = CachedObject(some_object, invalidate_after, idle_expiry)
			get_logger().debug('Cache : added %s:%s' % (key, repr(cls.get_cached(key))))
		cls.garbage_collection()

	@classmethod
	def clear(cls):
		""" Removes everything from the cache """
		with cls.data_mutex:
			num = len(cls._cache)
			cls._cache = dict()
		get_logger().debug('Cache : cleared (%s objects removed)' % num)

	@classmethod
	@new_thread
	def garbage_collection(cls):
		with cls.data_mutex:
			for k, v in cls._cache.iteritems():
				if v.is_idle_time_out or v.is_expired:
					cls.expire(k, str(v), 'ExpiredGarbageCollection')


# moved here on 19/05/2016
# TODO : Review
@dispatch(basestring)
def file_mod_time(path):
	from os.path import getmtime # , join

	return getmtime(path)


# moved here on 19/05/2016
@dispatch(basestring, basestring)
def file_mod_time(dir_name, fname):
	from os.path import join

	return file_mod_time(join(dir_name, fname))


# moved from settings on 19/05/2016
def recur(nb, function, args):
	while nb > 0:
		args = function(args)
		nb -= 1
	return args


# moved from settings on 19/05/2016
# TODO make a generator
def get_key(path=''):
	try:
		with open(path + 'secret') as f:
			return f.read()
	except Exception:
		pass
	return None


# moved from settings on 19/05/2016
def recur_rec(nb, function, args):
	if nb > 0:
		return recur_rec(nb - 1, function, function(args))
	return args


# moved from settings on 19/05/2016
def import_env():
	""" dynamically change the environement """
	import subprocess as sp
	import json
	import os
	source = 'source ~/.sge_profile'
	dump = 'python -c "import os, json;print json.dumps(dict(os.environ))"'
	pipe = sp.Popen(['/bin/bash', '-c', '%s && %s' % (source, dump)], stdout=sp.PIPE)
	env = json.loads(pipe.stdout.read())
	os.environ = env


# clem 20/04/2016 moved from compute_interface_module on 24/05/2016
def make_tarfile(output_filename, source_dir, do_raise=True):
	""" makes a tar.bz2 archive from source_dir, and stores it in output_filename

	:param output_filename: the name/path of the resulting archive
	:type output_filename: basestring
	:param source_dir: the path of the source folder
	:type source_dir: basestring
	:param do_raise: indicate wether to raise the error (in case of),
		if not it will be logged instead
	:type do_raise: bool
	:return: if success
	:rtype: bool
	"""
	try:
		import tarfile
		with tarfile.open(output_filename, 'w:bz2') as tar:
			tar.add(source_dir, arcname=basename(source_dir))
		return True
	except Exception as e:
		if do_raise:
			raise
		get_logger().exception('Error creating %s : %s' % (output_filename, str(e)))
	return False


# clem 23/05/2016  moved from compute_interface_module on 24/05/2016
def extract_tarfile(input_filename, destination_dir, do_raise=True):
	""" extract an tar.* to a destination folder

	:param input_filename: the name/path of the source archive
	:type input_filename: basestring
	:param destination_dir: the path of the destination folder
	:type destination_dir: basestring
	:param do_raise: indicate wether to raise the error (in case of),
		if not it will be logged instead
	:type do_raise: bool
	:return: if success
	:rtype: bool
	"""
	try:
		import tarfile
		with tarfile.open(input_filename, 'r:*') as tar:
			tar.extractall(destination_dir)
		return True
	except Exception as e:
		if do_raise:
			raise
		get_logger().log.exception('Error creating %s : %s' % (input_filename, str(e)))
	return False
