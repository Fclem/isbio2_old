# clem 31/03/2016
# adapted from https://pypi.python.org/pypi/hurry.filesize


class UnitSystem:
	traditional = [
		(1024 ** 5, 'P'),
		(1024 ** 4, 'T'),
		(1024 ** 3, 'G'),
		(1024 ** 2, 'M'),
		(1024 ** 1, 'K'),
		(1024 ** 0, 'B'),
	]

	alternative = [
		(1024 ** 5, ' PB'),
		(1024 ** 4, ' TB'),
		(1024 ** 3, ' GB'),
		(1024 ** 2, ' MB'),
		(1024 ** 1, ' KB'),
		(1024 ** 0, (' byte', ' bytes')),
	]

	verbose = [
		(1024 ** 5, (' petabyte', ' petabytes')),
		(1024 ** 4, (' terabyte', ' terabytes')),
		(1024 ** 3, (' gigabyte', ' gigabytes')),
		(1024 ** 2, (' megabyte', ' megabytes')),
		(1024 ** 1, (' kilobyte', ' kilobytes')),
		(1024 ** 0, (' byte', ' bytes')),
	]

	iec = [
		(1024 ** 5, 'Pi'),
		(1024 ** 4, 'Ti'),
		(1024 ** 3, 'Gi'),
		(1024 ** 2, 'Mi'),
		(1024 ** 1, 'Ki'),
		(1024 ** 0, ''),
	]

	si = [
		(1000 ** 5, 'P'),
		(1000 ** 4, 'T'),
		(1000 ** 3, 'G'),
		(1000 ** 2, 'M'),
		(1000 ** 1, 'K'),
		(1000 ** 0, 'B'),
	]


def file_size2human(bytes_count, system=UnitSystem.traditional, digit=0):
	"""Human-readable file size.

	Using the traditional system, where a factor of 1024 is used::

	>>> file_size2human(10)
	'10B'
	>>> file_size2human(100)
	'100B'
	>>> file_size2human(1000)
	'1000B'
	>>> file_size2human(2000)
	'1K'
	>>> file_size2human(10000)
	'9K'
	>>> file_size2human(20000)
	'19K'
	>>> file_size2human(100000)
	'97K'
	>>> file_size2human(200000)
	'195K'
	>>> file_size2human(1000000)
	'976K'
	>>> file_size2human(2000000)
	'1M'

	Using the SI system, with a factor 1000::

	>>> file_size2human(10, system=UnitSystem.si)
	'10B'
	>>> file_size2human(100, system=UnitSystem.si)
	'100B'
	>>> file_size2human(1000, system=UnitSystem.si)
	'1K'
	>>> file_size2human(2000, system=UnitSystem.si)
	'2K'
	>>> file_size2human(10000, system=UnitSystem.si)
	'10K'
	>>> file_size2human(20000, system=UnitSystem.si)
	'20K'
	>>> file_size2human(100000, system=UnitSystem.si)
	'100K'
	>>> file_size2human(200000, system=UnitSystem.si)
	'200K'
	>>> file_size2human(1000000, system=UnitSystem.si)
	'1M'
	>>> file_size2human(2000000, system=UnitSystem.si)
	'2M'

	:type bytes_count: int
	:type system: Systems
	:type digit: int
	:rtype str
	"""
	for factor, suffix in system:
		if bytes_count >= factor:
			break
	amount = float(bytes_count) / factor
	if isinstance(suffix, tuple):
		singular, multiple = suffix
		if int(amount) == 1:
			suffix = singular
		else:
			suffix = multiple
	return (('%%.0%sf' % digit) % amount) + suffix

