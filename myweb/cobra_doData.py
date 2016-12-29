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


# ��������method��cobra_method��
# ��ȡָ�����ڵĽӿڱ�res���ݣ�rpm���ݣ������ҵĿ�

def get_dates():
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	user = cf.get('cobra', 'user')
	password = cf.get('cobra', 'password')
	host = cf.get('cobra', 'host')

	try:
		conn = mysql.connector.connect(user=user, password=password, database='cobra', host=host)
		cursor = conn.cursor()
	except:
		print("connection timeout")
		sys.exit(0)
	# ��ȡ�ӿڱ�����
	cursor.execute("select id, name, description, type, version  from api_method where enabled = %s" % ('1',))
	values = cursor.fetchall()

	# ���������day_num���㷨�Ǿ���20160101�ж����죬��12,22����356
	today = datetime.datetime.now()
	begin = datetime.datetime(2016, 1, 1)
	
	#��ʽʹ��ʱ������2�У���Ϊ���ݿⲻ��ʵʱͬ������˽���������������
	yestoday_num =  (today - begin).days - 1
	print("day_index: %s" % yestoday_num)
	
	# ����2�е��� this_day��Ϊ��ɾ���Ѿ����������
	# yestoday_num = daynum
	
	# daynumת�����ͣ�Ϊ���������е�����
	this_day = datetime.datetime(2016, 1, 1) + datetime.timedelta(days=(yestoday_num))
	Datas.objects.filter(create_time=this_day).delete()
	print(this_day.date())
	
	# ��ѯ������������
	cursor.execute("select method_id, sum, day_num  from api_overview where day_num = %s" % yestoday_num)
	rpms = cursor.fetchall()
	# ��ѯ������Ӧʱ���
	cursor.execute("select method_id, cost_time, create_time, count_index, day_num  from stat_performance where day_num = %s and cost_time  > %s" % (yestoday_num, 0))
	ress = cursor.fetchall()
	
	cursor.close
	conn.close()
	
	return values, rpms, ress


def save_datas(values, rpms, ress):
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
			s.id = i [0]
			s.des = i [2]
			s.type = i[3]
			s.version = i[4]
			s.save()
	# save yestoday res&rpm
	# ress = [method_id, cost_time, create_time, count_index, day_num]
	# rpms = [method_id, sum, day_num]
	ress_IdList = [x[0] for x in ress]
	# �������нӿڣ����˵���û�����ݵĽӿ�
	for x in method_IdList:
		if x in ress_IdList:
			y = Datas(method_id=x)
			# ���ܸýӿ����е�resֵ����ƽ��
			cost_List = [z[1] for z in ress if z[0] == x]
			total = sum(cost_List)
			length = len(cost_List)
			try:
				y.res = round(total / length /1000, 3)
			except:
				print("res %s count failed" % x)
			try:
				y.rpm = [r[1] for r in rpms if r[0] == x][0]
			except:
				print("rpm %s count failed" % x)
			# ֱ��ȡcobra���е�create_time
			b = ress[0][2]
			y.create_time = b
			y.save()
		else:
			continue
		
if __name__ == '__main__':
	start = get_dates()
	values = start[0]
	rpms = start[1]
	ress = start[2]
	save_datas(values, rpms, ress)




