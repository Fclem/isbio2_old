# -*- coding: utf-8 -*-
import os, copy
from django.core.files import File
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response

from rpy2.robjects import r
import xml.etree.ElementTree as xml

import forms as breezeForms
from breeze.models import Rscripts

class RequestStorage():
    pass
storage = RequestStorage()

def get_logic(request, which):
    msg = 'MESSAGE'
    form = breezeForms.AddBasic(request.POST or None)
    if form.is_valid():
        # add new param to par table...
        return render_to_response('new-script.html', RequestContext(request, {
        'hidden_form': storage.hidden_form,
        'general_form': storage.form_general,
        'params_form': storage.form_details,
        'source_form': storage.form_sources,
        'layout': 'inline',
        'curr_tab': 'params',
        'status': 'info',
        }))
    return render_to_response('forms/new_param_modal.html', RequestContext(request, {
        'basic': form,
        'msg': msg,
    }))

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

def read_descr(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    return render_to_response('forms/descr_modal.html', RequestContext(request, { 'scr': script }))

def read_form(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    tree = xml.parse("/home/comrade/Projects/fimm/isbio/breeze/" + str(script.docxml))
    script_name = tree.getroot().attrib['name']
    script_inline = script.inln
    form = breezeForms.form_from_xml(tree)
    return render_to_response('forms/user_modal.html', RequestContext(request, {
        'id': sid,
        'name': script_name,
        'inline': script_inline,
        'form': form,
        'layout': "horizontal",
    }))

def run_script(request, sid):
    script = Rscripts.objects.get(id=sid)
    parameter = "TRUE"
    path = "/home/comrade/Projects/fimm/isbio/breeze/" + str(script.code)
    r.assign('path', path)
    r.assign('arg1', parameter)
    r('source(toString(path))')
    r('testfunc(toString(arg1))')

    return HttpResponseRedirect('/jobs/')

def append_param(request, which):
    basic_form = breezeForms.AddBasic(request.POST or None)
    extra_form = None
    if which == 'NUM':
        msg = 'NUMERIC'
    elif which == 'CHB':
        msg = 'CHECK BOX'
    elif which == 'DRP':
        msg = 'DROP DOWN'
        extra_form = breezeForms.AddOptions(request.POST or None)
    elif which == 'RAD':
        msg = 'RADIO BUTTONS'
        extra_form = breezeForms.AddOptions(request.POST or None)
    elif which == 'TEX':
        msg = 'TEXT INPUT'
    elif which == 'TAR':
        msg = 'TEXT AREA'
    elif which == 'FIL':
        msg = 'FILE INPUT'
    elif which == 'HED':
        msg = 'SECTION NAME'
    else:
        pass

    if basic_form.is_valid():
        # do smth with ParamForm to add a new field
        return render_to_response('new-script.html', RequestContext(request, {
            'hidden_form': storage.hidden_form,
            'general_form': storage.form_general,
            'params_form': storage.form_details,
            'source_form': storage.form_sources,
            'layout': 'inline',
            'curr_tab': 'params',
            'status': 'info',
            }))
    return render_to_response('forms/new_param_modal.html', RequestContext(request, {
        'msg': msg, 'basic': basic_form, 'extra': extra_form, "type": which,
    }))

def create(request):
    tab = 'general'
    ParametersTable = breezeForms.formset_factory(
                                        breezeForms.ScriptDetails,
                                        formset=breezeForms.BaseScriptDetails, extra=1, max_num=15
    )
    if request.method == 'POST':
        storage.hidden_form = breezeForms.HiddenForm(request.POST)
        tab = storage.hidden_form['next'].value()
        if storage.hidden_form['curr'].value() == 'general':
            storage.form_general = breezeForms.ScriptGeneral(request.POST, request.FILES)
            storage.form_general.is_valid()
#                storage.new_script.logo = request.FILES['logo']
        elif storage.hidden_form['curr'].value() == 'params':
            if storage.hidden_form['curr'].value() == storage.hidden_form['next'].value():
                cp = request.POST.copy()
                cp['form-TOTAL_FORMS'] = int(cp['form-TOTAL_FORMS']) + 1
                storage.form_details = ParametersTable(cp)
                storage.form_details.is_valid()
            else:
                storage.form_details = ParametersTable(request.POST)
                storage.form_details.is_valid()
        elif storage.hidden_form['curr'].value() == 'source':
            storage.form_sources = breezeForms.ScriptSources(request.POST, request.FILES)
            if storage.form_sources.is_valid():
                storage.new_script.code = request.FILES['code']
        elif storage.hidden_form['curr'].value() == 'summary':
            pass
    else:
        storage.hidden_form = breezeForms.HiddenForm()
        storage.form_general = breezeForms.ScriptGeneral()
        storage.form_details = ParametersTable()
        storage.form_sources = breezeForms.ScriptSources()
        storage.new_script = Rscripts()
    return render_to_response('new-script.html', RequestContext(request, {
        'hidden_form': storage.hidden_form,
        'general_form': storage.form_general,
        'params_form': storage.form_details,
        'source_form': storage.form_sources,
        'layout': 'inline',
        'curr_tab': tab,
        'status': 'info',
        }))

def save(request):
    if  storage.form_general.is_valid() and storage.form_details.is_valid() and storage.form_sources.is_valid():
        # .xml_from_form() - creates doc in tmp for now
        breezeForms.xml_from_form(storage.form_general, storage.form_details, storage.form_sources)
        storage.new_script.name = storage.form_general.cleaned_data['name']
        storage.new_script.inln = storage.form_general.cleaned_data['inln']
        storage.new_script.details = storage.form_general.cleaned_data['details']
        storage.new_script.category = storage.form_general.cleaned_data['category']
        storage.new_script.docxml.save('name.xml', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml')))
        storage.new_script.docxml.close()
        storage.new_script.save()
        # improve the manipulation with XML - tmp folder not a good idea!
        os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml")

        return HttpResponseRedirect('/scripts/')
    else:
        # need an error handler here!
        pass

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

