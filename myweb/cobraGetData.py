#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mysql.connector
import configparser
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from cobra.models import *
import datetime
import time

'''
采集cobra数据
1、 read conf , connect mysql
2、 set
3、 sync ints
4、 count rpm, res
5、 other
'''

# 1 read conf
cf = configparser.ConfigParser()
cf.read("/rd/pystudy/conf")
user = cf.get('cobra', 'user')
password = cf.get('cobra', 'password')
host = cf.get('cobra', 'host')
# try connet to mysql 3 times, sleep 10s everytimes
for i in range(3):
	try:
		conn = mysql.connector.connect(user=user, password=password, database='cobra', host=host)
		cursor = conn.cursor()
		break
	except:
		print("connection timeout")
		if i == 2:
			sys.exit(0)
	finally:
		time.sleep(10)

# 2 set
cursor.execute("select id, name, description, type, version from api_method where enabled = %s" % '1')
ints = cursor.fetchall()
# values = cursor.fetchall()

# 3 sync ints
method_IdList = []
for i in ints:
	method_IdList.append(i[0])
	method = i[1]
	version = i[4]
	p = Method.objects.filter(method=method).filter(version=version)
	if p:
		p[0].des = i[2]
		p[0].type = i[3]
		p[0].save()
	else:
		s = Method(method=method)
		s.id = i[0]
		s.des = i[2]
		s.type = i[3]
		s.version = version
		s.save()

# count & save day index
begin = datetime.datetime(2016, 1, 1)
today = datetime.datetime.now()
# 预存日期信息 参考 16-5-1 是121
# index = 0
# day = begin
# for x in range(1000):
# 	p = DayIndex(index=index)
# 	p.day = day
# 	index += 1
# 	day += datetime.timedelta(days=1)
# 	p.save()

for x in DayIndex.objects.filter(status='0').filter(day__lt=today):
	dayNum = x.index
	dayDate = x.day
	print('start count %s %s' % (dayNum, dayDate))

	# 吞吐量表
	cursor.execute("select method_id, sum from api_overview where day_num = %s and sum  > %s" % (dayNum, 0))
	rpms = cursor.fetchall()
	# 响应时间表
	cursor.execute("select method_id, cost_time, create_time  from stat_performance where day_num = %s and cost_time  > %s" % (dayNum, 0))
	ress = cursor.fetchall()
	# 查询渠道数据
	cursor.execute("select method_id, count, channel from api_channel_counter where day_num = %s" % (dayNum))
	channelNum = cursor.fetchall()
	# 查询项目调用情况
	cursor.execute("select project_name, count  from api_project where day_num = %s and count > %s" % (dayNum, 0))
	proNum = cursor.fetchall()

	# clear write
	Datas.objects.filter(create_time=dayDate).delete()
	Channel.objects.filter(day=dayDate).delete()
	Projects.objects.filter(day=dayDate).delete()

	for xx in method_IdList:
		y = Datas(method_id=xx)	# create new datas
		# 汇总该接口所有的res值，求平均
		cost_List = [z[1] for z in ress if z[0] == xx]
		total = sum(cost_List)
		length = len(cost_List)
		try:
			y.res = round(total / length /1000, 3)
		except ZeroDivisionError as e:
			pass

		try:
			rpm_li = [r[1] for r in rpms if r[0] == xx]
			y.rpm = sum(rpm_li)
		except IndexError as e:
			pass

		try:
			y.create_time = dayDate
			y.save()
		except:
			print('数据异常 %s' % dayDate)
			print('id:%s %s %s' % (xx, y.res, y.rpm))

		# save channel datas
		for cc in ['ANDROID', 'IPHONE', 'TOUCH']:
			cs = sum([y[1] for y in channelNum if y[0] == xx and y[2] == cc])
			if cs > 0:
				c = Channel(method_id=xx)	# 记录channel
				c.count = cs
				c.channel = cc
				c.day = dayDate
				c.save()
			else:
				continue

	# save project count
	for xxx in proNum:
		if xxx[1] > 0:
			p = Projects(pName=xxx[0])
			p.count = xxx[1]
			p.day = dayDate
			p.save()
		else:
			continue
	x.status = '1'
	x.save()

cursor.close
conn.close()
