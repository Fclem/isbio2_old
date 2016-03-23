from .utils import advanced_pretty_print as pp


def dev():
	# global client
	from .docker_interface import Docker

	return Docker()


def init():
	pass
	# return dev()


def same(a, b):
	return a is b or '%s != %s' % (hex(id(a)), hex(id(b)))


def parse(source, the_path):
	import re

	pattern = r'\s*("(/[^"]+)"|\'(/[^\']+)\')\s*'
	match = re.findall(str(pattern), source, re.DOTALL)
	if len(match) == 0:
		print 'NO MATCH IN LINE **************************************************************************'
	# for el in match:
	# 	print el
	return match


def check_scripts():
	from models import Rscripts
	from os.path import exists
	import shutil

	find = '/breeze/code'
	replace = '/breeze-dev/code'

	error_list = list()
	no_file_list = list()
	for script in Rscripts.objects.all():
		for file_path in [script._code_path, script._header_path]:
			try:
				change_list = list()
				occur_list = list()
				file_lines = list()
				with open(str(file_path), 'r') as a_file:
					i = 0
					for line in a_file.readlines():
						file_lines.append(line)
						i += 1
						if find in line:
							matches = parse(line, file_path)
							for match in matches:
								the_path = match[1] or match[2]
								new_path = the_path.replace(find, replace)
								if exists(new_path):
									occur_list.append(the_path)
									new_line = line.replace(find, replace)
									file_lines[-1] = new_line
									change_list.append('INITIAL l%s: %sCHANGED l%s: %s' % (i, line, i, new_line))
								else:
									no_file_list.append(
										'line %s in file "%s" was not modified because target file "%s" does not exist in DEV'
										% (i, file_path, new_path))
				if change_list:
					shutil.move(str(file_path), str(file_path) + '~')
					with open(str(file_path), 'w') as a_file:
						a_file.writelines(file_lines)
						print '%s: %s occurrence' % (file_path, len(change_list))
						# pp(occur_list)
						pp(change_list)
						# pp(file_lines)
						# return
			except IOError as e:
				if e.errno == 2:
					error_list.append('Err %s' % e)
				else:
					raise e
	if no_file_list:
		print 'Not modified :'
		pp(no_file_list)
	if error_list:
		print 'Errors :'
		pp(error_list)

docker = dev()
# docker.self_test()
client = docker.client
