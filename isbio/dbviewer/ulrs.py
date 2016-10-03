from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^dbviewer/?$', views.db_viewer),
	url(r'^db-policy/?$', views.db_policy),
]
