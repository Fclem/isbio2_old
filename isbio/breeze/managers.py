from django.db import models
from django.db.models.query import QuerySet as __original_QS
import django.db.models.query_utils


class Trans:
	def __init__(self, *args, **kwargs):
		self._translate(*args, **kwargs)

	_translation = {
		'name': '_name', 'jname': '_name',
		'description': '_description', 'jdetails': '_description',
		'author': '_author', 'juser_id': '_author',
		'type': '_type', 'script_id': '_type',
		'created': '_created', 'staged': '_created',
		'breeze_stat': '_breeze_stat', 'status': '_status',
		'rexec': '_rexec', 'rexecut': '_rexec',
		'dochtml': '_doc_ml', 'docxml': '_doc_ml',
		'institute': '_institute',
	}

	def _has(self, item):
		if isinstance(item, str) and item != '':
			text = item
			if text[0] == '-':
				text = text[1:]
			for key in self._translation.keys():
				if text.startswith(key):
					return item.replace(key, self._translation[key])
		return None

	def _translate(self, args, kwargs):
		new_arg = list(args)
		for pos, el in enumerate(new_arg):
			new_key = self._has(el)
			if new_key is not None:
				new_arg[pos] = new_key
		new_arg = tuple(new_arg)

		for key in kwargs.keys():
			new_key = self._has(key)
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


class WorkersManager(models.Manager):
	"""
	Just change the name of the fields parameters in a QuerySet
	this allow legacy backward compatibility with the new Runnable class
	while not needing to change all the query everywhere in the code.
	The Runnable allows to use unified name for fields, while keeping the old database models #TODO migrate
	Even though, such query should be done from this manager in the future #TODO
	"""
	def get_query_set(self):
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

	# TODO : re-write all the queries here
