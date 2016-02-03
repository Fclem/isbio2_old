# clement@fiere.fr 03/02/2016
class InvalidArgument(BaseException):
	pass


class CranArchiveDownloader: # special purpose light FTP downloader
	name = str
	# http_url = 'http://cran.r-project.org/src/contrib/Archive/'
	ftp_server = 'cran.r-project.org'
	ftp_path = '/pub/R/src/contrib/Archive/'
	ftp_home_url = 'ftp://%s' % ftp_server
	verbose = True
	login = 'anonymous'
	password = ''

	# ftp_url = '%s%s' % (ftp_home_url, ftp_path)

	def __init__(self, name=str):
		if type(name) == str and name:
			self.name = name
		else:
			raise InvalidArgument
		self._found = False
		from ftplib import FTP
		self.ftp = FTP(self.ftp_server)
		from os.path import dirname, realpath
		self._self_path = dirname(realpath(__file__))
		self._searched = False
		self.v = False
		self._nlst = dict()
		self.save_path = ''

	def find(self, suggest=True):
		"""
		Try to cd to the target library dir directly,
		and if not found call self.guess
		:type suggest: bool
		:rtype: bool|str
		"""
		if not self._searched: # don't do it twice
			self.ftp.login(self.login, self.password)
			if self.name:
				try:
					self.ftp.cwd("%s%s" % (self.ftp_path, self.name))
					if self.verbose:
						print 'found, last version :', self._last_version_file_name
					# No error, means folder exists == FOUND !
					self._found = True
				# url = '%s%s%s' % (self.ftp_home_url, pwd(), the_file)
				except Exception as e:
					if str(e).startswith('550'):
						if suggest:
							if self.verbose:
								print self.name, 'not found!'
							self._find_similar()
					elif self.verbose:
						print 'Error : ', str(e)
			self._searched = True
		return self._found

	def download(self):
		""" Download the latest version of the found package
		:rtype: bool|str
		"""
		if self._found or self.find(False):
			path = self._download_and_save()
			if self.verbose and not path:
				print 'Download failed'
			return path
		return False

	def extract_to(self, path):
		if path and (self._downloaded or self.download()):
			# TODO
			print 'NOT IMP'
		return False

	@property
	def _file_list(self):
		""" Returns file list of cwd with caching (don't ask twice for the same path)
		:rtype: str
		"""
		pwd = self._pwd
		if pwd not in self._nlst:
			self._nlst[pwd] = self.ftp.nlst()
		return self._nlst[pwd]

	@property
	def _pwd(self):
		""" Returns current working directory with trailing slash
		:rtype: str
		"""
		return '%s/' % self.ftp.pwd()

	@property
	def _last_version_file_name(self):
		return self._file_list[-1]

	def _downloader(self, filename, save_to):
		""" Download the file name filename from the CWD and save it to save_to
		:type filename: str
		:type save_to: str
		:rtype: bool
		"""
		with open(save_to, 'wb') as save_file:
			def _write(data):
				save_file.write(data)
				if self.verbose:
					import sys
					sys.stdout.write('.')

			try:
				if self.verbose:
					print 'Downloading', self.ftp.size(filename), 'bytes',
				self.ftp.retrbinary("RETR " + filename, _write)
				if self.verbose:
					print ' Done !\nsaved to', save_to
				return True
			except Exception as e:
				if self.verbose:
					print "Error", e
		return False

	def _download_and_save(self):
		""" Actually download and save the last legacy version of the package
		:rtype: bool|str
		"""
		filename = self._last_version_file_name
		self.save_path = '%s/%s' % (self._self_path, filename)
		if self._downloader(filename, self.save_path):
			self._downloaded = True
			return self.save_path
		return False

	def _guess(self):
		""" Go through the list of package and try to find matching package name (case insensitive and including self.name)
		:rtype: bool|list
		"""
		if self.name:
			self.name = self.name.lower()
			new_l = list()
			for e in self._file_list:
				l = str(e).lower()
				if l == self.name or self.name in l or l in self.name:
					new_l.append(str(e))
			if new_l != list():
				return new_l
		return False

	def _find_similar(self):
		""" Suggest on console similar package (case insensitive and including self.name) if verbose is enable
		:rtype: None
		"""
		self.ftp.cwd(self.ftp_path)
		real_name = self._guess()
		if self.verbose and real_name:
			for e in real_name:
				print 'Did you meant "%s" ?' % e
