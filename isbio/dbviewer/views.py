from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required # , permission_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from breeze.models import UserProfile # TODO move to a common base app
# from django.shortcuts import render
# from django.conf import settings
# from django.contrib import auth
# from django.shortcuts import redirect


@login_required(login_url='/')
def db_viewer(request):
	return render_to_response('dbviewer.html', RequestContext(request, {
		'dbviewer_status': 'active',
	}))


@login_required(login_url='/')
def db_policy(request):
	user_profile = UserProfile.objects.get(user=request.user)
	user_profile.db_agreement = True
	user_profile.save()
	# return HttpResponseRedirect('/dbviewer/') # FIXME hardcoded url
	return HttpResponseRedirect(reverse(db_viewer))

