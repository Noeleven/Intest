#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin

# Create your models here.
#数据录入表method+version,name,http,get,args,insertime
class Ints(models.Model):
    name = models.CharField(max_length=100, default='接口描述')
    method_version = models.CharField(max_length=100, default='api.com.xxx&version=x.0.0')
    ishttp = models.CharField(max_length=10, default="HTTP")
    isget = models.CharField(max_length=10,default="GET")
    params = models.TextField(default="URL里接口&之后的内容")
    inwhere = models.TextField(default="该接口的出现页面位置")
    timestamp = models.DateField(auto_now=True)

    def __str__(self):
        return self.method_version

#记录每个接口每次测试的数据
class Sdata(models.Model):
    name = models.CharField(max_length=100, default="未定义接口")
    method_version = models.CharField(max_length=100)
    url = models.TextField()
    code = models.CharField(max_length=100,null=True,blank=True)
    log_code = models.CharField(max_length=100,null=True,blank=True)
    debugmsg = models.CharField(max_length=200, null=True,blank=True)
    error = models.CharField(max_length=200, null=True,blank=True)
    message = models.CharField(max_length=200, null=True,blank=True)
    timestamp = models.DateTimeField(auto_now=True)
	
class IntsAdmin(admin.ModelAdmin):
	list_display = ('name', 'method_version', 'ishttp', 'isget', 'inwhere', 'timestamp')

admin.site.register(Ints, IntsAdmin)

