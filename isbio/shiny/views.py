from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
# from django.contrib.auth.decorators import login_required, permission_required
# from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponseRedirect # , HttpResponse, HttpResponsePermanentRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from breeze.utils import *
from breeze.models import Report, OffsiteUser
from breeze.views import report_file_view
import breeze.auxiliary as aux
# import sys


@csrf_exempt
@login_required(login_url='/')
def proxy_to(request, path, target_url, query_s=''):
	return aux.proxy_to(request, path, target_url, query_s)


# Shiny tab access from inside
@login_required(login_url='/')
def report_shiny_view_tab(request, rid):
	if not rid or rid == '':
		return aux.fail_with404(request)
	try:
		report = Report.objects.get(id=rid)
		assert isinstance(report, Report)
	except ObjectDoesNotExist:
		return aux.fail_with404(request)
	# Enforce user access restrictions
	if not report.has_access_to_shiny(request.user):
		raise PermissionDenied

	# return HttpResponseRedirect(reverse(report_shiny_in_wrapper, kwargs={ 'rid': rid }))
	return HttpResponseRedirect(report.get_shiny_report.url(report))


# Shiny tab access from outside (with the key)
def report_shiny_view_tab_out(request, s_key, u_key):
	__self__ = globals()[this_function_name()]  # instance to self
	try:  # TODO merge ACL with out wrapper in a new func
		# Enforces access control
		# both request will fail if the object is not found
		# we fetch the report
		a_report = Report.objects.get(shiny_key=s_key)
		# and if found, check the user with this key is in the share list of this report
		a_report.offsiteuser_set.get(user_key=u_key)
	except ObjectDoesNotExist:
		return aux.fail_with404(request)

	if request.GET.get('list'):
		page_index, entries_nb = aux.report_common(request)
		# get off-site user
		off_user = OffsiteUser.objects.get(user_key=u_key)
		# list all shiny-enabled report he has access to
		all_reports = off_user.shiny_access.exclude(shiny_key=None)
		for each in all_reports:
			each.url = reverse(__self__, kwargs={ 's_key': each.shiny_key, 'u_key': u_key })

		count = { 'total': all_reports.count() }
		paginator = Paginator(all_reports, entries_nb)  # show 18 items per page
		try:
			a_reports = paginator.page(page_index)
		except PageNotAnInteger:  # if page isn't an integer
			page_index = 1
			a_reports = paginator.page(page_index)
		except EmptyPage:  # if page out of bounds
			page_index = paginator.num_pages
			a_reports = paginator.page(page_index)

		count.update({
			'first': (page_index - 1) * entries_nb + 1,
			'last' : min(page_index * entries_nb, count['total'])
		})
		base_url = reverse(__self__, kwargs={ 's_key': a_report.shiny_key, 'u_key': u_key })
		return render_to_response('out_reports-paginator.html', RequestContext(request, {
			'reports'          : a_reports,
			'pagination_number': paginator.num_pages,
			'count'            : count,
			'base_url'         : base_url,
			'page'             : page_index
		}))
	# return report_shiny_view_tab_merged(request, a_report.id, outside=True, u_key=u_key)

	return report_shiny_view_tab_merged(request, a_report.id, outside=True, u_key=u_key)


# Shiny tab
# DO NOT CALL THIS VIEW FROM URL
def report_shiny_view_tab_merged(request, rid, outside=False, u_key=None):
	try:
		a_report = Report.objects.get(id=rid)
	except ObjectDoesNotExist:
		return aux.fail_with404(request, 'There is no report with id ' + rid + ' in DB')

	if outside:
		# TODO
		# nozzle = reverse(report_nozzle_out_wrapper, kwargs={'s_key': a_report.shiny_key, 'u_key': u_key})
		nozzle = ''
		base_url = '' # reverse(report_shiny_view_tab_out, kwargs={'s_key': a_report.shiny_key, 'u_key': u_key})
		frame_src = ''
	else:
		# Enforce user access restrictions for Breeze users
		if not a_report.has_access_to_shiny(request.user):
			raise PermissionDenied
		# nozzle = reverse(report_file_view, kwargs={'rid': a_report.id})
		frame_src = reverse(report_file_view, kwargs={ 'rid': rid })
		nozzle = ''
		base_url = settings.SHINY_URL
		frame_src = '%s%s' % (base_url, a_report.id)

	return render_to_response('shiny_tab.html', RequestContext(request, {
		'nozzle'   : nozzle,
		'args'     : a_report.args_string,
		'base_url' : base_url,
		'outside'  : outside,
		'frame_src': frame_src,
		'title'    : a_report.name
	}))


@csrf_exempt
@login_required(login_url='/')
def standalone_shiny_in_wrapper(request, path=None, sub=None):
	# Enforce user access restrictions

	# p1 = fitem.type.shiny_report.report_link_rel_path(fitem.id)
	path = path or ''
	sub = sub or ''
	return aux.proxy_to(request, path + '/' + sub, settings.SHINY_LOCAL_STANDALONE_BREEZE_URL)


@csrf_exempt
def standalone_pub_shiny_fw(request, path=''):
	from django.shortcuts import redirect
	return redirect(settings.SHINY_PUB_REDIRECT + path)


# Wrapper for ShinyApp accessed from inside (login + user access to said report)
# Proxy access manager
@csrf_exempt
@login_required(login_url='/')
def report_shiny_in_wrapper(request, rid, path=None):
	if not rid or rid == '':
		return aux.fail_with404(request)
	try:
		fitem = Report.objects.get(id=rid)
	except ObjectDoesNotExist:
		return aux.fail_with404(request)
	# Enforce user access restrictions
	if not fitem.has_access_to_shiny(request.user):
		raise PermissionDenied

	p1 = fitem.type.shiny_report.report_link_rel_path(fitem.id)
	return aux.proxy_to(request, '%s/%s' % (p1, path), settings.SHINY_TARGET_URL)


@csrf_exempt
@login_required(login_url='/')
def shiny_libs(request, path=None):
	return aux.proxy_to(request, '%s' % path, settings.SHINY_LIBS_TARGET_URL)
