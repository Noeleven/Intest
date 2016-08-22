# -*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin

# Create your models here.
#数据录入表method,name,version,args
class Ints(models.Model):
	method = models.CharField(max_length=100)
	name = models.CharField(max_length=100)
	version = models.CharField(max_length=10)
	args = models.TextField()
	timestamp = models.DateTimeField()

class IntsAdmin(admin.ModelAdmin):
	list_display = ('method', 'name', 'version', 'timestamp')

admin.site.register(Ints, IntsAdmin)
