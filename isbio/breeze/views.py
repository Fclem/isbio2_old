# -*- coding: utf-8 -*-
import os
from django.core.files import File
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response

from rpy2.robjects import r
import xml.etree.ElementTree as xml

import forms as breezeForms
from breeze.models import Rscripts

def breeze(request):
    return render_to_response('index.html')

def base(request):
    return render_to_response('base.html')

def login(request):
    return render_to_response('login.html')

def home(request):
    return render_to_response('home.html', {})

def scripts(request):
    all_scripts = Rscripts.objects.order_by("name")
    return render_to_response('scripts.html', {'script_list': all_scripts})

def jobs(request):
    return render_to_response('jobs.html', {})

def read_descr(request, sid):
    script = Rscripts.objects.get(id=sid)
    tree = xml.parse(script.docxml)
    print tree.getroot().find('inline').text
    return render_to_response('forms/descr_modal.html', RequestContext(request, { 'scr': script }))

def read_form(request, sid):
    script = Rscripts.objects.get(id=sid)
    tree = xml.parse(script.docxml)
    script_name = tree.getroot().attrib['name']
    script_inline = tree.getroot().find('inline').text
    form = breezeForms.form_from_xml(tree)
    return render_to_response('forms/user_modal.html', RequestContext(request, {
        'form': form,
        'name': script_name,
        'inline': script_inline,
        'layout': "horizontal",
    }))

def create(request):
    if request.method == 'POST':
        formG = breezeForms.ScriptGeneral(request.POST, request.FILES)
        formD = breezeForms.ScriptGeneral(request.POST, request.FILES)
        formS = breezeForms.ScriptGeneral(request.POST, request.FILES)
        if formG.is_valid() and formD.is_valid() and formS.is_valid():
            breezeForms.xml_from_form(formG)
            newscript = Rscripts(
                name=formG.cleaned_data['name'],  # code=request.FILES['code'],
                logo=request.FILES['logo'], inln=formG.cleaned_data['inln'],
                details=formG.cleaned_data['details']  # , category=formG.cleaned_data['category']
            )
            newscript.docxml.save('name.xml', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml')))
            newscript.docxml.close()
            newscript.save()
            # improve the manipulation with XML - tmp folder not a good idea!
            os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml")
            return HttpResponseRedirect('/scripts/')
    else:
        formG = breezeForms.ScriptGeneral()
        formD = breezeForms.ScriptDetails()
        formS = breezeForms.ScriptSource()
    return render_to_response('new-script.html', RequestContext(request, {
        'general_form': formG,
        'params_form': formD,
        'source_form': formS,
        'layout': 'horizontal',
        'curr_tab': 'params',
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

