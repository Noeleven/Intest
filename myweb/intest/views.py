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
#	获取用户输入的时间范围，确认数据列表 {'from_date': ['2016-08-29 '], 'to_date': ['2016-08-30 ']}
	if  'from_date' and 'to_date' in request.GET and request.GET['from_date'] != '' and request.GET['to_date'] != '':
		y = int(request.GET['from_date'].split('-')[0])
		m =  int(request.GET['from_date'].split('-')[1])
		d =  int(request.GET['from_date'].split('-')[2])
		date_from = datetime.datetime(y,m,d, 0, 0)
		y = int(request.GET['to_date'].split('-')[0])
		m =  int(request.GET['to_date'].split('-')[1])
		d =  int(request.GET['to_date'].split('-')[2])
		date_to = datetime.datetime(y,m,d, 23, 59)
	else:#today
		date_from = datetime.datetime(time.localtime().tm_year,time.localtime().tm_mon,time.localtime().tm_mday, 0, 0)
		date_to = datetime.datetime(time.localtime().tm_year,time.localtime().tm_mon,time.localtime().tm_mday, 23, 59)
		
	range_list = Sdata.objects.all().filter(timestamp__range=(date_from, date_to)) #包含日志错误的原数据
	error_list = Errs.objects.all().filter(timestamp__range=(date_from, date_to)) #错误表中的数据，仅http和log错误
	method_list = set()	#设置接口&版本唯一列表
	[method_list.add(x.method_version) for x in range_list]
	
	#请求成功的比例
	success_value = len(range_list.filter(log_code__exact="1"))
	total_value = len(error_list) + success_value
	err_value = total_value - success_value
	if total_value == 0:
		total_value = 1
	succ_dict = {}
	succ_dict['su_r'] = round((success_value *100 / total_value),2)
	succ_dict['er_r'] = round((err_value *100 / total_value),2)
	
	start = time.time()
	show_dict = {}	#接口性能数据字典
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
			r = [eval('y.'+ na) for y in ready_list] #	转换成字符串
			if None not in r:
				r.sort()
				#pp_value[na + "_avg"] = json.dumps(Decimal(round(sum(r) / len(r), 2)), cls=DecimalJSONEncoder)
				pp_value[na + "_avg"] = Decimal(round(sum(r) / len(r), 2))
				rr = r[:(round(len(r) * 0.95))] #取前95%的数据
				#pp_value[na + "_95line"] = json.dumps(Decimal(round(sum(rr) / len(rr), 2)), cls=DecimalJSONEncoder)
				pp_value[na + "_95line"] = Decimal(round(sum(rr) / len(rr), 2))
				pp_value[na + "_range"] = ("%s ~ %s" % (min(r),max(r)))
				
		if pp_value['total_time_avg'] == 0 or pp_value['total_time_avg'] == None:
			pp_value['total_time_avg'] = 1
		pp_value["dns_time_rate"] = round((pp_value["dns_time_avg"] * 100) / pp_value['total_time_avg'] , 2)
		pp_value['tcp_time_rate'] = round(( pp_value['tcp_time_avg'] * 100) / pp_value['total_time_avg'] , 2)
		pp_value['server_time_rate'] = round(( pp_value['server_time_avg'] * 100) / pp_value['total_time_avg'] , 2)
		pp_value['download_time_rate'] = round(( pp_value['download_time_avg'] * 100) / pp_value['total_time_avg'] , 2)
		show_dict[p] = pp_value
	end = time.time()
	print ("show dict %.2fs" % (end - start))
	ints_dict = sorted(show_dict.items(), key = lambda aab:aab[1]['total_time_avg'], reverse = True)	#变成列表

	show_errs = []	#接口错误数据字典
	#todo 去重
	for e in error_list:
		pp_error = {}	#如果没错误，下面是空的，可能会报错
		pp_error['name'] = e.name
		pp_error['url'] = e.url
		pp_error['method_version'] = e.method_version
		pp_error['httpcode'] = e.httpcode
		pp_error['log_code'] = e.log_code
		pp_error['error'] = e.error
		pp_error['message'] = e.message
		pp_error['timestamp'] = e.timestamp
		show_errs.append(pp_error)
		
	#计算接口占比
	server_li = []
	total_li = []
	server_res={}
	total_res={}
	show_rate = {}
	for k,v in show_dict.items():
		server_li.append(v['server_time_avg'])
		total_li.append(v['total_time_avg'])
	total_lens = len(method_list)
	if total_lens == 0:
		total_lens = 1
	server_res['ms'] = round((len([x for x in server_li if x<1]) *100 / total_lens), 2)
	server_res['os'] = round((len([x for x in server_li if 1<=x<2 ]) *100  / total_lens), 2)
	server_res['ts'] = round((len([x for x in server_li if 2<=x<3])  *100 / total_lens), 2)
	server_res['tts'] = round((len([x for x in server_li if 3<=x<4]) *100  / total_lens), 2)
	server_res['fs'] = round((len([x for x in server_li if 4<=x<5])  *100 / total_lens), 2)
	server_res['ffs'] = round((len([x for x in server_li if x>5]) *100  / total_lens), 2)
	total_res['ms'] = round((len([x for x in total_li if x<1])  *100 / total_lens), 2)
	total_res['os'] = round((len([x for x in total_li if 1<=x<2 ])  *100 / total_lens), 2)
	total_res['ts'] = round((len([x for x in total_li if 2<=x<3]) *100  / total_lens), 2)
	total_res['tts'] = round((len([x for x in total_li if 3<=x<4]) *100  / total_lens), 2)
	total_res['fs'] = round((len([x for x in total_li if 4<=x<5])  *100 / total_lens), 2)
	total_res['ffs'] = round((len([x for x in total_li if x>5])  *100 / total_lens), 2)
	show_rate['按首包时间'] = server_res
	show_rate['按总时间'] = total_res
	return render_to_response('home.html', {'show_errs': show_errs, 'show_rate':show_rate, 'succ_dict':json.dumps(succ_dict),'ints_dict':ints_dict})

#展示错误出现的页面
# def errors(request):
	# pass
	# return render_to_response('errors.html', {'show_dict': show_dict})
