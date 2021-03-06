from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import yawf
yawf.autodiscover()

urlpatterns = patterns('',
    url(r'^simple/', include('simple.urls')),
    url(r'^describe/(?P<workflow_id>\w+)/$', 'yawf.views.describe_workflow',
        name='describe'),
    url(r'^describe/(?P<workflow_id>\w+)/graph/handlers/$',
        'yawf.graph_views.handlers_graph'),
    url(r'^describe/(?P<workflow_id>\w+)/graph/effects/$',
        'yawf.graph_views.effects_graph',
        ),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
