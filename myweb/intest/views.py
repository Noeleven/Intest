#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import time
import datetime
import decimal
import sys
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


def int_report(request):
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

	reportlist = Sdata.objects.filter(recordTime__range=(date_from, date_to))
	succ = reportlist.filter(httpCode='200')
	todo = succ.exclude(response__contains='"code":"1"').exclude(response__contains='html').exclude(response__contains='codeImg')
	err = reportlist.exclude(httpCode='200')
	return render_to_response('int_report.html', locals())

def report_ajax(requests):
	mid = requests.GET['id']
	show = Sdata.objects.get(id=mid)
	# 判断返回结果，json有code，type有html/image，null，单纯报错html
	try:
		# respon = json.loads(show.response.replace('false', '"false"').replace('true', '"true"'), encoding='UTF-8')
		resp = json.loads(show.response)
	except:
		show.type = 'error'
		print("error:", sys.exc_info()[0])
	else:
		try:
			if 'type' in resp.keys():
				if resp['type'] == 'image':
					show.type = 'image'
				else:
					show.type = 'unknown'
			else:
				show.type = 'json'
		except:
			respon = json.dumps({"message": "该接口没返回,结果就是null"})
			show.type = 'json'
		else:
			respon = json.dumps(resp)
			print(show.type)
	return render_to_response('reportAjax.html', locals())
