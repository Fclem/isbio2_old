import socket
from . import sp
__version__ = '0.1'
__author__ = 'clem'
__date__ = '27/05/2016'


# clem on 20/08/2015
def is_host_online(host, deadline=5):
	""" Check if given host is online (whether it respond to ping)

	:param host: the IP address to test
	:type host: str
	:param deadline: the maximum time to wait in second (text format)
	:type deadline: str | int
	:rtype: bool
	"""
	res = sp.call(['ping', '-c', '3', '-i', '0.2', '-w', str(deadline), host], stdout=sp.PIPE)
	return res == 0


# clem 08/09/2016 moved here on 25/05/2016
def test_tcp_connect(host, port, timeout=2):
	""" Test if TCP can connect to target host on specified port

	:param host: ip address or FQDN of the target host
	:type host: str
	:param port: TCP port number to attempt connection to
	:type port: str
	:param timeout: connection timeout time in seconds
	:type timeout: int
	:return: if TCP connect is successful
	:rtype: bool
	:raises: socket.error or Exception
	"""
	try:
		s = socket.socket()
		try:
			s.settimeout(timeout)
			s.connect((host, port))
			return True
		finally:
			s.close()
	except Exception:
		raise


# clem 29/04/2016
def get_free_port():
	"""
	:return: the number of a free TCP port on the local machine
	"""
	sock = socket.socket()
	sock.bind(('', 0))
	return sock.getsockname()[1]
