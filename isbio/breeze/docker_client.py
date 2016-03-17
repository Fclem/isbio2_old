from docker import Client
from docker.errors import NotFound, APIError
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
	container_id = ''

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
	Image = DockerImage
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
				self.Image = a_dict.get('Image')
		else:
			self.Image = a_dict.get('Image')
		# _ = self.sig
		self.register_event_listener(event_callback)

	# @staticmethod # TODO del
	# def generate(run, some_id):
	# 	return DockerContainer({'Id': some_id}, event_callback=run.event_listener)

	# clem 15/03/2016
	def update(self, a_dict):
		assert isinstance(a_dict, dict)
		self.__dict__.update(a_dict)

	# FIXME deprecated
	def _get_sig(self):
		new_dict = self.__dict__
		if '_sig' in new_dict:
			new_dict.pop('_sig')
			new_dict.pop('_event_list')
			new_dict.pop('_event_listener')
		return get_md5(str(new_dict))

	# clem 15/03/2016
	def register_event_listener(self, listener):
		# if listener and callable(listener):
		if not self._event_listener:
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
					self._log = self.__client.cli.logs(self.Id) # FIXME this might be the issue
			self._event_listener(event)
			# Thread(target=self._event_listener, args=(event,)).start()

	# clem 15/03/2016
	@property
	def logs(self):
		return self._log

	@property # FIXME deprecated
	def sig(self):
		if not self._sig:
			self._sig = self._get_sig()
		return self._sig

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

	def _get_container(self): # TODO rewrite, change logic
		if not self._container or not self._container.name: # if not a container or container has no name, refresh
			# cid = self.res_id
			if self.Type == 'container':
				try:
					return self._attach_container(self.res_id)
				except NotFound:
					# self.__client.log('Related container cannot be found')
					# return self.res_id
					pass
			elif 'Attributes' in self.Actor and 'container' in self.Actor['Attributes']:
				return self._attach_container(self.Actor['Attributes']['container'])
			# self.__client.log('Event was not related to a container')
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
	__image_tree = dict()
	__watcher = None
	_container_list = list()
	_container_dict_by_id = dict()
	_event_list = list()

	def __init__(self, repo, daemon_url, run=None): # TODO change the run passing
		assert isinstance(repo, DockerRepo) and (not run or isinstance(run, DockerRun)) and \
			isinstance(daemon_url, basestring)
		self.repo = repo
		self.default_run = run
		self._daemon_url = daemon_url
		self._raw_cli = Client(base_url=daemon_url)
		self._console_mutex = Lock()
		self._data_mutex = Lock()
		self.start_event_watcher()
		self.login()

	# clem 14/03/2016
	def __cleanup(self):
		if self.__watcher:
			self.force_log('watcher terminated')

	# clem 14/03/2016
	def __del__(self):
		self.__cleanup()

	# clem 14/03/2016
	def __delete__(self, _):
		self.__cleanup()

	# clem 14/03/2016
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.__cleanup()

	# clem 10/03/2016
	def log(self, obj, force_print=False, sup_text=''):
		if self.DEBUG or force_print:
			if type(obj) is dict:
				with self._console_mutex:
					pretty_print_dict_tree(obj)
			else:
				with self._console_mutex:
					print str(obj) + str(sup_text)
		# TODO log

	# clem 10/03/2016
	def json_log(self, obj, force_print=False):
		self.log(self._json_parse(obj), force_print)

	# clem 10/03/2016
	def force_log(self, obj, sup_text=''):
		self.log(obj, True, sup_text)

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
	def event_log(self, obj, sup_text=''):
		self.force_log(self._json_parse(obj), str(sup_text))

	# clem 10/03/2016
	def login(self):
		if self.repo:
			try:
				result = self.cli.login(self.repo.login, self.repo.pwd, self.repo.email, self.repo.url)
				self.log(result)
				return 'username' in result or result[u'Status'] == u'Login Succeeded'
			except APIError as e:
				self.log(e)
			except Exception as e:
				self.force_log('Unable to connect : %s' % e)
		return False

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
			if image_descriptor in self.images_by_id.keys():
				return self.images_by_id[image_descriptor]
			elif image_descriptor in self.images_by_repo_tag.keys():
				return self.images_by_repo_tag[image_descriptor]
		return None

	# clem 17/03/2016
	def _inspect_container(self, container_id):
		"""
		Get all the refreshed raw information about the container
		:type container_id: basestring
		:rtype: str
		"""
		return self.cli.inspect_container(container_id)

	# clem 16/03/2016
	def rmi(self, image, force=False):
		try:
			return self.cli.remove_image(str(image), force)
		except Exception as e:
			self.force_log(e)
			if self.RAISE_ERR:
				raise e
		return None

	# clem 16/03/2016
	def _term_stream(self, a_dict):
		import sys

		for each in a_dict:
			sys.stdout.write('%s\n' % a_dict[each])
			sys.stdout.flush()  # As suggested by Rom Ruben

	# clem 16/03/2016
	def pull(self, image_name, tag):
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
				self.log(str(obj['error']))
				return None
			self.log(to_log)
			self._term_stream(a_dict)
			count += 1
		return True

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
			self.log('Unable to find image \'%s\' locally' % image_name)
			return self.pull(img.repo_and_name, img.tag)
		return True

	# clem 09/03/2016
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

		container_id = ''
		# Create the container
		try:
			# get the volume config
			a_dict = run.config_dict()
			if a_dict:
				# apply volume config
				vol = run.config_dict().keys()
				vol_config = self.cli.create_host_config(binds=run.config_dict())
				self.log('docker run %s %s -v %s' % (image_name, run.cmd, run.volumes))
				# container_id = self.cli.create_container(image_name, run.cmd, volumes=vol, host_config=vol_config)['Id']
				# container = DockerContainer.generate(run, self.cli.create_container(image_name, run.cmd,
				# 	volumes=vol, host_config=vol_config)['Id'])
				container = self.get_container(self.cli.create_container(image_name, run.cmd, volumes=vol,
																			host_config=vol_config)['Id'])
			else: # no volume config
				self.log('docker run %s %s' % (image_name, run.cmd))
				# container_id = self.cli.create_container(image_name, run.cmd)['Id']
				# container = DockerContainer.generate(run, self.cli.create_container(image_name, run.cmd)['Id'])
				container = self.get_container(self.cli.create_container(image_name, run.cmd)['Id'])

			if run.event_listener and callable(run.event_listener):
				container.register_event_listener(run.event_listener)

			self.log('run-id %s' % hex(id(container)))
			self.log('run-listener %s' % container.has_event_listener)

			# container =  self.get_container(container_id)
			# container = self.inspect_container(container.Id)
			if container:
				# if run.event_listener and callable(run.event_listener):
				# self.log('registering event listener')
				# with self._data_mutex:
				# 	container.register_event_listener(run.event_listener)
				# self.log('Event listener registered !')
				# else:
					# container.register_event_listener(self.event_log)
				self.log('Created %s : %s' % (container.name, container.Id))

				self.cli.start(container.Id)
				return container
		except NotFound as e:
			self.force_log('run: ' + str(e))
			if self.RAISE_ERR:
				raise e
		except APIError as e:
			self.log('Container run failed : %s' % e)
			out_log = self.cli.logs(container_id)
			if out_log:
				# self.log(out_log)
				self.log('Container run log :\n%s' % pretty_print_dict_tree(out_log, get_output=True))
			if self.RAISE_ERR:
				raise e
		# If you are not in detached mode:

		# Attach to the container, using logs=1 (to have stdout and stderr from the container's start) and stream=1

		# If in detached mode or only stdin is attached, display the container's id.

	#
	# EVENTS
	#

	# clem 14/03/2016
	def start_event_watcher(self):
		if not self.__watcher:
			self.__watcher = Thread(target=self._event_watcher)
			self.log('starting event watcher as Thread')
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
			self.force_log(e)
			if self.RAISE_ERR:
				raise e

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

	# clem 16/03/2016
	def _dispatch_event(self, event):
		assert isinstance(event, DockerEvent)
		cont = event.container
		self.log('event-id %s' % hex(id(cont)))
		self.log('event-listener %s' % cont.has_event_listener)
		# TODO add any resources
		if cont and isinstance(cont, DockerContainer): # FIXME
			if cont.has_event_listener:
				cont.new_event(event)
				return
			# self.log('ev <%s> cont.newev:%s' % (event, managed))
		else:
			self.log('NO CONT for <%s>' % event)
		# if no dispatch target exists, or target don't capture events, then we log it here
		self.event_log(event, ' <UE>') # FIXME
		# self.event_log('NO DISPATCH, not managed')

	# clem 16/03/2016
	def _new_event(self, event_literal):
		event = DockerEvent(event_literal, self)
		# process the event (for example removing object from image or container dict)
		self._process_event(event)
		# dispatch the event to the related container TODO dispatch to any available resource
		self._dispatch_event(event)

	# clem 14/03/2016
	def _event_watcher(self):
		"""
		Blocking procedure to receive events
		MUST RUN IN A SEPARATE THREAD
		:rtype: None
		"""
		self.log('Event watcher started')
		for event in self.cli.events(): # Generator, do no run code in here, but rather in _new_event for non blocking
			# Thread(target=self._new_event, args=(event,)).start()
			self._new_event(event)

	#
	# CONTAINERS
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
		# updates the container dict
		containers = self.cli.containers()
		images = self.images_by_id # caching, removing that will result in a visible slow down
		for e in containers:
			try:
				cont = self._get_container(e['Id'])
				if cont:
					cont.Image = images[cont.ImageID]
			except KeyError:
				pass
			except NotFound as e:
				self.force_log('ps_by_id: %s' % e)
		return self._container_dict_by_id

	# clem 10/03/2016
	@property
	def containers_list(self):
		"""
		extracts all DockerContainer objects from containers_by_id to return a list of them
		:rtype: list(DockerContainer.Id: DockerContainer, )
		"""
		self._container_list = list()
		ids = self.containers_by_id
		for e in ids:
			self._container_list.append(ids[e])
		return self._container_list

	# clem 10/03/2016
	@property
	def containers_by_name(self):
		"""
		a dictionary of DockerContainer objects indexed by Name[0]
		similar to ps_by_id, except here the DockerContainer objects are referenced by their first Names
		DockerContainer object are referenced from the other dict and thus not modified nor copied.
		:rtype: dict(DockerContainer.Name: DockerContainer)
		"""
		lbl_dict = dict()
		ids = self.containers_by_id
		for e in ids:
			cont = ids[e]
			lbl_dict[cont.Names[0]] = cont

		return lbl_dict

	# clem 10/03/2016
	def ps(self):
		pass

	#
	# IMAGES
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
		# updates the image dict
		imgs = self.cli.images()
		for e in imgs:
			img = DockerImage(e)
			if img.Id not in self.__image_dict_by_id or self.__image_dict_by_id[img.Id].sig != img.sig:
				with self._data_mutex:
					self.__image_dict_by_id[img.Id] = DockerImage(e)
		return self.__image_dict_by_id

	# clem 09/03/2016
	@property
	def images_list(self):
		"""
		extracts all DockerImage objects from images_by_id to return a list of them
		:rtype: list(DockerImage.Id: DockerImage, )
		"""
		self._images_list = list()
		ids = self.images_by_id
		for e in ids:
			self._images_list.append(ids[e])
		return self._images_list

	# clem 09/03/2016
	@property
	def images_by_repo_tag(self):
		"""
		a dictionary of DockerImage objects indexed by RepoTag[0]
		similar to images_by_id, except here the DockerImage objects are referenced by their first RepoTag
		DockerImage object are referenced from the other dict and thus not modified nor copied.
		:rtype: dict(DockerImage.tag: DockerImage)
		"""
		lbl_dict = dict()
		ids = self.images_by_id
		for e in ids:
			img = ids[e]
			lbl_dict[img.RepoTags[0]] = img

		return lbl_dict

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
