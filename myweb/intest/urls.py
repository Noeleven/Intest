# -*- coding: utf-8 -*-

from django.conf.urls import url
from intest.views import *
#import settings

urlpatterns = [
	url(r'^$', int_report, name='int_report'),
	# url(r'^int_percent$', int_percent, name='int_percent'),
	# url(r'^int_table$', home, name='home'),
	# url(r'^int_err$', err, name='err'),
	# url(r'^int_trace$', trace, name='trace'),
	url(r'^int_report$', int_report, name='int_report'),
	url(r'^report_ajax$', report_ajax, name='report_ajax'),
   ]
