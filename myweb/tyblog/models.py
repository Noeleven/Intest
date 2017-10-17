from django.db import models
from django.contrib import admin

# Create your models here.
# 接口表
class Ints(models.Model):
	des = models.CharField(max_length=100, default='接口描述')
	method = models.CharField(max_length=100, default='api.com.')
	version = models.CharField(max_length=10, default='1.0.0')

	def __str__(self):
		return self.method


# 占比率
class Rates(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	zero_level = models.IntegerField(default='0')
	one_level = models.IntegerField(default='0')
	two_level = models.IntegerField(default='0')
	three_level = models.IntegerField(default='0')
	four_level = models.IntegerField(default='0')
	five_level = models.IntegerField(default='0')


# 响应时间
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


# 吞吐量
class Rpm(models.Model):
	hostId = models.CharField(max_length=10, null=True,blank=True)
	method = models.CharField(max_length=100, default='api.com.')
	version = models.CharField(max_length=10, null=True,blank=True)
	lvversion = models.CharField(max_length=10, null=True,blank=True)
	isHttp = models.CharField(max_length=10, default="HTTP")
	isGet = models.CharField(max_length=10, default="GET")
	des = models.CharField(max_length=100, default='接口描述')
	rpm = models.DecimalField(max_digits=10, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)
	time = models.CharField(max_length=100, default='时间段')


# 	响应+吞吐 明细表
class RR(models.Model):
	hostId = models.CharField(max_length=10, null=True,blank=True)
	method = models.CharField(max_length=100, default='api.com.')
	version = models.CharField(max_length=10, null=True,blank=True)
	lvversion = models.CharField(max_length=10, null=True,blank=True)
	isHttp = models.CharField(max_length=10, default="HTTP")
	isGet = models.CharField(max_length=10, default="GET")
	des = models.CharField(max_length=100, default='接口描述')
	response = models.DecimalField(max_digits=6, decimal_places=3)
	rpm = models.DecimalField(max_digits=10, decimal_places=1)
	plantform = models.CharField(max_length=10, null=True,blank=True)
	time = models.CharField(max_length=100, default='时间段')


# 错误率
class errs(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	name = models.CharField(max_length=100, default='hostname')
	value = models.DecimalField(max_digits=6, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)


# 崩溃
class crashes(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	name = models.CharField(max_length=100, default='hostname')
	value = models.DecimalField(max_digits=6, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)


# 服务响应
class reses(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	name = models.CharField(max_length=100, default='hostname')
	value = models.DecimalField(max_digits=6, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)


# 交互响应
class views(models.Model):
	des = models.CharField(max_length=100, default='时间段')
	name = models.CharField(max_length=100, default='hostname')
	value = models.DecimalField(max_digits=6, decimal_places=3)
	plantform = models.CharField(max_length=10, null=True,blank=True)


class newData(models.Model):
	name = models.CharField(max_length=100, default='hostname')
	value = models.DecimalField(max_digits=6, decimal_places=3)
	platform = models.CharField(max_length=10, null=True,blank=True)
	date = models.DateField(blank=True, auto_now_add=False)
	type = models.CharField(max_length=100, default='')
	tid = models.CharField(max_length=10, default='')

# 管理视图
class IntsAdmin(admin.ModelAdmin):
    list_display = ('des', 'method', 'version')
    list_per_page = 30
    search_fields = ['des', 'method',]

admin.site.register(Ints, IntsAdmin)
