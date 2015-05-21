from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import patterns, include, url
from breeze import views
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^user_list$', views.user_list),
    url(r'^$', 'django_cas.views.login'),  # views.breeze),
    url(r'^breeze/$', views.breeze),
    # url(r'^test/$', views.dochelp),
    # url(r'^base/$', views.base),
    # url(r'^register/$', views.register_user),
    url(r'^logout/$', 'django_cas.views.logout'),  # views.logout),
    url(r'^stat/$', views.ajax_user_stat),
    url(r'^home/(?P<state>[a-z]+)?$', views.home),
    url(r'^ajax-rora-patients/(?P<which>[a-z]+)?$', views.ajax_patients_data),
    url(r'^ajax-rora/action/$', views.ajax_rora_action),
    url(r'^ajax-rora-plain-screens/(?P<gid>\d+)$', views.ajax_rora_screens),
    url(r'^ajax-rora-groupname/$', views.groupName),
    url(r'^update-user-info$', views.update_user_info_dialog),
    url(r'^update-server/$', views.updateServer),
    url(r'^help/$', views.dochelp),
    url(r'^db-policy/$', views.dbPolicy),
    #url(r'^store/deletefree/$', views.deletefree),
    #url(r'^store/installfree/$', views.installfree),
    url(r'^store/$', views.store),
    url(r'^store/deletefree/$', views.deletefree),
    url(r'^installscripts/(?P<sid>\d+)$', views.install),
    url(r'^installreport/(?P<sid>\d+)$', views.installreport),
    url(r'^mycart/$', views.mycart),
    url(r'^updatecart/$', views.updatecart),
    url(r'^addtocart/(?P<sid>\d+)$', views.addtocart),
    url(r'^dbviewer/$', views.dbviewer),
    url(r'^abortreports/(?P<rid>\d+)$', views.abort_report),
    url(r'^abortjobs/(?P<jid>\d+)$', views.abort_job),
    url(r'^search/(?P<what>[a-z]+)?$', views.search),
    url(r'^patient-data/(?P<which>\d+)?$', views.ajax_patients),
    url(r'^patient-new/$', views.ajax_patients_new),
    url(r'^screen-data/(?P<which>\d+)?$', views.screen_data),
    url(r'^reports/$', views.reports),
    url(r'^showdetails/(?P<sid>\d+)$', views.showdetails),
    url(r'^deletecart/(?P<sid>\d+)$', views.deletecart),
    url(r'^reports/search$', views.report_search),
    # url(r'^reports/ownreports', views.reports_owned), # incorporated into search
    # url(r'^reports/accessreports', views.reports_accessible), # incorporated into search
    url(r'^reports/view/(?P<rid>\d+)/(?P<fname>.+)?$', views.report_file_view),
    url(r'^reports/get/(?P<rid>\d+)/(?P<fname>.+)?$', views.report_file_get),
    url(r'^media/reports/(?P<rid>\d+)_(?P<rest>[^/]+)/(?P<fname>.+)?$', views.report_file_wrap),
    url(r'^media/reports/(?P<rid>\d+)/(?P<fname>.+)?$', views.report_file_wrap2),
    url(r'^reports/delete/(?P<rid>\d+)(?P<redir>-[a-z]+)?$', views.delete_report),
    url(r'^reports/edit_access/(?P<rid>\d+)$', views.edit_report_access),
    url(r'^reports/send/(?P<rid>\d+)$', views.send_report),
    url(r'^reports/add-offsite-user/(?P<rid>\d*)$', views.add_offsite_user_dialog),
    url(r'^reports/add-offsite-user/next/(?P<email>[\b[\w.-]+@[\w.-]+.\w{2,4}\b]*)$', views.add_offsite_user),
    url(r'^reports/add-offsite-user/next/$', views.add_offsite_user),
    url(r'^reports/overview/(?P<rtype>[A-Za-z]+)-(?P<iname>[^/-]+)-(?P<iid>[^/-]+)$', views.report_overview),
    url(r'^reports/shiny1/(?P<rid>\d+)/?$', views.report_shiny_view),
    url(r'^reports/shiny2/(?P<rid>\d+)/?$', views.report_shiny_view2),
    url(r'^reports/shiny-tab/(?P<rid>\d+)/?$', views.report_shiny_view_tab),
    #sub-level
    url(r'^shiny/(?P<path>.*)$', views.report_shiny_in_wrapper),
    url(r'^shiny-out/(?P<s_key>[a-z0-9]+)/(?P<u_key>[a-z0-9]+)/$', views.report_shiny_view_tab_out),
    url(r'^shiny-out/(?P<s_key>[a-z0-9]+)/(?P<u_key>[a-z0-9]+)/(?P<path>.*)$', views.report_shiny_out_wrapper),
    url(r'^reports/edit/(?P<jid>\d+)?$', views.edit_report),  # Re Run report
    url(r'^reports/check$', views.check_reports),  # Re Run report
    # fusion thoses lines
    url(r'^jobs/current', views.jobs, {'state': "current"}),
    url(r'^jobs/scheduled?$', views.jobs, {'state': "scheduled"}),
    url(r'^jobs/history?$', views.jobs),
    url(r'^jobs/(?P<state>[a-z]+)?$', views.jobs),
    # url(r'^jobs/live-container', views.jobs),
    url(r'^jobs/delete/(?P<jid>\d+)(?P<state>[a-z]+)?$', views.delete_job),
    url(r'^jobs/run/(?P<jid>\d+)$', views.run_script),
    url(r'^jobs/edit/jobs/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', views.edit_job), # ReSchedule, and Edit ?

    url(r'^jobs/show-code/(?P<jid>\d+)$', views.show_rcode),
    url(r'^jobs/download/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', views.send_zipfile),
    # url(r'^media/jobs/(?P<rid>\d+)_(?P<rest>[^/-]+)/(?P<fname>[^/-]+)?$', views.report_file_wrap),
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
    url(r'^resources/pipes/pipe-editor/(?P<pid>\d+)$', views.edit_rtype_dialog),
    url(r'^resources/pipes/delete/(?P<pid>\d+)$', views.delete_pipe),
    url(r'^resources/datasets/$', views.manage_scripts),
    url(r'^resources/files/$', views.manage_scripts),
    url(r'^resources/integration/$', views.manage_scripts),
    url(r'^pagination/home/$', views.home_paginate),

    url(r'^media/scripts/(?P<path>[^.]*(\.(jpg|jpeg|gif|png)))?$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT + 'scripts/'}),
    url(r'^media/pipelines/(?P<path>[^.]*(\.(pdf)))$', 'django.views.static.serve',
                 {'document_root': settings.MEDIA_ROOT + 'pipelines/'}),
    url(r'^media/mould/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT + 'mould/'}),

    #url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
    #             {'document_root': settings.MEDIA_ROOT}),
    # TODO test for completition of the access-enforced static files serving
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
        url(r'^reports/TEST/(?P<jid>\d+)?$', views.edit_reportMMMMM),  # Testing
        url(r'^shiny/sample/(?P<path>.*)$', views.proxy_to, {'target_url': 'http://127.0.0.1:3838/sample-apps/'}),  # testing
        # url(r'^shiny/(?P<path>.*)$', views.proxy_to, {'target_url': settings.SHINY_TARGET_URL}),
    )

urlpatterns += staticfiles_urlpatterns()
