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


# 更新线上method表到cobra_method表
# 获取指定日期的接口表，res数据，rpm数据，存入我的库

def get_dates(yestoday_num):
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	user = cf.get('cobra', 'user')
	password = cf.get('cobra', 'password')
	host = cf.get('cobra', 'host')

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
	# 获取接口表数据
	cursor.execute("select id, name, description, type, version  from api_method where enabled = %s" % '1')
	values = cursor.fetchall()

	if yestoday_num == 0:
		# 计算昨天的day_num，算法是距离20160101有多少天，如12,22号是356
		today = datetime.datetime.now()
		begin = datetime.datetime(2016, 1, 1)
		yestoday_num =  (today - begin).days - 1
	else:
		pass
		# 调试 this_day是为了删除已经存入的数据
		# yestoday_num = 472

	print("day_index: %s" % yestoday_num)

	# daynum转日期型，为了清理已有的数据
	this_day = datetime.datetime(2016, 1, 1) + datetime.timedelta(days=(yestoday_num))
	Datas.objects.filter(create_time=this_day).delete()
	print(this_day.date())

	# 查询昨日吞吐量表
	cursor.execute("select method_id, sum from api_overview where day_num = %s and sum  > %s" % (yestoday_num, 0))
	rpms = cursor.fetchall()
	# 查询昨日响应时间表
	cursor.execute("select method_id, cost_time, create_time  from stat_performance where day_num = %s and cost_time  > %s" % (yestoday_num, 0))
	ress = cursor.fetchall()
	# 查询渠道数据
	cursor.execute("select method_id, count, channel from api_channel_counter where day_num = %s" % (yestoday_num))
	channelNum = cursor.fetchall()
	# 查询项目调用情况
	cursor.execute("select project_name, count  from api_project where day_num = %s and count > %s" % (yestoday_num, 0))
	proNum = cursor.fetchall()

	cursor.close
	conn.close()

	return values, rpms, ress, channelNum, proNum


def save_datas(values, rpms, ress, channelNum, proNum):
	b = ress[0][2]
	Datas.objects.filter(create_time=b).delete()
	Channel.objects.filter(day=b).delete()
	Projects.objects.filter(day=b).delete()
	# save method
	method_IdList = []
	for i in values:
		method = i[1]
		method_IdList.append(i[0])
		version = i[4]
		p = Method.objects.filter(method=method).filter(version=version)
		if p:
			continue
		else:
			s = Method(method=method)
			s.id = i[0]
			s.des = i[2]
			s.type = i[3]
			s.version = i[4]
			s.save()
	# save yestoday res&rpm
	for x in method_IdList:
		y = Datas(method_id=x)	# 记录datas
		# 汇总该接口所有的res值，求平均
		cost_List = [z[1] for z in ress if z[0] == x]
		total = sum(cost_List)
		length = len(cost_List)
		try:
			y.res = round(total / length /1000, 3)
		except ZeroDivisionError as e:
			y.res = 0
			print("res %s count failed err:%s" % (x,e))
		try:
			y.rpm = sum([r[1] for r in rpms if r[0] == x])
		except IndexError as e:
			y.rpm = 0
			print("rpm %s count failed err:%s" % (x, e))
		if y.res == 0 and y.rpm == 0:
			pass
		else:
			y.create_time = b
			y.save()
		for cc in ['ANDROID', 'IPHONE', 'TOUCH']:
			cs = sum([y[1] for y in channelNum if y[0] == x and y[2] == cc])
			if cs > 0:
				print(cs)
				c = Channel(method_id=x)	# 记录channel
				c.count = cs
				c.channel = cc
				c.day = b
				c.save()
			else:
				continue
	print(proNum)
	for x in proNum:
		if x[1] > 0:
			p = Projects(pName=x[0])
			p.count = x[1]
			p.day = b
			p.save()
		else:
			continue


if __name__ == '__main__':
	for x in range(1):
		start = get_dates(x)
		values = start[0]
		rpms = start[1]
		ress = start[2]
		channelNum = start[3]
		proNum = start[4]
		save_datas(values, rpms, ress, channelNum, proNum)
