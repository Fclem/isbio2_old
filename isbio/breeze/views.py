# -*- coding: utf-8 -*-
import os, copy
import shutil
from django.core.files import File
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response

from rpy2.robjects import r
import xml.etree.ElementTree as xml
import shell as rshell

import forms as breezeForms
from breeze.models import Rscripts, Jobs
from django.forms.formsets import INITIAL_FORM_COUNT

class RequestStorage():
    form_details = dict()
    def get_param_list(self):
        class creepy():
            pass
        tmp = creepy()
        plist = list()
        pkeys = self.form_details.keys()
        pkeys.sort()
        for key in pkeys:
            tmp.var = self.form_details[key][0].cleaned_data['inline_var']
            tmp.type = self.form_details[key][0].cleaned_data['type']
            plist.append(copy.deepcopy(tmp))
        return plist

    def del_param(self, var):
        del self.form_details[var]

storage = RequestStorage()

def breeze(request):
    return render_to_response('index.html')

def base(request):
    return render_to_response('base.html')

def login(request):
    return render_to_response('login.html')

def home(request):
    return render_to_response('home.html', {'home_status': 'active'})

def scripts(request):
    all_scripts = Rscripts.objects.order_by("name")
    return render_to_response('scripts.html', {'script_list': all_scripts, 'scripts_status': 'active'})

def jobs(request):
    sched_jobs = Jobs.objects.filter(status__exact="scheduled")
    histr_jobs = Jobs.objects.exclude(status__exact="scheduled")
    return render_to_response('jobs.html', {
        'scheduled': sched_jobs,
        'history': histr_jobs,
        'jobs_status': 'active',
    })

def delete_job(request, jid):
    job = Jobs.objects.get(id=jid)
    rshell.del_job(job)
    return HttpResponseRedirect('/jobs/')

def delete_script(request, sid):
    script = Rscripts.objects.get(id=sid)
    rshell.del_script(script)
    return HttpResponseRedirect('/scripts/')

def read_descr(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    return render_to_response('forms/descr_modal.html', RequestContext(request, { 'scr': script }))

def edit_job(request, jid=None):
    job = Jobs.objects.get(id=jid)
    tree = xml.parse("/home/comrade/Projects/fimm/isbio/breeze/" + str(job.docxml))

    if request.method == 'POST':
        head_form = breezeForms.BasicJobForm(request.POST)
        custom_form = breezeForms.form_from_xml(xml=tree, req=request)
        if head_form.is_valid() and custom_form.is_valid():
            loc = rshell.get_job_folder(job.jname)
            shutil.rmtree(loc)

            breezeForms.get_job_xml(tree, custom_form, str(job.script.code), str(job.script.header))
            job.jname = head_form.cleaned_data['job_name']
            job.jdetails = head_form.cleaned_data['job_details']

            job.rexecut.save('name.r', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r')))
            job.docxml.save('name.xml', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml')))
            job.rexecut.close()
            job.docxml.close()

            rshell.submit_job(job)

            # improve the manipulation with XML - tmp folder not a good idea!
            os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml")
            os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r")
        return HttpResponseRedirect('/jobs/')
    else:
        head_form = breezeForms.BasicJobForm(initial={'job_name': str(job.jname), 'job_details': str(job.jdetails)})
        custom_form = breezeForms.form_from_xml(xml=tree)

    return render_to_response('forms/user_modal.html', RequestContext(request, {
        'url': "/scripts/apply-script/" + str(jid),
        'name': str(job.script.name),
        'inline': str(job.script.inln),
        'headform': head_form,
        'custform': custom_form,
        'layout': "horizontal",
        'mode': 'edit',
    }))

def create_job(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    new_job = Jobs()
    tree = xml.parse("/home/comrade/Projects/fimm/isbio/breeze/" + str(script.docxml))
    script_name = tree.getroot().attrib['name']
    script_inline = script.inln

    if request.method == 'POST':
        print request.FILES
        head_form = breezeForms.BasicJobForm(request.POST)
        custom_form = breezeForms.form_from_xml(xml=tree, req=request)
        if head_form.is_valid() and custom_form.is_valid():
            breezeForms.get_job_xml(tree, custom_form, str(script.code), str(script.header))
            new_job.jname = head_form.cleaned_data['job_name']
            new_job.jdetails = head_form.cleaned_data['job_details']
            new_job.script = script
            new_job.status = "scheduled"

            new_job.rexecut.save('name.r', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r')))
            new_job.docxml.save('name.xml', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml')))
            new_job.rexecut.close()
            new_job.docxml.close()

            rshell.submit_job(new_job)

            # improve the manipulation with XML - tmp folder not a good idea!
            os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml")
            os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r")
            return HttpResponseRedirect('/jobs/')
    else:
        head_form = breezeForms.BasicJobForm()
        custom_form = breezeForms.form_from_xml(xml=tree)

    return render_to_response('forms/user_modal.html', RequestContext(request, {
        # 'id': sid,
        'url': "/scripts/apply-script/" + str(sid),
        'name': script_name,
        'inline': script_inline,
        'headform': head_form,
        'custform': custom_form,
        'layout': "horizontal",
        'mode': 'create',
    }))

def run_script(request, jid):
    job = Jobs.objects.get(id=jid)
    script = str(job.script.code)
    rshell.run_job(job, script)
    return HttpResponseRedirect('/jobs/')

def delete_param(request, which):
    storage.del_param(which)
    local_representation = storage.get_param_list()
    return render_to_response('new-script.html', RequestContext(request, {
            'hidden_form': storage.hidden_form,
            'general_form': storage.form_general,
            'params_form': local_representation,
            'source_form': storage.form_sources,
            'layout': 'inline',
            'curr_tab': 'params',
            'status': 'info',
        }))

def append_param(request, which):
    basic_form = breezeForms.AddBasic(request.POST or None)
    extra_form = None
    extra_form_valid = True
    if which == 'NUM':
        msg = 'NUMERIC'
    elif which == 'CHB':
        msg = 'CHECK BOX'
    elif which == 'DRP':
        msg = 'DROP DOWN'
        extra_form = breezeForms.AddOptions(request.POST or None)
        extra_form_valid = extra_form.is_valid()
    elif which == 'RAD':
        msg = 'RADIO BUTTONS'
        extra_form = breezeForms.AddOptions(request.POST or None)
        extra_form_valid = extra_form.is_valid()
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

    if basic_form.is_valid() and extra_form_valid:
        # implement adding new param as a separate function in STORAGE class
        storage.form_details[basic_form.cleaned_data['inline_var']] = list()
        storage.form_details[basic_form.cleaned_data['inline_var']].append(basic_form)
        storage.form_details[basic_form.cleaned_data['inline_var']].append(extra_form)
        local_representation = storage.get_param_list()
        return render_to_response('new-script.html', RequestContext(request, {
            'hidden_form': storage.hidden_form,
            'general_form': storage.form_general,
            'params_form': local_representation,
            'source_form': storage.form_sources,
            'layout': 'inline',
            'curr_tab': 'params',
            'status': 'info',
        }))
    return render_to_response('forms/new_param_modal.html', RequestContext(request, {
        'msg': msg, 'basic': basic_form, 'extra': extra_form, "type": which,
    }))

def create_script(request):
    tab = 'general'
    if request.method == 'POST':
        storage.hidden_form = breezeForms.HiddenForm(request.POST)
        tab = storage.hidden_form['next'].value()
        if storage.hidden_form['curr'].value() == 'general':
            storage.form_general = breezeForms.ScriptGeneral(request.POST, request.FILES)
            storage.form_general.is_valid()
            local_representation = storage.get_param_list()
#                storage.new_script.logo = request.FILES['logo']
        elif storage.hidden_form['curr'].value() == 'params':
            local_representation = storage.get_param_list()
        elif storage.hidden_form['curr'].value() == 'source':
            storage.form_sources = breezeForms.ScriptSources(request.POST, request.FILES)
            local_representation = storage.get_param_list()
            if storage.form_sources.is_valid():
                storage.new_script.code = request.FILES['code']
        elif storage.hidden_form['curr'].value() == 'summary':
            pass
    else:
        storage.hidden_form = breezeForms.HiddenForm()
        storage.form_general = breezeForms.ScriptGeneral()
        storage.form_details = dict()
        local_representation = storage.get_param_list()
        storage.form_sources = breezeForms.ScriptSources()
        storage.new_script = Rscripts()
    return render_to_response('new-script.html', RequestContext(request, {
        'hidden_form': storage.hidden_form,
        'general_form': storage.form_general,
        'params_form': local_representation,
        'source_form': storage.form_sources,
        'layout': 'inline',
        'curr_tab': tab,
        'status': 'info',
        'scripts_status': 'active',
        }))

def save(request):
    # validate form_details also somehow in the IF below
    if  storage.form_general.is_valid() and storage.form_sources.is_valid():
        # .xml_from_form() - creates doc in tmp for now
        breezeForms.xml_from_form(storage.form_general, storage.form_details, storage.form_sources)
        breezeForms.build_header(storage.form_sources.cleaned_data['header'])
        storage.new_script.name = storage.form_general.cleaned_data['name']
        storage.new_script.inln = storage.form_general.cleaned_data['inln']
        storage.new_script.details = storage.form_general.cleaned_data['details']
        storage.new_script.category = storage.form_general.cleaned_data['category']

        storage.new_script.docxml.save('name.xml', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml')))
        storage.new_script.header.save('name.txt', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/header.txt')))
        storage.new_script.docxml.close()
        storage.new_script.header.close()

        storage.new_script.save()
        # improve the manipulation with XML - tmp folder not a good idea!
        os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml")
        os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/header.txt")

        return HttpResponseRedirect('/scripts/')
    else:
        # need an error handler here!
        pass

def show_rcode(request, jid):
    job = Jobs.objects.get(id=jid)
    name = str(job.jname)
    f = open("/home/comrade/Projects/fimm/isbio/breeze/" + str(job.rexecut))
    filecontents = f.readlines()
    code = ''
    for line in filecontents:
        code = code + line + '\r\n'
    # code = str(open("/home/comrade/Projects/fimm/isbio/breeze/" + str(job.rexecut), "r").read())
    return render_to_response('forms/code_modal.html', RequestContext(request, { 'job': name, 'scr': code }))

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

