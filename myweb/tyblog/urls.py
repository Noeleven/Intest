# -*- coding: utf-8 -*-

from django.conf.urls import url
from tyblog.views import tyreport,tt

urlpatterns = [
    url(r'^tyreport/$', tyreport, name='tyreport'),
    url(r'^tt/$', tt, name='tt'),
]
