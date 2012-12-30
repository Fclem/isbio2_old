from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import patterns, include, url
from breeze import views
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^breeze/$', views.breeze),
    url(r'^login/$', views.login),
    url(r'^home/$', views.home),
    url(r'^jobs/$', views.jobs),
    url(r'^scripts/$', views.scripts),
    url(r'^result/$', views.result),
    url(r'^download/$', views.send_zipfile),
    url(r'^base/$', views.base),
    url(r'^form/$', views.demo_form),
    url(r'^read-form/$', views.read_form),
    url(r'^new/$', views.create)
    # Examples:
    # Examples:
    # url(r'^$', 'isbio.views.home', name='home'),
    # url(r'^isbio/', include('isbio.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('django.contrib.staticfiles.views',
        url(r'^static/(?P<path>.*)$', 'serve'),
    )

urlpatterns += staticfiles_urlpatterns()
