# -*- coding: utf-8 -*-

from django.conf.urls import url
from intest.views import *
#import settings

urlpatterns = [
	url(r'^$', int_percent, name='int_percent'),
	url(r'^int_percent$', int_percent, name='int_percent'),
	url(r'^int_table$', home, name='home'),
	url(r'^int_err$', err, name='err'),
	url(r'^int_trace$', trace, name='trace'),
   ]
