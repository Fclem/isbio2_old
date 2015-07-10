from breeze.models import UserProfile
from breeze import views

class CheckUserProfile(object):
	@staticmethod
	def process_exception(request, exception):
		if isinstance(exception, UserProfile.DoesNotExist):
			return views.home(request)

