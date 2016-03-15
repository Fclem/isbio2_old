
def dev():
	# global client
	from .docker_interface import Docker
	return Docker().client


def init():
	pass
	# return dev()

client = dev()
