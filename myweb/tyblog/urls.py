# -*- coding: utf-8 -*-

from django.conf.urls import url
from tyblog.views import *

urlpatterns = [
    url(r'^index/$', index, name='index'),
    # url(r'^tyreport/$', tyreport, name='tyreport'),
	url(r'^login/$', login, name='login'),
	url(r'^ty_login/$', ty_login, name='ty_login'),
	url(r'^logout/$', logout, name='logout'),
	# 听云二期URL↓
	url(r'^$', ty_Overview, name='ty_Overview'),
	url(r'^ty_Overview$', ty_Overview, name='ty_Overview'),
	url(r'^ty_Android_All', ty_Android_All, name='ty_Android_All'),
	url(r'^ty_IOS_All', ty_IOS_All, name='ty_IOS_All'),
	url(r'^ty_siteApi3g2', ty_siteApi3g2, name='ty_siteApi3g2'),
	url(r'^ty_siteApi3g', ty_siteApi3g, name='ty_siteApi3g'),
	url(r'^ty_siteM', ty_siteM, name='ty_siteM'),
	url(r'^ty_rpmAll', ty_rpmAll, name='ty_rpmAll'),
	url(r'^ty_fullLists', ty_fullLists, name='ty_fullLists'),
	url(r'^ty_keyElements', ty_keyElements, name='ty_keyElements'),
]
