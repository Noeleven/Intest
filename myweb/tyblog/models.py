from django.db import models
from django.contrib import admin

# Create your models here.
class Ints(models.Model):
	des = models.CharField(max_length=100, default='接口描述')
	method = models.CharField(max_length=100, default='api.com.')
	version = models.CharField(max_length=10, default='1.0.0')
	
	def __str__(self):
		return self.method

class Rates(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	zero_level = models.IntegerField(default='0')
	one_level = models.IntegerField(default='0')
	two_level = models.IntegerField(default='0')
	three_level = models.IntegerField(default='0')
	four_level = models.IntegerField(default='0')
	five_level = models.IntegerField(default='0')
	
class Res(models.Model):
	hostId = models.CharField(max_length=10, null=True,blank=True)
	method = models.CharField(max_length=100, default='api.com.')
	version = models.CharField(max_length=10, null=True,blank=True)
	lvversion = models.CharField(max_length=10, null=True,blank=True)
	isHttp = models.CharField(max_length=10, default="HTTP")
	isGet = models.CharField(max_length=10, default="GET")
	des = models.CharField(max_length=100, default='接口描述')
	response = models.DecimalField(max_digits=6, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)
	time = models.CharField(max_length=100, default='时间段')
	
class Rpm(models.Model):
	hostId = models.CharField(max_length=10, null=True,blank=True)
	method = models.CharField(max_length=100, default='api.com.')
	version = models.CharField(max_length=10, null=True,blank=True)
	lvversion = models.CharField(max_length=10, null=True,blank=True)
	isHttp = models.CharField(max_length=10, default="HTTP")
	isGet = models.CharField(max_length=10, default="GET")
	des = models.CharField(max_length=100, default='接口描述')
	rpm = models.DecimalField(max_digits=8, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)
	time = models.CharField(max_length=100, default='时间段')
	
class errs(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	name = models.CharField(max_length=100, default='hostname')
	value = models.DecimalField(max_digits=6, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)

class crashes(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	name = models.CharField(max_length=100, default='hostname')
	value = models.DecimalField(max_digits=6, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)
	
class reses(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	name = models.CharField(max_length=100, default='hostname')
	value = models.DecimalField(max_digits=6, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)
	
class views(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	name = models.CharField(max_length=100, default='hostname')
	value = models.DecimalField(max_digits=6, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)

class IntsAdmin(admin.ModelAdmin):
    list_display = ('des', 'method', 'version')
    list_per_page = 30
    search_fields = ['des', 'method',]
	
admin.site.register(Ints, IntsAdmin)
