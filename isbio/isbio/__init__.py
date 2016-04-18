def patch_broken_pipe_error():
	"""Monkey Patch BaseServer.handle_error to not write
	a stacktrace to stderr on broken pipe.
	http://stackoverflow.com/a/7913160"""
	import sys
	from SocketServer import BaseServer
	from wsgiref import handlers

	handle_error = BaseServer.handle_error
	log_exception = handlers.BaseHandler.log_exception

	def is_broken_pipe_error():
		_, err, _ = sys.exc_info()
		num = err.errno if hasattr(err, 'errno') else 0
		return num == 32

	def my_handle_error(self, request, client_address):
		if not is_broken_pipe_error():
			handle_error(self, request, client_address)
		else:
			print 'broken pipe'

	def my_log_exception(self, exc_info):
		if not is_broken_pipe_error():
			log_exception(self, exc_info)

	BaseServer.handle_error = my_handle_error
	handlers.BaseHandler.log_exception = my_log_exception

patch_broken_pipe_error()
