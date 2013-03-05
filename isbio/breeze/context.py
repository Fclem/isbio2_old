def user_context(request):
    if request.user.is_authenticated():
        is_admin = request.user.groups.filter(name='GEEKS')
    else:
        is_admin = False

    return {
        'is_local_admin': is_admin
    }
