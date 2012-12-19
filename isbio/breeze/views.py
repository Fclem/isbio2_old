# -*- coding: utf-8 -*-

from django.template import Template, Context
from django.template.loader import get_template
from django.http import HttpResponse
from django.shortcuts import render_to_response
from breeze.models import Rscript

from django.core.servers.basehttp import FileWrapper
import os, tempfile, zipfile

from xml.dom import minidom

from breeze.forms import DataForm
from rpy2.robjects import r

def base(request):
    return render_to_response('base.html')

def login(request):
    return render_to_response('login.html')

def breeze(request):
    return render_to_response('index.html')

def home(request):
    return render_to_response('home.html', {})

def scripts(request):
    all_scripts = Rscript.objects.order_by("name")
    return render_to_response('scripts.html', {'script_list': all_scripts})

def jobs(request):
    return render_to_response('jobs.html', {})

def form(request):
    dom = minidom.parse('/home/comrade/Projects/fimm/isbio/breeze/templates/xml/fullExample.xml')
    script_name = dom.getElementsByTagName("rScript")[0].getAttribute("name")
    node = dom.getElementsByTagName("inline")[0]
    script_inline = getText(node.childNodes)

    return render_to_response('forms/base_form.html', {'name': script_name, 'inline': script_inline})

# Of course it is temporary here...
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


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
    r.assign('path', path)
    r.assign('option', polot_type)
    r('source(path)')
    r('test(toString(option))')
    image_file = open("/home/comrade/Projects/fimm/isbio/breeze/static/rplot.png", 'rb').read()
#    return render_to_response('/jobs.html')
    return HttpResponse(image_file, mimetype='image/png')

