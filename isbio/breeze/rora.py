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

def get_screens_info(params):
    """
        Exports information about screens
    """
    screens_table = list()

    # Source & export R code
    rcode = 'source("%s%s")' %(settings.RORA_LIB,'basic.R')
    ro.r( rcode )

    # Export a function to call
    r_getScreensInfo = ro.globalenv['getScreensInfo']

    # Prepare parameters for R
    start = int(params.get('iDisplayStart',0))
    span = int(params.get('iDisplayLength',25))
    search_text = params.get('sSearch', '').lower()
    sort_dir = params.get('sSortDir_0', 'asc')

    # R Call:
    screens_info = r_getScreensInfo(start, span)

    # Data table as such
    exported_data = screens_info[2]


    if len(exported_data) == 8:
        # Convert exported_data to a list of dict()
        for row in range(1,len(exported_data[0])+1):
            values = exported_data.rx(row,True)

            row_dict = list()
            for col in range(0,8):
                cell_data = values[col][0]
                row_dict.append( cell_data )

            screens_table.append( copy.copy(row_dict) )

        response = {
            'iTotalDisplayRecords': int(screens_info[0][0]),
            'iTotalRecords': int(screens_info[1][0]),
            'aaData': screens_table
        }
    else:
        response = {
            'iTotalDisplayRecords': 0,
            'iTotalRecords': 0,
            'aaData': screens_table
        }

    return response

def get_patients_info(params):
    """
        Exports information about patients
    """
    patient_table = list()

    # Source & export R code
    rcode = 'source("%s%s")' %(settings.RORA_LIB,'basic.R')
    ro.r( rcode )

    # Export a function to call
    r_getPatientsInfo = ro.globalenv['getPatientsInfo']

    # Prepare parameters for R
    start = int(params.get('iDisplayStart',0))
    span = int(params.get('iDisplayLength',25))
    search_text = params.get('sSearch', '').lower()
    sort_dir = params.get('sSortDir_0', 'asc')

    # R Call:
    patients_info = r_getPatientsInfo(start, span)

    # Data table as such
    exported_data = patients_info[2]


    if len(exported_data) == 9:
        # Convert exported_data to a list of dict()
        for row in range(1,len(exported_data[0])+1):
            values = exported_data.rx(row,True)

            row_dict = list()
            for col in range(0,9):
                cell_data = values[col][0]
                row_dict.append( cell_data )

            patient_table.append( copy.copy(row_dict) )

        response = {
            'iTotalDisplayRecords': int(patients_info[0][0]),
            'iTotalRecords': int(patients_info[1][0]),
            'aaData': patient_table
        }
    else:
        response = {
            'iTotalDisplayRecords': 0,
            'iTotalRecords': 0,
            'aaData': patient_table
        }

    return response