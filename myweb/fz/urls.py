# -*- coding: utf-8 -*-

from django.conf.urls import url
from fz.views import *
#import settings

urlpatterns = [
	url(r'^$', fz_home, name='fz_home'),
   ]
