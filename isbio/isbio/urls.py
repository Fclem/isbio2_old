from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import patterns, include, url
from breeze import views
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.breeze),
    url(r'^breeze/$', views.breeze),
    url(r'^base/$', views.base),
    url(r'^register/$', views.register_user),
    url(r'^logout/$', views.logout),
    url(r'^home/$', views.home),
    url(r'^help/$', views.dochelp),
    url(r'^jobs/(?P<state>[a-z]+)?$', views.jobs),
    url(r'^jobs/delete/(?P<jid>\d+)$', views.delete_job),
    url(r'^jobs/run/(?P<jid>\d+)$', views.run_script),
    url(r'^jobs/edit/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', views.edit_job),
    url(r'^jobs/show-code/(?P<jid>\d+)$', views.show_rcode),
    url(r'^jobs/download/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', views.send_zipfile),
    url(r'^update-jobs/(?P<jid>\d+)?$', views.update_jobs),
    url(r'^scripts/(?P<layout>[a-z]+)?$', views.scripts),
    url(r'^scripts/delete/(?P<sid>\d+)$', views.delete_script),
    url(r'^scripts/apply-script/(?P<sid>\d+)$', views.create_job),
    url(r'^scripts/read-descr/(?P<sid>\d+)$', views.read_descr),
    url(r'^new/append/(?P<which>[A-Z]+)$', views.append_param),
    url(r'^new/delete/(?P<which>.+)$', views.delete_param),
    url(r'^new/$', views.create_script),
    url(r'^new-script/$', views.new_script_dialog),
    url(r'^submit/$', views.save),
    url(r'^get/template/(?P<name>[^/]+)$', views.send_template),
    url(r'^get/(?P<ftype>[a-z]+)-(?P<fname>[A-Za-z]+)$', views.send_file),
    url(r'^builder/$', views.builder),
    url(r'^reports/(?P<what>[a-z]+)?$', views.reports),
    url(r'^reports/overview/(?P<rtype>[A-Za-z]+)-(?P<iname>[^/-]+)-(?P<iid>[^/-]+)(?P<mod>-[a-z]+)?$', views.report_overview),
    url(r'^resources/$', views.resources),
    url(r'^resources/scripts/$', views.manage_scripts),
    url(r'^resources/scripts/script-editor/(?P<sid>\d+)$', views.script_editor),
    url(r'^resources/scripts/script-editor/update/(?P<sid>\d+)$', views.script_editor_update),
    url(r'^resources/reports/$', views.manage_reports),
    url(r'^resources/datasets/$', views.manage_scripts),
    url(r'^resources/files/$', views.manage_scripts),
    url(r'^resources/integration/$', views.manage_scripts),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
                 {'document_root': settings.MEDIA_ROOT}),
    # Examples:
    # Examples:
    # url(r'^$', 'isbio.views.home', name='home'),
    # url(r'^isbio/', include('isbio.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('django.contrib.staticfiles.views',
        url(r'^static/(?P<path>.*)$', 'serve'),
    )

urlpatterns += staticfiles_urlpatterns()
