"""

A module that safely import drmaa if it exists
If not drmaa will be set to None

provide job_stat_class as alias to drmaa.JobState and as an replacement class if drmaa does not exists

"""

__version__ = '0.1'
__author__ = 'clem'
__date__ = '21/06/2016'

try:
	import drmaa

	job_stat_class = drmaa.JobState
except ImportError:
	drmaa = None

	class DrmaaJobState(object):
		UNDETERMINED = 'undetermined'
		QUEUED_ACTIVE = 'queued_active'
		SYSTEM_ON_HOLD = 'system_on_hold'
		USER_ON_HOLD = 'user_on_hold'
		USER_SYSTEM_ON_HOLD = 'user_system_on_hold'
		RUNNING = 'running'
		SYSTEM_SUSPENDED = 'system_suspended'
		USER_SUSPENDED = 'user_suspended'
		USER_SYSTEM_SUSPENDED = 'user_system_suspended'
		DONE = 'done'
		FAILED = 'failed'


	job_stat_class = DrmaaJobState

