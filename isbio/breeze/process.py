from multiprocessing import Process
import os
import sys
import itertools
__author__ = 'clem'

try:
	ORIGINAL_DIR = os.path.abspath(os.getcwd())
except OSError:
	ORIGINAL_DIR = None


class MyProcess(Process, object):
	def _bootstrap(self):
		from multiprocessing import util
		global _current_process

		try:
			self._children = set()
			self._counter = itertools.count(1)
			try:
				# sys.stdin.close()
				sys.stdin = open(os.devnull)
			except (OSError, ValueError):
				pass
			_current_process = self
			util._finalizer_registry.clear()
			util._run_after_forkers()
			util.info('child process calling self.run()')
			try:
				self.run()
				exitcode = 0
			finally:
				pass
				# util._exit_function()
		except SystemExit, e:
			if not e.args:
				exitcode = 1
			elif isinstance(e.args[0], int):
				exitcode = e.args[0]
			else:
				sys.stderr.write(str(e.args[0]) + '\n')
				sys.stderr.flush()
				exitcode = 1
		except:
			exitcode = 1
			import traceback
			sys.stderr.write('Process %s:\n' % self.name)
			sys.stderr.flush()
			traceback.print_exc()

		util.info('process exiting with exitcode %d' % exitcode)
		return exitcode
