# -*- coding: utf-8 -*-

from django.template import Template, Context
from django.template.context import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response
from breeze.models import Rscript
from bootstrap_toolkit.widgets import BootstrapUneditableInput

import xml.etree.ElementTree as xml
from forms import TestForm, generate_form, CreateScript
from django import forms

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

def demo_form(request):
    layout = request.GET.get('layout')
    if not layout:
        layout = 'horizontal'
    if request.method == 'POST':
        form = TestForm(request.POST)
        form.is_valid()
    else:
        form = TestForm()
    form.fields['title'].widget = BootstrapUneditableInput()
    return render_to_response('forms/base_form.html', RequestContext(request, {
        'form': form,
        'layout': layout,
    }))

def read_form(request):
    tree = xml.parse('/home/comrade/Projects/fimm/isbio/breeze/templates/xml/fullExample.xml')
    script_name = tree.getroot().attrib['name']
    script_inline = tree.getroot().find('inline').text
    form = generate_form(tree)
    return render_to_response('forms/user_modal.html', RequestContext(request, {
        'form': form,
        'name': script_name,
        'inline': script_inline,
        'layout': "horizontal",
    }))

def create(request):
    form = CreateScript()
    return render_to_response('forms/mbi_modal.html', RequestContext(request, {
        'form': form,
        'layout': 'horizontal',
    }))

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

