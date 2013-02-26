#!/usr/bin/env python
import os
import sys
import socket

if __name__ == "__main__":
    if socket.gethostname().startswith('breeze'):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "isbio.settings")
        os.environ.setdefault('DJANGO_CONFIGURATION', 'DevSettings')
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "isbio.settings")
        os.environ.setdefault('DJANGO_CONFIGURATION', 'BreezeSettings')

    from configurations.management import execute_from_command_line

    execute_from_command_line(sys.argv)
#    from django.core.management import execute_from_command_line
#
#    execute_from_command_line(sys.argv)
