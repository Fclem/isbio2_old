import os, shutil, re, sys, traceback, stat
from datetime import datetime
import xml.etree.ElementTree as xml
from Bio import Entrez
from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.files import File, base
import breeze.models
import logging
import subprocess

logger = logging.getLogger(__name__)

def init_script(name, inline, person):
    spath = str(settings.MEDIA_ROOT) + str(get_folder_name("scripts" , name, None))

    if not os.path.isdir(spath):
        os.makedirs(spath)
        dbitem = breeze.models.Rscripts(name=name, inln=inline, author=person, details="empty")

        # create empty files for header, code and xml
        dbitem.header.save('name.txt', base.ContentFile('write your header here...'))
        dbitem.code.save('name.r', base.ContentFile('copy and paste main code here...'))
        dbitem.save()

        root = xml.Element('rScript')
        root.attrib['ID'] = str(dbitem.id)
        input_array = xml.Element('inputArray')
        input_array.text = "empty"
        root.append(input_array)

        newxml = open(str(settings.TEMP_FOLDER) + 'script_%s.xml' % (person), 'w')
        xml.ElementTree(root).write(newxml)
        newxml.close()

        dbitem.docxml.save('script.xml', File(open(str(settings.TEMP_FOLDER) + 'script_%s.xml' % (person))))
        dbitem.save()
        os.remove(str(settings.TEMP_FOLDER) + 'script_%s.xml' % (person))
        # dbitem.docxml.save('name.xml', base.ContentFile(''))

        return spath

    return False

def update_script_dasics(script, form):
    """ 
        Update script name and its inline description. In case of a new name it
        careates a new folder for script and makes file copies but preserves db istance id 
    """

    if str(script.name) != str(form.cleaned_data['name']):
        new_folder = str(settings.MEDIA_ROOT) + str(get_folder_name("scripts", str(form.cleaned_data['name']), None))
        old_folder = str(settings.MEDIA_ROOT) + str(get_folder_name("scripts", script.name, None))
        new_slug = slugify(form.cleaned_data['name'])

        if not os.path.isdir(new_folder):
            os.makedirs(new_folder)
            script.name = form.cleaned_data['name']
            script.inln = form.cleaned_data['inline']
            script.save()
            # copy folder
            files_list = os.listdir(old_folder)
            for item in files_list:
                fileName, fileExtension = os.path.splitext(item)
                # shutil.copy2(old_folder + item, str(new_folder) + str(new_slug) + str(fileExtension))
                if fileExtension == '.xml':
                    script.docxml.save('name.xml', File(open(old_folder + item)))
                elif fileExtension == '.txt':
                    script.header.save('name.txt', File(open(old_folder + item)))
                elif fileExtension == '.r' or fileExtension == '.R':
                    script.code.save('name.r', File(open(old_folder + item)))
                else:
                    script.logo.save('name' + str(fileExtension), File(open(old_folder + item)))

            # delete old folder
            shutil.rmtree(old_folder)

            script.creation_date = datetime.now()
            script.save()
        return True
    else:
        script.inln = form.cleaned_data['inline']
        script.creation_date = datetime.now()
        script.save()
        return True

def update_script_description(script, post_data):
    script.details = str(post_data['description_field'])
    script.creation_date = datetime.now()
    script.save()
    return True

def update_script_xml(script, xml_data):
    file_path = str(settings.MEDIA_ROOT) + str(script.docxml)
    if os.path.isfile(file_path):
        handle = open(file_path, 'w')
        handle.write(str(xml_data))
        handle.close()

        script.creation_date = datetime.now()
        script.save()
        return True
    else:
        return False

def update_script_sources(script, post_data):
    if post_data['source_file'] == 'Header':
        file_path = settings.MEDIA_ROOT + str(script.header)
    elif post_data['source_file'] == 'Main':
        file_path = settings.MEDIA_ROOT + str(script.code)

    handle = open(file_path, 'w')
    handle.write(str(post_data['mirrorEditor']))
    handle.close()

    script.creation_date = datetime.now()
    script.save()
    return True

def update_script_logo(script, pic):
    if script.logo:
        os.remove(str(settings.MEDIA_ROOT) + str(script.logo))

    script.logo = pic
    script.creation_date = datetime.now()
    script.save()
    return True

def del_script(script):
    folder = str(settings.MEDIA_ROOT) + str(get_folder_name("scripts" , script.name, None))

    if os.path.isdir(folder):
        shutil.rmtree(folder)
        script.delete()
        return True

    return False

def schedule_job(job):
    """
        Creates SGE configuration file for QSUB command
    """
    job_path = str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', job.jname, job.juser.username))
    config_path = job_path + slugify(job.jname + '_' + job.juser.username) + '_config.sh'
    config = open(config_path, 'w')
    # config should be executble
    st = os.stat(config_path)
    os.chmod(config_path, st.st_mode | stat.S_IEXEC)

    command = str(settings.R_ENGINE_PATH) + 'CMD BATCH ' + str(settings.MEDIA_ROOT) + str(job.rexecut)

    config.write("#!/bin/bash \n")
    config.write("#$ -M dmitrii.bychkov@helsinki.fi\n")
    config.write("#$ -m abe\n")
    config.write(command)
    config.close()

    # job.progress = 0
    job.save()
    return 1

def del_job(job):
    docxml_path = str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', job.jname, job.juser.username))
    shutil.rmtree(docxml_path)
    job.delete()


def run_job(job, script):
    loc = str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', job.jname, job.juser.username))
    config = loc + slugify(job.jname + '_' + job.juser.username) + '_config.sh'
    job.progress = 10
    job.save()

    default_dir = os.getcwd()
    os.chdir(loc)

    os.system('qsub -cwd %s' % config)
    job.status = "succeed"
    job.progress = 100
    job.save()

    os.chdir(default_dir)
    return 1

def assemble_job_folder(jname, juser, tree, data, code, header, FILES):
    """ 
        Builds (singe) R-exacutable file: puts together sources, header
        and input parameters from user
    """

    # create job folder
    directory = get_job_folder(jname, juser)
    if not os.path.exists(directory):
        os.makedirs(directory)

    rexec = open(str(settings.TEMP_FOLDER) + 'rexec.r', 'w')
    script_header = open(str(settings.MEDIA_ROOT) + str(header), "rb").read()
    script_code = open(str(settings.MEDIA_ROOT) + str(code), "rb").read()

    params = ''
    for item in tree.getroot().iter('inputItem'):
        item.set('val', str(data.cleaned_data[item.attrib['comment']]))
        if item.attrib['type'] == 'CHB':
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(data.cleaned_data[item.attrib['comment']]).upper() + '\n'
        elif item.attrib['type'] == 'NUM':
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(data.cleaned_data[item.attrib['comment']]) + '\n'
        elif item.attrib['type'] == 'TAR':
            lst = re.split(', |,|\n|\r| ', str(data.cleaned_data[item.attrib['comment']]))
            seq = 'c('
            for itm in lst:
                if itm != "":
                    seq = seq + '\"%s\",' % itm
            seq = seq[:-1] + ')'
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
        elif item.attrib['type'] == 'FIL' or item.attrib['type'] == 'TPL':
            add_file_to_job(jname, juser, FILES[item.attrib['comment']])
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(data.cleaned_data[item.attrib['comment']]) + '"\n'
        elif item.attrib['type'] == 'DTS':
            path_to_datasets = str(settings.MEDIA_ROOT) + "datasets/"
            slug = slugify(data.cleaned_data[item.attrib['comment']]) + '.RData'
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(path_to_datasets) + str(slug) + '"\n'
        elif item.attrib['type'] == 'MLT':
            res = ''
            seq = 'c('
            for itm in data.cleaned_data[item.attrib['comment']]:
                if itm != "":
                    res += str(itm) + ','
                    seq = seq + '\"%s\",' % itm
            seq = seq[:-1] + ')'
            item.set('val', res[:-1])
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
        else:  # for text, text_are, drop_down, radio
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(data.cleaned_data[item.attrib['comment']]) + '"\n'

    # tree.write('/home/comrade/Projects/fimm/tmp/job.xml')
    tree.write(str(settings.TEMP_FOLDER) + 'job.xml')


    rexec.write("setwd(\"%s\")\n" % directory)
    rexec.write("#####################################\n")
    rexec.write("###       Code Section            ###\n")
    rexec.write("#####################################\n")
    rexec.write(script_code)
    rexec.write("\n\n#####################################\n")
    rexec.write("### Parameters Definition Section ###\n")
    rexec.write("#####################################\n")
    rexec.write(params)
    rexec.write("\n\n#####################################\n")
    rexec.write("###       Assembly Section        ###\n")
    rexec.write("#####################################\n")
    rexec.write(script_header)

    rexec.close()
    return 1

def build_header(data):
    # header = open("/home/comrade/Projects/fimm/tmp/header.txt", 'w')
    header = open(str(settings.TEMP_FOLDER) + 'header.txt', 'w')
    string = str(data)
    header.write(string)
    header.close()
    return header

def add_file_to_job(job_name, user_name, f):
    directory = get_job_folder(job_name, user_name)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(directory + f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def get_job_folder(name, user=None):
    return str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', name, user))

def get_folder_name(loc, name, user=None):
    if loc == "jobs":
        slug = slugify(name + '_' + str(user))
    else:
        slug = slugify(name)
    return '%s/%s/' % (loc, slug)

def get_dataset_info(path):
    path = str(settings.MEDIA_ROOT) + str(path)
    lst = list()

#    r('library(vcd)')
#    r.assign('dataset', str(path))
#    r('load(dataset)')
#    r('dataSet1 <- sangerSet[1:131,]')
#    drugs = r('featureNames(dataSet1)')
#
#    for pill in drugs:
#        lst.append(dict(name=str(pill), db="Sanger.RData"))

    return lst

def report_search(data_set, report_type, query):
    lst = list()

    ### DRUG - local db search for drugs ###
    if str(report_type) == 'Drug' and len(query) > 0:
        for dset in data_set:
            if dset.name == "Sanger" or dset.name == "Duplicate":
                data = str(settings.MEDIA_ROOT) + str(dset.rdata)
#                r('library(vcd)')
#                r.assign('dataset', str(data))
#                r('load(dataset)')
#                r('dataSet1 <- sangerSet[1:131,]')
#                r('featureNames(dataSet1) <- gsub("_IC_50","",featureNames(dataSet1))')
#                drugs = r('featureNames(dataSet1)')
#
#                if str(query) == "*":
#                    for pill in drugs:
#                        lst.append(dict(id=str("drugID"), name=str(pill), db=str(dset.name)))
#
#                else:
#                    for pill in drugs:
#                        if str(pill) == str(query):
#                            lst.append(dict(id=str("drugID"), name=str(pill), db=str(dset.name)))

    ### GENE - Entrez search with BioPython ###
    elif str(report_type) == 'Gene' and len(query) > 0:
        Entrez.email = "dmitrii.bychkov@helsinki.fi"
        instance = str(query) + '[Gene/Protein Name]'  #  e.g. 'DMPK[Gene/Protein Name]'
        species = 'Homo sapiens[Organism]'
        search_query = instance + ' AND ' + species
        handle = Entrez.esearch(db="gene", term=search_query)
        record = Entrez.read(handle)

        for item in record["IdList"]:
            record_summary = Entrez.esummary(db="gene", id=item)
            record_summary = Entrez.read(record_summary)
            if record_summary[0]["Name"]:
                lst.append(dict(id=str(record_summary[0]["Id"]), name=str(record_summary[0]["Name"]), db="Entrez[Gene]"))

    return lst

def get_report_overview(report_type, instance_name, instance_id):
    """ 
        Most likely will call rCode to generate overview in order 
        to separate BREEZE and report content. 
    """
    summary_srting = str()

    if str(report_type) == 'Drug' and len(instance_name) > 0:
        summary_srting = ""

    if str(report_type) == 'Gene' and len(instance_name) > 0:
        if instance_id is not None:
            record_summary = Entrez.esummary(db="gene", id=instance_id)
            record_summary = Entrez.read(record_summary)

            if record_summary[0]["NomenclatureName"]:
                summary_srting += record_summary[0]["NomenclatureName"]
            if record_summary[0]["Orgname"]:
                summary_srting += " [" + record_summary[0]["Orgname"] + "] "
        else:
            summary_srting = "Instance ID is missing!"

    return summary_srting

def build_report(report_type, instance_name, instance_id, author, taglist):
    """
        taglist: corresponds to list of input fields from TagList form
        in reports.html. Contains tag IDs and enabled/disabled-value
    """
    html_path = str()
    loc = str(settings.MEDIA_ROOT) + str("reports/")
    path = str(author.username) + '_' + str(instance_name)  # actually, it's report folder name
    dochtml = path + '/' + str(instance_name)

    report_name = report_type + ' Report' + ' :: ' + instance_name  # displayed as a header

#    try:
#        # setup R working directory
#        r.assign('location', loc)
#        r('setwd(toString(location))')
#        # create report folder for our new report
#        r.assign('path', path)
#        r('dir.create( toString(path), showWarnings=FALSE );')
#        # load required libraries
#        r('require( Nozzle.R1 )')
#
#        # create root report element
#        r.assign('report_name', report_name)
#        r('REPORT <- newCustomReport(toString(report_name));')
#
#        # tags come as elements of the first level (sections)
#        # section_list = list()
#        for key, val in sorted(taglist.items()):
#            if len(val) == 1:
#                if int(val) == 1:
#                    # if tag enabled
#                    # get db instance (which is a script)
#                    tag = breeze.models.Rscripts.objects.get(id=int(key))
#
#
#                    # source main code segment
#                    code = str(settings.MEDIA_ROOT) + str(tag.code)
#                    r.assign('code', code)
#                    r('source(toString(code))')
#
#                    # input parameters definition
#                    rstring = 'instance_id <- %d' % (int(instance_id))
#                    r(rstring)
#
#                    # final step - fire header
#                    header = str(settings.MEDIA_ROOT) + str(tag.header)
#                    r.assign('header', header)
#                    r('source(toString(header))')
#
#                else:
#                    # if tag disabled - do nothing
#                    pass
#
#        # render report to file
#        r.assign('dochtml', dochtml)
#        r('writeReport( REPORT, filename=toString(dochtml));')
#
#    except RRuntimeError:
#        # redirect to error-page
#        html_path = str("reports/rfail.html")
#    else:
#        # succeed
#        html_path = 'reports/' + dochtml + '.html'

    return html_path
