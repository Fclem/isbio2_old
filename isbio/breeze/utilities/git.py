from . import get_term_cmd_stdout, exists

__version__ = '0.1'
__author__ = 'clem'
__date__ = '27/05/2016'


# clem 18/04/2016
def get_branch():
	ret = ''
	s = get_term_cmd_stdout(["git", "branch"])
	if s:
		for line in s:
			if line.startswith('*'):
				ret = line.replace('*', '').strip()
	return ret


# clem 18/04/2016
def get_status():
	ret = ''
	try:
		s = get_term_cmd_stdout(["git", "status"])
		if s:
			ret = '%s / %s\n%s' % (s[0].strip(), get_commit_line(), s[1].strip())
	finally:
		return ret


# clem 18/04/2016 # FIXME : too much of an HACK
def get_commit_line(full=False, hash_only=False):
	ret = ''
	try:
		s = get_term_cmd_stdout(["git", "show"])
		if s:
			commit = s[0].strip()[:14] if not full else s[0].strip()
			if hash_only:
				return commit
			ret = '%s on %s' % (commit, s[2].replace('Date:   ', '').strip())
	finally:
		return ret


# clem 18/04/2016
def get_commit(full=False):
	return get_commit_line(full, True).replace('commit', '').strip()


# clem 18/04/2016
def get_head(folder=''):
	try:
		return open('%s.git/FETCH_HEAD' % folder).readline().replace('\n', '')
	except IOError:
		return ''


# clem 20/06/2016
def get_branch_from_fs(git_folder='./'):
	target = git_folder + '.git/HEAD'
	ret = ''
	try:
		if exists(target):
			with open(target) as file_read:
				ret = file_read.readline()
				if ret:
					ret = ret.replace('\n', '').split('/')
					if ret:
						ret = ret[-1]
	except IOError:
		pass
	return ret
