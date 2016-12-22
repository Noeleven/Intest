#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import time
import datetime
import decimal

from django.shortcuts import render, render_to_response
from django.db import connection
from intest.models import *
from decimal import Decimal
from multiprocessing import Pool, Manager
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from itertools import chain

# Create your views here.
class DecimalJSONEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, decimal.Decimal):
			return str(o)
		return super(DecimalJSONEncoder, self).default(o)


def tee(method, show_dict, date_from, date_to):
	now = datetime.datetime.now().day
	if date_from.day == now and date_to.day == now:
		ready_list = Sdata.objects.filter(method_version=method).filter(timestamp__range=(date_from, date_to)).values('method_version', 'url', 'log_time', 'dns_time', 'tcp_time', 'up_time', 'server_time', 'download_time', 'download_size', 'total_time')
	elif date_to.day is not now:
		ready_list = Ddata.objects.filter(method_version=method).filter(timestamp__range=(date_from, date_to)).values('method_version', 'url', 'log_time', 'dns_time', 'tcp_time', 'up_time', 'server_time', 'download_time', 'download_size', 'total_time')
	else:
		chain_list =  chain(Ddata.objects.filter(method_version=method).filter(timestamp__range=(date_from, date_to)).values('method_version', 'url', 'log_time', 'dns_time', 'tcp_time', 'up_time', 'server_time', 'download_time', 'download_size', 'total_time'), Sdata.objects.filter(method_version=method).filter(timestamp__range=(date_from, date_to)).values('method_version', 'url', 'log_time', 'dns_time', 'tcp_time', 'up_time', 'server_time', 'download_time', 'download_size', 'total_time'))
		ready_list = [x for x in chain_list]

	if ready_list:
		pp_value = {
			'name': Ints.objects.filter(method_version=method).values('name')[0]['name'],
			'url': ready_list[0]['url'],
			'method_version': method,
			'download_size': ready_list[0]['download_size'],
		}
		time_name = ['log_time', 'dns_time', 'tcp_time', 'server_time', 'download_time', 'total_time']
		for name in time_name:  # slow======6
			# r = [eval('y.' + name) for y in ready_list]  # 转换成字符串
			r = [y[name] for y in ready_list]
			if None not in r:
				r.sort()
				rr = r[:(round(len(r) * 0.95))]  # 取前95%的数据
				pp_value["%s_avg" % name] = Decimal(round(sum(r) / len(r), 2))
				pp_value["%s_95line" % name] = Decimal(round(sum(rr) / len(rr), 2))
				pp_value["%s_range" % name] = ("%s ~ %s" % (min(r), max(r)))
		# 进度条显示，默认都分配10，剩余60%在均分，然后累加显示
		base_rate = 10
		total = pp_value['dns_time_avg'] + pp_value['tcp_time_avg'] + pp_value['server_time_avg'] + pp_value['download_time_avg']
		pp_value['dns_time_rate'] = base_rate + (pp_value['dns_time_avg'] / total) * 60
		pp_value['tcp_time_rate'] = base_rate + (pp_value['tcp_time_avg'] / total) * 60
		pp_value['server_time_rate'] = base_rate + (pp_value['server_time_avg'] / total) * 60
		pp_value['download_time_rate'] = base_rate + (pp_value['download_time_avg'] / total) * 60
		
		show_dict[method] = pp_value
	
	# error_ready_list = Errs.objects.filter(method_version=method).filter(timestamp__range=(date_from, date_to))
	# http_err_len = error_ready_list.exclude(httpcode='200').count()
	# correct_len = ready_list.count()  # slow======4
	# total_len = http_err_len + correct_len
	# pp_value['error_rate'] = round(((http_err_len * 100) / total_len), 2)

		

@login_required
def home(request):
	if 'from_date' and 'to_date' in request.GET and request.GET['from_date'] is not '' and request.GET[
		'to_date'] is not '':
		y = int(request.GET['from_date'].split('-')[0])
		m = int(request.GET['from_date'].split('-')[1])
		d = int(request.GET['from_date'].split('-')[2])
		date_from = datetime.datetime(y, m, d, 0, 0)
		y = int(request.GET['to_date'].split('-')[0])
		m = int(request.GET['to_date'].split('-')[1])
		d = int(request.GET['to_date'].split('-')[2])
		date_to = datetime.datetime(y, m, d, 23, 59)
	else:
		date_from = datetime.datetime(time.localtime().tm_year, time.localtime().tm_mon, time.localtime().tm_mday, 0, 0)
		date_to = datetime.datetime(time.localtime().tm_year, time.localtime().tm_mon, time.localtime().tm_mday, 23, 59)
	# 收集methodlist，当天的查Sdata，历史查Ddata，跨当天和历史的都查
	now = datetime.datetime.now().day
	if date_from.day == now and date_to.day == now:
		range_list = Sdata.objects.filter(timestamp__range=(date_from, date_to)).values('method_version')
	elif date_to.day is not now:
		range_list = Ddata.objects.filter(timestamp__range=(date_from, date_to)).values('method_version')
	else:
		range_list = chain(Sdata.objects.filter(timestamp__range=(date_from, date_to)).values('method_version'), Ddata.objects.filter(timestamp__range=(date_from, date_to)).values('method_version'))

	method_list = set([x['method_version'] for x in range_list])
	print(len(method_list))
	# 释放数据库链接，不然会出错
	connection.close()
	show_dict = Manager().dict()  # 接口性能数据字典
	start = time.time()
	p = Pool(4)
	for method in method_list:
		p.apply_async(tee, args=(method, show_dict, date_from, date_to))
	p.close()
	p.join()
	end = time.time()
	print('Time: %s' % (end - start))

	ints_dict = sorted(show_dict.items(), key=lambda aab: aab[1]['total_time_avg'], reverse=True)

	return render_to_response('int_home.html', {'ints_dict': ints_dict})

	
@login_required
@cache_page(3600)
def chart(request):
	server = Rate.objects.filter(type='s')
	total = Rate.objects.filter(type='t')
	limit = Rate.objects.filter(type='l')
	label = [x['des'] for x in server.values('des').distinct().order_by('des')]
	server_list = []
	total_list = []
	# limit_list = []
	for x in label:
		try:
			value = server.filter(des=x)[0]
			server_dict = {
				'des': value.des,
				'zero_level': value.ms,
				'one_level': value.os,
				'two_level': value.ts,
				'three_level': value.tts,
				'four_level': value.fs,
				'five_level': value.ffs,
				'err': value.err_rate,
			}
			server_list.append(server_dict)
		except:
			pass
			
		try:
			value1 = total.filter(des=x)[0]
			total_dict = {
				'des': value1.des,
				'zero_level': value1.ms,
				'one_level': value1.os,
				'two_level': value1.ts,
				'three_level': value1.tts,
				'four_level': value1.fs,
				'five_level': value1.ffs,
			}
			total_list.append(total_dict)
		except:
			pass
		# try:
			# value2 = limit.filter(des=x)[0]
			# limit_dict = {
				# 'des': value2.des,
				# 'zero_level': value2.ms,
				# 'one_level': value2.os,
				# 'two_level': value2.ts,
				# 'three_level': value2.tts,
				# 'four_level': value2.fs,
				# 'five_level': value2.ffs,
			# }
			# limit_list.append(limit_dict)
		# except:
			# pass
		
	return render_to_response('int_chart.html', {'server_list': server_list, 'total_list': total_list})

	
@login_required
def err(request):
	if 'from_date' and 'to_date' in request.GET and request.GET['from_date'] is not '' and request.GET[
		'to_date'] is not '':
		y = int(request.GET['from_date'].split('-')[0])
		m = int(request.GET['from_date'].split('-')[1])
		d = int(request.GET['from_date'].split('-')[2])
		date_from = datetime.datetime(y, m, d, 0, 0)
		y = int(request.GET['to_date'].split('-')[0])
		m = int(request.GET['to_date'].split('-')[1])
		d = int(request.GET['to_date'].split('-')[2])
		date_to = datetime.datetime(y, m, d, 23, 59)
	else:
		date_from = datetime.datetime(time.localtime().tm_year, time.localtime().tm_mon, time.localtime().tm_mday, 0, 0)
		date_to = datetime.datetime(time.localtime().tm_year, time.localtime().tm_mon, time.localtime().tm_mday, 23, 59)

	error_list = Errs.objects.all().filter(timestamp__range=(date_from, date_to))
	show_errs = []  # 接口错误数据字典
	# 去重,如果去重则忽略发生的时间，错误数量会减少，这是不合理的
	for e in error_list:
		pp_error = {'name': e.name, 'url': e.url, 'method_version': e.method_version, 'httpcode': e.httpcode,
					'log_code': e.log_code, 'error': e.error, 'message': e.message,
					'timestamp': e.timestamp}  # 如果没错误，下面是空的，可能会报错
		show_errs.append(pp_error)
	return render_to_response('int_err.html', {'show_errs': show_errs})

	
@login_required	
@cache_page(3600)
def trace(request):
# 筛选下最近2周有不是0的接口
	time_list = Wdata.objects.values('timestamp').distinct().order_by('-timestamp')[:2]
	method_list = []
	for time in time_list:
		time = time['timestamp'].strftime("%Y-%m-%d")
		method_list_src = Wdata.objects.filter(timestamp=time).exclude(ms_tag=0).values('method_version').distinct().order_by('method_version')
		method_list_ready = [x['method_version'] for x in method_list_src]
		[method_list.append(x) for x in method_list_ready]
	
	method_list = set(method_list)
	show_list = []
	for method in method_list:
		my_dates = Wdata.objects.filter(method_version=method).order_by('timestamp')
		my_dict = {
						'name' : my_dates[0].name,
						'method_version' : method,
						'label' : [x.timestamp.strftime('%Y-%m-%d') for x in my_dates],
						'value' : [x.ms_tag for x in my_dates],
						}
		show_list.append(my_dict)
	paginator = Paginator(show_list, 5)
	page = request.GET.get('page')
	try:
		show_list = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		show_list = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		show_list = paginator.page(paginator.num_pages)
		
	return render_to_response('int_trace.html', {'show_list' : show_list})