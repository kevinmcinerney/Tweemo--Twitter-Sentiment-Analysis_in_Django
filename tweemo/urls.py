from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^all/$', 'tweemo.views.home'),
    url(r'^temp_test/$', 'tweemo.views.temp_test'),
    url(r'^tweets/$', 'tweemo.views.tweets'),
    url(r'^contactus/$', 'tweemo.views.contactus'),
    url(r'^aboutus/$', 'tweemo.views.aboutus'),
    url(r'^results/$', 'tweemo.views.results'),
    url(r'^stream/$', 'tweemo.views.stream'),
    url(r'^thankyou/$', 'tweemo.views.thankyou'),
    url(r'^gallary/$', 'tweemo.views.gallary'),
    url(r'^usingtweemo/$', 'tweemo.views.usingtweemo'),
    url(r'^howto/$', 'tweemo.views.howto'),
    
)
