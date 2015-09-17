# from django.shortcuts import render_to_response
from django.http import HttpResponse


def down(request):
	return HttpResponse(open('/homes/dbychkov/dev/isbio/isbio/down/templates/down.html').read())
