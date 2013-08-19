import re, copy
from django.db.models import Q


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

            el['reschedhref'] = '%s-repl' % str(item.id)

            el['delhref'] = '/jobs/delete/%s' % str(item.id)

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

            el['reschedhref'] = ''

            el['delhref'] = '/reports/delete/%s-dash' % str(item.id)

            el['progress'] = item.progress

        merged.append( copy.deepcopy(el) )

    # sort list according to creation datenad time
    merged.sort(key=lambda r: r['staged'])
    merged.reverse()

    return merged