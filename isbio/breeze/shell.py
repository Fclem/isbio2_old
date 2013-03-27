import os, shutil, re, sys, traceback
from datetime import datetime
import xml.etree.ElementTree as xml
from rpy2.robjects import r
import rpy2.robjects as robjects
from rpy2.rinterface import RRuntimeError
from Bio import Entrez
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
    lst = list()

    ### DRUG - local db search for drugs ###
    if str(report_type) == 'Drug' and len(query) > 0:
        for dset in data_set:
            if dset.name == "Sanger" or dset.name == "Duplicate":
                data = str(settings.MEDIA_ROOT) + str(dset.rdata)
                r('library(vcd)')
                r.assign('dataset', str(data))
                r('load(dataset)')
                r('dataSet1 <- sangerSet[1:131,]')
                r('featureNames(dataSet1) <- gsub("_IC_50","",featureNames(dataSet1))')
                drugs = r('featureNames(dataSet1)')

                if str(query) == "*":
                    for pill in drugs:
                        lst.append(dict(id=str("drugID"), name=str(pill), db=str(dset.name)))

                else:
                    for pill in drugs:
                        if str(pill) == str(query):
                            lst.append(dict(id=str("drugID"), name=str(pill), db=str(dset.name)))

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
        to partition BREEZE and report content. 
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
    html_path = str()
    loc = str(settings.MEDIA_ROOT) + str("reports/")
    path = str(author.username) + '_' + str(instance_name)
    dochtml = path + '/' + str(instance_name)
    report_name = report_type + ' Report' + ' :: ' + instance_name

    try:
        r.assign('location', loc)
        r('setwd(toString(location))')
        r.assign('path', path)
        r('dir.create( toString(path), showWarnings=FALSE );')
        r('require( Nozzle.R1 )')

        r.assign('report_name', report_name)
        r('REPORT <- newCustomReport(toString(report_name));')

        # tags come here
        section_list = list()
        for key, val in sorted(taglist.items()):
            if len(val) == 1:
                if int(val) == 1:
                    tag = breeze.models.Rscripts.objects.get(id=int(key))

                    t_id = str(tag.id)
                    sec_id = t_id
                    t_name = str(tag.name)
                    sec_name = t_name
                    rstring = 'section_%s' % (sec_id)
                    section_list.append(rstring)
                    rstring = 'section_%s <- newSection("%s");' % (sec_id, sec_name)
                    r(rstring)

                    code = str(settings.MEDIA_ROOT) + str(tag.code)
                    r.assign('code', code)
                    r('source(toString(code))')

                    rstring = 'gene_id <- %d' % (int(instance_id))
                    r(rstring)

                    header = str(settings.MEDIA_ROOT) + str(tag.header)
                    r.assign('header', header)
                    r('source(toString(header))')

                    if sec_name == "Gene Summary":
                        rstring = 'section_%s <- addTo( section_%s, addTo( newSubSubSection("Gene ID"), newParagraph( mySummary$Id )) )' % (sec_id, sec_id)
                        r(rstring)
                        rstring = 'section_%s <- addTo( section_%s, addTo( newSubSubSection("Aliases"), newParagraph( mySummary$OtherAliases )) )' % (sec_id, sec_id)
                        r(rstring)
                        rstring = 'section_%s <- addTo( section_%s, addTo( newSubSubSection("Description"), newParagraph( mySummary$Summary )) )' % (sec_id, sec_id)
                        r(rstring)

                    if sec_name == "Protein Information":
                        other = r('mySummary$`Entrezgene_prot`$`Prot-ref`$`Prot-ref_name`')
                        other = list(other)

                        rstring = 'section_%s <- addTo( section_%s, addTo( newSubSubSection("Prefered Name"), newParagraph( mySummary$`Entrezgene_prot`$`Prot-ref`$`Prot-ref_desc` )) )' % (sec_id, sec_id)
                        r(rstring)

                        rstring = 'section_%s <- addTo( section_%s, addTo( newSubSubSection("Other names"), newList( ' % (sec_id, sec_id)
                        for name in other:
                            rstring += 'newParagraph( "%s" ),' % (name)
                        rstring = rstring[:-1] + ') ) )'

                        print rstring
                        r(rstring)

        # collect sections
        rstring = 'REPORT <- addTo( REPORT'
        for sse in section_list:
            rstring += ', ' + sse
        rstring += ')'
        r(rstring)
        r.assign('dochtml', dochtml)
        r('writeReport( REPORT, filename=toString(dochtml));')

    except RRuntimeError:
        # redirect to error-page
        html_path = str("reports/rfail.html")
    else:
        # succeed
        html_path = 'reports/' + dochtml + '.html'

    return html_path
