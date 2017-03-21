# -*- coding: utf-8 -*-

from django.conf.urls import url
from automation.views import *

urlpatterns = [
	url(r'^$', auto_list, name='auto_list'),
	url(r'^auto_list/(.+)/$', auto_list, name='auto_list'),
	url(r'^auto_edit_save/(.+)/$', auto_edit_save, name='auto_edit_save'),
	url(r'^auto_config$', auto_config, name='auto_config'),
	url(r'^auto_response$', auto_response, name='auto_response'),
	url(r'^auto_del$', auto_del, name='auto_del'),
	url(r'^auto_copy$', auto_copy, name='auto_copy'),
	url(r'^new_add$', new_add, name='new_add'),
	url(r'^new_save$', new_save, name='new_save'),
	url(r'^new_edit/(.+)/$', new_edit, name='new_edit'),
	url(r'^auto_caseJson$', auto_caseJson, name='auto_caseJson'),
	url(r'^test_list$', test_list, name='test_list'),
]
