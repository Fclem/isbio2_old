import re, copy, os
from django.db.models import Q
import breeze.models
from django.utils import timezone
from subprocess import Popen, PIPE


def updateServer_routine():
    # hotfix
    if 'QSTAT_BIN' in os.environ:
        qstat = os.environ['QSTAT_BIN']
    else:
        qstat = 'qstat'

    # get the server info by directly parsing qstat
    # p = subprocess.Popen([qstat, "-g", "c"], stdout=subprocess.PIPE)
    p = Popen([qstat, "-g", "c"], stdout=PIPE)
    output, err = p.communicate()
    server = 'unknown'
    for each in output.splitlines():
        if 'hugemem.q' in each.split(): #  TODO switch to dynamic server
            s_name = each.split()[0]
            cqload = each.split()[1]
            used = each.split()[2]
            avail = each.split()[4]
            total = each.split()[5]
            cdsuE = 0 + int(each.split()[7])

            if total == cdsuE:
                server = 'bad'
            elif int(avail) <= 3:
                server = 'busy'
            elif float(cqload) > 30:
                server = 'busy'
            else:
                server = 'idle'
    server_info = {
          's_name': s_name,
          'cqload': cqload,
          'cdsuE': str(cdsuE),
          'total': total,
          'avail': avail,
          'used': used,
    }
    return server, server_info

def update_last_active(user):
    pass


def clean_up_dt_id(lst):
    """ Cleans up row ids that come from the DataTable plugin.

    Arguments:
    lst      -- list of ids
    """
    cleaned = map(lambda line: int(line[4:]), lst)  # (trim firs 4 chars)

    return cleaned

def save_new_project(form, author):
    """ Saves New Project data from a valid form to DB model.

    Arguments:
    form        -- instance of NewProjectForm
    author      -- user name
    """
    insti = breeze.models.UserProfile.objects.get(user=author).institute_info
    dbitem = breeze.models.Project(
                name=str(form.cleaned_data.get('project_name', None)),
                manager=str(form.cleaned_data.get('project_manager', None)),
                pi=str(form.cleaned_data.get('principal_investigator', None)),
                author=author,
                collaborative=form.cleaned_data.get('collaborative', None),
                wbs=str(form.cleaned_data.get('wbs', None)),
                external_id=str(form.cleaned_data.get('eid', None)),
                description=str(form.cleaned_data.get('description', None)),
                institute=insti
            )

    dbitem.save()

    return True

def save_new_group(form, author, post):
    """ Saves New Group data from a valid form to DB model.

    Arguments:
    form        -- instance of GroupForm
    author      -- user name
    """

    dbitem = breeze.models.Group(
                name=str(form.cleaned_data.get('group_name', None)),
                author=author
            )

    # Important:
    # Before using ManyToMany we should first save the model!!!
    dbitem.save()

    for chel in post.getlist('group_team'):
        dbitem.team.add( breeze.models.User.objects.get(id=chel) )

    dbitem.save()

    return True

def edit_project(form, project):
    """ Edit Project data.

    Arguments:
    form        -- instance of EditProjectForm
    project     -- db instance of existing Project
    """
    project.wbs = str( form.cleaned_data.get('wbs', None) )
    project.external_id = str( form.cleaned_data.get('eid', None) )
    project.description = str( form.cleaned_data.get('description', None) )
    project.save()

    return True

def edit_group(form, group, post):
    """ Edit Group data.

    Arguments:
    form        -- instance of EditGroupForm
    group       -- db instance of existing Group
    """
    # clean up first
    group.team.clear()
    group.save()

    for chel in post.getlist('group_team'):
        group.team.add( breeze.models.User.objects.get(id=chel) )

    group.save()

    return True


def delete_project(project):
    """ Remove a project from a DB model.

    Arguments:
    project     -- db instance of Project
    """
    project.delete()

    return True

def delete_group(group):
    """ Remove a group from a DB model.

    Arguments:
    group     -- db instance of Group
    """
    group.delete()

    return True

def open_folder_permissions(path, permit=0770):
    """ Traverses a directory recursively and set permissions.

    Arguments:
    path        -- a path string ( default '' )
    permit      -- permissions to be set in oct
                ( default 0770 ) - '?rwxrwx---'
    """

    for dirname, dirnames, filenames in os.walk(path):
        for subdirname in dirnames:
            full_dir_path = os.path.join(dirname, subdirname)
            os.chmod(full_dir_path, permit)

        for filename in filenames:
            full_file_path = os.path.join(dirname, filename)
            os.chmod(full_file_path, permit)

    os.chmod(path, permit)

    return True

def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:

        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    '''
    query = None # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query
    
def get_query_new(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    '''
    query = None # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query

def extract_users(groups, users):
    ''' Produce a unique list of users from 2 lists.
        Merge users from each group and set of individual users
        and extracts a union of those people.
    '''
    people = list()

    #  Process Groups
    if groups:
        for group_id in map(int, groups.split(',')):
            dbitem = breeze.models.Group.objects.get(id=group_id)
            ref = dbitem.team.all()
            people = list(set(people) | set(ref))

    #  Process Individual Users
    if users:
        users_ids = map(int, users.split(','))
        ref = breeze.models.User.objects.filter(id__in=users_ids)
        people = list(set(people) | set(ref))

    return people

def merge_job_history(jobs, reports):
    ''' Merge reports and jobs in a unified object (list)
        So that repors and jobs can be processed similatly on the client side
    '''
    merged = list()
    pool = list(jobs) + list(reports)

    for item in pool:
        el = dict()

        if 'script_id' in item.__dict__:  # job
            el['instance'] = 'script'
            el['id'] = item.id
            el['jname'] = item.jname
            el['status'] = item.status
            el['staged'] = item.staged

            el['rdownhref'] = '/jobs/download/%s-result' % str(item.id)  # results
            el['ddownhref'] = '/jobs/download/%s-code' % str(item.id)  # debug
            el['fdownhref'] = '/jobs/download/%s' % str(item.id)  # full folder

            el['home'] = ''
            el['reschedhref'] = '%s-repl' % str(item.id)

            el['delhref'] = '/jobs/delete/%s' % str(item.id)
            el['abohref'] = '/abortjobs/%s' % str(item.id)

            el['progress'] = item.progress

        else:                             # report
            el['instance'] = 'report'
            el['id'] = item.id
            el['jname'] = item.name
            el['status'] = item.status
            el['staged'] = item.created

            el['rdownhref'] = '/get/report-%s' % str(item.id)  # results
            el['ddownhref'] = ''  # debug
            el['fdownhref'] = ''  # full folder

            el['home'] = item.home
            el['reschedhref'] = ''

            el['delhref'] = '/reports/delete/%s-dash' % str(item.id)
            el['abohref'] = '/abortreports/%s' % str(item.id)

            el['progress'] = item.progress

        merged.append( copy.deepcopy(el) )

    # sort list according to creation datenad time
    merged.sort(key=lambda r: r['staged'])
    merged.reverse()

    return merged


def merge_job_lst(item1, item2):
    ''' Merge reports with reports or jobs with jobs in a unified object (list)
    '''
    merged = list()
    merged = list(item1) + list(item2)

    # sort list according to creation datenad time
    merged.sort(key=lambda r: r['staged'])
    merged.reverse()

    return merged