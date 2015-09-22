from logging import Handler
import breeze.models
import re, copy, os, sys
import urllib, urllib2, glob, mimetypes, logging
from breeze.models import Report, Jobs, DataSet
from datetime import datetime
# from django.contrib import messages
from django import http
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from breeze.managers import Q
from django.http import Http404, HttpResponse
from django.template import loader
from django.template.context import RequestContext
from isbio import settings
from subprocess import Popen, PIPE, call
import sys
import utils
# from django.utils import timezone

logger = logging.getLogger(__name__)

# system integrity checks moved to system_check.py on 31/08/2015


def updateServer_routine():
	# hotfix
	if 'QSTAT_BIN' in os.environ:
		qstat = os.environ['QSTAT_BIN']
	else:
		qstat = 'qstat'

	# get the server info by directly parsing qstat
	# p = subprocess.Popen([qstat, "-g", "c"], stdout=subprocess.PIPE)
	p = Popen([qstat, "-g", "c"], stdout=PIPE)
	output, err = p.communicate()
	server = 'unknown'
	s_name = ''
	cqload = 0
	used = 0
	avail = 0
	total = 0
	cdsuE = 0
	for each in output.splitlines():
		if 'hugemem.q' in each.split(): # TODO switch to dynamic server
			s_name = each.split()[0]
			cqload = int(float(each.split()[1])*100)
			used = each.split()[2]
			avail = each.split()[4]
			total = each.split()[5]
			cdsuE = 0 + int(each.split()[7])

			if total == cdsuE:
				server = 'bad'
			elif int(avail) <= 3:
				server = 'busy'
			elif float(cqload) > 30:
				server = 'busy'
			else:
				server = 'idle'
	server_info = {
		's_name': s_name or '',
		'cqload': str(cqload or '') + "%",
		'cdsuE': str(cdsuE or ''),
		'total': total or '',
		'avail': avail or '',
		'used': used or '',
	}
	return server, server_info


###
### TODO	How about moving those shits to Models ?
###


def update_last_active(user):
	pass


def clean_up_dt_id(lst):
	""" Cleans up row ids that come from the DataTable plugin.

	Arguments:
	lst      -- list of ids
	"""
	cleaned = map(lambda line: int(line[4:]), lst)  # (trim firs 4 chars)

	return cleaned


def save_new_project(form, author):
	""" Saves New Project data from a valid form to DB model.

	Arguments:
	form        -- instance of NewProjectForm
	author      -- user name
	"""
	insti = breeze.models.UserProfile.objects.get(user=author).institute_info
	dbitem = breeze.models.Project(
		name=str(form.cleaned_data.get('project_name', None)),
		manager=str(form.cleaned_data.get('project_manager', None)),
		pi=str(form.cleaned_data.get('principal_investigator', None)),
		author=author,
		collaborative=form.cleaned_data.get('collaborative', None),
		wbs=str(form.cleaned_data.get('wbs', None)),
		external_id=str(form.cleaned_data.get('eid', None)),
		description=str(form.cleaned_data.get('description', None)),
		institute=insti
	)

	dbitem.save()

	return True


def save_new_group(form, author, post):
	""" Saves New Group data from a valid form to DB model.

	Arguments:
	form        -- instance of GroupForm
	author      -- user name
	"""

	dbitem = breeze.models.Group(
		name=str(form.cleaned_data.get('group_name', None)),
		author=author
	)

	# Important:
	# Before using ManyToMany we should first save the model!!!
	dbitem.save()

	for chel in post.getlist('group_team'):
		dbitem.team.add(breeze.models.User.objects.get(id=chel))

	dbitem.save()

	return True


def edit_project(form, project):
	""" Edit Project data.

	Arguments:
	form        -- instance of EditProjectForm
	project     -- db instance of existing Project
	"""
	project.wbs = str(form.cleaned_data.get('wbs', None))
	project.external_id = str(form.cleaned_data.get('eid', None))
	project.description = str(form.cleaned_data.get('description', None))
	project.save()

	return True


def edit_group(form, group, post):
	""" Edit Group data.

	Arguments:
	form        -- instance of EditGroupForm
	group       -- db instance of existing Group
	"""
	# clean up first
	group.team.clear()
	group.save()

	for chel in post.getlist('group_team'):
		group.team.add(breeze.models.User.objects.get(id=chel))

	group.save()

	return True


def delete_project(project):
	""" Remove a project from a DB model.

	Arguments:
	project     -- db instance of Project
	"""
	project.delete()

	return True


def delete_group(group):
	""" Remove a group from a DB model.

	Arguments:
	group     -- db instance of Group
	"""
	group.delete()

	return True


def open_folder_permissions(path, permit=0770):
	""" Traverses a directory recursively and set permissions.

	Arguments:
	path        -- a path string ( default '' )
	permit      -- permissions to be set in oct
				( default 0770 ) - '?rwxrwx---'
	"""

	for dirname, dirnames, filenames in os.walk(path):
		for subdirname in dirnames:
			full_dir_path = os.path.join(dirname, subdirname)
			os.chmod(full_dir_path, permit)

		for filename in filenames:
			full_file_path = os.path.join(dirname, filename)
			os.chmod(full_file_path, permit)

	os.chmod(path, permit)

	return True


###
###	TODO	How about moving those shits to Managers ?
###


def normalize_query(query_string,
					findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
					normspace=re.compile(r'\s{2,}').sub):
	''' Splits the query string in invidual keywords, getting rid of unecessary spaces
		and grouping quoted words together.
		Example:

		>>> normalize_query('  some random  words "with   quotes  " and   spaces')
		['some', 'random', 'words', 'with quotes', 'and', 'spaces']
	'''
	return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(str(query_string))]


def get_query(query_string, search_fields, exact=True):
	''' Returns a query, that is a combination of Q objects. That combination
		aims to search keywords within a model by testing the given search fields.
	'''
	from breeze.managers import Q
	query = None  # Query to search for every search term
	terms = normalize_query(query_string) if query_string else []
	for term in terms:
		or_query = None  # Query to search for a given term in each field
		for field_name in search_fields:
			q = Q(**{ "%s" % field_name: term }) if exact else Q(**{ "%s__icontains" % field_name: term })
			if or_query is None:
				or_query = q
			else:
				or_query = or_query | q
		if query is None:
			query = or_query
		else:
			query = query & or_query
	return query


def extract_users(groups, users):
	''' Produce a unique list of users from 2 lists.
		Merge users from each group and set of individual users
		and extracts a union of those people.
	'''
	people = list()

	#  Process Groups
	if groups:
		for group_id in map(int, groups.split(',')):
			dbitem = breeze.models.Group.objects.get(id=group_id)
			ref = dbitem.team.all()
			people = list(set(people) | set(ref))

		# Process Individual Users
	if users:
		users_ids = map(int, users.split(','))
		ref = breeze.models.OrderedUser.objects.filter(id__in=users_ids)
		people = list(set(people) | set(ref))

	return people


# TODO get rid of that
def merge_job_history(jobs, reports, user=None):
	""" Merge reports and jobs in a unified object (list)
		So that repors and jobs can be processed similatly on the client side
	"""
	merged = list()
	pool = list(jobs) + list(reports)

	from breeze.models import Runnable

	for item in pool:
		assert isinstance(item, Runnable)
		el = dict()
		# automatize this part
		if item.is_job:
			el['instance'] = 'script'
			el['id'] = item.id
			el['jname'] = item.jname
			el['status'] = item.status
			el['staged'] = item.staged

			el['rdownhref'] = '/jobs/download/%s-result'%str(item.id)  # results
			el['ddownhref'] = '/jobs/download/%s-code'%str(item.id)  # debug
			el['fdownhref'] = '/jobs/download/%s'%str(item.id)  # full folder
			
			el['home'] = item._home_folder_rel
			el['reschedhref'] = '/jobs/edit/%s-repl'%str(item.id)

			el['delhref'] = '/jobs/delete/%s'%str(item.id)
			el['abohref'] = '/abortjobs/%s'%str(item.id)

			el['progress'] = item.progress
			el['type'] = item.script
			el['r_error'] = item.r_error

			el['shiny_key'] = ''
			el['go_shiny'] = False

		else:                             # report
			el['instance'] = 'report'
			el['id'] = item.id
			el['jname'] = item.name
			el['status'] = item.status
			el['staged'] = item.created

			# el['rdownhref'] = '/get/report-%s'%str(item.id)  # results
			el['rdownhref'] = '/report/download/%s-result'%str(item.id)  # results
			el['ddownhref'] = '/report/download/%s-code' % str(item.id)  # debug
			el['fdownhref'] = '/report/download/%s' % str(item.id)  # full folder

			el['home'] = item._home_folder_rel
			el['reschedhref'] = '/reports/edit/%s'%str(item.id)

			el['delhref'] = '/reports/delete/%s-dash'%str(item.id)
			el['abohref'] = '/abortreports/%s'%str(item.id)

			el['progress'] = item.progress
			el['type'] = item.type
			el['r_error'] = item.r_error

			el['shiny_key'] = item.shiny_key
			el['go_shiny'] = item.is_shiny_enabled and item.has_access_to_shiny(user)

		merged.append(copy.deepcopy(el))

	# sort list according to creation daten and time
	merged.sort(key=lambda r: r['staged'])
	merged.reverse()

	return merged


def merge_job_lst(item1, item2):
	''' Merge reports with reports or jobs with jobs in a unified object (list)
	'''
	merged = list()
	merged = list() + list(item1) + list(item2)

	# sort list according to creation date and time
	merged.sort(key=lambda r: r['staged'])
	merged.reverse()

	return merged


###
###	*** END ***
###

#02/06/2015 Clem
def viewRange(page_index, entries_nb, total):
	"""
	Calculate and return a dict with the number of the first and last elements in the current view of the paginator
	:param page_index: number of the current page in the paginator (1 to x)
	:type page_index: int
	:param entries_nb: number of elements to be disaplayed in the view
	:type entries_nb: int
	:param total: total number of elements
	:type total: int
	:return: dict(first, last, total)
	:rtype: dict
	"""
	return dict(first=(page_index - 1)*entries_nb + 1, last=min(page_index*entries_nb, total), total=total)

# 28/04/2015 Clem
def makeHTTP_query(request):
	"""
	serialize GET or POST data from a query into a dict string
	:param request: Django Http request object
	:type request: http.HttpRequest
	:return: QueryString
	:rtype: str
	"""
	if request.method == 'POST':
		args = request.POST.copy()
	else:
		args = request.GET.copy()

	if args.get('page'):
		del args['page']
	if args.get('csrfmiddlewaretoken'):
		del args['csrfmiddlewaretoken']

	queryS = ''
	for each in args:
		if args[each] != '':
			queryS = queryS + each + ': "' + args[each] + '", '

	if len(queryS) > 0:
		queryS = queryS[:-2]

	return queryS


# 10/03/2015 Clem
def report_common(request, max=15):
	"""
	:type request: django.core.handlers.wsgi.WSGIRequest
	:type max: int
	:return: page_index, entries_nb
		page_index: int
			current page number to display
		entries_nb: int
			number of item to display in a page
	"""
	if request.REQUEST.get('page'):  # and type(request.REQUEST.get('page') == 'int'):
		page_index = int(request.REQUEST['page'])
	else:
		page_index = 1

	if request.REQUEST.get('entries'):
		entries_nb = int(request.REQUEST['entries'])
	else:
		entries_nb = max
	return page_index, entries_nb


### TODO	move the following to managers ?

def get_job_safe(request, job_id):
	"""
		Return a Jobs instance, or fail with 404 if no such job, or 403 if user has no access to this job
		Ensure that job/report designated by obj_id exists or fail with 404
		Ensure that current user is OWNER of said object or fail with 403
		:param request: Django Http request object
		:type request: http.HttpRequest
		:param job_id: id of the requested Job
		:type job_id: int
		:return: requested object instance or fail_with404
		:rtype: Report or Jobs
	"""
	return get_worker_safe_abstract(request, job_id, Jobs)


def get_report_safe(request, report_id, owner=True):
	"""
		Return a Report instance, or fail with 404 if no such report, or 403 if user has no access to this report
		Ensure that job/report designated by obj_id exists or fail with 404
		Ensure that current user is OWNER of said object or fail with 403
		:param request: Django Http request object
		:type request: http.HttpRequest
		:param report_id: id of the requested Report
		:type report_id: int
		:return: requested object instance or fail_with404
		:rtype: Report or Jobs
	"""
	return get_worker_safe_abstract(request, report_id, Report)


def get_worker_safe_abstract(request, obj_id, model):
	"""
	Ensure that job/report designated by obj_id exists or fail with 404
	Ensure that current user is OWNER of said object or fail with 403
	:param request: Django Http request object
	:type request: http.HttpRequest
	:param obj_id: table pk of the requested object
	:type obj_id: int
	:param model: class Report or class Jobs instance
	:type model: Report or Jobs
	:return: requested object instance
	:rtype: Report or Jobs
	"""
	# assert isinstance(model, Report) or isinstance(model, Jobs), 'argument is neither a Job or Report class'
	try:
		obj = model.objects.get(id=obj_id)
		user = obj.author if model.__name__ == Report.__name__ else obj.juser
		# Enforce access rights
		if user != request.user:
			raise PermissionDenied
		return obj
	except ObjectDoesNotExist:
		raise Http404()


### *** END ***

# 10/03/2015 Clem / ShinyProxy
def uPrint(request, url, code=None, size=None, datef=None):
	print uPrint_sub(request, url, code, size, datef)


def uPrint_sub(request, url, code=None, size=None, datef=None):
	proto = request.META['SERVER_PROTOCOL'] if request.META.has_key('SERVER_PROTOCOL') else ''
	return console_print_sub("\"PROX %s   %s %s\" %s %s" % (request.method, url, proto, code, size), datef=datef)


# 25/06/2015 Clem
def console_print(text, datef=None):
	# print console_print_sub(text, datef=datef)
	utils.console_print(text, datef)


def console_print_sub(text, datef=None):
	# return "[%s] %s" % (dateT(datef), text)
	return utils.console_print_sub(text, datef)


# 10/03/2015 Clem / ShinyProxy
def dateT(dateF = None):
	# if dateF is None:
	# 	dateF = settings.USUAL_DATE_FORMAT
	# return str(datetime.now().strftime(dateF))
	return utils.dateT(dateF)


# Used to check for missing reports, following lost report event
def get_report_path(fitem, fname=None):
	"""
		Return the path of an object, and checks that the path is existent or fail with 404
		:param fitem: a Report.objects from db
		:type fitem: Report or DataSet
		:param fname: a specified file name (optional, default is report.html)
		:type fname: str
		:return: (local_path, path_to_file)
		:rtype: (str, str)
	"""
	assert isinstance(fitem, (Report, DataSet))
	errorMsg = ''
	if fname is None: fname = 'report.html'

	if isinstance(fitem, DataSet):
		home = fitem.rdata
	else:
		home = fitem._home_folder_rel
	local_path = home + '/' + unicode.replace(unicode(fname), '../', '')
	path_to_file = str(settings.MEDIA_ROOT) + local_path

	# hack to access reports that were generated while dev was using prod folder
	if not os.path.exists(path_to_file) and settings.DEV_MODE:
		dir_exists = os.path.isdir(os.path.dirname(path_to_file))
		errorMsg = 'File ' + str(path_to_file) + ' NOT found. The folder ' + (
			'DO NOT ' if not dir_exists else ' ') + 'exists.'
		path_to_file = str(settings.MEDIA_ROOT).replace('-dev', '') + local_path

	if not os.path.exists(path_to_file):
		dir_exists = os.path.isdir(os.path.dirname(path_to_file))
		raise Http404(errorMsg + '<br />\n' + 'File ' + str(path_to_file) + ' NOT found. The folder ' + (
		'DO NOT ' if not dir_exists else ' ') + 'exists.')

	return local_path, path_to_file


# Used to check for missing reports, following lost report event
def get_report_path_test(fitem, fname=None, NoFail=False):
	"""
	:param fitem: a Report.objects from db
	:type fitem: Report or DataSet
	:param fname: a specified file name (optional, default is report.html)
	:type fname: str
	:return: (old_local_path, path_to_file, file_exists, dir_exists)
	:rtype: (str, str, str, str)
	"""

	if fname is None: fname = 'report.html'
	local_path = fitem._home_folder_rel + '/' + unicode.replace(unicode(fname), '../', '')
	path_to_file = str(settings.MEDIA_ROOT) + local_path

	file_exists = os.path.exists(path_to_file)
	dir_exists = os.path.isdir(os.path.dirname(path_to_file))

	old_local_path = os.path.dirname(str(settings.MEDIA_ROOT) + local_path)

	# hack to access reports that were generated while dev was using prod folder
	if not (dir_exists and file_exists) and settings.DEV_MODE:
		path_to_file = str(settings.MEDIA_ROOT).replace('-dev', '') + local_path
		old_local_path = (old_local_path, os.path.dirname(path_to_file))
		file_exists = os.path.exists(path_to_file)
		dir_exists = os.path.isdir(os.path.dirname(path_to_file))

	return old_local_path, path_to_file, file_exists, dir_exists


def fail_with404(request, errorMsg=None):
	"""
	custom 404 method that enable 404 template even in debug mode (discriminate from real 404),
	Raise no exception so call it with return
	:param request: Django request object
	:type request: http.HttpRequest
	:param errorMsg: The message to display on the 404 page
	:type errorMsg: str
	:return: custom 404 page
	:rtype: http.HttpResponseNotFound
	"""

	t = loader.get_template('404.html')

	if type(errorMsg) is not list:
		errorMsg = [errorMsg]

	return http.HttpResponseNotFound(t.render(RequestContext(request, {
		'request_path': request.path if request is not None else '',
		'messages': errorMsg,
	})))


DASHED_LINE = '---------------------------------------------------------------------------------------------------------------'


def proxy_to(request, path, target_url, query_s='', silent=False):
	import fileinput
	CONSOLE_DATE_F = settings.CONSOLE_DATE_F
	log_obj = logger.getChild(sys._getframe().f_code.co_name)
	assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only
	# TODO deploy on prod and then remove
	# if not settings.DEV_MODE:
	# 	raise PermissionDenied
	qs = ''
	url = '%s%s'%(target_url, path)
	if query_s and query_s != '':
		qs = '?' + query_s
		url += qs
	elif request.META.has_key('QUERY_STRING') and request.META['QUERY_STRING'] != "":
		qs = '?' + request.META['QUERY_STRING']
		url += qs
	opener = urllib2.build_opener()
	# copies headers
	# for each in request.META.keys():
	#    if each[0:4] == "HTTP":
	#        opener.addheaders.append((each[5:], request.META[each]))
	# copies form data
	data = ""
	if request.method == 'POST':
		for each in request.POST.keys():
			data = data + each + "=" + urllib.quote_plus(request.POST[each]) + "&"
		data = data[:-1]

	log = '/var/log/shiny-server.log'
	log_size = os.stat(log).st_size
	proxied_request = None
	try:
		log_obj.debug(uPrint_sub(request, path + str(qs)))
		if settings.VERBOSE: uPrint(request, path + str(qs), datef=CONSOLE_DATE_F)
		proxied_request = opener.open(url, data or None)
	except urllib2.HTTPError as e:
		more = ''
		# add the shiny-server log tail
		if log_size < os.stat(log).st_size:
			more = "/var/log/shiny-server.log :\n"
			try:
				f = open(log)
				f.seek(log_size)
				for line in f.readlines():
					more += line + '\n'
			except:
				pass
			finally:
				f.close()
			more = more[:-1] + DASHED_LINE + '\n'

		# try to read the shiny app log :
		p = '/var/log/shiny-server/' + path[:-1] + '-shiny-*'
		for fileName in glob.glob(p):
			# more += os.path.basename(fileName) + ' : \n'
			more += fileName + ' :\n'
			for line in fileinput.input(fileName, openhook=fileinput.hook_encoded("utf8")):
				more += line + '\n'
			fileinput.close()
			try:
				os.remove(fileName)
			except:
				pass
			more = more[:-1] + DASHED_LINE + '\n'

		try:
			content = e.read()
		except:
			content = 'SHINY SERVER : %s\nReason : %s\n%s\n%s'%(e.msg, e.reason, DASHED_LINE, more)

		logger.getChild('shiny_server').error(request.method + ' ' + path + str(qs) + '\n' + more)
		# rep = HttpResponse(content, status=e.code, mimetype='text/plain')
		rep = HttpResponse(content, status=e.code, mimetype=e.headers.typeheader)
	else:
		status_code = proxied_request.code
		mimetype = proxied_request.headers.typeheader or mimetypes.guess_type(url)
		content = proxied_request.read()
		if proxied_request.code != 200:
			print 'PROX::', proxied_request.code
		log_obj.debug(uPrint_sub(request, path + str(qs), proxied_request.code, str(len(content))))
		if settings.DEBUG and not silent: uPrint(request, path + str(qs), proxied_request.code, str(len(content)), datef=CONSOLE_DATE_F)
		rep = HttpResponse(content, status=status_code, mimetype=mimetype)
	return rep

# 29/05/2015 TOOOOOOOO SLOW
# DELETED update_all_jobs_sub on 30/06/2015
