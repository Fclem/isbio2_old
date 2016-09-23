from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.utils.functional import SimpleLazyObject


def site(request):
    site = SimpleLazyObject(lambda: get_current_site(request))
    protocol = 'https' if request.is_secure() else 'http'
    
    return {
        'site'     : site,
        'site_root': SimpleLazyObject(lambda: "{0}://{1}".format(protocol, site.domain)),
    }


def user_context(request):
    is_auth = request.user.is_authenticated()
    is_admin = False
    # assert isinstance(request.user, User)
    is_admin = is_auth and (request.user.is_staff or request.user.is_superuser)

    return {
        'is_local_admin': is_admin,
        'is_authenticated': is_auth
    }


def date_context(_):
    import datetime
    return { 'now': datetime.datetime.now() }
