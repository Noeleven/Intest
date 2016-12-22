#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import datetime
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from cobra.models import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# Create your views here.
@login_required
def cobra_chart(request):
	#判断时间周期选择数据范围
	if 'from_date' and 'to_date' in request.GET and request.GET['from_date'] is not '' and request.GET[
		'to_date'] is not '':
		y = int(request.GET['from_date'].split('-')[0])
		m = int(request.GET['from_date'].split('-')[1])
		d = int(request.GET['from_date'].split('-')[2])
		date_from = datetime.datetime(y, m, d)
		y = int(request.GET['to_date'].split('-')[0])
		m = int(request.GET['to_date'].split('-')[1])
		d = int(request.GET['to_date'].split('-')[2])
		date_to = datetime.datetime(y, m, d)
	else:
		# 默认展示一个月的占比趋势
		now = datetime.datetime.now()
		week_ago = now - datetime.timedelta(days=30)
		date_from = datetime.datetime(now.year, week_ago.month, week_ago.day)
		date_to = datetime.datetime(now.year, now.month, now.day)
	range_list = Datas.objects.filter(create_time__range=(date_from, date_to))
	# 判断间隔周期生产占比数据
	# 占比，范围内所有接口这段时间，以间隔算平均时间，之后在占比，总数应该是400+接口
	show_data = []
	time_label = [ x['create_time'] for x in range_list.values('create_time').distinct().order_by('create_time')]
	for x in time_label:
		label = x.strftime("%Y-%m-%d")
		all_list = [x['res'] for x in range_list.filter(create_time=x).values('res') if x['res'] > 0]
		total = len(all_list)
		rate = {}
		rate[label] = {
							'ms':round(len([x for x in all_list if x < 1]) * 100 / total, 2),
							'os':round(len([x for x in all_list if 0.999 < x < 2]) * 100 / total, 2),
							'ts':round(len([x for x in all_list if 2 <= x < 3]) * 100 / total, 2),
							'tts':round(len([x for x in all_list if 3 <= x < 4]) * 100 / total, 2),
							'fs':round(len([x for x in all_list if 4 <= x < 5]) * 100 / total, 2),
							'ffs':round(len([x for x in all_list if x >= 5]) * 100 / total, 2),
							'num':total,
							}
		show_data.append(rate)
	return render(request, 'cobra_chart.html', {'show_data':show_data})

@login_required
@cache_page(300)
def cobra_datas(request):
	
	if 'from_date' and 'to_date' in request.GET and request.GET['from_date'] is not '' and request.GET[
		'to_date'] is not '':
		y = int(request.GET['from_date'].split('-')[0])
		m = int(request.GET['from_date'].split('-')[1])
		d = int(request.GET['from_date'].split('-')[2])
		date_from = datetime.datetime(y, m, d)
		y = int(request.GET['to_date'].split('-')[0])
		m = int(request.GET['to_date'].split('-')[1])
		d = int(request.GET['to_date'].split('-')[2])
		date_to = datetime.datetime(y, m, d)
	else:
		now = datetime.datetime.now()
		week_ago = now - datetime.timedelta(days=30)
		date_from = datetime.datetime(now.year, week_ago.month, week_ago.day)
		date_to = datetime.datetime(now.year, now.month, now.day)
	range_list = Datas.objects.filter(create_time__range=(date_from, date_to))
	# 统计时间范围内接口的平均耗时，访问量 访问量趋势图
	method_list = [x['method_id'] for x in range_list.values('method_id').distinct().order_by('method_id')]
	show_data = []
	for x in method_list:
		try:
			source = Method.objects.filter(id=x).values('method', 'des', 'type')[0]
		except:
			continue
		method = source['method']
		# 去空值和非正数
		rpm_src = [x['rpm'] for x in range_list.filter(method_id=x).values('rpm') if x['rpm']]
		my_dict = {
						'method' : method,
						'des' : source['des'],
						'type' : source['type'],
						'rpm' : str(round(sum([x for x in rpm_src if x > 0]))),
						}
		res_src = [x['res'] for x in range_list.filter(method_id=x).values('res') if x['res']]
		res = [x for x in res_src if x > 0]
		try:
			my_dict['res'] = str(round(sum(res) / len(res), 2))
		except:
			my_dict['res'] = ''
		show_data.append(my_dict)
	return render(request, 'cobra_datas.html', {'show_data':show_data})

@login_required
# @cache_page(300)
def cobra_trace(request):
	# 确定近一个月的范围
	now = datetime.datetime.now()
	week_ago = now - datetime.timedelta(days=30)
	date_from = datetime.datetime(now.year, week_ago.month, week_ago.day)
	date_to = datetime.datetime(now.year, now.month, now.day)
	range_list = Datas.objects.filter(create_time__range=(date_from, date_to))
	time_label = [ x['create_time'] for x in range_list.values('create_time').distinct().order_by('create_time')]
	# 确定接口范围
	method_list = [ x['method_id'] for x in range_list.values('method_id').distinct().order_by('method_id')]
	show_list = []
	# 过滤接口，检测响应时间有没有>= 1的，如果有就保留，去掉都是毫毛级的稳定接口
	for method in method_list:
		res_list = [x['res'] for x in range_list.filter(method_id=method).values('res') if x['res']]
		judge_res = [x for x in res_list if x >= 1]
		if judge_res:
			res_list = [{'create_time':x['create_time'].strftime("%Y-%m-%d"),'res':x['res']} for x in range_list.filter(method_id=method).values('res', 'create_time').order_by('create_time') if x['res']]
			print(res_list)
			show_ready_res = [x for x in res_list if x['res'] > 0]
			# 转换下数字格式
			show_res = [{'create_time':x['create_time'],'res':float(x['res'])} for x in show_ready_res]
			try:
				source = Method.objects.filter(id=method).values('method', 'des', 'type')[0]
			except:
				continue
			my_dict = {
							'method':source['method'],
							'des':source['des'],
							'type':source['type'],
							'time':show_res,
							}
			print("%s--%s" % (method, my_dict))
			show_list.append(my_dict)
		else:
			continue
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
		
	return render_to_response('cobra_trace.html', {'show_list' : show_list})
