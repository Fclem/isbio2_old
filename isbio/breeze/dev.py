
def dev():
	# global client
	from .docker_interface import docker
	return docker()


def init():
	pass
	# return dev()

client = dev()
