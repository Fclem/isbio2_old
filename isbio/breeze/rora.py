import rpy2.robjects as ro
import copy
from django.conf import settings

def get_dtm_samples():
    """
        Exports Samples from Dotmatix
    """
    samples = list()

    rcode = 'source("%s%s")' %(settings.RORA_LIB,'basic.R')
    ro.r( rcode )

    r_dotmatixSamples = ro.globalenv['dotmatixSamples']

    res = r_dotmatixSamples()

    # If the data frame is of appropriate format
    if len(res) == 2:
        for row in range(1,len(res[0])+1):
            rn = res.rx(row, True)
            gid = 'S' + rn[0][0]
            samples.append( tuple((gid, rn[1][0])) )

    return samples

def get_dtm_sample_groups(author):
    """
        Exports Sample Groups from Dotmatix
    """
    groups = list()

    # Check if author is not empty:
    # here...

    rcode = 'source("%s%s")' %(settings.RORA_LIB,'basic.R')
    ro.r( rcode )

    r_dotmatixSampleGroups = ro.globalenv['dotmatixSampleGroups']

    res = r_dotmatixSampleGroups(author)

    # If the data frame is of appropriate format
    if len(res) == 2:
        for row in range(1,len(res[0])+1):
            rn = res.rx(row, True)
            sid = 'G' + rn[0][0]
            groups.append( tuple((sid, rn[1][0])) )

    return groups

def get_patients_info(params, subject):
    """
        Exports information about patients.

        Arguments:
        params     -- request dictionary
        subject    -- can be: "patient", "screen","sample"
    """

    # Source & export R code
    rcode = 'source("%s%s")' %(settings.RORA_LIB,'basic.R')
    ro.r( rcode )

    # Export a function to call
    if subject == "patient":
        r_getterFunc = ro.globalenv['getPatientsInfo']
    if subject == "screen":
        r_getterFunc = ro.globalenv['getScreensInfo']
    if subject == "sample":
        r_getterFunc = ro.globalenv['getSamplesInfo']

    # Prepare parameters for R
    start = int(params.get('start',0))
    span = int(params.get('length',25))
    search_text = params.get('search', '').lower()
    sort_dir = params.get('sortDir_0', 'asc')

    # R Call:
    r_getter_output = r_getterFunc(start, span)

    # Data table as such
    exported_data = r_getter_output[2]


    # count number of cols & rows in exported table
    exported_col_num = len(exported_data)
    exported_row_num = len(exported_data[0])

    # Convert exported_data to a list ( of lists )
    subject_table = list()
    row_dict = list()
    for row in range(1,exported_row_num+1):
        values = exported_data.rx(row,True)

        row_dict = list()
        for col in range(0,exported_col_num):
            cell_data = values[col][0]
            # append to cols
            row_dict.append( cell_data )

        # append to rows
        subject_table.append( copy.copy(row_dict) )

    response = {
        'iTotalDisplayRecords': int(r_getter_output[0][0]),
        'iTotalRecords': int(r_getter_output[1][0]),
        'aaData': subject_table
    }

    return response