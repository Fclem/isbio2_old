from docker import Client
from docker.errors import NotFound, APIError, NullResource
from .utils import get_md5, pretty_print_dict_tree
from threading import Thread, Lock


# clem 10/03/2016
class DockerVolume:
	path = ''
	mount_point = ''
	mode = ''

	def __init__(self, path, mount_point, mode='ro'):
		assert isinstance(path, basestring) and isinstance(mount_point, basestring) and\
			isinstance(mode, basestring)
		self.path = path
		self.mount_point = mount_point
		self.mode = mode

	# clem 15/03/2016
	def pretty_print(self):
		pretty_print_dict_tree(self.__dict__)

	# clem 14/03/2016
	def __str__(self):
		return '%s:%s:%s' % (self.path, self.mount_point, self.mode)


# clem 10/03/2016
class DockerRun:
	image_full_name = ''
	_image = None
	cmd = ''
	_volumes = list()
	created_container_id = ''
	created_container = None

	# clem 11/03/2016
	@property
	def volumes(self):
		return self._volumes

	# _check_volumes deleted 14/03/2016 (last git commit 32844a2)
	# _check_if_volume_exists deleted 14/03/2016 (last git commit 32844a2)
	# _volume_exists deleted 14/03/2016 (last git commit 32844a2)

	def __init__(self, image, cmd='', volumes=None, ev_listener=None):
		assert isinstance(image, (DockerImage, basestring)) and isinstance(cmd, basestring) and\
			(volumes is None or isinstance(volumes, (list, DockerVolume)))
		self.image_full_name = image
		self.cmd = cmd
		self._volumes = volumes
		self.event_listener = ev_listener

	# clem 17/03/2016
	def container_created(self, container):
		"""
		Take care of registering the event listener (if any) to the provided container
		:type container: DockerContainer
		"""
		if self.event_listener and isinstance(container, DockerContainer) and callable(self.event_listener):
			self.created_container = container
			self.created_container_id = container.Id
			container.register_event_listener(self.event_listener)

	# clem 14/03/2016
	def config_dict(self):
		a_dict = dict()
		vol_list = self._volumes if isinstance(self._volumes, list) else [self._volumes]
		for each in vol_list:
			assert isinstance(each, DockerVolume)
			a_dict[each.path] = { 'bind': each.mount_point,
									'mode': each.mode,
			}
		return a_dict

	# clem 16/03/2016
	@property # temp wrapper
	def image(self):
		if self._image:
			return self._image
		return self.image_full_name

	# temp wrapper
	def link_image(self, client=None):
		if self._image:
			return self._image
		elif isinstance(client, DockerClient):
			self._image = client.get_image(self.image_full_name)
			return self.link_image()
		return DockerImage({ 'RepoTags': self.image_full_name })

	# clem 15/03/2016
	def pretty_print(self):
		pretty_print_dict_tree(self.__dict__)

	def __repr__(self):
		return str((self.image, self.cmd, self.volumes))


# clem 10/03/2016
class DockerRepo:
	url = ''
	login = ''
	pwd = ''
	email = ''

	def __init__(self, login, pwd, email='', url='https://index.docker.io'):
		assert isinstance(login, basestring) and isinstance(pwd, basestring) and isinstance(email, basestring) and \
			isinstance(url, basestring)
		self.login = login
		self.pwd = pwd
		self.email = email
		self.url = url


# clem 09/03/2016
class DockerImage:
	Created = 0
	Labels = dict()
	VirtualSize = 0
	ParentId = u''
	Size = 0
	RepoDigests = None
	Id = u''
	RepoTags = list()
	_sig = ''
	_repo = ''
	_name = ''
	_tag = ''

	def __init__(self, a_dict):
		assert isinstance(a_dict, dict)
		self.__dict__.update(a_dict)
		_ = self.sig

	def _get_sig(self):
		new_dict = self.__dict__
		if '_sig' in new_dict:
			new_dict.pop('_sig')
		return get_md5(str(new_dict))

	@property
	def sig(self):
		if not self._sig:
			self._sig = self._get_sig()
		return self._sig

	# clem 16/03/2016
	def _process_name(self):
		full_n = self.full_name
		if '/' in full_n:
			self._repo, rest = full_n.split('/', 1)
		else:
			self._repo, rest = 'library', full_n

		if ':' in rest:
			self._name, self._tag = rest.split(':', 1)
		else:
			self._name, self._tag = rest, ''

	# clem 16/03/2016
	@property
	def tag(self):
		if not self._tag:
			self._process_name()
		return self._tag

	# clem 16/03/2016
	@property
	def name(self):
		if not self._name:
			self._process_name()
		return self._name

	# clem 16/03/2016
	@property
	def repo_name(self):
		if not self._repo:
			self._process_name()
		return self._repo

	# clem 16/03/2016
	@property
	def repo_and_name(self):
		return '%s/%s' % (self.repo_name, self.name)

	# clem 10/03/2016
	@property
	def full_name(self):
		if type(self.RepoTags) is list and len(self.RepoTags) > 0:
			return str(self.RepoTags[0])
		else:
			return str(self.RepoTags)

	# clem 15/03/2016
	def pretty_print(self):
		pretty_print_dict_tree(self.__dict__)

	def __repr__(self):
		return '<DockerImage %s>' % self.full_name

	# clem 10/03/2016
	def __str__(self):
		return str(self.full_name)


# clem 09/03/2016
class DockerContainer:
	RestartCount = 0
	Labels = dict()
	Image = None
	NetworkSettings = dict()
	HostConfig = dict()
	State = dict()
	GraphDriver = dict()
	Config = dict()
	Status = u''
	ImageID = u''
	ProcessLabel = u''
	Command = u''
	Created = u''
	LogPath = u''
	AppArmorProfile = u''
	HostsPath = u''
	ResolvConfPath = u''
	Id = u''
	Path = u''
	Driver = u''
	HostnamePath = u''
	MountLabel = u''
	Name = u''
	Names = list()
	Ports = list()
	Args = list()
	Mounts = list()
	_sig = u''
	_log = u''
	_event_list = list()
	_event_listener = None
	__client = None

	def __init__(self, a_dict, client=None, event_callback=None):
		assert isinstance(a_dict, dict) and (not client or isinstance(client, DockerClient))
		self.__dict__.update(a_dict)
		if client: # if we got a client in argument, we chain this container to its DockerImage object
			self.__client = client
			try:
				self.Image = client.images_by_id[self.ImageID]
			except KeyError:
				self.Image = a_dict.get('Image', None)
		else:
			self.Image = a_dict.get('Image', None)
		# _ = self.sig
		self.register_event_listener(event_callback)

	# @staticmethod # TODO del
	# def generate(run, some_id):
	# 	return DockerContainer({'Id': some_id}, event_callback=run.event_listener)

	# clem 15/03/2016
	def update(self, a_dict):
		assert isinstance(a_dict, dict)
		self.__dict__.update(a_dict)

	# clem 15/03/2016
	def register_event_listener(self, listener, replace=False):
		# if listener and callable(listener):
		if not self._event_listener or replace:
			self._event_listener = listener

	# clem 16/03/2016
	@property
	def has_event_listener(self):
		return self._event_listener and callable(self._event_listener)

	# clem 15/03/2016
	def new_event(self, event):
		self._event_list.append(event)
		if self.has_event_listener:
			if event.status == 'die':
				if self.__client:
					self._log = self.__client.logs(self.Id)
			self._event_listener(event)
			# Thread(target=self._event_listener, args=(event,)).start()

	# clem 15/03/2016
	@property
	def logs(self):
		return self._log

	# clem 14/03/2016
	@property
	def name(self):
		if self.Names:
			return self.Names[0] if len(self.Names) > 0 else ''
		elif self.Name:
			return self.Name
		else:
			return ''

	# clem 15/03/2016
	def pretty_print(self):
		pretty_print_dict_tree(self.__dict__)

	def __str__(self):
		return self.name if self.name else self.Id

	def __repr__(self):
		return '<DockerContainer %s>' % str(self)


# clem 15/03/2016
class DockerEventCategories:
	CREATE = 's:create'
	START = 's:start'
	DIE = 's:die'
	KILL = 's:kill'
	PAUSE = 's:pause'
	UNPAUSE = 's:unpause'
	DELETE = 's:delete'
	UNTAG = 's:untag'
	TAG = 's:tag'
	PULL = 's:pull'
	CONNECT = 'A:connect'
	DISCONNECT = 'A:disconnect'
	MOUNT = 'A:mount'
	UNMOUNT = 'A:unmount'
	RESTART = 'A:restart'
	UNKNOWN = ''

	a_dict = { CREATE: CREATE, START: START, DIE: DIE, KILL: KILL, PAUSE: PAUSE, UNPAUSE: UNPAUSE, CONNECT: CONNECT,
				DISCONNECT: DISCONNECT, MOUNT: MOUNT, UNMOUNT: UNMOUNT, RESTART: RESTART}

	def __init__(self):
		pass


# clem 14/03/2016
class DockerEvent:
	status = u''
	Action = u''
	Type = u''
	id = u''
	# from = u''
	timeNano = int()
	time = int()
	Actor = dict()
	_container = None
	__client = None

	def __init__(self, a_dict, client=None):
		assert isinstance(a_dict, (dict, str)) and (not client or isinstance(client, DockerClient))
		if type(a_dict) is str:
			import json
			a_dict = json.loads(a_dict)
		self.__dict__.update(a_dict)
		if client: # if we got a client in argument, we chain this container to its DockerImage object
			self.__client = client
			# self._get_container() # we''ll do it upon access, as this container might not yet be in the ps list

	# clem 16/03/2016
	def _attach_container(self, res_id):
		self._container = self.__client.get_container(res_id)
		return self._container

	def _get_container(self):
		if not self._container or not self._container.name: # if not a container or container has no name, refresh
			if self.Type == 'container':
				try:
					return self._attach_container(self.res_id)
				except NotFound:
					pass
			elif 'Attributes' in self.Actor and 'container' in self.Actor['Attributes']:
				return self._attach_container(self.Actor['Attributes']['container'])
			return self.res_id
		return self._container

	@property
	def container(self):
		return self._get_container()

	@property
	def res_id(self):
		ret = None
		if self.id:
			ret = self.id
		elif self.Type == 'container':
			ret = self.Actor['Attributes']['container']
		return ret

	# clem 16/03/2016
	@property
	def _get_resource(self):
		if self.Type == 'container':
			return self.container
		return self.res_id

	# clem 15/03/2016
	@property
	def dt(self):
		from datetime import datetime
		secs = float(self.timeNano / 1e9)
		return datetime.fromtimestamp(secs)

	# clem 15/03/2016
	@property
	def dt_formatted(self):
		return self.dt.strftime('%Y-%m-%dT%Hh%M:%S.%f')

	# clem 15/03/2016
	@property
	def date_formatted(self):
		return self.dt.strftime('%Y-%m-%d')

	# clem 15/03/2016
	@property
	def time_formatted(self):
		return self.dt.strftime('%Hh%M:%S.%f')

	# clem 15/03/2016
	def pretty_print(self):
		pretty_print_dict_tree(self.__dict__)

	# clem 15/03/2016
	@property
	def description(self):
		return 's:%s' % self.status if self.status else 'A:%s' % self.Action

	# clem 15/03/2016
	@property
	def category(self):
		desc = self.description
		return DockerEventCategories.a_dict.get(desc, DockerEventCategories.UNKNOWN)

	def __str__(self):
		return '%s [%s] %s %s' % (self._get_container(), self.time_formatted, self.Type, self.description)

	def __repr__(self):
		txt = 's:%s' % self.status if self.status else 'A:%s' % self.Action
		return '<DockerEvent [%s] %s %s>' % (self.timeNano, self.Type, txt)


# clem 08/03/2016
class DockerClient:
	RAISE_ERR = False
	DEV = False
	DEBUG = True
	repo = None
	default_run = None
	_raw_cli = None
	_console_mutex = None # use to ensure exclusive access to console
	_data_mutex = None # use to ensure exclusive access to console

	_daemon_url = ''

	_images_list = list()
	__image_dict_by_id = dict()
	__image_dict_by_tag = dict()
	__image_tree = dict()
	__watcher = None
	_container_list = list()
	_container_dict_by_id = dict()
	_container_dict_by_name = dict()
	_event_list = list()
	_run_dict = dict()

	#
	# CLASS MANAGEMENT
	#

	def __init__(self, repo, daemon_url, run=None): # TODO change the run passing
		assert isinstance(repo, DockerRepo) and (not run or isinstance(run, DockerRun)) and \
			isinstance(daemon_url, basestring)
		self.repo = repo
		self.default_run = run
		self._daemon_url = daemon_url
		self._raw_cli = Client(base_url=daemon_url)
		self._console_mutex = Lock()
		self._data_mutex = Lock()
		self._start_event_watcher()
		self.login()

	# clem 14/03/2016
	def __cleanup(self):
		if self.__watcher:
			self._force_log('watcher terminated')

	# clem 14/03/2016
	def __del__(self):
		self.__cleanup()

	# clem 14/03/2016
	def __delete__(self, _):
		self.__cleanup()

	# clem 14/03/2016
	def __exit__(self, *_):
		self.__cleanup()

	# clem 17/03/2016
	def _auto_raise(self, e):
		if self.RAISE_ERR:
			raise e

	# clem 17/03/2016
	def _exception_handler(self, e, msg='', force=True):
		msg = str(e) if not msg else str(msg)
		self._force_log(msg) if force else self._log(msg)
		self._auto_raise(e)

	#
	# LOGGING
	#

	# clem 10/03/2016
	def _log(self, obj, force_print=False, sup_text=''):
		if self.DEBUG or force_print:
			if type(obj) is dict:
				with self._console_mutex:
					pretty_print_dict_tree(obj)
			else:
				with self._console_mutex:
					print str(obj) + str(sup_text)
		# TODO log

	# clem 10/03/2016
	def _json_log(self, obj, force_print=False):
		self._log(self._json_parse(obj), force_print)

	# clem 10/03/2016
	def _force_log(self, obj, sup_text=''):
		self._log(obj, True, sup_text)

	# clem 16/03/2016
	def _json_parse(self, obj):
		if type(obj) is str:
			try:
				import json
				obj = json.loads(obj)
			except ValueError:
				pass
		return obj

	# clem 14/03/2016
	def _event_log(self, obj, sup_text=''):
		self._force_log(self._json_parse(obj), str(sup_text))

	#
	# INTERNALS
	#

	# clem 09/03/2016
	@property
	def __pp_cli(myself):
		"""
		A wrapper for self.raw_cli instance, that applies pretty_print on output of any command passed to docker client
		:rtype: Client
		"""
		# originally from http://stackoverflow.com/a/2704528/5094389
		class Prettyfy(object):
			def __getattribute__(self, name):
				attr = myself._raw_cli.__getattribute__(name)
				if hasattr(attr, '__call__'):
					def new_func(*args, **kwargs):
						result = attr(*args, **kwargs)
						if type(result) == dict:
							pretty_print_dict_tree(result)
						return result

					return new_func
				else:
					return attr

		return Prettyfy()

	# clem 16/03/2016
	def _term_stream(self, a_dict):
		import sys

		for each in a_dict:
			sys.stdout.write('%s\n' % a_dict[each])
			sys.stdout.flush()  # As suggested by Rom Ruben

	# clem 16/03/2016
	def _img_exists_or_pulled(self, run):
		"""
		check if image exists locally, and pull it if not
		Return True if image exists, or pulled successfully, False otherwise
		@params:
			run  - Required  : current iteration (DockerRun)
		@return: True if image exists, or pulled successfully, False otherwise
		@rtype: bool
		"""
		# TODO check if connected to repo
		image_name = str(run.image)
		if type(run.image) is not DockerImage and image_name not in self.images_by_repo_tag:
			# image not found, let's try to pull it
			img = run.link_image(self)
			self._log('Unable to find image \'%s\' locally' % image_name)
			return self.pull(img.repo_and_name, img.tag)
		return True

	# clem 17/03/2016
	def _error_managed(func):
		"""
		Error management wrapper for _run and _start
		:type func: function
		:rtype: function
		"""

		def decorated_func(self, arg):
			assert isinstance(self, DockerClient) and (isinstance(arg, DockerRun) or isinstance(arg, DockerContainer))
			msg = 'creation' if isinstance(arg, DockerRun) else 'start'
			try:
				if isinstance(arg, DockerRun):
					return func(self, arg)
				elif isinstance(arg, DockerContainer):
					return func(self, arg)
			except NotFound as e:
				self._exception_handler(e, '%s: %s' % (msg, str(e)))
			except APIError as e:
				self._log('Container %s failed : %s' % (msg, e))
				if isinstance(arg, DockerContainer):
					out_log = self.logs(arg.Id)
					if out_log:
						self._log('Container run log :\n%s' % pretty_print_dict_tree(out_log, get_output=True))
				self._auto_raise(e)
			except NullResource as e:
				self._exception_handler(e, '%s: %s' % (msg, e))
			except Exception as e:
				self._exception_handler(e, 'Unhandled %s exception : %s' % (msg, e))

		return decorated_func

	# clem 09/03/2016
	@_error_managed
	def _run(self, run):
		"""
		TBD
		:type run: DockerRun
		:rtype: DockerContainer
		"""
		assert isinstance(run, DockerRun)

		image_name = str(run.image)
		# check if image exists locally, and pull it if not
		if not self._img_exists_or_pulled(run): # if pulled failed
			return None

		# Create the container
		a_dict = run.config_dict() # get the volume config
		if a_dict:
			# apply volume config
			vol = run.config_dict().keys()
			vol_config = self.cli.create_host_config(binds=run.config_dict())
			self._log('docker run %s %s -v %s' % (image_name, run.cmd, run.volumes))
			container = self.get_container(self.cli.create_container(image_name, run.cmd, volumes=vol,
																	host_config=vol_config)['Id'])
		else: # no volume config
			self._log('docker run %s %s' % (image_name, run.cmd))
			container = self.get_container(self.cli.create_container(image_name, run.cmd)['Id'])

		if container: # container was successfully created and acquired
			with self._data_mutex:
				self._run_dict.update(
					{ container.Id: run }) # store the run, for event manager to start the container
			# client.start() now happens upon receiving the create event
			return container
		# If you are not in detached mode:
		# Attach to the container, using logs=1 (to have stdout and stderr from the container's start) and stream=1
		# If in detached mode or only stdin is attached, display the container's id.

	# clem 17/03/2016
	@_error_managed
	def _start(self, container):
		self.cli.start(container.Id)

	# clem 17/03/2016
	def _inspect_container(self, container_id):
		"""
		Get all the refreshed raw information about the container
		:type container_id: basestring
		:rtype: str
		"""
		try:
			return self.cli.inspect_container(container_id)
		except (NotFound, APIError) as e:
			self._exception_handler(e)
		except Exception as e:
			self._exception_handler(e)
		return dict()

	# clem 17/03/2016
	def _make_container(self, container_id):
		"""
		Return a new DockerContainer object, from a container_id
		:type container_id: basestring
		:rtype: DockerContainer
		"""
		return DockerContainer(self._inspect_container(container_id))

	# clem 17/03/2016
	def _get_container(self, container_id):
		"""
		Check if container in cache, if not create it with self.make_container and store it in the dict
		:type container_id: basestring
		:rtype: DockerContainer
		"""
		with self._data_mutex:
			if container_id in self._container_dict_by_id.keys():
				return self._container_dict_by_id[container_id]
			else:
				cont = self._make_container(container_id)
				self._container_dict_by_id[cont.Id] = cont
				return cont # self.inspect_container(container_id)

	#
	# CLASS INTERFACE
	#

	# clem 09/03/2016
	@property
	def cli(self):
		if not self.DEV:
			return self._raw_cli
		else:
			return self.__pp_cli

	# clem 09/03/2016
	@property
	def pretty_cli(self):
		return self.__pp_cli

	# clem 10/03/2016
	def run_default(self):
		if self.default_run: # TODO change that too
			return self._run(self.default_run)

	# clem 09/03/2016
	def img_run(self, img, cmd, volume=list()):
		"""
		TBD
		:type img: str
		:type cmd: str
		:type volume: DockerVolume|list
		:rtype:
		"""
		return self._run(DockerRun(img, cmd, volume))

	# clem 14/03/2016
	def get_container(self, container_id):
		"""
		Refresh the cached container list, and return the cached container
		:type container_id: str
		:rtype: DockerContainer
		"""
		if container_id:
			_ = self.containers_by_id # refresh cache
			return self._get_container(container_id)
		return None

	# clem 16/03/2016
	def get_image(self, image_descriptor):
		"""
		Get the cached image, and if not found try to refresh the cache for this entry only
		image_descriptor can be either the id, or the full name as repo/image:tag
		:type image_descriptor: str
		:rtype: DockerImage | None
		"""
		if image_descriptor:
			images_ids = self.images_by_id
			images_tags = self._get_images_by_repo_tag(images_ids) # call the sub-method to save time
			if image_descriptor in images_ids.keys():
				return images_ids.get(image_descriptor)
			elif image_descriptor in images_tags.keys():
				return images_tags.get(image_descriptor)
		return None

	#
	# DOCKER CLIENT MAPPINGS
	#

	# clem 10/03/2016
	def login(self):
		if self.repo:
			try:
				result = self.cli.login(self.repo.login, self.repo.pwd, self.repo.email, self.repo.url)
				self._log(result)
				return 'username' in result or result[u'Status'] == u'Login Succeeded'
			except APIError as e:
				self._exception_handler(e)
			except Exception as e:
				self._exception_handler(e, 'Unable to connect : %s' % e)
		return False

	# clem 16/03/2016
	def rmi(self, image, force=False):
		try:
			return self.cli.remove_image(str(image), force)
		except Exception as e:
			self._exception_handler(e)
		return None

	# clem 16/03/2016
	def pull(self, image_name, tag):
		try:
			gen = self.cli.pull(image_name, tag, stream=True)
			a_dict = dict()
			count = 0
			for line in gen: # TODO use streaming to terminal
				obj = self._json_parse(line)
				to_log = obj
				if 'status' in obj:
					if 'id' in obj:
						# to_log = '%s: %s' % (obj['id'], obj['status'])
						to_log = ''
						a_dict.update({ obj['id']: '%s: %s' % (obj['id'], obj['status'])})
					else:
						# a_dict.update({ count: str(obj['status']) })
						to_log = str(obj['status'])
				elif 'error' in obj:
					self._log(str(obj['error']))
					return None
				self._log(to_log)
				self._term_stream(a_dict)
				count += 1
			return True
		except Exception as e:
			self._exception_handler(e)

	# clem 17/03/2016
	def logs(self, container):
		assert isinstance(container, (basestring, DockerContainer))
		if isinstance(container, DockerContainer):
			container = container.Id
		try:
			return self.cli.logs(container)
		except Exception as e:
			self._exception_handler(e, 'cli.logs: %s' % e)
		return ''

	#
	# EVENTS LISTENER, PROCESSOR AND DISPATCHER
	#

	# clem 14/03/2016
	def _start_event_watcher(self):
		if not self.__watcher:
			self.__watcher = Thread(target=self._event_watcher)
			self._log('starting event watcher as Thread')
			self.__watcher.start()

	# clem 16/03/2016
	def _del_res(self, a_dict, res_id):
		"""
		Delete res_id from a_dict with error handling
		:type a_dict: dict
		:type res_id: basestring
		:rtype: None
		"""
		assert isinstance(a_dict, dict)
		try:
			with self._data_mutex:
				del a_dict[res_id]
		except Exception as e:
			self._exception_handler(e)

	# clem 16/03/2016
	def _process_event(self, event):
		assert isinstance(event, DockerEvent)
		self._event_list.append(event)
		if event.description == DockerEventCategories.DELETE:
			if event.Type == 'image':
				self._del_res(self.__image_dict_by_id, event.id)
			if event.Type == 'container':
				self._del_res(self._container_dict_by_id, event.id)
				_ = self.containers_by_id # refresh container cached list
		elif event.description == DockerEventCategories.CREATE:
			if event.Type == 'container':
				cont = event.container
				if cont and isinstance(cont, DockerContainer):
					run = None
					while not run: # wait for the run object to be added to this dict #sync
						# TODO check for timeout
						run = self._run_dict.pop(cont.Id, None)
					if run and isinstance(run, DockerRun):
						run.container_created(cont)
				self._start(cont)

	# clem 16/03/2016
	def _dispatch_event(self, event):
		assert isinstance(event, DockerEvent)
		cont = event.container
		# TODO add any resources
		if cont and isinstance(cont, DockerContainer):
			if cont.has_event_listener:
				cont.new_event(event)
			else: # if dispatch target exists but don't capture events, then we log it here
				self._event_log(event, ' <UE>')
		else: # if no dispatch target exists, then we log it here
			self._log('Event <%s> had no related containers' % event)

	# clem 16/03/2016
	def _new_event(self, event_literal):
		event = DockerEvent(event_literal, self)
		# process the event (for example removing object from image or container dict)
		self._process_event(event)
		# dispatch the event to the related container
		self._dispatch_event(event)

	# clem 14/03/2016
	def _event_watcher(self):
		"""
		Blocking procedure to receive events
		MUST RUN IN A SEPARATE THREAD
		:rtype: None
		"""
		try:
			self._log('Event watcher started')
			for event in self.cli.events(): # Generator, do no run code in here, but rather in _new_event for non blocking
				# Thread(target=self._new_event, args=(event,)).start() # disabled: due to variable processing time for
																		# various events, they might arrive out of order
				self._new_event(event)
		except Exception as e:
			self._exception_handler(e)

	#
	# CONTAINERS DATA OBJECT MANAGEMENT AND INTERFACE
	#

	# clem 10/03/2016
	@property
	def containers_by_id(self):
		"""
		a dictionary of DockerContainer objects indexed by Id
		internally containers lists is stored in a dict indexed with containers' Ids.
		Each time this property is used the dict is refreshed by calling 'docker containers'
		DockerContainer objects from the cache dict are altered only if container entry changed.
		DockerContainer objects stores an internal md5 of its dictionary so that a modified container (invariant Id)
			will be updated
		similar to images_by_id()
		:rtype: dict(DockerContainer.Id: DockerContainer)
		"""
		try:
			containers = self.cli.containers()
			images = self.images_by_id # caching, removing that will result in a visible slow down
			for e in containers:
				# retrieve or updates the container dict
				cont = self._get_container(e.get('Id'))
				if cont:
					cont.Image = images.get(cont.ImageID)
			return self._container_dict_by_id
		except KeyError as e:
			self._exception_handler(e)
		except NotFound as e:
			self._exception_handler(e, 'ps_by_id: %s' % e)

	# clem 17/03/2016
	def _get_containers_list(self, container_ids):
		"""
		extracts all DockerContainer objects from containers_by_id to return a list of them
		:type container_ids: dict
		:rtype: list(DockerContainer.Id: DockerContainer, )
		"""
		assert isinstance(container_ids, dict)
		self._container_list = list()
		for container in container_ids.itervalues():
			self._container_list.append(container)
		return self._container_list

	# clem 10/03/2016
	@property
	def containers_list(self):
		"""
		extracts all DockerContainer objects from containers_by_id to return a list of them
		:rtype: list(DockerContainer.Id: DockerContainer, )
		"""
		return self._get_containers_list(self.containers_by_id)

	# clem 17/03/2016
	def _get_containers_by_name(self, container_ids):
		"""
		a dictionary of DockerContainer objects indexed by Name[0]
		similar to ps_by_id, except here the DockerContainer objects are referenced by their first Names
		DockerContainer object are referenced from the other dict and thus not modified nor copied.
		:type container_ids: dict
		:rtype: dict(DockerContainer.Name: DockerContainer)
		"""
		assert isinstance(container_ids, dict)
		self._container_dict_by_name = dict()
		for container in container_ids.itervalues():
			self._container_dict_by_name[container.name] = container
		return self._container_dict_by_name

	# clem 10/03/2016
	@property
	def containers_by_name(self):
		"""
		a dictionary of DockerContainer objects indexed by Name[0]
		similar to ps_by_id, except here the DockerContainer objects are referenced by their first Names
		DockerContainer object are referenced from the other dict and thus not modified nor copied.
		:rtype: dict(DockerContainer.Name: DockerContainer)
		"""
		return self._get_containers_by_name(self.containers_by_id)

	# clem 10/03/2016
	def ps(self):
		pass

	#
	# IMAGES DATA OBJECT MANAGEMENT AND INTERFACE
	#

	# clem 09/03/2016
	@property
	def images_by_id(self):
		"""
		a dictionary of DockerImage objects indexed by Id
		internally images lists is stored in a dict indexed with images' Ids.
		Each time this property is used the dict is refreshed by calling 'docker images'
		DockerImage objects from the cache dict are altered only if image entry changed.
		DockerImage objects stores an internal md5 of its dictionary so that a modified image (invariant Id) will be
			updated
		similar to ps_by_id()
		:rtype: dict(DockerImage.Id: DockerImage)
		"""
		try:
			images = self.cli.images()
			for e in images:
				img = DockerImage(e)
				if img.Id not in self.__image_dict_by_id: # or self.__image_dict_by_id[img.Id].sig != img.sig:
					with self._data_mutex: # updates the image dict
						self.__image_dict_by_id[img.Id] = DockerImage(e)
			return self.__image_dict_by_id
		except Exception as e:
			self._exception_handler(e)

	# clem 17/03/2016
	def _get_image_list(self, image_ids):
		"""
		extracts all DockerImage objects from images_by_id to return a list of them
		:type image_ids: dict
		:rtype: list(DockerImage.Id: DockerImage, )
		"""
		assert isinstance(image_ids, dict)
		self._images_list = list()
		for image in image_ids.itervalues():
			self._images_list.append(image)
		return self._images_list

	# clem 09/03/2016
	@property
	def images_list(self):
		"""
		extracts all DockerImage objects from images_by_id to return a list of them
		:rtype: list(DockerImage.Id: DockerImage, )
		"""
		return self._get_image_list(self.images_by_id)

	# clem 17/03/2016
	def _get_images_by_repo_tag(self, image_ids):
		"""
		a dictionary of DockerImage objects indexed by RepoTag[0]
		similar to images_by_id, except here the DockerImage objects are referenced by their first RepoTag
		DockerImage object are referenced from the other dict and thus not modified nor copied.
		:type image_ids: dict
		:rtype: dict(DockerImage.tag: DockerImage)
		"""
		assert isinstance(image_ids, dict)
		self.__image_dict_by_tag = dict()
		for image in image_ids.itervalues():
			self.__image_dict_by_tag[image.full_name] = image

		return self.__image_dict_by_tag

	# clem 09/03/2016
	@property
	def images_by_repo_tag(self):
		"""
		a dictionary of DockerImage objects indexed by RepoTag[0]
		similar to images_by_id, except here the DockerImage objects are referenced by their first RepoTag
		DockerImage object are referenced from the other dict and thus not modified nor copied.
		:rtype: dict(DockerImage.tag: DockerImage)
		"""
		return self._get_images_by_repo_tag(self.images_by_id)

	# clem 09/03/2016
	@property
	def images_tree(self):
		imgs = self.images_by_repo_tag
		self.__image_tree = dict()
		for name, img in imgs.iteritems():
			assert isinstance(img, DockerImage)
			if img.repo_name not in self.__image_tree:
				self.__image_tree[img.repo_name] = dict()
			repo = self.__image_tree[img.repo_name]
			if img.repo_name not in repo:
				repo[img.name] = dict()
			repo[img.name][img.tag] = imgs[name]

		return self.__image_tree

	# clem 09/03/2016
	def show_repo_tree(self):
		pretty_print_dict_tree(self.images_tree)
