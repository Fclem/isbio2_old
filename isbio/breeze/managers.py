from django.db.models.query import QuerySet as __original_QS
import django.db.models.query_utils


class Trans:
	def __init__(self, *args, **kwargs):
		self._translate(*args, **kwargs)

	translation = {
		'name': '_name', 'jname': '_name',
		'description': '_description', 'jdetails': '_description',
		'author': '_author', 'juser': '_author',
		'type': '_type', 'script': '_type',
		'created': '_created', 'staged': '_created',
		'breeze_stat': '_breeze_stat', 'status': '_status',
		'rexec': '_rexec', 'rexecut': '_rexec',
		'dochtml': '_doc_ml', 'docxml': '_doc_ml',
		'institute': '_institute',
	}

	@staticmethod
	def swap(item):
		a = Trans.has(item)
		if a is not None:
			return a
		return item

	@staticmethod
	def has(item):
		if isinstance(item, str) and item != '':
			text = item
			if text[0] == '-': # for order_by
				text = text[1:]
			if text.endswith('_id'): # for ForeignKeys
				text = text[:-3]
			for key in Trans.translation.keys():
				if text.startswith(key):
					return item.replace(key, Trans.translation[key])
		return None

	def _translate(self, args, kwargs):
		new_arg = list(args)
		for pos, el in enumerate(new_arg):
			new_key = self.has(el)
			if new_key is not None:
				new_arg[pos] = new_key
		new_arg = tuple(new_arg)

		for key in kwargs.keys():
			new_key = self.has(key)
			if new_key is not None:
				kwargs[new_key] = kwargs[key]
				del kwargs[key]
		self.args, self.kwargs = new_arg, kwargs

	def get(self):
		return self.args, self.kwargs


def _translate(args, kwargs):
	return Trans(args, kwargs).get()


class Q(django.db.models.query_utils.Q):
	def __init__(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		super(Q, self).__init__(*args, **kwargs)


class QuerySet(__original_QS):
	def _filter_or_exclude(self, negate, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(QuerySet, self)._filter_or_exclude(negate, *args, **kwargs)

	def filter(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(QuerySet, self).filter(*args, **kwargs)

	def annotate(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(QuerySet, self).annotate(*args, **kwargs)

	def get(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(QuerySet, self).get(*args, **kwargs)

	def exclude(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(QuerySet, self).exclude(*args, **kwargs)

	def order_by(self, *field_names):
		field_names, _ = _translate(field_names, dict())
		return super(QuerySet, self).order_by(*field_names)

#JobStat = breeze.models.JobStat

class WorkersManager(django.db.models.Manager):
	"""
	Overrides change the name of the fields parameters in a QuerySet
	this allow legacy backward compatibility with the new Runnable class
	while not needing to change all the query everywhere in the code.
	The Runnable allows to use unified name for fields, while keeping the old database models #TODO migrate
	From now on, every request to Report and Jobs should be done trough included request filters
	"""
	##
	# Overrides
	##
	def get_query_set(self):
		"""
		:rtype: QuerySet
		"""
		return QuerySet(self.model, using=self._db)

	def filter(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(WorkersManager, self).filter(*args, **kwargs)

	def annotate(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(WorkersManager, self).annotate(*args, **kwargs)

	def get(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(WorkersManager, self).get(*args, **kwargs)

	def exclude(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(WorkersManager, self).exclude(*args, **kwargs)

	def order_by(self, *args, **kwargs):
		args, kwargs = _translate(args, kwargs)
		return super(WorkersManager, self).order_by(*args, **kwargs)

	##
	# Request filtering
	##
	def get_not_scheduled(self):
		"""
		Returns ALL the jobs that are NOT scheduled
		"""
		from breeze.models import JobStat
		return self.all().exclude(_status=JobStat.SCHEDULED).exclude(_breeze_stat=JobStat.SCHEDULED)

	def get_incomplete(self):
		"""
		Returns all the jobs that are NOT completed, excluding Scheduled jobs
		That also includes active job that are not running yet
		"""
		from breeze.models import JobStat
		return self.get_not_scheduled().exclude(_breeze_stat=JobStat.DONE)

	def get_run_wait(self):
		"""
		Returns all the jobs that are waiting to be run
		"""
		from breeze.models import JobStat
		return self.get_not_scheduled().filter(_breeze_stat=JobStat.RUN_WAIT)

	def get_active(self):
		"""
		Returns all the jobs that are currently active
		(this include INIT, PREPARE_RUN, RUNNING, QUEUED_ACTIVE but not RUN_WAIT nor SCHEDULED)
		This is the set you want to refresh periodically
		"""
		from breeze.models import JobStat
		return self.get_not_scheduled().exclude(_breeze_stat=JobStat.RUN_WAIT).exclude(_breeze_stat=JobStat.DONE)

	def get_running(self):
		"""
		Returns all the jobs that are currently active and actually running
		(does NOT include INIT, PREPARE_RUN, QUEUED_ACTIVE, etc)
		"""
		from breeze.models import JobStat
		return self.get_not_scheduled().filter(_breeze_stat=JobStat.RUNNING, _status=JobStat.RUNNING)

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

	def get_aborted(self):
		"""
		Returns all the jobs history
		includes succeeded, failed and aborted ones
		"""
		from breeze.models import JobStat

		return self.get_history().filter(Q(_status=JobStat.ABORTED) or Q(_status=JobStat.ABORT))
