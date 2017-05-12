from django.db import models
from django.contrib import admin

# Create your models here.

class Method(models.Model):
	method = models.CharField(max_length=100, default='api.com.')
	version = models.CharField(max_length=10, default='1.0.0')
	des = models.CharField(max_length=100, default='接口描述', null=True, blank=True)
	type = models.CharField(max_length=100, default='品类', null=True, blank=True)
	enabled = models.CharField(max_length=1, default='1')

	def __str__(self):
		return self.method


# 每天把当天的接口吞吐和响应存入一个平均值
class Datas(models.Model):
	method_id = models.IntegerField()
	res = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
	rpm = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
	create_time = models.DateField(auto_now=False)

class Projects(models.Model):
	pName = models.CharField(max_length=50, default='')
	count = models.IntegerField(blank=True, null=True)
	day = models.DateField(auto_now=False)

class Channel(models.Model):
	method_id = models.IntegerField()
	channel = models.CharField(max_length=50, default='NONE')
	count = models.IntegerField()
	day = models.DateField(auto_now=False)
