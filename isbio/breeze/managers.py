from django.db.models.query_utils import Q as __originalQ

__translation = {
	'name': '_name',
	'jname': '_name',

	'description': '_description',
	'jdetails': '_description',

	'author': '_author',
	'juser_id': '_author',

	'type': '_type',
	'script_id': '_type',

	'created': '_created',
	'staged': '_created',

	'breeze_stat': '_breeze_stat',
	'status': '_status',

	'rexec': '_rexec',
	'rexecut': '_rexec',

	'dochtml': '_doc_ml',
	'docxml': '_doc_ml',
}

def _translate(*args, **kwargs):
	for key in kwargs:
		if key in __translation.keys():
			kwargs[__translation[key]] = kwargs[key]
			del kwargs[key]
	return args, kwargs

class Q(__originalQ):
	"""
	Overloads original Q class
	"""
	def __init__(self, *args, **kwargs):
		super(Q, self).__init__(_translate(*args, **kwargs))

# now import QuerySet which should use the new Q class
from django.db.models.query import QuerySet as __original_QS

class QuerySet(__original_QS):
	"""
	Overloads original QuerySet class
	"""
	__translate = _translate # writing shortcut

	def annotate(self, *args, **kwargs):
		super(QuerySet, self).annotate(self.__translate(*args, **kwargs))

	def filter(self, *args, **kwargs):
		args, kwargs = self.__translate(*args, **kwargs)
		super(QuerySet, self).filter(args, kwargs)

	def get(self, *args, **kwargs):
		super(QuerySet, self).get(self.__translate(*args, **kwargs))

	def exclude(self, *args, **kwargs):
		super(QuerySet, self).exclude(self.__translate(*args, **kwargs))

# now import QuerySet which should use the new QuerySet class
from django.db import models

class WorkersManager(models.Manager):
	"""
	Just change the name of the fields parameters in a QuerySet
	this allow legacy backward compatibility with the new Runnable class
	while not needing to change all the query everywhere in the code.
	The Runnable allows to use unified name for fields, while keeping the old database models #TODO migrate
	Even though, such query should be done from this manager in the future #TODO
	"""

	def get_queryset(self):

		return QuerySet(self.model, using=self._db)
		# parent = super(WorkersManager, self)
		# return QuerySet(parent.model, using=parent._db)
		# return super(WorkersManager, self).get_queryset()
