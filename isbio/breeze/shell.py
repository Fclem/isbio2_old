from rpy2.robjects import r
import xml.etree.ElementTree as xml


def submit_job(job):
    print "submit job"
    job.save()
    return 1
#    script = Rscripts.objects.get(id=sid)
#    xml_path = "/home/comrade/Projects/fimm/isbio/breeze/" + str(script.docxml)
#    code_path = "/home/comrade/Projects/fimm/isbio/breeze/" + str(script.code)
#    r.assign('code_path', code_path)
#    r('source(toString(code_path))')
#    return 1
