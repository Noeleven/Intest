# -*- coding: utf-8 -*-

from django.conf.urls import url
from tyblog.views import tyreport

urlpatterns = [
    url(r'^tyreport/$', tyreport, name='tyreport'),
]
