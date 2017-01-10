#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin

# Create your models here.
#数据录入表method+version,name,http,get,args,insertime
class Ints(models.Model):
    name = models.CharField(max_length=100, default='品类-接口描述')
    method_version = models.CharField(max_length=100, default='api.com.route.creatOrder&version=1.0.0')
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
    params = models.TextField(default="&firstChannel=LVMM&secondChannel=...")
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
    method_version = models.CharField(max_length=100)
    url = models.TextField()
    code = models.CharField(max_length=100,null=True,blank=True)
    log_code = models.CharField(max_length=100,null=True,blank=True)
    debugmsg = models.CharField(max_length=200, null=True,blank=True)
    error = models.CharField(max_length=200, null=True,blank=True)
    message = models.CharField(max_length=200, null=True,blank=True)
    timestamp = models.DateTimeField(auto_now=True)

class IntsAdmin(admin.ModelAdmin):
    list_display = ('name', 'method_version', 'ishttp', 'isget', 'type', 'inwhere', 'inuse', 'timestamp')
    list_per_page = 30
    search_fields = ['name', 'method_version', 'type', 'inuse']

admin.site.register(Ints, IntsAdmin)
