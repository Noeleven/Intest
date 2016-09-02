#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from intest.models import *
import decimal
from decimal import Decimal

import os, sys, io, json, pycurl, time, datetime
from io import StringIO

# Create your views here.

# 流程：home选择时间 -- 船体数据过来 -- 当天的返回ddate里的数据 -- 范围的提供范围列表 并计算do_count() -- 返回show_dict数据 ，展示在页面上
# 平日每日数据，自定义时间存入SDATA数据，并自动每日计算存入Ddate数据 --TODO

class DecimalJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalJSONEncoder, self).default(o)
		
def home(request):
#	获取用户输入的时间范围，确认数据列表
	#{'from_date': ['2016-08-29 '], 'to_date': ['2016-08-30 ']}
	if  'from_date' and 'to_date' in request.GET and request.GET['from_date'] != '' and request.GET['to_date'] != '':
		y = int(request.GET['from_date'].split('-')[0])
		m =  int(request.GET['from_date'].split('-')[1])
		d =  int(request.GET['from_date'].split('-')[2])
		date_from = datetime.datetime(y,m,d, 0, 0)
		y = int(request.GET['to_date'].split('-')[0])
		m =  int(request.GET['to_date'].split('-')[1])
		d =  int(request.GET['to_date'].split('-')[2])
		date_to = datetime.datetime(y,m,d, 23, 59)
	else:
		date_from = datetime.datetime(time.localtime().tm_year,time.localtime().tm_mon,time.localtime().tm_mday, 0, 0)
		date_to = datetime.datetime(time.localtime().tm_year,time.localtime().tm_mon,time.localtime().tm_mday, 23, 59)
	range_list = Sdata.objects.all().filter(timestamp__range=(date_from, date_to))
	error_list = Errs.objects.all().filter(timestamp__range=(date_from, date_to))
	# do_count(range_list)	#返回范围数据，需要计算 得出show_dict
	method_list = set()
	# x下面是获取不重复的method_version列表
	[method_list.add(x.method_version) for x in range_list]
	# 下面是根据method_version列表来查询所有的记录，每项存在list中并计算平均值和范围
	show_dict = {}
	all_list = len(method_list)
	for p in method_list:
		# 准备好时间范围内指定方法的所有数据列表
		ready_list = range_list.filter(method_version=p)
		error_ready_list = error_list.filter(method_version=p)
		# pp 是某一条数据
		pp_value = {}
		pp_value['name'] = ready_list[0].name
		pp_value['url'] = ready_list[0].url
		pp_value['method_version'] = ready_list[0].method_version
		pp_value['download_size'] = ready_list[0].download_size
		pp_value['error_rate'] = round((len([x.httpcode for x in error_ready_list if x.httpcode != '200']) * 100) / (len([x.code for x in ready_list]) + len([x.httpcode for x in error_ready_list if x.log_code == ''])),2)
		pp_value['log_error_rate'] = round((len([x.log_code for x in ready_list if x.log_code != '1']) * 100) / len([x.log_code for x in ready_list]), 2)
		time_name = ["log_time", "dns_time", "tcp_time", "server_time", "download_time", "total_time"]
		for na in time_name:
		#	转换成字符串
			r = [eval('y.'+ na) for y in ready_list]
			r.sort()
			#这里平均值可以考虑算95%line
			pp_value[na + "_avg"] = json.dumps(Decimal(round(sum(r) / len(r), 2)), cls=DecimalJSONEncoder)
			rr = r[:(round(len(r) * 0.95))] #取前95%的数据
			pp_value[na + "_95line"] = json.dumps(Decimal(round(sum(rr) / len(rr), 2)), cls=DecimalJSONEncoder)
			pp_value[na + "_range"] = ("%s ~ %s" % (min(r),max(r)))
		show_dict[p] = pp_value
	return render_to_response('home.html', {'show_dict': show_dict})

#展示错误出现的页面
def errors(request):
	pass
	return render_to_response('errors.html', {'show_dict': show_dict})