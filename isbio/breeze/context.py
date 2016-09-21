from django.contrib.auth.models import User


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
