from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'aib.views.index'),
    (r'^(?P<board>\w+)/$', 'aib.views.board'),
    (r'^(?P<board>\w+)/post/$', 'aib.views.post', {"thread":"new"}),

    (r'^(?P<board>\w+)/(?P<thread>\d+)/$', 'aib.views.thread'),
    (r'^(?P<board>\w+)/(?P<thread>\d+)/post/$', 'aib.views.post'),

    (r'^image/(?P<image_key>[^/]+)/$', 'aib.views.image'),
    (r'^thumb/(?P<thumb_key>[^/]+)/$', 'aib.views.thumb'),

)
