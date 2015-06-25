__author__ = 'clem'
import django
from django.template.defaulttags import now
import os, shutil, re, stat, copy
from datetime import datetime
from multiprocessing import Process
from Bio import Entrez
from django.template.defaultfilters import slugify
from django.conf import settings
import auxiliary as aux
import logging
import pickle, json
import hashlib
from django.utils import timezone
from datetime import timedelta
from breeze.models import Report, Jobs
import time
from exceptions import Exception


class Watcher():
	jobs_lst = dict()
	report_lst = dict()

	def refresh(self):
		pass

class Watched():
	type = None

	def __unicode__(self):
		return self.type

	class Meta:
		abstract = True


class WatchedJob(Watched):
	type = Jobs

	@property
	def status(self):
		return self.type

class WatchedReport():
	type = Report

	@property
	def status(self):
		return self.type


def runner():

	watching = Watcher()

	while True:
		watching.refresh()
		time.sleep(2)
