# -*- coding: utf-8 -*-
import os, copy, tempfile, zipfile, shutil
from django.contrib import auth
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required, permission_required

import xml.etree.ElementTree as xml
import shell as rshell

import forms as breezeForms
from breeze.models import Rscripts, Jobs, DataSet

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
    login_form = breezeForms.LoginForm(request.POST or None)
    if login_form.is_valid():
        username = request.POST['user_name']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect('/home/')

    return render_to_response('index.html', RequestContext(request, {'log_form': login_form, 'layout': 'inline' }))

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/breeze/')

def base(request):
    return render_to_response('base.html')

@login_required(login_url='/breeze/')
def home(request):
    return render_to_response('home.html', RequestContext(request, {'home_status': 'active'}))

@login_required(login_url='/breeze/')
def scripts(request):
    all_scripts = Rscripts.objects.all()

    cat_list = dict()
    categories = list()
    for script in all_scripts:
        if str(script.category).capitalize() not in categories:
            categories.append(str(script.category).capitalize())
            cat_list[str(script.category).capitalize()] = Rscripts.objects.filter(category__exact=str(script.category))

    if request.user.has_perm('breeze.add_rscripts'):
        cat_list['_My_Scripts_'] = Rscripts.objects.filter(author__exact=request.user)
        cat_list['_Datasets_'] = DataSet.objects.all()

    return render_to_response('scripts.html', RequestContext(request, {
        'script_list': all_scripts,
        'scripts_status': 'active',
        'cat_list': sorted(cat_list.iteritems())
    }))

@login_required(login_url='/breeze/')
def jobs(request):
    sched_jobs = Jobs.objects.filter(juser__exact=request.user).filter(status__exact="scheduled")
    histr_jobs = Jobs.objects.filter(juser__exact=request.user).exclude(status__exact="scheduled")
    return render_to_response('jobs.html', RequestContext(request, {
        'scheduled': sched_jobs,
        'history': histr_jobs,
    }))

@login_required(login_url='/breeze/')
def delete_job(request, jid):
    job = Jobs.objects.get(id=jid)
    rshell.del_job(job)
    return HttpResponseRedirect('/jobs/')

@login_required(login_url='/breeze/')
def delete_script(request, sid):
    script = Rscripts.objects.get(id=sid)
    rshell.del_script(script)
    return HttpResponseRedirect('/scripts/')

@login_required(login_url='/breeze/')
def read_descr(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    return render_to_response('forms/descr_modal.html', RequestContext(request, { 'scr': script }))

@login_required(login_url='/breeze/')
def edit_job(request, jid=None, mod=None):
    job = Jobs.objects.get(id=jid)
    tree = xml.parse("/home/comrade/Projects/fimm/isbio/breeze/" + str(job.docxml))

    if mod is not None:
        mode = 'replicate'
        tmpname = str(job.jname) + '_REPL'
    else:
        mode = 'edit'
        tmpname = str(job.jname)

    if request.method == 'POST':
        head_form = breezeForms.BasicJobForm(request.POST)
        custom_form = breezeForms.form_from_xml(xml=tree, req=request)
        if head_form.is_valid() and custom_form.is_valid():
            rshell.assemble_job_folder(str(head_form.cleaned_data['job_name']), tree, custom_form,
                                                    str(job.script.code), str(job.script.header), request.FILES)

            if mode == 'replicate':
                tmpscript = job.script
                job = Jobs()
                job.script = tmpscript
                job.status = "scheduled"
                job.juser = request.user
            else:
                loc = rshell.get_job_folder(job.jname)
                shutil.rmtree(loc)

            job.jname = head_form.cleaned_data['job_name']
            job.jdetails = head_form.cleaned_data['job_details']

            job.rexecut.save('name.r', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r')))
            job.docxml.save('name.xml', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml')))
            job.rexecut.close()
            job.docxml.close()

            rshell.schedule_job(job)

            # improve the manipulation with XML - tmp folder not a good idea!
            os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml")
            os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r")
            return HttpResponseRedirect('/jobs/')
    else:
        head_form = breezeForms.BasicJobForm(initial={'job_name': str(tmpname), 'job_details': str(job.jdetails)})
        custom_form = breezeForms.form_from_xml(xml=tree)

    return render_to_response('forms/user_modal.html', RequestContext(request, {
        'url': "/jobs/edit/" + str(jid),
        'name': str(job.script.name),
        'inline': str(job.script.inln),
        'headform': head_form,
        'custform': custom_form,
        'layout': "horizontal",
        'mode': mode,
    }))

@login_required(login_url='/breeze/')
def create_job(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    new_job = Jobs()
    tree = xml.parse("/home/comrade/Projects/fimm/isbio/breeze/" + str(script.docxml))
    script_name = tree.getroot().attrib['name']
    script_inline = script.inln

    if request.method == 'POST':
        head_form = breezeForms.BasicJobForm(request.POST)
        custom_form = breezeForms.form_from_xml(xml=tree, req=request)

        if head_form.is_valid() and custom_form.is_valid():
            rshell.assemble_job_folder(str(head_form.cleaned_data['job_name']), tree, custom_form,
                                                    str(script.code), str(script.header), request.FILES)
            new_job.jname = head_form.cleaned_data['job_name']
            new_job.jdetails = head_form.cleaned_data['job_details']
            new_job.script = script
            new_job.status = "scheduled"
            new_job.juser = request.user

            new_job.rexecut.save('name.r', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r')))
            new_job.docxml.save('name.xml', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml')))
            new_job.rexecut.close()
            new_job.docxml.close()

            rshell.schedule_job(new_job)

            # improve the manipulation with XML - tmp folder not a good idea!
            os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml")
            os.remove(r"/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r")
            return HttpResponseRedirect('/jobs/')
    else:
        head_form = breezeForms.BasicJobForm()
        custom_form = breezeForms.form_from_xml(xml=tree)

    return render_to_response('forms/user_modal.html', RequestContext(request, {
        'url': "/scripts/apply-script/" + str(sid),
        'name': script_name,
        'inline': script_inline,
        'headform': head_form,
        'custform': custom_form,
        'layout': "horizontal",
        'mode': 'create',
    }))

@login_required(login_url='/breeze/')
def run_script(request, jid):
    job = Jobs.objects.get(id=jid)
    script = str(job.script.code)
    rshell.run_job(job, script)
    return HttpResponseRedirect('/jobs/')

@login_required(login_url='/breeze/')
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

@login_required(login_url='/breeze/')
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
    elif which == 'DTS':
        msg = 'DATASET SELECTOR'
        extra_form = breezeForms.AddDatasetSelect(request.POST or None)
        extra_form_valid = extra_form.is_valid()
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

@login_required(login_url='/breeze/')
@permission_required('breeze.add_rscripts', login_url="/breeze/")
def create_script(request):
    tab = 'general'
    if request.method == 'POST':
        storage.hidden_form = breezeForms.HiddenForm(request.POST)
        tab = storage.hidden_form['next'].value()
        if storage.hidden_form['curr'].value() == 'general':
            storage.form_general = breezeForms.ScriptMainForm(request.POST, request.FILES)
            storage.form_general.is_valid()
            local_representation = storage.get_param_list()
        elif storage.hidden_form['curr'].value() == 'params':
            local_representation = storage.get_param_list()
        elif storage.hidden_form['curr'].value() == 'source':
            storage.form_sources = breezeForms.ScriptSources(request.POST, request.FILES)
            local_representation = storage.get_param_list()
            if storage.form_sources.is_valid():
                storage.code = request.FILES['code']
        elif storage.hidden_form['curr'].value() == 'summary':
            pass
    else:
        storage.hidden_form = breezeForms.HiddenForm()
        storage.form_general = breezeForms.ScriptMainForm()
        storage.form_details = dict()
        local_representation = storage.get_param_list()
        storage.form_sources = breezeForms.ScriptSources()

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

@login_required(login_url='/breeze/')
def save(request):
    # validate form_details also somehow in the IF below
    if  storage.form_general.is_valid() and storage.form_sources.is_valid():
        # .xml_from_form() - creates doc in tmp for now
        breezeForms.xml_from_form(storage.form_general, storage.form_details, storage.form_sources)
        rshell.build_header(storage.form_sources.cleaned_data['header'])

        dbinst = storage.form_general.save(commit=False)

        dbinst.author = request.user
        dbinst.code = storage.code
        dbinst.docxml.save('name.xml', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml')))
        dbinst.header.save('name.txt', File(open('/home/comrade/Projects/fimm/isbio/breeze/tmp/header.txt')))

        dbinst.save()

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

@login_required(login_url='/breeze/')
def send_zipfile(request, jid):
    job = Jobs.objects.get(id=jid)
    loc = rshell.get_job_folder(str(job.jname))
    files_list = os.listdir(loc)
    zipname = 'attachment; filename=' + str(job.jname) + '.zip'

    temp = tempfile.TemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    for item in files_list:
        archive.write(loc + item, str(item))

    archive.close()
    wrapper = FileWrapper(temp)
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = zipname  # 'attachment; filename=test.zip'
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response
