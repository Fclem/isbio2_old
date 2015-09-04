#!/usr/bin/env python
import os
import sys
import socket
import breeze

if __name__ == "__main__":
	if socket.gethostname().startswith('breeze'):
		os.environ.setdefault("DJANGO_SETTINGS_MODULE", "isbio.settings")
		os.environ.setdefault('DJANGO_CONFIGURATION', 'DevSettings')
	else:
		os.environ.setdefault("DJANGO_SETTINGS_MODULE", "isbio.settings")
		os.environ.setdefault('DJANGO_CONFIGURATION', 'BreezeSettings')

	from configurations.management import execute_from_command_line

	if sys.argv[1] == 'cron':
		# may have a independent jobKeeper here
		print('JobKeeper is automatically run and checked upon, on each HTTP requests.\n'
				+ 'There is no need to run it independently')
	else:
		execute_from_command_line(sys.argv)

	breeze.SKIP_SYSTEM_CHECK = True
	DEBUG = True
