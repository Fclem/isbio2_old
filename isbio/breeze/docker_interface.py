from docker import Client
from docker.errors import NotFound, APIError
from .utils import get_md5, pretty_print_dict_tree
from threading import Thread, Lock
# from multiprocessing import Process, Lock

PWD = '.VaQOap_U"@%+D.YQZ[%\')7^}.#Heh?Dq'
AZURE_REMOTE_URL = 'tcp://127.0.0.1:4243'


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

	# clem 14/03/2016
	def __str__(self):
		return '%s:%s:%s' % (self.path, self.mount_point, self.mode)


# clem 10/03/2016
class DockerRun:
	image = ''
	cmd = ''
	_volumes = list()

	# clem 11/03/2016
	@property
	def volumes(self):
		return self._volumes

	# _check_volumes deleted 14/03/2016 (last git commit 32844a2)
	# _check_if_volume_exists deleted 14/03/2016 (last git commit 32844a2)
	# _volume_exists deleted 14/03/2016 (last git commit 32844a2)

	def __init__(self, image, cmd='', volumes=None):
		assert isinstance(image, (DockerImage, basestring)) and isinstance(cmd, basestring) and\
			(volumes is None or isinstance(volumes, (list, DockerVolume)))
		self.image = image
		self.cmd = cmd
		self._volumes = volumes

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

	# clem 10/03/2016
	@property
	def tag(self):
		if type(self.RepoTags) is list and len(self.RepoTags) > 0:
			return str(self.RepoTags[0])
		else:
			return str(self.RepoTags)

	def __repr__(self):
		return '<DockerImage %s>' % self.tag

	# clem 10/03/2016
	def __str__(self):
		return str(self.tag)


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
	_event_list = list()
	_event_listener = None

	def __init__(self, a_dict, client=None, event_callback=None):
		assert isinstance(a_dict, dict) and (not client or isinstance(client, DockerClient))
		self.__dict__.update(a_dict)
		if client: # if we got a client in argument, we chain this container to its DockerImage object
			try:
				self.Image = client.images_by_id[self.ImageID]
			except KeyError:
				self.Image = a_dict['Image']
		else:
			self.Image = a_dict['Image']
		# _ = self.sig
		self.register_event_listener(event_callback)

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
		if listener and callable(listener):
			self._event_listener = listener

	# clem 15/03/2016
	def new_event(self, event):
		self._event_list.append(event)
		if self._event_listener and callable(self._event_listener):
			self._event_listener(event)

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

	def __str__(self):
		return self.name if self.name else self.Id

	def __repr__(self):
		return '<DockerContainer %s>' % str(self)


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

	# clem 14/03/2016
	def _get_container(self):
		if not self._container or not self._container.name: # if not a container or container has no name, refresh
			self._container = self.__client.get_container(self.container_id)

	# clem 14/03/2016
	@property
	def container(self):
		self._get_container()
		return self._container

	@property
	def container_id(self):
		if self.id:
			return self.id
		else:
			return self.Actor['Attributes']['container']

	@property
	def dt(self):
		from datetime import datetime
		secs = float(self.timeNano / 1e9)
		return datetime.fromtimestamp(secs)

	@property
	def dt_formatted(self):
		return self.dt.strftime('%Y-%m-%dT%Hh%M:%S.%f')

	@property
	def date_formatted(self):
		return self.dt.strftime('%Y-%m-%d')

	@property
	def time_formatted(self):
		return self.dt.strftime('%Hh%M:%S.%f')

	def __str__(self):
		txt = 's:%s' % self.status if self.status else 'A:%s' % self.Action
		# return '%s [%s] %s' % (str(repr(self.container)), self.timeNano, txt)
		# return '%s [%s] %s' % (self.container, str(self.timeNano)[:-5], txt)
		# t = float(self.timeNano) / 1e6
		# return '%s [%s] %s' % (self.container, '{:.1f}'.format(t), txt)
		return '%s [%s] %s' % (self.container, self.time_formatted, txt)

	def __repr__(self):
		txt = 's:%s' % self.status if self.status else 'A:%s' % self.Action
		return '<DockerEvent [%s] %s>' % (self.timeNano, txt)


# clem 08/03/2016
class DockerClient:
	RAISE_ERR = False
	DEV = False
	DEBUG = True
	repo = None
	default_run = None
	_raw_cli = None
	_console_mutex = None # use to ensure exclusive access to console

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
		self.start_event_watcher()
		self.login()

	# clem 14/03/2016
	def __cleanup(self):
		if self.__watcher:
			# self.__watcher.
			# self.__watcher.terminate()
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
	def log(self, obj, force_print=False):
		if self.DEBUG or force_print:
			if type(obj) is dict:
				with self._console_mutex:
					pretty_print_dict_tree(obj)
			else:
				with self._console_mutex:
					print str(obj)
		# TODO log

	# clem 10/03/2016
	def force_log(self, obj):
		self.log(obj, True)

	# clem 14/03/2016
	def event_log(self, obj):
		if type(obj) is str:
			import json
			obj = json.loads(obj)
		self.force_log(obj)

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

	# clem 14/03/2016
	def get_container(self, container_id):
		"""
		Get the cached container, and if not found try to refresh the cache for this entry only
		:type container_id: str
		:rtype: DockerContainer
		"""
		if container_id in self._container_dict_by_id.keys():
			return self._container_dict_by_id[container_id]
		else:
			return self.inspect_container(container_id)

	# clem 14/03/2016
	def inspect_container(self, container_id):
		"""
		Get all the refreshed information about the container
		:type container_id: str
		:rtype: DockerContainer
		"""
		if container_id in self._container_dict_by_id.keys():
			# refresh
			info = self.cli.inspect_container(container_id)
			self._container_dict_by_id[container_id].update(info)
			return self._container_dict_by_id[container_id]
		else:
			# create the container from the info we get from inspect_container
			cont = DockerContainer(self.cli.inspect_container(container_id))
			self._container_dict_by_id[cont.Id] = cont
		return self._container_dict_by_id[cont.Id]

	# clem 09/03/2016
	def _run(self, run):
		"""
		TBD
		:type run: DockerRun
		:rtype: DockerContainer
		"""
		assert isinstance(run, DockerRun)

		# TODO check if connected to repo
		image_name = str(run.image)
		if not (type(run.image) is DockerImage or run.image in self.images_by_repo_tag):
			# image not found, let's try to pull it
			pass # TODO

		container_id = ''
		# Create the container
		try:
			# get the volume config
			a_dict = run.config_dict()
			if a_dict:
				# apply volume config
				vol = run.config_dict().keys()
				vol_config = self.cli.create_host_config(binds=run.config_dict())
				# if vol:
				self.log('docker run %s %s -v %s' % (image_name, run.cmd, run.volumes))
				container_id = self.cli.create_container(image_name, run.cmd, volumes=vol, host_config=vol_config)['Id']
			else: # no volume config
				self.log('docker run %s %s' % (image_name, run.cmd))
				container_id = self.cli.create_container(image_name, run.cmd)['Id']

			container = self.get_container(container_id)
			container.register_event_listener(self.event_log)
			self.log('Created %s : %s' % (container.name, container.Id))

			self.cli.start(container.Id)
			return container
		except APIError as e:
			self.log('Container run failed : %s' % e)
			out_log = self.cli.logs(container_id)
			if out_log:
				# self.log(out_log)
				self.log('Container run log :\n%s' % pretty_print_dict_tree(out_log, get_output=True))
			if self.RAISE_ERR:
				raise e
		except NotFound as e:
			raise NotFound(e)
		# If you are not in detached mode:

		# Attach to the container, using logs=1 (to have stdout and stderr from the container's start) and stream=1

		# If in detached mode or only stdin is attached, display the container's id.

	# clem 14/03/2016
	def start_event_watcher(self):
		if not self.__watcher:
			# self.__watcher = Process(target=self._event_watcher)
			self.__watcher = Thread(target=self._event_watcher)
			self.__watcher.start()
			# self.log('watcher started PID %s' % self.__watcher.id)
			self.log('watcher started as Thread')

	# clem 14/03/2016
	def _event_watcher(self):
		for event in self.cli.events():
			event = DockerEvent(event, self)
			self._event_list.append(event)
			# self.event_log(event)
			_ = self.ps_by_id
			# dispatch the event to the related container
			cont = event.container
			if cont:
				cont.new_event(event)

	# clem 10/03/2016
	@property
	def ps_by_id(self):
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
			# cont = DockerContainer(e)
			cont = self.get_container(e['Id'])
			try:
				cont.Image = images[cont.ImageID]
			except KeyError:
				pass
			# if cont.Id not in self._container_dict_by_id or self._container_dict_by_id[cont.Id].sig != cont.sig:
			# 	self._container_dict_by_id[cont.Id] = cont
		return self._container_dict_by_id

	# clem 10/03/2016
	@property
	def ps_list(self):
		"""
		extracts all DockerContainer objects from containers_by_id to return a list of them
		:rtype: list(DockerContainer.Id: DockerContainer, )
		"""
		self._container_list = list()
		ids = self.ps_by_id
		for e in ids:
			self._container_list.append(ids[e])
		return self._container_list

	# clem 10/03/2016
	def show_ps(self):
		pass

	# clem 10/03/2016
	@property
	def ps_by_name(self):
		"""
		a dictionary of DockerContainer objects indexed by Name[0]
		similar to ps_by_id, except here the DockerContainer objects are referenced by their first Names
		DockerContainer object are referenced from the other dict and thus not modified nor copied.
		:rtype: dict(DockerContainer.Name: DockerContainer)
		"""
		lbl_dict = dict()
		ids = self.ps_by_id
		for e in ids:
			cont = ids[e]
			lbl_dict[cont.Names[0]] = cont

		return lbl_dict

	# clem 09/03/2016
	@property
	def images_tree(self):
		imgs = self.images_by_repo_tag
		self.__image_tree = dict()
		for e in imgs:
			if '/' in e:
				repo_name, rest = e.split('/', 1)
			else:
				repo_name, rest = 'library', e

			if ':' in rest:
				img_name, tag = rest.split(':', 1)
			else:
				img_name, tag = rest, ''

			if repo_name not in self.__image_tree:
				self.__image_tree[repo_name] = dict()
			repo = self.__image_tree[repo_name]
			if img_name not in repo:
				repo[img_name] = dict()
			repo[img_name][tag] = imgs[e]
		# self.__image_tree[repo_name][img_name][tag] = imgs[e]

		return self.__image_tree

	# clem 09/03/2016
	def show_repo_tree(self):
		pretty_print_dict_tree(self.images_tree)

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
		for e in self.cli.images():
			img = DockerImage(e)
			if img.Id not in self.__image_dict_by_id or self.__image_dict_by_id[img.Id].sig != img.sig:
				self.__image_dict_by_id[img.Id] = DockerImage(e)
		return self.__image_dict_by_id

	# clem 09/03/2016
	@property
	def images_by_repo_tag(self):
		"""
		a dictionary of DockerImage objects indexed by RepoTag[0]
		similar to images_by_id, except here the DockerImage objects are referenced by their first RepoTag
		DockerImage object are referenced from the other dict and thus not modified nor copied.
		:rtype: dict(DockerImage.tag: DockerImage)
		"""
		# assert isinstance(self.cli, Client)
		lbl_dict = dict()
		ids = self.images_by_id
		for e in ids:
			img = ids[e]
			lbl_dict[img.RepoTags[0]] = img

		return lbl_dict


def docker():
	fimm_docker_hub = DockerRepo('fimm', PWD, email='clement.fiere@fimm.fi')
	fimm_test_volume = DockerVolume('/home/breeze/data/', '/breeze', 'rw')
	fimm_test_run = DockerRun('fimm/r-light:op', './run.sh', fimm_test_volume)
	cli = DockerClient(fimm_docker_hub, AZURE_REMOTE_URL, fimm_test_run)
	return cli
