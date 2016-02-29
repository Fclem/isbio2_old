import rpy2.robjects as ro
import copy
from django.conf import settings
from rpy2.rinterface import RRuntimeError
from utils import get_logger

DISABLE_DOTM = False
PATIENT_MODULE_FILE_NAME = 'patient-module.R'


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
	r_code = 'path <- "%s"; source("%s%s")' % (settings.RORA_LIB, settings.RORA_LIB, file_name)
	ro.r(r_code)

	return True


# clem on 20/08/2015
def test_rora_connect():
	"""
	Test if RORA server is online and connection can be made successfully
	:return: True|False
	:rtype: bool
	"""
	r_code = 'source("%sconnection.R");' % settings.RORA_LIB
	r_code += 'link <- roraConnect();'
	r_code += 'dbDisconnect(link);'
	try:
		ro.r(r_code)
	except RRuntimeError as e:
		get_logger().error(e)
		return False

	return True


# clem on 20/08/2015
def test_dotm_connect():
	"""
	Test if Dotmatics server is online and connection can be made successfully
	:return: True|False
	:rtype: bool
	"""
	r_code = 'source("%sconnection.R");' % settings.RORA_LIB
	r_code += 'link <- dotmConnect();'
	r_code += 'dbDisconnect(link);'
	try:
		ro.r(r_code)
	except RRuntimeError as e:
		# print e
		get_logger().error(e)
		return False

	return True


def get_dtm_screens(disabled=DISABLE_DOTM):
	"""
		Exports Samples from Dotmatics
	"""
	samples = list()

	# if disabled or not test_dotm_connect():
	if disabled:
		return samples
	res = global_r_call('getDTMScreens')

	# If the data frame is of appropriate format
	if len(res) == 2:
		for row in range(1, len(res[0]) + 1):
			rn = res.rx(row, True)
			gid = 'ScreenID_' + rn[0][0]
			samples.append( tuple((gid, rn[1][0])))

	return samples


def get_dtm_screen_groups(disabled=DISABLE_DOTM):
	"""
		Exports Sample Groups from Dotmatics
	"""
	groups = list()

	# if disabled or not test_dotm_connect():
	if disabled:
		return groups
	res = global_r_call('getDTMScreenGroups')

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
	# Prepare parameters for R
	start = int(params.get('start', 0))
	start += 1

	span = int(params.get('length', 10))
	# search_text = params.get('search', '').lower()

	# sorting
	sort_ind = params.get('order[0][column]', '')
	post_key = ('columns[%s][data]' % sort_ind)
	sort_col = params.get(post_key, '')
	sort_dir = str(params.get('order[0][dir]', '')).upper()

	# General Search
	search_value = params.get('search[value]', '')

	# R Call:
	# r_getter_output = r_getter_func(subject, start, span, sort_col, sort_dir, search_value)
	r_getter_output = global_r_call('getPSSData', r_file='basic.R',
									args=(subject, start, span, sort_col, sort_dir, search_value))

	subject_table = list()
	result_nb = 0
	displayed_nb = 0
	if r_getter_output:
		# Nb of total records found
		result_nb = int(r_getter_output[1][0])
		# Number of record on display (?)
		displayed_nb = int(r_getter_output[0][0])
		if result_nb: # ensure that at least one record was found
			# Data table as such
			exported_data = r_getter_output[2] # FIXME out of range

			# count number of cols & rows in exported table
			headers = list(exported_data.colnames)

			exported_col_num = len(headers)
			exported_row_num = len(exported_data[0])

			# Convert exported_data to a list ( of dicts )
			for row in range(1, exported_row_num + 1):
				row_values = exported_data.rx(row, True)

				row_dict = dict()
				for col in range(0, exported_col_num):
					cell_data = row_values[col][0]
					# append to cols
					row_dict[ str(headers[col]) ] = cell_data

				# append to rows
				subject_table.append( copy.copy(row_dict) )

	response = {
		'iTotalDisplayRecords': displayed_nb,
		'iTotalRecords': result_nb,
		'aaData': subject_table
	}

	return response


def patient_data(pid):
	"""
		Return one row from table by ID
	"""
	return global_r_call('searchPatient', pid)


def screen_data(pid):
	"""
		Return one row from table by ID
	"""
	return global_r_call('searchScreen', pid)


def get_all_patient():
	""""
		Return all patients data (id and identifier)
	"""
	return global_r_call('getAllPatient')


def sex_data():
	""""
		Return all possible sex category
	"""
	return global_r_call('searchSex')


def media_type():
	""""
		Return all possible media types
	"""
	return global_r_call('searchMediaType')


def sample_type():
	""""
		Return all possible media types
	"""
	return global_r_call('searchSampleType')


def disease_sub_type():
	""""
		Return all possible media types
	"""
	return global_r_call('searchDiseaseSubType')


def histology():
	""""
		Return all possible histology
	"""
	return global_r_call('searchHistology')


def disease_state_data():
	""""
		Return all possible disease states
	"""
	return global_r_call('searchDiseaseState')


def experiment_type_data():
	""""
		Return all possible disease states
	"""
	return global_r_call('searchExperimentType')


def disease_grade_data():
	""""
		Return all possible disease grades
	"""
	return global_r_call('searchDiseaseGrade')


def disease_stage_data():
	""""
		Return all possible disease stages
	"""
	return global_r_call('searchDiseaseStage')


def organism_data():
	"""
		Return all possible organism options
	"""
	return global_r_call('searchOrganism')


def read_out_data():
	"""
		Return all possible organism options
	"""
	return global_r_call('searchReadOut')


def update_patient(data):
	update = global_r_call('updatePatient', ro.DataFrame(data))
	print 'update_patient : ', update
	return True


def update_screen(data):
	update = global_r_call('updateScreen', ro.DataFrame(data))
	print 'update_screen : ', update
	return True


def insert_row(table, data):
	"""
		Adds a new record to one of the tables in RORA
	"""
	# Prepare for R call
	if table == "groups":
		global_r_call('createScreenGroup', (data['group_user'], data['group_name']))
	elif table == "patients":
		print(data)
		print(ro.DataFrame(data))
		global_r_call('createPatient', ro.DataFrame(data))
	return True


def remove_row(table, ids):
	"""
		Removes data from one of the tables in RORA
	"""
	r_out = None
	# export R function
	if table == "groups":
		r_out = global_r_call('deleteSampleGroup', ids)
	elif table == "patients":
		r_out = global_r_call('deletePatient', ids)
	elif table == "content":
		r_out = global_r_call('deleteGroupContent', ids)
	elif table == "screen":
		r_out = global_r_call('deleteScreen', ids)

	return r_out


def update_row(table, content, iid):
	"""
		UPdaTE
	"""
	r_output = None
	# Prepare for R call
	if table == "groups":
		content = map(int, content)
		r_output = global_r_call('updateSampleGroups', (content, iid))

	return r_output


def request_data(table, iid):
	result = None
	if table == "screen":
		result = global_r_call('requestScreen', iid)

	return result


def update_screen_group_content(content, group_id):
	return global_r_call('updateSampleGroups', (content, group_id))


def get_screen_group_content(group_id):
	"""
		Returns Screen Group content for a given group in json format;
		In particular: Screen ID, Screen Name, status -- if in the group or not.
	"""
	exported_data = global_r_call('listGroupScreens', group_id)

	screens = dict()
	exported_row_num = len(exported_data[0])
	# Convert exported_data to a dict() of dict()
	for row in range(1, exported_row_num + 1):
		inner = dict()
		row_values = exported_data.rx(row, True)

		# cell_data = row_values[col][0]
		inner[ 'selected' ] = int( row_values[2][0] )
		inner[ 'name' ] = str( row_values[1][0] )

		screens[ str( int(row_values[0][0]) ) ] = inner

	return screens


def get_screen_group(group_id):
	"""		Get the screen group content	"""
	return global_r_call('getScreenGroupContent', group_id)


def get_all_screens():
	"""		Get all the screens	"""
	return global_r_call('getAllScreen')


# clem 04/11/2015
def global_r_call(function_name, args=None, r_file=PATIENT_MODULE_FILE_NAME):
	"""
	Writing shortcut for all previous function using this same code
	:param function_name: name of the ro.globalenv function to call
	:type function_name: str
	:param args: usually a selector like GroupID
	:type args:
	:param r_file: The file to be loaded for the call
	:type r_file: str
	:rtype:
	"""
	# Source & export R code
	source_file(r_file)

	# Export a function to call
	r_getter_func = ro.globalenv[function_name]

	# R call
	data = list()
	try:
		# Arguments magics
		if args:
			if type(args) is not tuple:
				args = (args,)
			data = r_getter_func(*args)
		else:
			data = r_getter_func()
	except RRuntimeError as e:
		get_logger().error(e)

	return data
