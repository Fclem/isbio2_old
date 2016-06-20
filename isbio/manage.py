#!/usr/bin/env python
import os
import sys
import socket
import breeze

if __name__ == "__main__":
	sys.path.append(os.path.dirname(__file__))

	# if socket.gethostname().startswith('breeze'):
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "isbio.settings")

	# from configurations.management import execute_from_command_line
	from django.core.management import execute_from_command_line

	if sys.argv[1] == 'cron':
		# may have a independent jobKeeper here
		print('JobKeeper is automatically run and checked upon, on each HTTP requests.\n'
				+ 'There is no need to run it independently')
	else:
		execute_from_command_line(sys.argv)

	breeze.SKIP_SYSTEM_CHECK = True
	DEBUG = True
