def user_context(request):
    if request.user.is_authenticated():
        is_admin = request.user.groups.filter(name='GEEKS')
        is_auth = True
    else:
        is_admin = False
        is_auth = False

    return {
        'is_local_admin': is_admin,
        'is_authenticated': is_auth
    }
