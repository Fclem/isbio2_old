__author__ = 'clem'

import logging
import sys

def get_logger(name=None):
	logger = logging.getLogger(__name__)
	if name is None:
		name = sys._getframe(2).f_code.co_name
	log_obj = logger.getChild(name)
	assert isinstance(log_obj, logging.getLoggerClass())  # for code assistance only
	return log_obj
