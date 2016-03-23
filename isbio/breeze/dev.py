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


def check_scripts():
	from models import Rscripts
	error_list = list()
	for script in Rscripts.objects.all():
		for file_path in [script._code_path, script._header_path]:
			try:
				a_file = open(str(file_path), 'r')
				change_list = list()
				i = 0
				for line in a_file.readlines():
					i += 1
					# print line
					if '/breeze/code' in line:
						change_list.append('%s: %s' % (i, line))
				if change_list:
					print '%s: %s occurrence' % (file_path, len(change_list))
					pp(change_list)
			except IOError as e:
				error_list.append('Err %s' % e)
	if error_list:
		print 'Errors :'
		pp(error_list)

docker = dev()
# docker.self_test()
client = docker.client
