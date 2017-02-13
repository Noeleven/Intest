# -*- coding: utf-8 -*-

from django.conf.urls import url
from automation.views import *

urlpatterns = [
	url(r'^$', auto_list, name='auto_list'),
	url(r'^auto_list/(.+)/$', auto_list, name='auto_list'),
	url(r'^auto_add$', auto_add, name='auto_add'),
	url(r'^auto_edit/(.+)/$', auto_edit, name='auto_edit'),
	url(r'^auto_save$', auto_save, name='auto_save'),
]
