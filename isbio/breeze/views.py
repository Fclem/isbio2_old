# -*- coding: utf-8 -*-
import os
from django.core.files import File
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response

from rpy2.robjects import r
import xml.etree.ElementTree as xml

import forms as breezeForms
from breeze.models import Rscripts, newrscript


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

def create(request):
    ParametersTable = breezeForms.formset_factory(
                                        breezeForms.ScriptDetails,
                                        formset=breezeForms.BaseScriptDetails, extra=2, max_num=15
    )
    if request.method == 'POST':
        hidden_form = breezeForms.HiddenForm(request.POST)
        if hidden_form['curr'].value() == 'general':
            print "hey GENERAL"
        elif hidden_form['curr'].value() == 'params':
            print "hey PARAMS"
        elif hidden_form['curr'].value() == 'source':
            print "hey SOURCE"
        elif hidden_form['curr'].value() == 'summary':
            pass

    else:
        hidden_form = breezeForms.HiddenForm()
        form_general = breezeForms.ScriptGeneral()
        form_details = ParametersTable()
        form_sources = breezeForms.ScriptSources()

    return render_to_response('new-script.html', RequestContext(request, {
        'hidden_form': hidden_form,
        'general_form': form_general,
        'params_form': form_details,
        'source_form': form_sources,
        'layout': 'inline',
        'curr_tab': 'general',
        }))

def c_reate(request):
    global newrscript
    if  breezeForms.formG.is_valid():
        breezeForms.xml_from_form(breezeForms.formG, breezeForms.formD)
        newrscript.name = breezeForms.formG.cleaned_data['name']
        newrscript.inln = breezeForms.formG.cleaned_data['inln']
        newrscript.details = breezeForms.formG.cleaned_data['details']
        newrscript.docxml.save('name.xml', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml')))
        newrscript.docxml.close()
        newrscript.save()
        # improve the manipulation with XML - tmp folder not a good idea!
        os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml")

        breezeForms.formG = breezeForms.ScriptGeneral()
        breezeForms.formD = breezeForms.ScriptDetails()
        breezeForms.formS = breezeForms.ScriptSources()
        newrscript = Rscripts()
        return HttpResponseRedirect('/scripts/')
    else:
        return render_to_response('new-script.html', RequestContext(request, {
        'general_form': breezeForms.formG,
        'params_form': breezeForms.formD,
        'source_form': breezeForms.formS,
        'hidden_form': breezeForms.hidden_form,
        'layout': 'inline',
        'curr_tab': 'general',
        }))

def validate_general(request):
    global newrscript
    if request.method == 'POST':
        breezeForms.formG = breezeForms.ScriptGeneral(request.POST)
        breezeForms.hidden_form = breezeForms.HiddenForm(request.POST)
        print breezeForms.hidden_form['curr'].value()
        breezeForms.formG.is_valid()
    else:
        pass
    return render_to_response('new-script.html', RequestContext(request, {
        'general_form': breezeForms.formG,
        'params_form': breezeForms.formD,
        'source_form': breezeForms.formS,
        'hidden_form': breezeForms.hidden_form,
        'layout': 'inline',
        'curr_tab': 'params',
    }))

def validate_details(request):
    global newrscript
    if request.method == 'POST':
        breezeForms.formD = breezeForms.ScriptDetails(request.POST)
        breezeForms.hidden_form = breezeForms.HiddenForm(request.POST)
        mv = breezeForms.hidden_form['next'].value()
        print breezeForms.hidden_form['curr'].value()
        breezeForms.hidden_form.is_valid()
        breezeForms.formD.is_valid()
    else:
        pass
    return render_to_response('new-script.html', RequestContext(request, {
        'general_form': breezeForms.formG,
        'params_form': breezeForms.formD,
        'source_form': breezeForms.formS,
        'hidden_form': breezeForms.hidden_form,
        'layout': 'inline',
        'curr_tab': mv,
    }))

def validate_sources(request):
    global newrscript
    if request.method == 'POST':
        breezeForms.formS = breezeForms.ScriptSources(request.POST, request.FILES)
        breezeForms.hidden_form = breezeForms.HiddenForm(request.POST)
        mv = breezeForms.hidden_form['next'].value()
        print breezeForms.hidden_form['curr'].value()
        breezeForms.hidden_form.is_valid()
        if breezeForms.formS.is_valid():
            newrscript.code = request.FILES['code']
    else:
        pass
    return render_to_response('new-script.html', RequestContext(request, {
        'general_form': breezeForms.formG,
        'params_form': breezeForms.formD,
        'source_form': breezeForms.formS,
        'hidden_form': breezeForms.hidden_form,
        'layout': 'horizontal',
        'curr_tab': mv,
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

