#!/usr/bin/env python
# -*- coding:utf8 -*-
import django
import os
import sys
import datetime
import time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from intest.models import *
from cobra.models import Method

'''
计算内网测试接口占比、周追踪、归纳日数据
'''
# 时间函数 求一周前开始、今天结束时间、时间描述
def time_des():
	d = datetime.datetime.now()
	# 调试，下面doDdata也要改改
	# d = datetime.datetime(2017, 2, 5, 23, 50, 00, 000000)

	this_year = d.year
	this_month = d.month
	this_day = d.day
	week_from = d - datetime.timedelta(days=6)

	date_from = datetime.datetime(week_from.year, week_from.month, week_from.day, 00, 00)
	date_to = datetime.datetime(this_year, this_month, this_day, 23, 59)
	flag = 0
	if this_day == 7:
		des = ("%s%s第1周" % (this_year, this_month))
		flag = 1
	elif this_day == 14:
		des = ("%s%s第2周" % (this_year, this_month))
		flag = 1
	elif this_day == 21:
		des = ("%s%s第3周" % (this_year, this_month))
		flag = 1
	elif this_day == 28:
		des = ("%s%s第4周" % (this_year, this_month))
		flag = 1
	else:
		des = ''
		pass
	return date_from, date_to, des, flag


# 计算周占比 存Rate表
def doRate():
	date_from = time_des()[0]
	date_to = time_des()[1]
	des = time_des()[2]

	range_list = Ddata.objects.all().filter(timestamp__range=(date_from, date_to))
	# err_list = Errs.objects.all().filter(timestamp__range=(date_from, date_to)).exclude(httpcode=200)
	# err_rate = round(len(err_list) * 100 / len(range_list), 2)
	if range_list:
		pass
	else:
		sys.exit(0)

	method_list_src = range_list.values('method_version').distinct().order_by('method_version')
	method_list = [x['method_version'] for x in method_list_src]
	# 首包占比
	server_li = []
	# 总时间占比
	total_li = []

	for method in method_list:
		my_list = range_list.filter(method_version=method)
		# 算该接口的平均首包和平均总时间
		server_avg = sum([x['server_time'] for x in my_list.values('server_time')]) / len(my_list)
		server_li.append(server_avg)
		total_avg = sum([x['total_time'] for x in my_list.values('total_time')]) / len(my_list)
		total_li.append(total_avg)
	# type=s 首包计算
	Rate.objects.filter(des=des).delete()
	server_len = len(server_li)
	p = Rate(des=des)
	p.type = 's'
	p.ms = round((len([x for x in server_li if x<1]) *100 / server_len), 2)
	p.os = round((len([x for x in server_li if 1<=x<2 ]) *100  / server_len), 2)
	p.ts = round((len([x for x in server_li if 2<=x<3])  *100 / server_len), 2)
	p.tts = round((len([x for x in server_li if 3<=x<4]) *100  / server_len), 2)
	p.fs = round((len([x for x in server_li if 4<=x<5])  *100 / server_len), 2)
	p.ffs = round((len([x for x in server_li if x>5]) *100  / server_len), 2)
	# p.err_rate = err_rate
	p.save()
	# type=t 总时间计算
	total_len = len(total_li)
	p = Rate(des=des)
	p.type = 't'
	p.ms = round((len([x for x in total_li if x<1])  *100 / total_len), 2)
	p.os = round((len([x for x in total_li if 1<=x<2 ])  *100 / total_len), 2)
	p.ts = round((len([x for x in total_li if 2<=x<3]) *100  / total_len), 2)
	p.tts = round((len([x for x in total_li if 3<=x<4]) *100  / total_len), 2)
	p.fs = round((len([x for x in total_li if 4<=x<5])  *100 / total_len), 2)
	p.ffs = round((len([x for x in total_li if x>5])  *100 / total_len), 2)
	p.save()



# 归纳Sdata到周数据，每周更新一次
def doWdata():
	date_from = time_des()[0]
	date_to = time_des()[1]
	now = time_des()[1].strftime("%Y-%m-%d")
	# 调试
	# date_from = datetime.datetime(2016, 12, 22, 00, 00)
	# date_to = datetime.datetime(2016, 12, 28, 23, 59)
	# now = "2016-12-28"
	# 计算数据平均值
	range_list = Ddata.objects.filter(timestamp__range=(date_from, date_to))
	method_list_src = range_list.values('method_version').distinct().order_by('method_version')
	method_list = [x['method_version'] for x in method_list_src]
	print("now is %s" % now)
	Wdata.objects.filter(timestamp=now).delete()
	for method in method_list:
		p = Wdata(method_version=method)
		rr = range_list.filter(method_version=method).order_by('-timestamp')
		total = len([x.dns_time for x in rr])
		p.url = rr[0].url
		print(method)
		try:
			p.name = Ints.objects.filter(method_version=method)[0].name
		except:
			print("method %s name error!" % method)
		p.log_time = sum([x.log_time for x in rr if x.log_time]) / total
		p.dns_time = sum([x.dns_time for x in rr]) / total
		p.tcp_time = sum([x.tcp_time for x in rr]) / total
		p.up_time = sum([x.up_time for x in rr]) / total
		p.server_time = sum([x.server_time for x in rr]) / total
		p.download_time = sum([x.download_time for x in rr]) / total
		p.download_size = sum([x.download_size for x in rr]) / total
		p.total_time = sum([x.total_time for x in rr]) / total
		p.ms_tag = int(p.server_time) # 按照servertime来确认标签
		p.timestamp = now
		p.save()


# 归纳Sdata到日数据，每周更新一次
def doDdata():
	now = datetime.datetime.now()
	date_from = datetime.datetime(now.year, now.month, now.day, 00, 00)
	date_to = datetime.datetime(now.year, now.month, now.day, 23, 59)
	# 历史数据生成，这里没有处理跨月的，因此开始结束时间请不要跨月
	# date_from = datetime.datetime(2017, 2, 5, 00, 00)
	# date_to = datetime.datetime(2017, 2, 5, 23, 59)
	for day in range(date_from.day, date_to.day + 1):
		print("day%s begin" % day)
		stamp = datetime.datetime(date_from.year, date_from.month, day).strftime("%Y-%m-%d")
		# 确定当天数据范围
		my_range = Sdata.objects.filter(timestamp__contains=stamp)
		# 先删除之前存入的重复数据
		Ddata.objects.filter(timestamp__contains=stamp).delete()

		day_list = my_range.values('method_version').distinct().order_by('method_version')
		method_list = [x['method_version'] for x in day_list]
		n = 0
		for method in method_list:
			n += 1
			# 筛选当前接口当天的所有数据
			rr = my_range.filter(method_version=method).order_by('-timestamp')
			if rr:
				total = rr.count()
				p = Ddata(method_version=method)
				p.url = rr[0].url
				p.log_time = sum([x.log_time for x in rr if x.log_time]) / total
				p.dns_time = sum([x.dns_time for x in rr]) / total
				p.tcp_time = sum([x.tcp_time for x in rr]) / total
				p.up_time = sum([x.up_time for x in rr]) / total
				p.server_time = sum([x.server_time for x in rr]) / total
				p.download_time = sum([x.download_time for x in rr]) / total
				p.download_size = sum([x.download_size for x in rr]) / total
				p.total_time = sum([x.total_time for x in rr]) / total
				p.timestamp = stamp
				p.save()
			else:
				print("%s %s" % (n, method))
	Sdata.objects.filter(timestamp__range=(date_from, date_to)).delete()


if __name__ == '__main__':
	print("周flag:%s" % time_des()[3])
	# 判断指定日，不是指定日，只归纳日数据
	if time_des()[3] == 0:
		print("非指定日")
		doDdata()
	else:
		print("指定日")
		doDdata()
		doRate()
		doWdata()
