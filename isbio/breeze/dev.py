
def dev():
	# global client
	from ssh import docker
	client = docker()
	return client


def init():
	pass
	# return dev()

# client = dev()
