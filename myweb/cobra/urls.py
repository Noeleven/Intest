# -*- coding: utf-8 -*-

from django.conf.urls import url
from cobra.views import *

urlpatterns = [
	url(r'^cobra_chart$', cobra_chart, name='cobra_chart'),
	url(r'^cobra_datas$', cobra_datas, name='cobra_datas'),
	url(r'^cobra_trace$', cobra_trace, name='cobra_trace'),
	url(r'^single$', single, name='single'),
	url(r'^project$', project, name='project'),
]
