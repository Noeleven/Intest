#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.db import connection
from intest.models import *
import decimal
from decimal import Decimal

import os, sys, io, json, pycurl, time, datetime, multiprocessing
from io import StringIO
from multiprocessing import Pool, Manager
# Create your views here.

# 流程：home选择时间 -- 船体数据过来 -- 当天的返回ddate里的数据 -- 范围的提供范围列表 并计算do_count() -- 返回show_dict数据 ，展示在页面上
# 平日每日数据，自定义时间存入SDATA数据，并自动每日计算存入Ddate数据 --TODO

class DecimalJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalJSONEncoder, self).default(o)
		
def tee(method,show_dict,date_from,date_to):
	ready_list = Sdata.objects.all().filter(timestamp__range=(date_from, date_to)).filter(method_version=method)
	error_list = Errs.objects.all().filter(timestamp__range=(date_from, date_to))
	error_ready_list = error_list.filter(method_version=method)
	base_info = ready_list.order_by('-id')[0] #slow======1
	pp_value = {'name':base_info.name, 'url':base_info.url, 'method_version':base_info.method_version, 'download_size':base_info.download_size}
	http_err_len = error_ready_list.exclude(httpcode='200').count()
	log_err_len = error_ready_list.filter(httpcode='200').count()
	correct_len = ready_list.filter(log_code='1').count()  #slow======4
	total_len = error_ready_list.count() + correct_len #总数是所有错误数量 + 原始表中code为1的总和，因为有些错误会人为从err中删除，统计是以err为准的
	pp_value['error_rate'] = round((( http_err_len * 100) / total_len ),2)
	pp_value['log_error_rate'] = round(((log_err_len * 100) / total_len), 2)
	
	time_name = ["log_time", "dns_time", "tcp_time", "server_time", "download_time", "total_time"]
	for na in time_name: #slow======6
		r = [eval('y.'+ na) for y in ready_list] #转换成字符串
		if None not in r:
			r.sort()
			pp_value["%s_avg" % na] = Decimal(round(sum(r) / len(r), 2))
			rr = r[:(round(len(r) * 0.95))] #取前95%的数据
			pp_value["%s_95line" % na] = Decimal(round(sum(rr) / len(rr), 2))
			pp_value["%s_range" % na] = ("%s ~ %s" % (min(r),max(r)))

	if pp_value['total_time_avg'] == 0 or pp_value['total_time_avg'] == None:
		pp_value = {'dns_time_rate':0, 'tcp_time_rate':0, 'server_time_rate':0, 'download_time_rate':0}
	else:
		pp_value["dns_time_rate"] = round((pp_value["dns_time_avg"] * 100) / pp_value['total_time_avg'] , 2)
		pp_value['tcp_time_rate'] = round(( pp_value['tcp_time_avg'] * 100) / pp_value['total_time_avg'] , 2)
		pp_value['server_time_rate'] = round(( pp_value['server_time_avg'] * 100) / pp_value['total_time_avg'] , 2)
		pp_value['download_time_rate'] = round(( pp_value['download_time_avg'] * 100) / pp_value['total_time_avg'] , 2)
	show_dict[method] = pp_value
	
def home(request):
	if  'from_date' and 'to_date' in request.GET and request.GET['from_date'] is not '' and request.GET['to_date'] is not '':
		y = int(request.GET['from_date'].split('-')[0])
		m =  int(request.GET['from_date'].split('-')[1])
		d =  int(request.GET['from_date'].split('-')[2])
		date_from = datetime.datetime(y,m,d, 0, 0)
		y = int(request.GET['to_date'].split('-')[0])
		m =  int(request.GET['to_date'].split('-')[1])
		d =  int(request.GET['to_date'].split('-')[2])
		date_to = datetime.datetime(y,m,d, 23, 59)
	else:#today 用户并不关心当天的结果，不如取空数据，加快首页展示
		date_from = datetime.datetime(time.localtime().tm_year,time.localtime().tm_mon,time.localtime().tm_mday, 0, 0)
		date_to = datetime.datetime(time.localtime().tm_year,time.localtime().tm_mon,time.localtime().tm_mday, 0, 0)
	start = time.time()
	range_list = Sdata.objects.all().filter(timestamp__range=(date_from, date_to)) #包含日志错误的原数据
	error_list = Errs.objects.all().filter(timestamp__range=(date_from, date_to)) #错误表中的数据，仅http和log错误
	
	#请求成功的比例
	success_value = range_list.filter(log_code="1").count()
	total_value = error_list.count() + success_value
	err_value = total_value - success_value
	if total_value is not 0:
		succ_dict = {}
		succ_dict['su_r'] = round((success_value *100 / total_value),2)
		succ_dict['er_r'] = round((err_value *100 / total_value),2)
	else:
		succ_dict = {'su_r':100, 'er_r':0}
		
	method_list_src = Sdata.objects.all().filter(timestamp__range=(date_from, date_to)).values('method_version').distinct().order_by('method_version')
	method_list = [x['method_version'] for x in method_list_src]
	connection.close()
	
	show_dict = Manager().dict()	#接口性能数据字典
	p = Pool(4)
	for method in method_list:
		p.apply_async(tee, args=(method,show_dict,date_from,date_to))
	p.close()
	p.join()
	
	ints_dict = sorted(show_dict.items(), key = lambda aab:aab[1]['total_time_avg'], reverse = True)	#变成列表
	ints_server = sorted(show_dict.items(), key = lambda aab:aab[1]['server_time_avg'], reverse = True)	#变成列表

	show_errs = []	#接口错误数据字典
	#todo 去重,如果去重则忽略发生的时间，错误数量会减少，这是不合理的
	for e in error_list:
		pp_error = {'name':e.name, 'url':e.url, 'method_version':e.method_version, 'httpcode':e.httpcode, 'log_code':e.log_code, 'error':e.error, 'message':e.message, 'timestamp':e.timestamp}	#如果没错误，下面是空的，可能会报错
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
	if total_lens is not 0:
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
	else:
		show_rate['按首包时间'] = {'ms':0,'os':0,'ts':0,'tts':0,'fs':0,'ffs':0}
		show_rate['按总时间'] = {'ms':0,'os':0,'ts':0,'tts':0,'fs':0,'ffs':0}
	
	end = time.time()
	print ('Time: %s' % (end - start))
	return render_to_response('home.html', {'show_errs': show_errs, 'show_rate':show_rate, 'succ_dict':json.dumps(succ_dict),'ints_dict':ints_dict,'ints_server':ints_server})
