import os, shutil, re, sys, traceback
from datetime import datetime
import xml.etree.ElementTree as xml
from rpy2.robjects import r
from rpy2.rinterface import RRuntimeError
from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.files import File
import breeze.models

def init_script(name, person):
    spath = str(settings.MEDIA_ROOT) + str(get_folder_name("scripts" , name, None))

    if not os.path.isdir(spath):
        os.makedirs(spath)
        dbitem = breeze.models.Rscripts(name=name, author=person)
        dbitem.save()
        return spath

    return False

def update_script_dasics(script, form):
    """ 
        Careates a new folder for script and makes file copies but preserves db istance id 
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

def update_script_xml(script, xml_data):
    if os.path.isfile(str(settings.MEDIA_ROOT) + str(script.docxml)):
        os.remove(str(settings.MEDIA_ROOT) + str(script.docxml))
    root = xml.Element('rScript')
    root.attrib['name'] = str(script.name)
    inline = xml.Element('inline')
    inline.text = str(script.inln)
    root.append(inline)
    details = xml.Element('details')
    details.text = str(script.details)
    root.append(details)
    draft = xml.Element('draft')
    draft.attrib['val'] = str(script.draft)
    root.append(draft)
    input_array = xml.Element('inputArray')

    # important stuff goes here
    input_array.text = xml_data

    root.append(input_array)

    newxml = open(str(settings.TEMP_FOLDER) + 'script.xml', 'w')
    xml.ElementTree(root).write(newxml)
    newxml.close()

    script.docxml.save('script.xml', File(open(str(settings.TEMP_FOLDER) + 'script.xml')))
    script.creation_date = datetime.now()
    script.save()
    os.remove(str(settings.TEMP_FOLDER) + 'script.xml')
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
    # job.progress = 0
    job.save()
    return 1

def del_job(job):
    docxml_path = str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', job.jname, job.juser.username))
    shutil.rmtree(docxml_path)
    job.delete()


def run_job(job, script):
    loc = str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', job.jname, job.juser.username))
    path = str(settings.MEDIA_ROOT) + str(job.rexecut)
    job.progress = 10
    job.save()

    try:
        r.assign('location', loc)
        r('setwd(toString(location))')

        job.progress = 30
        job.save()
        r('Sys.sleep(2)')
        job.progress = 50
        job.save()
        r('Sys.sleep(1)')
        job.progress = 70
        job.save()

        r.assign('path', path)
        r('source(toString(path))')
    except RRuntimeError:
        job.status = "failed"

        log = open(loc + job.jname + ".log", 'w')
        Type, Value, Trace = sys.exc_info()
        log.write("Type: %s \nValue: %s \nTrace: %s \n\n" % (str(Type), str(Value), str(Trace)))
        log.write("print_exception()".center(40, "-") + "\n")
        traceback.print_exception(Type, Value, Trace, limit=5, file=log)
        log.close()
    else:
        job.status = "succeed"
        job.progress = 100

    job.save()
    return 1

def assemble_job_folder(jname, juser, tree, data, code, header, FILES):
    # rexec = open("/home/comrade/Projects/fimm/tmp/rexec.r", 'w')
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
        else:  # for text, text_are, drop_down, radio
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(data.cleaned_data[item.attrib['comment']]) + '"\n'

    # tree.write('/home/comrade/Projects/fimm/tmp/job.xml')
    tree.write(str(settings.TEMP_FOLDER) + 'job.xml')


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

    r('library(vcd)')
    r.assign('dataset', str(path))
    r('load(dataset)')
    r('dataSet1 <- sangerSet[1:131,]')
    drugs = r('featureNames(dataSet1)')

    for pill in drugs:
        lst.append(dict(name=str(pill), db="Sanger.RData"))

    return lst

def report_search(data_set, report_type, query):
    data_set = str(settings.MEDIA_ROOT) + str(data_set)
    lst = list()

    if str(report_type) == 'Drug':
        r('library(vcd)')
        r.assign('dataset', str(data_set))
        r('load(dataset)')
        r('dataSet1 <- sangerSet[1:131,]')
        r('featureNames(dataSet1) <- gsub("_IC_50","",featureNames(dataSet1))')
        drugs = r('featureNames(dataSet1)')

        if str(query) == "*":
            for pill in drugs:
                lst.append(dict(name=str(pill), db="Sanger.RData"))

        else:
            for pill in drugs:
                if str(pill) == str(query):
                    lst.append(dict(name=str(pill), db="Sanger.RData"))

    return lst
