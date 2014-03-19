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

def get_screens_info():
    """
        Exports information about screens
    """
    screen_table = list()

    rcode = 'source("%s%s")' %(settings.RORA_LIB,'basic.R')
    ro.r( rcode )

    r_getScreensInfo = ro.globalenv['getScreensInfo']

    exported_data = r_getScreensInfo()

    # Convert exported_data to a list of dict()
    if len(exported_data) == 6:
        for row in range(1,len(exported_data[0])+1):
            headers = ["id","sample_name","screen_name","tissue","experiment","source"]
            values = exported_data.rx(row,True)

            row_dict = dict()
            for col in range(0,6):
                cell_data = values[col][0]
                cell_name = headers[col]
                row_dict[cell_name] = cell_data

            screen_table.append( copy.deepcopy(row_dict) )

    return screen_table