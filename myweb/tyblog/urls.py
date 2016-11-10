# -*- coding: utf-8 -*-

from django.conf.urls import url
from tyblog.views import tyreport, index, ty_index, ty_overview, ty_Todo, ty_fullLists, ty_NewVersion, ty_keyElements

urlpatterns = [
    url(r'^index/$', index, name='index'),
    url(r'^tyreport/$', tyreport, name='tyreport'),
	# 听云二期URL↓
	url(r'^$', ty_index, name='ty_index'),
	url(r'^ty_overview', ty_overview, name='ty_overview'),
	url(r'^ty_Todo', ty_Todo, name='ty_Todo'),
	url(r'^ty_fullLists', ty_fullLists, name='ty_fullLists'),
	url(r'^ty_NewVersion', ty_NewVersion, name='ty_NewVersion'),
	url(r'^ty_keyElements', ty_keyElements, name='ty_keyElements'),
]
