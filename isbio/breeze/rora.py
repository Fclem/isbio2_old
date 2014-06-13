import rpy2.robjects as ro
import copy
from django.conf import settings

def get_dtm_screens():
    """
        Exports Samples from Dotmatix
    """
    samples = list()

    rcode = 'source("%s%s")' %(settings.RORA_LIB,'patient-module.R')
    ro.r( rcode )

    r_dotmatixSamples = ro.globalenv['getDTMScreens']

    res = r_dotmatixSamples()

    # If the data frame is of appropriate format
    if len(res) == 2:
        for row in range(1,len(res[0])+1):
            rn = res.rx(row, True)
            gid = 'ScreenID_' + rn[0][0]
            samples.append( tuple((gid, rn[1][0])) )

    return samples

def get_dtm_screen_groups():
    """
        Exports Sample Groups from Dotmatix
    """
    groups = list()

    rcode = 'source("%s%s")' %(settings.RORA_LIB,'patient-module.R')
    ro.r( rcode )

    r_dotmatixSampleGroups = ro.globalenv['getDTMScreenGroups']

    res = r_dotmatixSampleGroups()

    # If the data frame is of appropriate format
    if len(res) == 2:
        for row in range(1,len(res[0])+1):
            rn = res.rx(row, True)
            sid = 'GroupID_' + rn[0][0]
            groups.append( tuple((sid, rn[1][0])) )

    return groups

def get_patients_info(params, subject):
    """
        Exports information about patients.

        Arguments:
        params     -- request dictionary
        subject    -- can be: "patient", "screen", "sample", "group", "content"
    """

    # Source & export R code
    rcode = 'source("%s%s")' %(settings.RORA_LIB,'basic.R')
    ro.r( rcode )

    # Export a function to call
    r_getterFunc = ro.globalenv['getPSSData']

    # Prepare parameters for R
    start = int(params.get('start',0))
    start = start + 1

    span = int(params.get('length',10))
    #search_text = params.get('search', '').lower()

    # sorting
    sort_ind = params.get('order[0][column]','')
    post_key = ('columns[%s][data]' % sort_ind)
    sort_col = params.get(post_key,'')
    sort_dir = str(params.get('order[0][dir]','')).upper()

    # General Search
    search_value = params.get('search[value]','')

    # R Call:
    r_getter_output = r_getterFunc(subject, start, span, sort_col, sort_dir, search_value)

    # Data table as such
    exported_data = r_getter_output[2]

    # count number of cols & rows in exported table
    headers = list(exported_data.colnames)

    exported_col_num = len(headers)
    exported_row_num = len(exported_data[0])

    # Convert exported_data to a list ( of dicts )
    subject_table = list()
    row_dict = dict()
    for row in range(1, exported_row_num+1):
        row_values = exported_data.rx(row,True)

        row_dict = dict()
        for col in range(0, exported_col_num):
            cell_data = row_values[col][0]
            # append to cols
            row_dict[ str(headers[col]) ] = cell_data

        # append to rows
        subject_table.append( copy.copy(row_dict) )

    response = {
        'iTotalDisplayRecords': int(r_getter_output[0][0]),
        'iTotalRecords': int(r_getter_output[1][0]),
        'aaData': subject_table
    }

    return response

def insert_row(table, data):
    """
        Adds a new record to one of the tables in RORA
    """
    # Source & export R code
    rcode = 'source("%s%s")' %(settings.RORA_LIB,'patient-module.R')
    ro.r( rcode )

    # Prepare for R call
    if table == "groups":
        # export R function
        r_getterFunc = ro.globalenv['createScreenGroup']

        r_getter_output = r_getterFunc(data['group_user'], data['group_name'])


    return True

def remove_row(table, ids):
    """
        Removes data from one of the tables in RORA
    """
    # Source & export R code
    rcode = 'source("%s%s")' %(settings.RORA_LIB,'patient-module.R')
    ro.r( rcode )

    # Prepare for R call
    if table == "groups":
        # export R function
        r_removerFunc = ro.globalenv['deleteSampleGroup']

    if table == "patients":
        # export R function
        r_removerFunc = ro.globalenv['deletePatient']

    if table == "content":
        # export R function
        r_removerFunc = ro.globalenv['deleteGroupContent']

    if table == "screen":
        # export R function
        r_removerFunc = ro.globalenv['deleteScreen']


    r_remover_output = r_removerFunc(ids)

    return r_remover_output

def update_row(table, content, iid):
    """
        UPdaTE
    """
    # Source & export R code
    rcode = 'source("%s%s")' %(settings.RORA_LIB,'patient-module.R')
    ro.r( rcode )

    # Prepare for R call
    if table == "groups":
        content = map(int, content)
        # export R function
        r_updateFunc = ro.globalenv['updateSampleGroups']

    if table == "patients":
        pass

    r_output = r_updateFunc(content, iid)


    return r_output

def getScreenGroupContent(groupID):
    """
        Returns Screen Group content for a given group in json format;
        In particular: Screen ID, Screen Name, status -- if in the group or not.
    """
    # Source & export R code
    rcode = 'source("%s%s")' %(settings.RORA_LIB,'patient-module.R')
    ro.r( rcode )

    r_getterFunc = ro.globalenv['listGroupScreens']
    exported_data = r_getterFunc(groupID)

    screens = dict()
    exported_row_num = len(exported_data[0])
    # Convert exported_data to a dict() of dict()
    for row in range(1, exported_row_num+1):
        inner = dict()
        row_values = exported_data.rx(row,True)

        #cell_data = row_values[col][0]
        inner[ 'selected' ] = int( row_values[2][0] )
        inner[ 'name' ] = str( row_values[1][0] )


        screens[ str( int(row_values[0][0]) ) ] = inner


    return screens
