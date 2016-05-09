import breeze.models
import re
import copy
import os
import urllib
import urllib2
import glob
import mimetypes
import logging
from django import http
from django.template.defaultfilters import slugify
from django.http import HttpResponse # , Http404
from django.template import loader
from django.template.context import RequestContext
from django.conf import settings
import sys
import utils

# from breeze.models import Report, Jobs, DataSet
# from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
# import time
# from subprocess import Popen, PIPE #, call
# from django.utils import timezone
# from django.contrib import messages
# from datetime import datetime
# from logging import Handler
# from breeze.managers import Q

logger = logging.getLogger(__name__)

# system integrity checks moved to system_check.py on 31/08/2015


# FIXME : deprecated
def restart():
	python = sys.executable
	os.execl(python, python, *sys.argv)
	# time.sleep(2)
	# os._exit(0)
	# exit()


def update_server_routine():
	from b_exceptions import SGEError
	from qstat import Qstat
	try:
		server_info = Qstat().queue_stat

		if server_info.total == server_info.cdsuE:
			server = 'bad'
		elif int(server_info.avail) == 0:
			server = 'full'
		elif int(server_info.avail) <= 3:
			server = 'busy'
		elif float(server_info.cqload) > 30:
			server = 'busy'
		else:
			server = 'idle'

		return server, server_info.__dict__
	except AttributeError, SGEError:
		return 'bad', dict()


###
# ## TODO	How about moving those shits to Models ?
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
# ##	TODO	How about moving those shits to Managers ?
###


def normalize_query(query_string,
					find_terms=re.compile(r'"([^"]+)"|(\S+)').findall,
					norm_space=re.compile(r'\s{2,}').sub):
	""" Splits the query string in individual keywords, getting rid of unnecessary spaces
		and grouping quoted words together.
		Example:

		>>> normalize_query('  some random  words "with   quotes  " and   spaces')
		['some', 'random', 'words', 'with quotes', 'and', 'spaces']
	"""
	return [norm_space(' ', (t[0] or t[1]).strip()) for t in find_terms(str(query_string))]


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
			
			el['home'] = item.home_folder_rel
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

			el['home'] = item.home_folder_rel
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
# ##	*** END ***
###

# 02/06/2015 Clem
def view_range(page_index, entries_nb, total):
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
def make_http_query(request):
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

	query_string = ''
	for each in args:
		if args[each] != '':
			query_string = query_string + each + ': "' + args[each] + '", '

	if len(query_string) > 0:
		query_string = query_string[:-2]

	return query_string


# 10/03/2015 Clem
def report_common(request, v_max=15):
	"""
	:type request: django.core.handlers.wsgi.WSGIRequest
	:type v_max: int
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
		entries_nb = v_max
	return page_index, entries_nb

# DELETED get_job_safe(request, job_id) 19/02/2016 replaced by manager.owner_get
# DELETED get_report_safe(request, job_id, owner=True) 19/02/2016 replaced by manager.owner_get
# DELETED  get_worker_safe_abstract(request, obj_id, model) 19/02/2016 replaced by manager.owner_get


# 10/03/2015 Clem / ShinyProxy
def u_print(request, url, code=None, size=None, date_f=None):
	print u_print_sub(request, url, code, size, date_f)


def u_print_sub(request, url, code=None, size=None, date_f=None):
	proto = request.META['SERVER_PROTOCOL'] if request.META.has_key('SERVER_PROTOCOL') else ''
	return console_print_sub("\"PROX %s   %s %s\" %s %s" % (request.method, url, proto, code, size), date_f=date_f)


# 25/06/2015 Clem
def console_print(text, date_f=None):
	utils.console_print(text, date_f)


def console_print_sub(text, date_f=None):
	return utils.console_print_sub(text, date_f)


# 10/03/2015 Clem / ShinyProxy
def date_t(date_f=None):
	# if dateF is None:
	# 	dateF = settings.USUAL_DATE_FORMAT
	# return str(datetime.now().strftime(dateF))
	return utils.date_t(date_f)


# DELETED get_report_path(f_item, fname=None) 19/02/2016 moved to comp.py
# DELETED get_report_path_test(f_item, fname=None, no_fail=False): 19/02/2016 moved to comp.py


def fail_with404(request, error_msg=None):
	"""
	custom 404 method that enable 404 template even in debug mode (discriminate from real 404),
	Raise no exception so call it with return
	Will log a warning message

	:param request: Django request object
	:type request: http.HttpRequest
	:param error_msg: The message to display on the 404 page
	:type error_msg: str|list
	:return: custom 404 page
	:rtype: http.HttpResponseNotFound
	"""

	t = loader.get_template('404.html')

	if type(error_msg) is not list:
		error_msg = [error_msg]

	rq_path = request.path if request is not None else ''

	logger.warning('404 %s: %s' % (rq_path, error_msg))

	return http.HttpResponseNotFound(t.render(RequestContext(request, {
		'request_path': rq_path,
		'messages': error_msg,
	})))


DASHED_LINE = \
	'---------------------------------------------------------------------------------------------------------------'


def proxy_to(request, path, target_url, query_s='', silent=False, timeout=None):
	import fileinput
	console_date_f = settings.CONSOLE_DATE_F
	log_obj = logger.getChild(sys._getframe().f_code.co_name)
	assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only

	qs = ''
	url = '%s%s' % (target_url, path)
	if query_s and query_s != '':
		qs = '?' + query_s
		url += qs
	elif 'QUERY_STRING' in request.META and request.META['QUERY_STRING'] != "":
		qs = '?' + request.META['QUERY_STRING']
		url += qs
	opener = urllib2.build_opener()
	data = ""
	if request.method == 'POST':
		for each in request.POST.keys():
			data = data + each + "=" + urllib.quote_plus(request.POST[each]) + "&"
		data = data[:-1]

	log = '/var/log/shiny-server.log'
	log_size = os.stat(log).st_size
	proxied_request = None
	msg = ''
	reason = ''
	more = ''
	rep = HttpResponse(status=200, mimetype=HttpResponse)
	try:
		if not silent:
			log_obj.debug(u_print_sub(request, path + str(qs)))
		if settings.VERBOSE:
			u_print(request, path + str(qs), date_f=console_date_f)
		if timeout:
			proxied_request = opener.open(url, data or None, timeout=timeout)
		else:
			proxied_request = opener.open(url, data or None)
	except urllib2.HTTPError as e:
		# add the shiny-server log tail
		if log_size < os.stat(log).st_size:
			more = "%s :\n" % log
			try:
				with open(log) as f:
					f.seek(log_size)
					for line in f.readlines():
						more += line + '\n'
			except Exception as e:
				pass
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
			except Exception as e:
				pass
			more = more[:-1] + DASHED_LINE + '\n'

		try:
			content = e.read()
		except Exception as e:
			if hasattr(e, 'msg'):
				msg = e.msg
			if hasattr(e, 'reason'):
				reason = e.reason
			content = 'SHINY SERVER : %s\nReason : %s\n%s\n%s' % (msg, reason, DASHED_LINE, more)

		msg, reason, code, mime = '', '', '', ''
		if hasattr(e, 'code'):
			code = e.code
		if hasattr(e, 'headers'):
			mime = e.headers.typeheader
		logger.getChild('shiny_server').warning('%s : %s %s%s\n%s' % (e, request.method, path, str(qs), more))
		rep = HttpResponse(content, status=code, mimetype=mime)
	except urllib2.URLError as e:
		log_obj.error(e)
		pass
	else:
		status_code = proxied_request.code
		mime_type = proxied_request.headers.typeheader or mimetypes.guess_type(url)
		content = proxied_request.read()
		if proxied_request.code != 200:
			print 'PROX::', proxied_request.code
		if not silent:
			log_obj.debug(u_print_sub(request, path + str(qs), proxied_request.code, str(len(content))))
		if settings.DEBUG and not silent:
			u_print(request, path + str(qs), proxied_request.code, str(len(content)), date_f=console_date_f)
		rep = HttpResponse(content, status=status_code, mimetype=mime_type)
	return rep

# 29/05/2015 TOOOOOOOO SLOW
# DELETED update_all_jobs_sub on 30/06/2015


# clem 02/10/2015
def html_auto_content_cache(path_to_file):
	"""
	Figure out if an HTML file has been cached or not, and return file content.
	If file was not cached, checks for image content and return <i>image_embedding()</i> processed markup
	<i>image_embedding()</i> transform images link in embedded images and save a cache file.
	<i>Experimental results shows browser <u>loading time decrease by <b>factor 10+</b></u> (2000+ images)</i>

	:param path_to_file: path to the HTML file
	:type path_to_file: str
	:rtype: str
	"""
	from os.path import splitext, dirname, basename, isfile

	file_name, file_ext = splitext(basename(path_to_file))
	file_ext = slugify(file_ext)

	if file_ext != 'html' and file_ext != 'htm':
		f = open(path_to_file)
		return f.read()

	dir_path = dirname(path_to_file) + '/'
	cached_path = dir_path + file_name + '_cached.' + file_ext

	if isfile(cached_path): # and getsize(cached_path) > pow(1024, 2): # 1 Mibi
		f = open(cached_path)
		return f.read()

	return image_embedding(path_to_file, cached_path)


# clem 30/09/2015
def image_embedding(path_to_file, cached_path=None):
	"""
	Replace <img> links in HTML's <i>path_to_file</i> content by corresponding base64_encoded embedded images
	Save the generated file to [<i>original_file_name</i>]_cached.[extension]
	<u>images files's urls have to be a path inside path_to_file's containing folder</u>

	:param path_to_file: path to the HTML file
	:type path_to_file: str
	:rtype: str
	"""
	from os.path import splitext, dirname
	from bs4 import BeautifulSoup
	changed = False

	f = open(path_to_file)
	# soup = BeautifulSoup(f.read(), 'lxml')
	dir_path = dirname(path_to_file) + '/'
	soup = BeautifulSoup(f.read(), 'html.parser')
	all_imgs = soup.findAll('img')
	for each in all_imgs:
		if not str(each['src']).startswith('data:'):
			ext = slugify(splitext(each['src'])[1])
			if ext in ['jpg', 'jpeg', 'png', 'gif']:
				changed = True
				data_uri = open(dir_path + each['src'], 'rb').read().encode('base64').replace('\n', '')
				img_tag = BeautifulSoup('<img src="data:image/{0};base64,{1}">'.format(ext, data_uri), 'html.parser')
				each.replace_with(img_tag)

	if cached_path and changed:
		f2 = open(cached_path, 'w')
		f2.write(str(soup))

	return str(soup)
