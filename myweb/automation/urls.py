# -*- coding: utf-8 -*-

from django.conf.urls import url
from automation.views import *

urlpatterns = [
	url(r'^$', auto_list, name='auto_list'),
	url(r'^auto_list/(.+)/$', auto_list, name='auto_list'),
	url(r'^auto_add$', auto_add, name='auto_add'),
	url(r'^auto_edit/(.+)/$', auto_edit, name='auto_edit'),
	url(r'^auto_save$', auto_save, name='auto_save'),
	url(r'^auto_edit_save/(.+)/$', auto_edit_save, name='auto_edit_save'),
	url(r'^auto_config$', auto_config, name='auto_config'),
	url(r'^auto_response$', auto_response, name='auto_response'),
	url(r'^auto_del$', auto_del, name='auto_del'),
	url(r'^auto_copy$', auto_copy, name='auto_copy'),
]
