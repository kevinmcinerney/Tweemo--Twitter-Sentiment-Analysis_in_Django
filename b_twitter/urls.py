from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^', include('tweemo.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
