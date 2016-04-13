import openpyxl
import xlrd
# Clem 09/03/2016
# module used to bootstrap environement for the Django python console from Intellij PyCharm


def dev():
	# global client
	# from .ssh import docker
	# return docker()
	pass


def init():
	# return dev()
	pass


BASE_PATH = '/projects/breeze-dev/db/testing/'
DATA_PATH = '/projects/breeze-dev/db/testing/Data/'
F_NAME = 'exp_info_s2.xls'
F_PATH = BASE_PATH + '/' + F_NAME


def get_sheet():
	# wb = openpyxl.load_workbook(f_path)
	# sheet = wb.get_sheet_by_name('Sheet3')
	# sheet['A1'].value
	wb = xlrd.open_workbook(F_PATH)
	sheet = wb.sheet_by_index(0)
	return sheet


# https://stackoverflow.com/questions/23861680/convert-spreadsheet-number-to-column-letter
def column_string(n, has_zero=True):
	if has_zero:
		n += 1
	div, string, temp = n, '', 0
	while div > 0:
		module = (div - 1) % 26
		string = chr(65 + module) + string
		div = int((div - module) / 26)
	return string


def check_file():
	import os
	is_okay, missing, error, sh, y, x = True, list(), '', get_sheet(), 0, 1

	def cell_val(yy=None, xx=None): # return the striped value content of cell (yy, xx) if provided or (y, x) if not
		return unicode(sh.cell(yy or y, xx or x).value).strip()

	kw = (u'file_name', u'filename', u'file name')
	try:
		while cell_val().lower() not in kw: # scroll through column X to find the column header (in kw)
			y += 1
		# file_list = list()
		try:
			while True: # scrolling through the column, collecting all file names
				y += 1
				if not cell_val(): # we reached an empty cell, might be the last (empty) row (or not)
					error = 'Reached an empty cell at ' + column_string(x)
					break
				# file_list.append(last)
				if not os.path.exists(DATA_PATH + cell_val()): # if the file does not exists
					is_okay, error = False, 'Missing file(s)'
					missing.append((cell_val(), '%s' % column_string(x) + str(y)))
		except IndexError: # we reached the last row
			pass
	except IndexError: # we reached the last row
		is_okay, error = False, 'Cannot find the column header "%s" or "%s" in column B%s' % (column_string(x),) + kw

	return is_okay, error, missing


def excel_test():
	ok, error_msg, missings = check_file()
	if not ok:
		print error_msg, ':'
		for each in missings:
			print each[1], ':', each[0]


# client = dev()
