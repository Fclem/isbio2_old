# from .utils import advanced_pretty_print as pp
from utils import pp
import cmd
import os

docker = None
client = None


def dev():
	# global client
	from docker_interface import Docker

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


class HelloWorld(cmd.Cmd):
	_locals = dict()

	def __init__(self, *args, **kwargs):
		cmd.Cmd.__init__(self, *args, **kwargs)
		self.prompt = 'docker> '

	def completedefault(self, *ignored):
		if not ignored:
			completions = globals()
		else:
			completions = [ignored]
		return completions

	@classmethod
	def kill_self(cls):
		bash_command = "kill -15 %s" % os.getpid()
		print "$ %s" % bash_command
		os.system(bash_command)

	@classmethod
	def do_exit(cls, _):
		cls.kill_self()

	@classmethod
	def _has_valid_object(cls, line):
		a_list = [line.partition('.'), line.partition('('), line.partition('[')]
		all_keys = globals().keys()
		for each in a_list:
			if each[0].lower() in [a.lower() for a in all_keys]:
				return each
		return False

	def default(self, line=''):
		import sys

		parsed = self._has_valid_object(line)
		# if parsed:
		# 	return
		if parsed or line:
			try:
				res = eval(compile(line, sys.stderr.name, 'single'), globals(), self._locals)
				if res:
					print 'ret:', type(res), res
			except Exception as e:
				print e
		# print "def:", line

	def completenames(self, text, *ignored):
		dotext = 'do_' + text
		lst = self._advanced_get_names(text)
		result = list()
		for a in lst:
			item = a[3:] if a.startswith(dotext) else a if text.lower() in a.lower() else None
			result.append(item) if item else None
		return result

	def _advanced_get_names(self, text=''):
		a_object = self._has_valid_object(text)
		# print a_object
		if a_object[1] == '.':
			# return dir(eval(a_object[0], globals())) # getattr(eval(a_object[0], globals()), '__dict__')
			return dir(globals()[a_object[0]]) # getattr(eval(a_object[0], globals()), '__dict__')
		return self._get_names()

	def _get_names(self):
		# This method used to pull in base class attributes
		# at a time dir() didn't do it yet.
		return dir(self.__class__) + globals().keys()


def base():
	global docker, client
	docker = dev()
	# docker.self_test()
	client = docker.client


def cmd_line():
	try:
		HelloWorld().cmdloop()
	except KeyboardInterrupt:
		HelloWorld.kill_self()
	except Exception as e:
		print e
		return cmd_line()
		# kill_self()

if __name__ == '__main__':
	# command line
	base()
	cmd_line()
elif __name__ == 'breeze.dev':
	# PyCharm python console
	base()
