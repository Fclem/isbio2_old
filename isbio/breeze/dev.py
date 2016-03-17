

def dev():
	# global client
	from .docker_interface import Docker
	return Docker()


def init():
	pass
	# return dev()

docker = dev()
docker.self_test()
client = docker.client

