from docker import Client
from docker.errors import NotFound
from .utils import get_md5, pretty_print_dict_tree


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

	def __repr__(self):
		return '<DockerImage %s>' % self.RepoTags[0]


# clem 08/03/2016
class DockerClient:
	DEV = False
	_raw_cli = None
	_images = list()
	__image_dict_by_id = dict()
	__image_tree = dict()

	def __init__(self):
		self._raw_cli = Client(base_url='tcp://127.0.0.1:4243')

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

	# clem 09/03/2016
	def run(self):
		# Create the container
		try:
			out = self.cli.create_container('fimm/r-light:op')
			container_id = out['Id']
			self.cli.start(container_id)

		except NotFound as e:
			raise NotFound(e)

		# If the status code is 404, it means the image doesn't exist:

		# Try to pull it.
		# Then, retry to create the container.
		# Start the container.

		# If you are not in detached mode:

		# Attach to the container, using logs=1 (to have stdout and stderr from the container's start) and stream=1

		# If in detached mode or only stdin is attached, display the container's id.
		pass

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
		:rtype: list(DockerImage)
		"""
		self._images = list()
		ids = self.images_by_id
		for e in ids:
			self._images.append(ids[e])
		return self._images

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
		:rtype: dict(DockerImage)
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
		:rtype: dict(DockerImage)
		"""
		# assert isinstance(self.cli, Client)
		lbl_dict = dict()
		ids = self.images_by_id
		for e in ids:
			img = ids[e]
			lbl_dict[img.RepoTags[0]] = img

		return lbl_dict


def docker():
	cli = DockerClient()
	return cli
