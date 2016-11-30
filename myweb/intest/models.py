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
	isget = models.CharField(max_length=10, default="GET")
	params = models.TextField(default="URL里接口&之后的内容")
	inwhere = models.TextField(default="该接口的出现页面位置")
	inuse_choice = (
		('0', '弃用'),
		('1', '在用'),
	)
	inuse = models.CharField(max_length=1, choices=inuse_choice, default='1')
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
	log_time = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	dns_time = models.DecimalField(max_digits=5, decimal_places=2)
	tcp_time = models.DecimalField(max_digits=5, decimal_places=2)
	up_time = models.DecimalField(max_digits=5, decimal_places=2)
	server_time = models.DecimalField(max_digits=5, decimal_places=2)
	download_time = models.DecimalField(max_digits=5, decimal_places=2)
	download_size = models.DecimalField(max_digits=5, decimal_places=2)
	total_time = models.DecimalField(max_digits=5, decimal_places=2)
	error = models.CharField(max_length=200, null=True,blank=True)
	message = models.CharField(max_length=200, null=True,blank=True)
	timestamp = models.DateTimeField(auto_now=True)

class Wdata(models.Model):
	name = models.CharField(max_length=100, default="未定义接口")
	method_version = models.CharField(max_length=100)
	url = models.TextField()
	log_time = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	dns_time = models.DecimalField(max_digits=5, decimal_places=2)
	tcp_time = models.DecimalField(max_digits=5, decimal_places=2)
	up_time = models.DecimalField(max_digits=5, decimal_places=2)
	server_time = models.DecimalField(max_digits=5, decimal_places=2)
	download_time = models.DecimalField(max_digits=5, decimal_places=2)
	download_size = models.DecimalField(max_digits=5, decimal_places=2)
	total_time = models.DecimalField(max_digits=5, decimal_places=2)
	ms_tag = models.IntegerField()
	timestamp = models.DateField(auto_now=False)
	
class Rate(models.Model):
	des = models.CharField(max_length=20, null=True, blank=True)
	type = models.CharField(max_length=1, default='0')
	err_rate = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
	ms = models.DecimalField(max_digits=4, decimal_places=2)
	os = models.DecimalField(max_digits=4, decimal_places=2)
	ts = models.DecimalField(max_digits=4, decimal_places=2)
	tts = models.DecimalField(max_digits=4, decimal_places=2)
	fs = models.DecimalField(max_digits=4, decimal_places=2)
	ffs = models.DecimalField(max_digits=4, decimal_places=2)
	
class Errs(models.Model):
	name = models.CharField(max_length=100, default="未定义接口")
	method_version = models.CharField(max_length=100)
	url = models.TextField() 
	httpcode = models.CharField(max_length=100, null=True,blank=True)
	log_code = models.CharField(max_length=100, null=True,blank=True)
	error = models.CharField(max_length=200, null=True,blank=True)
	message = models.CharField(max_length=200, null=True,blank=True)
	timestamp = models.DateTimeField(auto_now=True)
	
class IntsAdmin(admin.ModelAdmin):
    list_display = ('name', 'method_version', 'ishttp', 'isget', 'inwhere', 'inuse', 'timestamp')
    list_per_page = 30
    search_fields = ['name', 'method_version',]

admin.site.register(Ints, IntsAdmin)
