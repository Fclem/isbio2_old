from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^login/?$', process_login, name='process_login'),
    url(r'^logout/?$', trigger_logout, name='trigger_logout'),
]
