import os, shutil, re, sys, traceback
from rpy2.robjects import r
from rpy2.rinterface import RRuntimeError
from django.template.defaultfilters import slugify

def new_script_folder(name):
    path = ""
    return path

def schedule_job(job):
    # job.progress = 0
    job.save()
    return 1

def del_job(job):
    docxml_path = "/home/comrade/Projects/fimm/isbio/breeze/" + str(file_name('jobs', job.jname, job.juser.username))
    shutil.rmtree(docxml_path)
    job.delete()

def del_script(script):
    # docxml_path = "/home/comrade/Projects/fimm/isbio/breeze/" + str(file_name("r_scripts" , script.name, None))
    # shutil.rmtree(docxml_path)
    script.delete()

def run_job(job, script):
    loc = "/home/comrade/Projects/fimm/isbio/breeze/" + str(file_name('jobs', job.jname, job.juser.username))
    path = "/home/comrade/Projects/fimm/isbio/breeze/" + str(job.rexecut)
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
    rexec = open("/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r", 'w')
    script_header = open("/home/comrade/Projects/fimm/isbio/breeze/" + str(header), "rb").read()
    script_code = open("/home/comrade/Projects/fimm/isbio/breeze/" + str(code), "rb").read()

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
            path_to_datasets = "/home/comrade/Projects/fimm/isbio/breeze/datasets/"
            slug = slugify(data.cleaned_data[item.attrib['comment']]) + '.RData'
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(path_to_datasets) + str(slug) + '"\n'
        else:  # for text, text_are, drop_down, radio
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(data.cleaned_data[item.attrib['comment']]) + '"\n'

    tree.write('/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml')


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
    header = open("/home/comrade/Projects/fimm/isbio/breeze/tmp/header.txt", 'w')
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
    return "/home/comrade/Projects/fimm/isbio/breeze/" + str(file_name('jobs', name, user))

def file_name(loc, name, user=None):
    if loc == "jobs":
        slug = slugify(name + '_' + str(user))
    else:
        slug = slugify(name)
    return '%s/%s/' % (loc, slug)
