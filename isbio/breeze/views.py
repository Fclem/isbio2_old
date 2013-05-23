# -*- coding: utf-8 -*-
import os, copy, tempfile, zipfile, shutil, fnmatch
from datetime import datetime
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
from breeze.models import Rscripts, Jobs, DataSet, UserProfile, InputTemplate, Report, ReportType

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


def breeze(request):
    return render_to_response('index.html', RequestContext(request, {'layout': 'inline' }))

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')

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

@login_required(login_url='/')
def home(request):
    occurrences = dict()

    occurrences['jobs_running'] = Jobs.objects.filter(juser__exact=request.user).filter(status__exact="active").count()
    occurrences['jobs_scheduled'] = Jobs.objects.filter(juser__exact=request.user).filter(status__exact="scheduled").count()
    occurrences['jobs_history'] = Jobs.objects.filter(juser__exact=request.user).exclude(status__exact="scheduled").exclude(status__exact="active").count()

    occurrences['scripts_total'] = Rscripts.objects.filter(draft="0").count()
    occurrences['scripts_tags'] = Rscripts.objects.filter(draft="0").filter(istag="1").count()

    return render_to_response('home.html', RequestContext(request, {'home_status': 'active', 'dbStat': occurrences }))

@login_required(login_url='/')
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

@login_required(login_url='/')
def scripts(request, layout="list"):
    if layout == "nails":
        nails = True
    else:
        nails = False

    # all_scripts = Rscripts.objects.all()
    all_scripts = Rscripts.objects.filter(draft="0").filter(istag="0")

    cat_list = dict()
    categories = list()
    for script in all_scripts:
        if str(script.category).capitalize() not in categories:
            categories.append(str(script.category).capitalize())
            cat_list[str(script.category).capitalize()] = Rscripts.objects.filter(category__exact=str(script.category)).filter(draft="0").filter(istag="0")

    # if request.user.has_perm('breeze.add_rscripts'):
    #    cat_list['_My_Scripts_'] = Rscripts.objects.filter(author__exact=request.user)
    #    cat_list['_Datasets_'] = DataSet.objects.all()

    return render_to_response('scripts.html', RequestContext(request, {
        'script_list': all_scripts,
        'scripts_status': 'active',
        'cat_list': sorted(cat_list.iteritems()),
        'thumbnails': nails
    }))

@login_required(login_url='/')
def reports(request):
    all_reports = Report.objects.filter(status="ready").order_by('-created')
    report_type_lst = ReportType.objects.all()
    return render_to_response('reports.html', RequestContext(request, {'reports_status': 'active', 'reports': all_reports, 'rtypes': report_type_lst }))

@login_required(login_url='/')
def report_overview(request, rtype, iname, iid=None, mod=None):
    if mod is None:
        ### renders an Overview with available Tags ###

        # BUILD OVERVIEW SECTION
        overview = dict()
        overview['report_type'] = rtype
        overview['instance_name'] = iname
        overview['instance_id'] = iid
        overview['details'] = rshell.get_report_overview(rtype, iname, iid)

        # BUILD LIST OF TAGS
        # filter tags according to report type
        tags = Rscripts.objects.filter(draft="0").filter(istag="1").filter(report_type=ReportType.objects.get(type=rtype))

        attribs = dict()
        tags_attrib = list()
        for item in tags:
            attribs['id'] = item.id
            attribs['inline'] = str(item.inln)
            attribs['name'] = str(item.name)
            attribs['form'] = "no form"  # breezeForms.form_from_xml(xml=tree)
            tags_attrib.append(copy.deepcopy(attribs))

        return render_to_response('search.html', RequestContext(request, {'reports_status': 'active', 'overview': True, 'tags_available': tags_attrib, 'overview_info': overview }))

    elif mod == '-full':
        #### renders Full Report (should create a new tab/window for that) ####

        if request.method == 'POST':
            html = rshell.build_report(rtype, iname, iid, request.user, copy.deepcopy(request.POST))
            return HttpResponse(True)
            # return render_to_response('search.html', RequestContext(request, {'reports_status': 'active', 'full_report': True, 'report_html': html }))
        else:
            tags = None
            html = rshell.build_report(rtype, iname, iid, request.user, tags)
            return render_to_response('search.html', RequestContext(request, {'reports_status': 'active', 'full_report': True, 'report_html': html }))

    else:
        ### if smth stupid came as a mod ###
        return render_to_response('search.html', RequestContext(request, {'reports_status': 'active', 'search_bars': True }))

@login_required(login_url='/')
def search(request, what=None):
    report_type_lst = ReportType.objects.all()
    ds = DataSet.objects.all()
    ds_count = len(ds)

    overview = dict()
    query_val = str()
    overview['report_type'] = str()

    # when query
    if request.method == 'POST':
        result_type = what

        # search for ENTITIES (right bar)
        if what == 'entity':
            overview['report_type'] = request.POST['type']
            query_val = str(request.POST['query'])

            output = rshell.report_search(ds, overview['report_type'], query_val)

        # search for DATASETS (left bar)
        if what == 'dataset':
            output = ds

        return render_to_response('search.html', RequestContext(request, {
            'search_status': 'active',
            'search_bars': True,
            'search_result': True,
            'rtypes': report_type_lst,
            'ds_count': ds_count,
            'result_type': result_type,
            'query_value': query_val,
            'overview_info': overview,
            'output': output
        }))

    else:
        pass

    return render_to_response('search.html', RequestContext(request, {'search_status': 'active', 'search_bars': True, 'ds_count': ds_count, 'rtypes': report_type_lst }))

@login_required(login_url='/')
def resources(request):
    return render_to_response('resources.html', RequestContext(request, {'resources_status': 'active', }))

@login_required(login_url='/')
def manage_scripts(request):
    all_scripts = Rscripts.objects.all()
    return render_to_response('manage-scripts.html', RequestContext(request, {
        'script_list': all_scripts,
        'resources_status': 'active',
    }))

@login_required(login_url='/')
def manage_reports(request):
    return render_to_response('manage-reports.html', RequestContext(request, {
        'resources_status': 'active',
    }))

@login_required(login_url='/')
def dochelp(request):
    return render_to_response('help.html', RequestContext(request, {'help_status': 'active'}))


######################################
###      SUPPLEMENTARY VIEWS       ###
######################################
@login_required(login_url='/')
def script_editor(request, sid=None, tab=None):
    script = Rscripts.objects.get(id=sid)

    f_basic = breezeForms.ScriptBasics(edit=script.name, initial={'name': script.name, 'inline': script.inln })
    f_attrs = breezeForms.ScriptAttributes(instance=script)
    f_logos = breezeForms.ScriptLogo()

    if tab is None:
        tab = '-general_tab'

    return render_to_response('script-editor.html', RequestContext(request, {
        str(tab)[1:]: 'active',
        'resources_status': 'active',
        'script': script,
        'basic_form': f_basic,
        'attr_form': f_attrs,
        'logo_form': f_logos
    }))

@login_required(login_url='/')
def script_editor_update(request, sid=None):
    if request.method == 'POST':
        script = Rscripts.objects.get(id=sid)

        # General Tab
        if request.POST['form_name'] == 'general':
            f_basic = breezeForms.ScriptBasics(script.name, request.POST)
            if f_basic.is_valid():
                rshell.update_script_dasics(script, f_basic)
                return HttpResponseRedirect('/resources/scripts/script-editor/' + str(script.id) + '-general_tab')
        else:
            f_basic = breezeForms.ScriptBasics(edit=script.name, initial={'name': script.name, 'inline': script.inln })

        # Description Tab
        if request.POST['form_name'] == 'description' and request.is_ajax():
            return HttpResponse(rshell.update_script_description(script, request.POST))
        else:
            pass

        # Attributes Tab
        if request.POST['form_name'] == 'attributes':
            f_attrs = breezeForms.ScriptAttributes(request.POST, instance=script)
            if f_attrs.is_valid():
                f_attrs.save()
                script.creation_date = datetime.now()
                script.save()
                return HttpResponseRedirect('/resources/scripts/script-editor/' + str(script.id) + '-attribut_tab')
        else:
            f_attrs = breezeForms.ScriptAttributes(instance=script)

        # Form Builder Tab
        if request.POST['form_name'] == 'xml_data' and request.is_ajax():
            return HttpResponse(rshell.update_script_xml(script, request.POST['xml_data']))
        else:
            pass  # return HttpResponse(False)

        # Sources Tab
        if request.POST['form_name'] == 'source_files' and request.is_ajax():
            rshell.update_script_sources(script, request.POST)
            return HttpResponse(True)
        else:
            pass  # return HttpResponse(False)

        # Logos Tab
        if request.POST['form_name'] == 'logos':
            f_logos = breezeForms.ScriptLogo(request.POST, request.FILES)
            if f_logos.is_valid():
                rshell.update_script_logo(script, request.FILES['logo'])
                return HttpResponseRedirect('/resources/scripts/script-editor/' + str(script.id) + '-logos_tab')
        else:
            f_logos = breezeForms.ScriptLogo()

        return render_to_response('script-editor.html', RequestContext(request, {
                'resources_status': 'active',
                'script': script,
                'basic_form': f_basic
                # 'attr_form': f_attrs,
                # 'logo_form': f_logos
            }))
    # if NOT POST
    return HttpResponseRedirect('/resources/scripts/script-editor/' + script.id)

@login_required(login_url='/')
def get_form(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    builder_form = ""

    if request.method == 'GET' and sid is not None:
        file_path = rshell.settings.MEDIA_ROOT + str(script.docxml)

        if os.path.isfile(file_path):
            tree = xml.parse(file_path)
            if tree.getroot().find('builder') is not None:
                builder_form = tree.getroot().find('builder').text
            else:
                builder_form = "False"
        else:
            builder_form = "False"

    return HttpResponse(builder_form)


@login_required(login_url='/')
def get_rcode(request, sid=None, sfile=None):
    script = Rscripts.objects.get(id=sid)
    rcode = ""
    if request.method == 'GET' and sid is not None:

        if sfile == 'Header':
            file_path = rshell.settings.MEDIA_ROOT + str(script.header)
        elif sfile == 'Main':
            file_path = rshell.settings.MEDIA_ROOT + str(script.code)

        if os.path.isfile(file_path):
            handle = open(file_path, 'r')
            rcode = handle.read()
            handle.close()
        else:
            rcode = "file does not exist"

    return HttpResponse(rcode)

@login_required(login_url='/')
def delete_job(request, jid):
    job = Jobs.objects.get(id=jid)
    if (job.status == "scheduled"):
        tab = ""
    else:
        tab = "history"
    rshell.del_job(job)
    return HttpResponseRedirect('/jobs/' + tab)

@login_required(login_url='/')
def delete_script(request, sid):
    script = Rscripts.objects.get(id=sid)
    rshell.del_script(script)
    return HttpResponseRedirect('/resources/scripts/')

@login_required(login_url='/')
def delete_report(request, rid):
    report = Report.objects.get(id=rid)
    rshell.del_report(report)
    return HttpResponseRedirect('/reports/')

@login_required(login_url='/')
def read_descr(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    return render_to_response('forms/descr_modal.html', RequestContext(request, { 'scr': script }))

@login_required(login_url='/')
def edit_job(request, jid=None, mod=None):
    job = Jobs.objects.get(id=jid)
    tree = xml.parse(str(settings.MEDIA_ROOT) + str(job.docxml))
    user_info = User.objects.get(username=request.user)

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

            rshell.schedule_job(job, request.POST)

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
        'email': user_info.email
    }))

@login_required(login_url='/')
def create_job(request, sid=None):
    script = Rscripts.objects.get(id=sid)
    new_job = Jobs()
    tree = xml.parse(str(settings.MEDIA_ROOT) + str(script.docxml))
    script_name = str(script.name)  # tree.getroot().attrib['name']
    script_inline = script.inln
    user_info = User.objects.get(username=request.user)

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

            rshell.schedule_job(new_job, request.POST)

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
        'email': user_info.email
    }))

@login_required(login_url='/')
def run_script(request, jid):
    job = Jobs.objects.get(id=jid)
    script = str(job.script.code)
    p = Process(target=rshell.run_job, args=(job, script))
    p.start()

    # rshell.run_job(job, script)
    return HttpResponseRedirect('/jobs/')

@login_required(login_url='/')
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

@login_required(login_url='/')
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

@login_required(login_url='/')
@permission_required('breeze.add_rscripts', login_url="/")
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

@login_required(login_url='/')
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
    script = job.jname  # docxml.getroot().attrib["name"]
    inline = job.script.inln  # docxml.getroot().find('inline').text

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

@login_required(login_url='/')
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

@login_required(login_url='/')
def send_template(request, name):
    template = InputTemplate.objects.get(name=name)
    path_to_file = str(settings.MEDIA_ROOT) + str(template.file)
    f = open(path_to_file, 'r')
    myfile = File(f)
    response = HttpResponse(myfile, mimetype='application/force-download')
    folder, slash, file = str(template.file).rpartition('/')
    response['Content-Disposition'] = 'attachment; filename=' + file
    return response

@login_required(login_url='/')
def send_file(request, ftype, fname):
    """
        Supposed to be generic function that can send single file to client.
        Each IF case prepare dispatch data of a certain type.
        ! Should supbstitute send_template() function soon !
    """
    if ftype == 'dataset':
        fitem = DataSet.objects.get(name=str(fname))
        local_path = str(fitem.rdata)
        path_to_file = str(settings.MEDIA_ROOT) + local_path

    if ftype == 'report':
        fitem = Report.objects.get(id=fname)
        local_path = fitem.home + '/report.html'
        path_to_file = str(settings.MEDIA_ROOT) + local_path

    f = open(path_to_file, 'r')
    myfile = File(f)
    response = HttpResponse(myfile, mimetype='application/force-download')
    folder, slash, file = local_path.rpartition('/')
    response['Content-Disposition'] = 'attachment; filename=' + file
    return response

@login_required(login_url='/')
def update_jobs(request, jid):
    job = Jobs.objects.get(id=jid)
    response = dict(id=job.id, name=str(job.jname), staged=str(job.staged), status=str(job.status), progress=job.progress)

    return HttpResponse(simplejson.dumps(response), mimetype='application/json')

@login_required(login_url='/')
def send_dbcontent(request, content, iid=None):
    response = dict()

    if content == "datasets":
        clist = DataSet.objects.all()
    elif content == "templates":
        clist = InputTemplate.objects.all()
    elif content == "description":
        script = Rscripts.objects.get(id=int(iid[1:]))
        response["description"] = script.details
        return HttpResponse(simplejson.dumps(response), mimetype='application/json')
    else:
        # return empty dictionary if content was smth creepy
        return HttpResponse(simplejson.dumps(response), mimetype='application/json')

    for item in clist:
        response[item.name] = item.description

    return HttpResponse(simplejson.dumps(response), mimetype='application/json')


@login_required(login_url='/')
def builder(request):
    form = breezeForms.ScriptMainForm()
    return render_to_response('form-builder.html', RequestContext(request, {'forma': form, }))


@login_required(login_url='/')
def new_script_dialog(request):
    """
        This view provides a dialog to create a new script and save new script in DB.
        If script name is valid, the view creates an instance in DB which has the following fields completed:
        Name, Category, Creation Date, Author and Script's root folder.
    """
    form = breezeForms.NewScriptDialog(request.POST or None)

    if form.is_valid():
        sname = str(form.cleaned_data.get('name', None))
        sinline = str(form.cleaned_data.get('inline', None))
        newpath = rshell.init_script(sname, sinline, request.user)
        return HttpResponseRedirect('/resources/scripts/')

    return render_to_response('forms/basic_form_dialog.html', RequestContext(request, {
        'form': form,
        'action': '/new-script/',
        'header': 'Create New Script',
        'layout': 'horizontal',
        'submit': 'Add'
    }))

@login_required(login_url='/')
def new_rtype_dialog(request):
    """
        This view provides a dialog to create a new report type in DB.
    """
    form = breezeForms.NewRepTypeDialog(request.POST or None)

    if form.is_valid():
        form.save()
        return HttpResponse(True)

    return render_to_response('forms/basic_form_dialog.html', RequestContext(request, {
        'form': form,
        'action': '/new-rtype/',
        'header': 'Create New Report Type',
        'layout': 'horizontal',
        'submit': 'Add'
    }))


@login_required(login_url='/')
def update_user_info_dialog(request):
    user_info = User.objects.get(username=request.user)

    if request.method == 'POST':
        personal_form = breezeForms.PersonalInfo(request.POST)
        if personal_form.is_valid():
            user_info.first_name = personal_form.cleaned_data.get('first_name', None)
            user_info.last_name = personal_form.cleaned_data.get('last_name', None)
            user_info.email = personal_form.cleaned_data.get('email', None)
            user_info.save()
            return HttpResponseRedirect('/home/')
        else:
            return render_to_response('forms/user_info.html', RequestContext(request, {
                'form': personal_form,
                'action': '/update-user-info/'
            }))
    else:
        personal_form = breezeForms.PersonalInfo(initial={'first_name': user_info.first_name, 'last_name': user_info.last_name, 'email': user_info.email })

    return render_to_response('forms/user_info.html', RequestContext(request, {
        'form': personal_form,
        'action': '/update-user-info/'
    }))
