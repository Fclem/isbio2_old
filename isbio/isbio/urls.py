from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import patterns, include, url
from breeze import views
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'django_cas.views.login'),  # views.breeze),
    url(r'^breeze/$', views.breeze),
    # url(r'^test/$', views.dochelp),
    # url(r'^base/$', views.base),
    # url(r'^register/$', views.register_user),
    url(r'^logout/$', 'django_cas.views.logout'),  # views.logout),
    url(r'^home/(?P<state>[a-z]+)?$', views.home),
    url(r'^ajax-rora-patients/(?P<which>[a-z]+)?$', views.ajax_patients_data),
    url(r'^ajax-rora/action/$', views.ajax_rora_action),
    url(r'^ajax-rora-plain-screens/(?P<gid>\d+)$', views.ajax_rora_screens),
    url(r'^update-user-info/$', views.update_user_info_dialog),
    url(r'^help/$', views.dochelp),
    url(r'^dbviewer/$', views.dbviewer),
    url(r'^search/(?P<what>[a-z]+)?$', views.search),
    url(r'^reports/$', views.reports),
    url(r'^reports/search$', views.report_search),
    url(r'^reports/delete/(?P<rid>\d+)(?P<redir>-[a-z]+)?$', views.delete_report),
    url(r'^reports/overview/(?P<rtype>[A-Za-z]+)-(?P<iname>[^/-]+)-(?P<iid>[^/-]+)$', views.report_overview),
    url(r'^jobs/(?P<state>[a-z]+)?$', views.jobs),
    url(r'^jobs/delete/(?P<jid>\d+)$', views.delete_job),
    url(r'^jobs/run/(?P<jid>\d+)$', views.run_script),
    url(r'^jobs/edit/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', views.edit_job),
    url(r'^jobs/show-code/(?P<jid>\d+)$', views.show_rcode),
    url(r'^jobs/download/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', views.send_zipfile),
    url(r'^update-jobs/(?P<jid>\d+)-(?P<item>[a-z]+)$', views.update_jobs),
    url(r'^scripts/(?P<layout>[a-z]+)?$', views.scripts),
    url(r'^scripts/delete/(?P<sid>\d+)$', views.delete_script),
    url(r'^scripts/apply-script/(?P<sid>\d+)$', views.create_job),
    url(r'^scripts/read-descr/(?P<sid>\d+)$', views.read_descr),
    url(r'^new/append/(?P<which>[A-Z]+)$', views.append_param),
    url(r'^new/delete/(?P<which>.+)$', views.delete_param),
    url(r'^new/$', views.create_script),
    url(r'^new-script/$', views.new_script_dialog),
    url(r'^new-rtype/$', views.new_rtype_dialog),
    url(r'^projects/create$', views.new_project_dialog),
    url(r'^projects/edit/(?P<pid>\d+)$', views.edit_project_dialog),
    url(r'^projects/view/(?P<pid>\d+)$', views.veiw_project),
    url(r'^projects/delete/(?P<pid>\d+)$', views.delete_project),
    url(r'^groups/create$', views.new_group_dialog),
    url(r'^groups/edit/(?P<gid>\d+)$', views.edit_group_dialog),
    url(r'^groups/view/(?P<gid>\d+)$', views.view_group),
    url(r'^groups/delete/(?P<gid>\d+)$', views.delete_group),
    url(r'^submit/$', views.save),
    url(r'^get/template/(?P<name>[^/]+)$', views.send_template),
    url(r'^get/(?P<ftype>[a-z]+)-(?P<fname>[^/-]+)$', views.send_file),
    url(r'^builder/$', views.builder),
    url(r'^resources/$', views.resources),
    url(r'^resources/scripts/$', views.manage_scripts),
    url(r'^resources/scripts/script-editor/(?P<sid>\d+)(?P<tab>-[a-z_]+)?$', views.script_editor),
    url(r'^resources/scripts/script-editor/update/(?P<sid>\d+)$', views.script_editor_update),
    url(r'^resources/scripts/script-editor/get-content/(?P<content>[^/-]+)(?P<iid>-\d+)?$', views.send_dbcontent),
    url(r'^resources/scripts/script-editor/get-code/(?P<sid>\d+)/(?P<sfile>[^/-]+)$', views.get_rcode),
    url(r'^resources/scripts/script-editor/get-form/(?P<sid>\d+)$', views.get_form),
    url(r'^resources/pipes/$', views.manage_pipes),
    url(r'^resources/pipes/delete/(?P<pid>\d+)$', views.delete_pipe),
    url(r'^resources/datasets/$', views.manage_scripts),
    url(r'^resources/files/$', views.manage_scripts),
    url(r'^resources/integration/$', views.manage_scripts),
    url(r'^pagination/home/$', views.home_paginate),
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
