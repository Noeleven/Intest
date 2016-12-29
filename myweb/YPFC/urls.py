# -*- coding: utf-8 -*-

from django.conf.urls import url
from YPFC.views import *

urlpatterns = [
	url(r'^$', memView, name='memView'),
	url(r'^memView$', memView, name='memView'),
	url(r'^cashView$', cashView, name='cashView'),
	url(r'^Summary$', Summary, name='Summary'),
	url(r'^saveDate$', saveDate, name='saveDate'),
	url(r'^cashDetail/(.+)/$', cashDetail, name='cashDetail'),
]
