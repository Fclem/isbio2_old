# -*- coding: utf-8 -*-
import os, copy, tempfile, zipfile, shutil, fnmatch
from collections import OrderedDict
from django.contrib import auth
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.conf import settings
from multiprocessing import Process
from django.utils import simplejson

import xml.etree.ElementTree as xml
import shell as rshell

import forms as breezeForms
from breeze.models import Rscripts, Jobs, DataSet, UserProfile, InputTemplate

class RequestStorage():
    form_details = OrderedDict()
    def get_param_list(self):
        class creepy():
            pass
        tmp = creepy()
        plist = list()
        pkeys = self.form_details.keys()
        for key in pkeys:
            tmp.var = self.form_details[key][0].cleaned_data['inline_var']
            tmp.type = self.form_details[key][0].cleaned_data['type']
            plist.append(copy.deepcopy(tmp))
        return plist

    def del_param(self, var):
        del self.form_details[var]

storage = RequestStorage()
storage.progress = 10

def test(request):
    print request.FILES
    return HttpResponseRedirect('/home/')

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

def register_user(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/home/')
    if request.method == 'POST':
        form = breezeForms.RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(username=form.cleaned_data['username'],
                                    email=form.cleaned_data['email'], password=form.cleaned_data['password'])
            g = Group.objects.get(name='USERS')
            g.user_set.add(user)
            user.is_staff = False
            user.save()
            profile = UserProfile(user=user, first_name=form.cleaned_data['first_name'],
                                        last_name=form.cleaned_data['last_name'], fimm_group=form.cleaned_data['fimm_group'])
            profile.save()
            return render_to_response('forms/welcome_modal.html', RequestContext(request))
        else:
            return render_to_response('forms/register.html', RequestContext(request, {'form': form}))
    else:
        form = breezeForms.RegistrationForm()
        return render_to_response('forms/register.html', RequestContext(request, {'form': form}))

    return 1

def base(request):
    return render_to_response('base.html')

@login_required(login_url='/breeze/')
def home(request):
    return render_to_response('home.html', RequestContext(request, {'home_status': 'active'}))

@login_required(login_url='/breeze/')
def dochelp(request):
    return render_to_response('help.html', RequestContext(request, {'help_status': 'active'}))

@login_required(login_url='/breeze/')
def scripts(request, layout="list"):
    if layout == "nails":
        nails = True
    else:
        nails = False

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
        'cat_list': sorted(cat_list.iteritems()),
        'thumbnails': nails
    }))

@login_required(login_url='/breeze/')
def jobs(request, state="scheduled"):
    if state == "history":
        tab = "history_tab"
        show_tab = "show_hist"
    else:
        tab = "scheduled_tab"
        show_tab = "show_sched"

    scheduled_jobs = Jobs.objects.filter(juser__exact=request.user).filter(status__exact="scheduled").order_by("-id")
    history_jobs = Jobs.objects.filter(juser__exact=request.user).exclude(status__exact="scheduled").exclude(status__exact="active").order_by("-id")
    active_jobs = Jobs.objects.filter(juser__exact=request.user).filter(status__exact="active").order_by("-id")
    return render_to_response('jobs.html', RequestContext(request, {
        str(tab): 'active',
        str(show_tab): 'active',
        'jobs_status': 'active',
        'dash_history': history_jobs[0:3],
        'scheduled': scheduled_jobs,
        'history': history_jobs,
        'current': active_jobs,
    }))

@login_required(login_url='/breeze/')
def delete_job(request, jid):
    job = Jobs.objects.get(id=jid)
    if (job.status == "scheduled"):
        tab = ""
    else:
        tab = "history"
    rshell.del_job(job)
    return HttpResponseRedirect('/jobs/' + tab)

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
    tree = xml.parse(str(settings.MEDIA_ROOT) + str(job.docxml))

    if mod is not None:
        mode = 'replicate'
        tmpname = str(job.jname) + '_REPL'
        edit = ""
    else:
        mode = 'edit'
        tmpname = str(job.jname)
        edit = str(job.jname)

    if request.method == 'POST':
        head_form = breezeForms.BasicJobForm(request.user, edit, request.POST)
        custom_form = breezeForms.form_from_xml(xml=tree, req=request)
        if head_form.is_valid() and custom_form.is_valid():

            if mode == 'replicate':
                tmpscript = job.script
                job = Jobs()
                job.script = tmpscript
                job.status = "scheduled"
                job.juser = request.user
                job.progress = 0
            else:
                loc = rshell.get_job_folder(str(job.jname), str(job.juser.username))
                shutil.rmtree(loc)

            rshell.assemble_job_folder(str(head_form.cleaned_data['job_name']), str(request.user), tree, custom_form,
                                                    str(job.script.code), str(job.script.header), request.FILES)

            job.jname = head_form.cleaned_data['job_name']
            job.jdetails = head_form.cleaned_data['job_details']

            job.rexecut.save('name.r', File(open(str(settings.TEMP_FOLDER) + 'rexec.r')))
            job.docxml.save('name.xml', File(open(str(settings.TEMP_FOLDER) + 'job.xml')))
            job.rexecut.close()
            job.docxml.close()

            rshell.schedule_job(job)

            # improve the manipulation with XML - tmp folder not a good idea!
            os.remove(str(settings.TEMP_FOLDER) + 'job.xml')
            os.remove(str(settings.TEMP_FOLDER) + 'rexec.r')
            return HttpResponseRedirect('/jobs/')
    else:
        head_form = breezeForms.BasicJobForm(user=request.user, edit=str(job.jname), initial={'job_name': str(tmpname), 'job_details': str(job.jdetails)})
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
    tree = xml.parse(str(settings.MEDIA_ROOT) + str(script.docxml))
    script_name = tree.getroot().attrib['name']
    script_inline = script.inln

    if request.method == 'POST':
        head_form = breezeForms.BasicJobForm(request.user, None, request.POST)
        custom_form = breezeForms.form_from_xml(xml=tree, req=request)

        if head_form.is_valid() and custom_form.is_valid():
            rshell.assemble_job_folder(str(head_form.cleaned_data['job_name']), str(request.user), tree, custom_form,
                                                    str(script.code), str(script.header), request.FILES)
            new_job.jname = head_form.cleaned_data['job_name']
            new_job.jdetails = head_form.cleaned_data['job_details']
            new_job.script = script
            new_job.status = "scheduled"
            new_job.juser = request.user
            new_job.progress = 0

            new_job.rexecut.save('name.r', File(open(str(settings.TEMP_FOLDER) + 'rexec.r')))
            new_job.docxml.save('name.xml', File(open(str(settings.TEMP_FOLDER) + 'job.xml')))
            new_job.rexecut.close()
            new_job.docxml.close()

            rshell.schedule_job(new_job)

            # improve the manipulation with XML - tmp folder not a good idea!
            os.remove(str(settings.TEMP_FOLDER) + 'job.xml')
            os.remove(str(settings.TEMP_FOLDER) + 'rexec.r')
            return HttpResponseRedirect('/jobs/')
    else:
        head_form = breezeForms.BasicJobForm(user=request.user, edit=None)
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
    p = Process(target=rshell.run_job, args=(job, script))
    job.status = "active"
    job.save()
    p.start()
    # rshell.run_job(job, script)
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
    elif which == 'TPL':
        msg = 'TEMPLATE INPUT'
        extra_form = breezeForms.AddTemplateInput(request.POST or None)
        extra_form_valid = extra_form.is_valid()
    elif which == 'DTS':
        msg = 'DATASET SELECTOR'
        extra_form = breezeForms.AddDatasetSelect(request.POST or None)
        extra_form_valid = extra_form.is_valid()
    else:
        pass

    if basic_form.is_valid() and extra_form_valid:
        # implement adding new param as a separate function in STORAGE class
        storage.form_details[str(basic_form.cleaned_data['inline_var'])] = list()
        storage.form_details[str(basic_form.cleaned_data['inline_var'])].append(basic_form)
        storage.form_details[str(basic_form.cleaned_data['inline_var'])].append(extra_form)
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
        storage.form_details = OrderedDict()
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
        dbinst.docxml.save('name.xml', File(open(str(settings.TEMP_FOLDER) + 'test.xml')))
        dbinst.header.save('name.txt', File(open(str(settings.TEMP_FOLDER) + 'header.txt')))

        dbinst.save()

        # improve the manipulation with XML - tmp folder not a good idea!
        os.remove(str(settings.TEMP_FOLDER) + 'test.xml')
        os.remove(str(settings.TEMP_FOLDER) + 'header.txt')

        return HttpResponseRedirect('/scripts/')
    else:
        # need an error handler here!
        return HttpResponseRedirect('/scripts/')

def show_rcode(request, jid):
    job = Jobs.objects.get(id=jid)
    docxml = xml.parse(str(settings.MEDIA_ROOT) + str(job.docxml))
    script = docxml.getroot().attrib["name"]
    inline = docxml.getroot().find('inline').text

    fields = list()
    values = list()
    input_array = docxml.getroot().find('inputArray')
    if input_array != None:
        for input_item in input_array:
            fields.append(input_item.attrib["comment"])
            values.append(input_item.attrib["val"])
    parameters = zip(fields, values)

    return render_to_response('forms/code_modal.html', RequestContext(request, {
        'name': str(job.jname),
        'script': script,
        'inline': inline,
        'description': str(job.jdetails),
        'input': parameters,
    }))

@login_required(login_url='/breeze/')
def send_zipfile(request, jid, mod=None):
    job = Jobs.objects.get(id=jid)
    loc = rshell.get_job_folder(str(job.jname), str(job.juser.username))
    files_list = os.listdir(loc)
    zipname = 'attachment; filename=' + str(job.jname) + '.zip'

    temp = tempfile.TemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)

    if mod is None:
        for item in files_list:
            archive.write(loc + item, str(item))
    elif mod == "-code":
        for item in files_list:
            if fnmatch.fnmatch(item, '*.r'):
                archive.write(loc + item, str(item))
    elif mod == "-result":
        for item in files_list:
            if not fnmatch.fnmatch(item, '*.xml') and not fnmatch.fnmatch(item, '*.r'):
                archive.write(loc + item, str(item))
    elif mod == "-summary":
        pass

    archive.close()
    wrapper = FileWrapper(temp)
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = zipname  # 'attachment; filename=test.zip'
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response

@login_required(login_url='/breeze/')
def send_template(request, name):
    template = InputTemplate.objects.get(name=name)
    path_to_file = str(settings.MEDIA_ROOT) + str(template.file)
    f = open(path_to_file, 'r')
    myfile = File(f)
    response = HttpResponse(myfile, mimetype='application/force-download')
    folder, slash, file = str(template.file).rpartition('/')
    response['Content-Disposition'] = 'attachment; filename=' + file
    return response


@login_required(login_url='/breeze/')
def update_jobs(request, jid):
    job = Jobs.objects.get(id=jid)
    response = dict(id=job.id, name=str(job.jname), staged=str(job.staged), status=str(job.status), progress=job.progress)

    return HttpResponse(simplejson.dumps(response), mimetype='application/json')

@login_required(login_url='/breeze/')
def builder(request):
    form = breezeForms.ScriptMainForm()
    return render_to_response('form-builder.html', RequestContext(request, {'forma': form, }))

@login_required(login_url='/breeze/')
def editor(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    basic = breezeForms.ScriptBasics()
    attrs = breezeForms.ScriptAttributes()
    logos = breezeForms.ScriptLogo()
    return render_to_response('script-editor.html', RequestContext(request, {
        'scripts_status': 'active',
        'script': script,
        'basic_form': basic,
        'attr_form': attrs,
        'logo_form': logos
    }))

@login_required(login_url='/breeze/')
def new_script_dialog(request):
    """
    This view provides a dialog to create a new script and save new script in DB.
    If script name is valid, the view creates an instance in DB which has the following fields completed:
    Name, Category, Creation Date, Author and Script's root folder.
    """
    form = breezeForms.NewScriptDialog(request.POST or None)

    if form.is_valid():
        sname = str(form.cleaned_data.get('name', None))
        newpath = rshell.new_script_folder(sname)
        dbitem = Rscripts(name=sname, author=request.user)
        dbitem.save()
        return HttpResponseRedirect('/scripts/')

    return render_to_response('forms/basic_form_dialog.html', RequestContext(request, {
        'form': form,
        'action': '/new-script/',
        'header': 'Create New Script',
        'layout': 'horizontal',
        'submit': 'Add'
    }))

