# -*- coding: utf-8 -*-
"""myweb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView


urlpatterns = [
    url(r'^$', RedirectView.as_view(url=r"/tyblog/index/")),
    url(r'^admin/', admin.site.urls),
    url(r'^intest/', include('intest.urls')),
    url(r'^fz/', include('fz.urls')),
    url(r'^tyblog/', include('tyblog.urls')),
    url(r'^cobra/', include('cobra.urls')),
	url(r'^accounts/login/', RedirectView.as_view(url=r'/tyblog/login')),
	url(r'^favicon.ico$',RedirectView.as_view(url=r'static/favicon.ico')),
	url(r'^logout/$', RedirectView.as_view(url=r"/tyblog/logout/")),
]
