import rpy2.robjects as ro
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
            samples.append( tuple((rn[0][0], rn[1][0])) )

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
            groups.append( tuple((rn[0][0], rn[1][0])) )

    return groups