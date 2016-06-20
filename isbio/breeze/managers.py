from __builtin__ import property

from django.db.models.query import QuerySet as __original_QS
from django.db.models import Manager
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
import django.db.models.query_utils
from django.conf import settings
from django.http import Http404
from breeze.b_exceptions import InvalidArguments
from comp import translate

org_Q = django.db.models.query_utils.Q


# clem 20/06/2016
class CustomManager(Manager):
	context_user = None
	context_obj = None

	def __init__(self):
		super(CustomManager, self).__init__()

	# clem 20/06/2016
	def safe_get(self, *_, **kwargs):
		has_id = 'id' in kwargs.keys()
		has_pk = 'pk' in kwargs.keys()
		if not (has_id or has_pk):
			raise InvalidArguments
		try:
			the_key = kwargs.pop('id' if has_id else 'pk')
			# self.context_obj = self.get(id=the_key) if has_id else self.get(pk=the_key)
			self.context_obj = super(CustomManager, self).get(id=the_key) if has_id else \
				super(CustomManager, self).get(pk=the_key)
			return self.context_obj
		except ObjectDoesNotExist:
			raise ObjectDoesNotExist

	# clem 20/06/2016
	def user_get(self, *args, **kwargs):
		if 'user' not in kwargs.keys():
			raise InvalidArguments
		self.context_user = kwargs.pop('user')
		return self.safe_get(*args, **kwargs)

	# clem 20/06/2016
	@staticmethod
	def admin_override_param(user):
		return settings.SU_ACCESS_OVERRIDE and user.is_superuser

	# clem 20/06/2016
	@staticmethod
	def get_author_param(obj):
		auth = None
		if hasattr(obj, 'author'):
			auth = obj.author
		elif hasattr(obj, 'juser'): # Jobs
			auth = obj.juser
		elif hasattr(obj, '_author'):
			auth = obj._author
		return auth

	# clem 20/06/2016
	@classmethod
	def has_full_access_param(cls, obj, user):
		author = cls.get_author_param(obj) # author/owner of the object
		return author == user or cls.admin_override_param(user)

	# clem 20/06/2016
	@classmethod
	def has_read_access_param(cls, obj, user):
		return cls.has_full_access_param(obj, user) or \
			(hasattr(obj, 'shared') and user in obj.shared.all())

	@property
	def has_context(self):
		return self.context_obj and self.context_user

	###
	#  Old methods, now property, wrapper of the real methods
	###

	# clem 19/02/2016
	@property
	def admin_override(self):
		assert self.has_context
		return self.__class__.admin_override_param(self.context_user)

	# clem 19/02/2016
	@property
	def get_author(self):
		assert self.has_context
		return self.__class__.get_author_param(self.context_obj)

	# clem 19/02/2016
	@property
	def has_full_access(self):
		assert self.has_context
		return self.has_full_access_param(self.context_obj, self.context_user)

	# clem 19/02/2016
	@property
	def has_read_access(self):
		assert self.has_context
		return self.has_read_access_param(self.context_obj, self.context_user)


class Q(django.db.models.query_utils.Q):
	def __init__(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		super(Q, self).__init__(*args, **kwargs)


class QuerySet(__original_QS):
	def __init__(self, *args, **kwargs):
		super(QuerySet, self).__init__(*args, **kwargs)
	
	def _filter_or_exclude(self, negate, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		return super(QuerySet, self)._filter_or_exclude(negate, *args, **kwargs)

	def filter(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		return super(QuerySet, self).filter(*args, **kwargs)

	def annotate(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		return super(QuerySet, self).annotate(*args, **kwargs)

	def get(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		return super(QuerySet, self).get(*args, **kwargs)

	def exclude(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		return super(QuerySet, self).exclude(*args, **kwargs)

	def order_by(self, *field_names):
		field_names, _ = translate(field_names, dict())
		return super(QuerySet, self).order_by(*field_names)

	##
	# Request filtering
	##
	def owned(self, user):
		"""
		Returns ALL the jobs that ARE scheduled
		"""
		return self.filter(_author__exact=user)

	def get_scheduled(self):
		"""
		Returns ALL the jobs that ARE scheduled
		"""
		from breeze.models import JobStat
		return self.filter(_status=JobStat.SCHEDULED).filter(_author__id__gt=0)

	def get_not_scheduled(self):
		"""
		Returns ALL the jobs that are NOT scheduled
		"""
		from breeze.models import JobStat
		return self.exclude(_status=JobStat.SCHEDULED).exclude(_breeze_stat=JobStat.SCHEDULED).filter(
			_author__id__gt=0)

	def get_incomplete(self):
		"""
		Returns all the jobs that are NOT completed, excluding Scheduled jobs
		That also includes active job that are not running yet
		"""
		from breeze.models import JobStat
		return self.get_not_scheduled().exclude(_breeze_stat=JobStat.DONE) | self.get_aborting()

	def get_run_wait(self):
		"""
		Returns all the jobs that are waiting to be run
		"""
		from breeze.models import JobStat
		return self.get_not_scheduled().filter(_breeze_stat=JobStat.RUN_WAIT)

	def get_active(self):
		"""
		Returns all the jobs that are currently active
		(this include INIT, PREPARE_RUN, RUNNING, QUEUED_ACTIVE, ABORT but not RUN_WAIT nor SCHEDULED)
		This is the set you want to refresh periodically
		"""
		from breeze.models import JobStat
		return self.get_not_scheduled().exclude(_breeze_stat=JobStat.RUN_WAIT).exclude(_breeze_stat=JobStat.DONE) | \
			self.get_aborting()

	def get_running(self):
		"""
		Returns all the jobs that are currently active and actually running
		(does NOT include INIT, PREPARE_RUN, QUEUED_ACTIVE, etc)
		"""
		from breeze.models import JobStat
		return self.get_not_scheduled().filter(_breeze_stat=JobStat.RUNNING, _status=JobStat.RUNNING) | \
			self.get_aborting()

	def get_history(self):
		"""
		Returns all the jobs history
		includes succeeded, failed and aborted ones
		"""
		from breeze.models import JobStat
		return self.get_not_scheduled().filter(_breeze_stat=JobStat.DONE)

	def get_done(self, include_failed=True, include_aborted=True):
		"""
		Returns all the jobs that are done,
		including or not the failed and aborted ones
		"""
		from breeze.models import JobStat

		r = self.get_history()

		if not include_failed:
			r = r.exclude(_status=JobStat.FAILED)
		if not include_aborted:
			r = r.exclude(_status=JobStat.ABORTED)

		return r

	def get_failed(self):
		"""
		Returns all the jobs history
		includes succeeded, failed and aborted ones
		"""
		from breeze.models import JobStat
		return self.get_history().filter(_status=JobStat.FAILED)

	def get_aborting(self):
		"""
		Returns the jobs marked for abortion
		"""
		from breeze.models import JobStat

		return self.filter(_breeze_stat=JobStat.ABORT)

	def get_aborted(self):
		"""
		Returns all the jobs history
		includes succeeded, failed and aborted ones
		"""
		from breeze.models import JobStat

		return self.get_history().filter(Q(_status=JobStat.ABORTED) or Q(_status=JobStat.ABORT))


class WorkersManager(CustomManager):
	"""
	Overrides change the name of the fields parameters in a QuerySet
	this allow legacy backward compatibility with the new Runnable class
	while not needing to change all the query everywhere in the code.
	The Runnable allows to use unified name for fields, while keeping the old database models #TODO migrate
	From now on, every request to Report and Jobs should be done trough included request filters
	"""
	def __init__(self, inst_type=None):
		self.inst_type = inst_type
		super(WorkersManager, self).__init__()

	##
	# Overrides
	##
	def get_query_set(self):
		"""
		:rtype: QuerySet
		"""
		return QuerySet(self.model, using=self._db)

	def filter(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		# return super(WorkersManager, self).filter(*args, **kwargs)
		return self.get_query_set().filter(*args, **kwargs)

	def annotate(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		return super(WorkersManager, self).annotate(*args, **kwargs)

	def get(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		a = super(WorkersManager, self).get(*args, **kwargs)
		if self.inst_type:
			assert isinstance(a, self.inst_type)
		return a

	def exclude(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		return super(WorkersManager, self).exclude(*args, **kwargs)

	def order_by(self, *args, **kwargs):
		args, kwargs = translate(args, kwargs)
		return super(WorkersManager, self).order_by(*args, **kwargs)

	def all(self):
		return self.get_query_set()

	@property
	def f(self):
		return self.all()

	def owner_get(self, request, obj_id, fail_ex=Http404):
		"""
		Ensure that job/report designated by obj_id exists or fail with 404
		Ensure that current user is OWNER of said object (or admin) or fail with 403
		implements admin bypass if settings. is True

		:param request: Django Http request object
		:type request: django.http.HttpRequest
		:param obj_id: table pk of the requested object
		:type obj_id: int
		:param fail_ex: an exception to raise in case of failure
		:type fail_ex: Exception
		:return: requested object instance
		:rtype: type(self.model)
		"""
		try:
			obj = self.get(id=obj_id)
			# Enforce access rights
			# if user != request.user:
			if not has_full_access(obj, request.user):
				raise PermissionDenied
			return obj
		except ObjectDoesNotExist:
			raise fail_ex()

	def read_get(self, request, obj_id, fail_ex=Http404):
		"""
		Ensure that job/report designated by obj_id exists or fail with 404
		Ensure that current user has read access to said object or fail with 403

		:param request: Django Http request object
		:type request: django.http.HttpRequest
		:param obj_id: table pk of the requested object
		:type obj_id: int
		:param fail_ex: an exception to raise in case of failure
		:type fail_ex: Exception
		:return: requested object instance
		:rtype: type(self.model)
		"""
		try:
			obj = self.get(id=obj_id)
			# Enforce access rights
			# if user != request.user:
			if not has_read_access(obj, request.user):
				raise PermissionDenied
			return obj
		except ObjectDoesNotExist:
			raise fail_ex()


# TODO extend to all objects
class ObjectsWithAuth(CustomManager):
	def __init__(self):
		super(ObjectsWithAuth, self).__init__()
	
	def secure_get(self, *_, **kwargs):
		# get the object if it exists
		self.user_get(**kwargs)

		# Enforce user access restrictions
		if not self.has_full_access:
			if self.has_read_access:
				self.context_obj.prop_read_only = True
				return self.context_obj
			raise PermissionDenied
		return self.context_obj


# clem 19/04/2016
class ProjectManager(CustomManager):
	def __init__(self):
		super(ProjectManager, self).__init__()

	def available(self, user):
		""" a list of projects available to the specified user

		:type user:
		:rtype: list
		"""
		return super(ProjectManager, self).exclude(
			~org_Q(author__exact=user) & org_Q(collaborative=False)).order_by("name")
