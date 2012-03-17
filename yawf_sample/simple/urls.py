from django.conf.urls import patterns, include, url

urlpatterns = patterns('simple.views',
    url(r'^window/(?P<pk>\d+)/resize/$', 'window_resize'),
    url(r'^window/(?P<pk>\d+)/maximize/$', 'window_maximize'),
)
