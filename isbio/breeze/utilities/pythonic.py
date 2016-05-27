from . import this_function_caller_name, Thread
__version__ = '0.1'
__author__ = 'clem'
__date__ = '27/05/2016'


# clem 05/04/2016
def new_thread(func):
	""" Wrapper to run functions in a new Thread (use as a @decorator)

	:type func:
	:rtype:
	"""

	# assert callable(func)

	def decorated(*args):
		Thread(target=func, args=args).start()

	return None if not func else decorated


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


# moved from settings on 19/05/2016
def recur_rec(nb, function, args):
	if nb > 0:
		return recur_rec(nb - 1, function, function(args))
	return args


# moved from settings on 19/05/2016
def recur(nb, function, args):
	while nb > 0:
		args = function(args)
		nb -= 1
	return args


# moved in utils on 19/05/2016
def not_imp(self): # writing shortcut for abstract classes
	raise NotImplementedError("%s was not implemented in concrete class %s." % (
		this_function_caller_name(), self.__class__.__name__))
