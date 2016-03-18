from .utils import advanced_pretty_print as pp


def dev():
	# global client
	from .docker_interface import Docker

	return Docker()


def init():
	pass
	# return dev()


def same(a, b):
	return a is b or '%s != %s' % (hex(id(a)), hex(id(b)))

docker = dev()
# docker.self_test()
client = docker.client

