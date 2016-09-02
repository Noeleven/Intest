# -*- coding: utf-8 -*-

from django.conf.urls import url
from intest.views import *
#import settings

urlpatterns = [
	url(r'^$', home, name='home'),
   ]
