import rpy2.robjects as ro
import copy
from django.conf import settings
from rpy2.rinterface import RRuntimeError

DISABLE_DOTM = False


# clem on 17/06/2015
def source_file(file_name):
	"""
	Source & export R code
	set the variable 'path' in R context so that every source() done in R files,
	can use it to load the appropriated files accordingly.
	Enables using different versions or RORALib
	:param file_name: the file name of the module to load from the RORALib folder
	:type file_name: str
	:return: True
	:rtype: bool
	"""
	rcode = 'path <- "%s"; source("%s%s")' % (settings.RORA_LIB, settings.RORA_LIB, file_name)
	ro.r(rcode)

	return True


# clem on 20/08/2015
def test_rora_connect():
	"""
	Test if RORA server is online and connection can be made successfully
	:return: True|False
	:rtype: bool
	"""
	rcode = 'source("%sconnection.R");' % settings.RORA_LIB
	rcode += 'link <- roraConnect();'
	rcode += 'dbDisconnect(link);'
	try:
		x = ro.r(rcode)
	except RRuntimeError as e:
		print e
		return False

	return True


# clem on 20/08/2015
def test_dotm_connect():
	"""
	Test if Dotmatics server is online and connection can be made successfully
	:return: True|False
	:rtype: bool
	"""
	rcode = 'source("%sconnection.R");' % settings.RORA_LIB
	rcode += 'link <- dotmConnect();'
	rcode += 'dbDisconnect(link);'
	try:
		x = ro.r(rcode)
	except RRuntimeError as e:
		print e
		return False

	return True


def get_dtm_screens(disabled=DISABLE_DOTM):
	"""
		Exports Samples from Dotmatics
	"""
	samples = list()

	if disabled or not test_dotm_connect():
		return samples

	source_file('patient-module.R')

	r_dotmatixSamples = ro.globalenv['getDTMScreens']

	res = r_dotmatixSamples()

	# If the data frame is of appropriate format
	if len(res) == 2:
		for row in range(1, len(res[0]) + 1):
			rn = res.rx(row, True)
			gid = 'ScreenID_' + rn[0][0]
			samples.append( tuple((gid, rn[1][0])) )

	return samples


def get_dtm_screen_groups(disabled=DISABLE_DOTM):
	"""
		Exports Sample Groups from Dotmatics
	"""
	groups = list()

	if disabled or not test_dotm_connect():
		return groups

	source_file('patient-module.R')

	r_dotmatixSampleGroups = ro.globalenv['getDTMScreenGroups']

	res = r_dotmatixSampleGroups()

	# If the data frame is of appropriate format
	if len(res) == 2:
		for row in range(1, len(res[0]) + 1):
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
	source_file('basic.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['getPSSData']

	# Prepare parameters for R
	start = int(params.get('start',0))
	start = start + 1

	span = int(params.get('length',10))
	# search_text = params.get('search', '').lower()

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


def patient_data(id):
	"""
		Return one row from table by ID
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchPatient']

	# R call
	data = r_getterFunc(id)
	return data


def screen_data(id):
	"""
		Return one row from table by ID
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchScreen']

	# R call
	data = r_getterFunc(id)
	return data


def get_all_patient():
	""""
		Return all patients data (id and identifier)
	"""

	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['getAllPatient']

	# R call
	data = r_getterFunc()

	return data

def sex_data():
	""""
		Return all possible sex category
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchSex']

	# R call
	data = r_getterFunc()

	return data


def media_type():
	""""
		Return all possible media types
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchMediaType']

	# R call
	data = r_getterFunc()
	return data


def sample_type():
	""""
		Return all possible media types
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchSampleType']

	# R call
	data = r_getterFunc()
	return data


def disease_sub_type():
	""""
		Return all possible media types
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchDiseaseSubType']

	# R call
	data = r_getterFunc()
	return data


def histology():
	""""
		Return all possible histology
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchHistology']

	# R call
	data = r_getterFunc()
	return data


def disease_state_data():
	""""
		Return all possible disease states
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchDiseaseState']

	# R call
	data = r_getterFunc()
	return data


def experiment_type_data():
	""""
		Return all possible disease states
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchExperimentType']

	# R call
	data = r_getterFunc()
	return data


def disease_grade_data():
	""""
		Return all possible disease grades
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchDiseaseGrade']

	# R call
	data = r_getterFunc()
	return data


def disease_stage_data():
	""""
		Return all possible disease stages
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchDiseaseStage']

	# R call
	data = r_getterFunc()
	return data


def organism_data():
	""""
		Return all possible organism options
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchOrganism']

	# R call
	data = r_getterFunc()

	return data


def read_out_data():
	""""
		Return all possible organism options
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['searchReadOut']

	# R call
	data = r_getterFunc()

	return data


def update_patient(data):
	# Source & export R code
	source_file('patient-module.R')
	# Export a function to call
	r_getterFunc = ro.globalenv['updatePatient']

	# R call
	update = r_getterFunc(ro.DataFrame(data))
	return True


def update_screen(data):
	# Source & export R code
	source_file('patient-module.R')
	# Export a function to call
	r_getterFunc = ro.globalenv['updateScreen']

	# R call
	update = r_getterFunc(ro.DataFrame(data))
	return True


def insert_row(table, data):
	"""
		Adds a new record to one of the tables in RORA
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Prepare for R call
	if table == "groups":
		# export R function
		r_getterFunc = ro.globalenv['createScreenGroup']

		r_getter_output = r_getterFunc(data['group_user'], data['group_name'])
	elif table == "patients":
		print(data)
		r_getterFunc = ro.globalenv['createPatient']
		print(ro.DataFrame(data))
		r_getter_output = r_getterFunc(ro.DataFrame(data))
	return True


def remove_row(table, ids):
	"""
		Removes data from one of the tables in RORA
	"""
	# Source & export R code
	source_file('patient-module.R')

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
	source_file('patient-module.R')

	# Prepare for R call
	if table == "groups":
		content = map(int, content)
		# export R function
		r_updateFunc = ro.globalenv['updateSampleGroups']

	if table == "patients":
		pass

	r_output = r_updateFunc(content, iid)


	return r_output


def request_data(table, iid):
	source_file('patient-module.R')

	if table == "screen":
		r_updateFunc = ro.globalenv['requestScreen']

	r_output = r_updateFunc(iid)

	return r_output


def updateScreenGroupContent(content, groupid):
	# Source & export R code
	source_file('patient-module.R')

	r_updateFunc = ro.globalenv['updateSampleGroups']
	r_output = r_updateFunc(content, groupid)
	return r_output


def getScreenGroupContent(groupID):
	"""
		Returns Screen Group content for a given group in json format;
		In particular: Screen ID, Screen Name, status -- if in the group or not.
	"""
	# Source & export R code
	source_file('patient-module.R')

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


def getScreenGroup(groupID):
	""""
		Get the screen group content
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['getScreenGroupContent']

	# R call
	data = r_getterFunc(groupID)

	return data


def getAllScreens():
	""""
		Get all the screens
	"""
	# Source & export R code
	source_file('patient-module.R')

	# Export a function to call
	r_getterFunc = ro.globalenv['getAllScreen']

	# R call
	data = r_getterFunc()

	return data
