import shutil
from rpy2.robjects import r
from django.template.defaultfilters import slugify

def submit_job(job):
    job.save()
    return 1

def del_job(job):
    docxml_path = "/home/comrade/Projects/fimm/isbio/breeze/" + str(file_name('jobs', job.jname))
    shutil.rmtree(docxml_path)
    job.delete()

def del_script(script):
    docxml_path = "/home/comrade/Projects/fimm/isbio/breeze/" + str(file_name("r_scripts" , script.name))
    shutil.rmtree(docxml_path)
    script.delete()

def run_job(job, script):
    loc = "/home/comrade/Projects/fimm/isbio/breeze/" + str(file_name('jobs', job.jname))
    r.assign('location', loc)
    r('setwd(toString(location))')

    path = "/home/comrade/Projects/fimm/isbio/breeze/" + str(job.rexecut)
    r.assign('path', path)
    r('source(toString(path))')

    job.status = "succeed"
    job.save()
    return 1

def get_job_folder(name):
    return "/home/comrade/Projects/fimm/isbio/breeze/" + str(file_name('jobs', name))

def file_name(loc, name):
        slug = slugify(name)
        return '%s/%s/' % (loc, slug)
