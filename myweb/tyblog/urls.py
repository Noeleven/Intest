# -*- coding: utf-8 -*-

from django.conf.urls import url
from tyblog.views import *

urlpatterns = [
    url(r'^index/$', index, name='index'),  # 测试平台
	url(r'^login/$', login, name='login'),
	url(r'^ty_login/$', ty_login, name='ty_login'),
	url(r'^logout/$', logout, name='logout'),
	# 听云二期URL↓
	url(r'^$', newCrash, name='newCrash'),
	url(r'^ty_Overview$', ty_Overview, name='ty_Overview'),
    # 听云3期URL↓
    url(r'^newCrash$', newCrash, name='newCrash'),
    url(r'^newErr$', newErr, name='newErr'),
    url(r'^newView$', newView, name='newView'),
    url(r'^newRes$', newRes, name='newRes'),
]
