"""
WSGI config for isbio project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application
from breeze.system_check import run_system_test

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "isbio.settings")
# os.environ.setdefault('DJANGO_CONFIGURATION', 'DevSettings')

application = get_wsgi_application()

run_system_test()
