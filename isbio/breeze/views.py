# -*- coding: utf-8 -*-

from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse
from django.shortcuts import render_to_response
import os, tempfile, zipfile
from breeze.forms import DataForm
from rpy2.robjects import r

def breeze(request):
    return render_to_response('index.html')

def home(request):
    return render_to_response('home.html')

def scripts(request):
    return render_to_response('scripts.html')

def jobs(request):
    return render_to_response('jobs.html')

def send_zipfile(request):
    response = HttpResponse(content_type='String')    
    response['Content-Disposition'] = 'attachment; filename="/home/comrade/Projects/fimm/isbio/breeze/static/dp.png"'

#    temp = tempfile.TemporaryFile()
#    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
#    for index in range(10):
#        filename = __file__ # Select your files here.                           
#        archive.write(filename, 'file%d.txt' % index)
#    archive.close()
#    wrapper = FileWrapper(temp)
#    response = HttpResponse(wrapper, content_type='application/zip')
#    response['Content-Disposition'] = 'attachment; filename=test.zip'
#    response['Content-Length'] = temp.tell()
#    temp.seek(0)
#    return response 

    return response

def search_form(request):
    return render_to_response('search_form/search_form.html')

def contact(request):
    data_form = DataForm()
	
    return render_to_response('contact_form.html', {'form': data_form})

def result(request):
    polot_type = request.GET.getlist('plot')
    path = '/home/comrade/Projects/fimm/isbio/breeze/r_scripts/data.r'
    r.assign('path',path)
    r.assign('option',polot_type)
    r('source(path)')
    r('test(toString(option))')
    image_file = open("/home/comrade/Projects/fimm/isbio/breeze/static/rplot.png",'rb').read()
#    return render_to_response('/jobs.html')
    return HttpResponse(image_file,mimetype='image/png')

