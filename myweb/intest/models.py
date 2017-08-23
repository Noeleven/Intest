#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin

# Create your models here.
#数据录入表method+version,name,http,get,args,insertime
class Ints(models.Model):
	name = models.CharField(max_length=100, default='接口描述',blank=True)
	method_version = models.CharField(max_length=100, default='api.com.xxx&version=1.0.0')
	ishttp_choice = (
		('HTTP', 'HTTP'),
		('HTTPS', 'HTTPS'),
		('UNKNOW', 'UNKNOW'),
	)
	ishttp = models.CharField(max_length=10, choices=ishttp_choice, default="UNKNOW")
	isget_choice = (
		('GET', 'GET'),
		('POST', 'POST'),
		('UNKNOW', 'UNKNOW'),
	)
	isget = models.CharField(max_length=10, choices=isget_choice, default="UNKNOW")
	type_choice = (
		('用户', '用户'),
		('线路', '线路'),
		('门票', '门票'),
		('微游', '微游'),
		('特卖会', '特卖会'),
		('签证', '签证'),
		('点评', '点评'),
		('支付', '支付'),
		('定制游', '定制游'),
		('度假酒店', '度假酒店'),
		('酒店', '酒店'),
		('邮轮', '邮轮'),
		('订单', '订单'),
		('其他', '其他'),
		('火车票', '火车票'),
		('EBK', 'EBK'),
		('兑吧', '兑吧'),
		('提醒', '提醒'),
		('搜索', '搜索'),
		('登录注册', '登录注册'),
		('wifi/电话卡', 'wifi/电话卡'),
	)
	type = models.CharField(max_length=10, choices=type_choice, default="其他")
	params = models.TextField(default="完整URL或请求参数，参数以&相连")
	inwhere = models.TextField(default="该接口的出现页面位置")
	rpm = models.IntegerField(blank=True, null=True)
	inuse_choice = (
		('0', '弃用'),
		('1', '在用'),
		('2', '未配置'),
	)
	inuse = models.CharField(max_length=1, choices=inuse_choice, default='1')
	timestamp = models.DateField(auto_now=True)

	def __str__(self):
		return self.method_version

#记录每个接口每次测试的数据
class Sdata(models.Model):
	name = models.CharField(max_length=100, default="未知接口")
	method_version = models.CharField(max_length=100)
	url = models.TextField()
	ci = models.CharField(max_length=20)
	method = models.CharField(max_length=10)
	httpCode = models.CharField(max_length=100,null=True,blank=True)
	requesTime = models.DateTimeField(null=True,blank=True)
	log_code = models.CharField(max_length=100,null=True,blank=True)
	log_time = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	dnsTime = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	conneTime = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	sslTime = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	serverTime = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	downloadTime = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	size = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	total_time = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	speed = models.CharField(max_length=10,null=True,blank=True)
	response = models.TextField()
	recordTime = models.DateTimeField(auto_now=True)

# 周数据
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

# 天数据
class Ddata(models.Model):
	method_version = models.CharField(max_length=100, default="api.com.xxx")
	url = models.TextField()
	log_time = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
	dns_time = models.DecimalField(max_digits=5, decimal_places=2)
	tcp_time = models.DecimalField(max_digits=5, decimal_places=2)
	up_time = models.DecimalField(max_digits=5, decimal_places=2)
	server_time = models.DecimalField(max_digits=5, decimal_places=2)
	download_time = models.DecimalField(max_digits=5, decimal_places=2)
	download_size = models.DecimalField(max_digits=5, decimal_places=2)
	total_time = models.DecimalField(max_digits=5, decimal_places=2)
	timestamp = models.DateField(auto_now=False)

# 个级别占比数据
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

# 错误记录表
class Errs(models.Model):
	name = models.CharField(max_length=100,default="未定义接口")
	type = models.CharField(max_length=20,null=True,blank=True,default="其他")
	method_version = models.CharField(max_length=100)
	url = models.TextField()
	httpcode = models.CharField(max_length=100,null=True,blank=True)
	log_code = models.CharField(max_length=100,null=True,blank=True)
	error = models.CharField(max_length=200,null=True,blank=True)
	message = models.CharField(max_length=200,null=True,blank=True)
	timestamp = models.DateTimeField(auto_now=True)


class IntsAdmin(admin.ModelAdmin):
    list_display = ('name', 'method_version', 'ishttp', 'isget', 'type', 'rpm', 'inwhere', 'inuse', 'timestamp')
    list_per_page = 30
    search_fields = ['name', 'method_version', 'type', 'inuse']

admin.site.register(Ints, IntsAdmin)
