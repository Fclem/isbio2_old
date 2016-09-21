from django.conf.urls import url # , include
# from django.conf import settings
# from django.contrib.staticfiles.views import serve
from . import views
# from breeze.middlewares import is_on

urlpatterns = [
	# Shiny page in
	url(r'^reports/shiny-tab/(?P<rid>\d+)/?$', views.report_shiny_view_tab),
	url(r'^shiny/sample/(?P<path>.*)$', views.proxy_to,
		kwargs={ 'target_url': 'http://127.0.0.1:3838/sample-apps/', }),
	url(r'^shiny/rep/(?P<rid>\d+)/nozzle$', views.report_file_view_redir),
	url(r'^shiny/apps/((?P<path>[^/]*)/(?P<sub>.*))?$', views.standalone_shiny_in_wrapper),
	url(r'^shiny/pubs?(/(?P<path>.+))?/?$', views.standalone_pub_shiny_fw),
	url(r'^shiny/rep/(?P<rid>\d+)/(?P<path>.*)?$', views.report_shiny_in_wrapper),
	url(r'^shiny/libs/(?P<path>.*)$', views.shiny_libs),
]
