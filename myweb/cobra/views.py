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
@cache_page(10)
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
		date_from = datetime.datetime(week_ago.year, week_ago.month, week_ago.day)
		date_to = datetime.datetime(now.year, now.month, now.day)
	range_list = Datas.objects.filter(create_time__range=(date_from, date_to))
	pro_list = Channel.objects.filter(day__range=(date_from, date_to))
	# 判断间隔周期生产占比数据
	# 占比，范围内所有接口这段时间，以间隔算平均时间，之后在占比，总数应该是400+接口
	show_data = []
	channel_data = []
	time_label = [ x['create_time'] for x in range_list.values('create_time').distinct().order_by('create_time')]
	for x in time_label:
		label = x.strftime("%Y-%m-%d")
		all_list = [x.res for x in range_list.filter(create_time=x) if x.res]
		total = len(all_list)
		if total == 0:
			pass
		else:
			rate = {}
			rate[label] = {
				'ms':round(len([x for x in all_list if x < 1]) * 100 / total, 2),
				'os':round(len([x for x in all_list if 0.999 < x < 2]) * 100 / total, 2),
				'ts':round(len([x for x in all_list if 2 <= x < 3]) * 100 / total, 2),
				'tts':round(len([x for x in all_list if 3 <= x < 4]) * 100 / total, 2),
				'fs':round(len([x for x in all_list if 4 <= x < 5]) * 100 / total, 2),
				'ffs':round(len([x for x in all_list if x >= 5]) * 100 / total, 2),
				'num':total,
				'count':round(sum([x.rpm for x in range_list.filter(create_time=x) if x.rpm]), 0),
				}
			show_data.append(rate)
		# 统计channeldata
		cdata = {}
		cdata[label] = {
			'ANDROID':sum([k.count for k in pro_list.filter(channel='ANDROID').filter(day=x)]),
			'TOUCH':sum([k.count for k in pro_list.filter(channel='TOUCH').filter(day=x)]),
			'IOS':sum([k.count for k in pro_list.filter(channel='IPHONE').filter(day=x)]),
		}
		channel_data.append(cdata)

	return render(request, 'cobra_chart.html', locals())

@login_required
# @cache_page(10)
def cobra_datas(request):
	if 'from_date' and 'to_date' in request.GET and request.GET['from_date'] is not '' and request.GET[
		'to_date'] is not '':
		foo = request.GET['from_date']
		too = request.GET['to_date']
		y,m,d = int(foo.split('-')[0]),int(foo.split('-')[1]),int(foo.split('-')[2])
		date_from = datetime.datetime(y, m, d)
		y,m,d = int(too.split('-')[0]),int(too.split('-')[1]),int(too.split('-')[2])
		date_to = datetime.datetime(y, m, d)

		range_list = Datas.objects.filter(create_time__range=(date_from, date_to))

		try:
			inter = request.GET['interface']
			method_list = set([x.id for x in Method.objects.filter(method__contains=inter)])
		except:
			method_list = set([x.method_id for x in range_list])

		show_data = []
		for x in method_list:
			try:
				source = Method.objects.get(id=x)
			except:
				print('methodID %s not exist' % x)
				continue
			method = source.method
			# 去空值和非正数
			rpm_src = [x.rpm for x in range_list.filter(method_id=x) if x.rpm]
			my_dict = {
				'id': source.id,
				'method' : method,
				'version': source.version,
				'des' : source.des,
				'type' : source.type,
				'rpm' : round(sum([x for x in rpm_src if x > 0])),
				}
			if my_dict['rpm'] <= 0:
				continue
			else:
				res_src = [x.res for x in range_list.filter(method_id=x) if x.res]
				res = [x for x in res_src if x > 0]
				try:
					my_dict['res'] = round(sum(res) / len(res), 2)
				except:
					my_dict['res'] = ''
				show_data.append(my_dict)

	return render(request, 'cobra_datas.html', locals())

@login_required
@cache_page(10)
def cobra_trace(request):
	# 确定近一个月的范围
	now = datetime.datetime.now()
	week_ago = now - datetime.timedelta(days=30)
	date_from = datetime.datetime(week_ago.year, week_ago.month, week_ago.day)
	date_to = datetime.datetime(now.year, now.month, now.day)
	range_list = Datas.objects.filter(create_time__range=(date_from, date_to))
	time_label = [ x['create_time'] for x in range_list.values('create_time').distinct().order_by('create_time')]
	# 确定接口范围
	method_list = [ x['method_id'] for x in range_list.values('method_id').distinct().order_by('method_id')]
	show_list = []
	# 过滤接口，检测响应时间有没有>= 1的，如果有就保留，去掉都是毫毛级的稳定接口
	for method in method_list:
		res_list = [x.res for x in range_list.filter(method_id=method) if x.res]
		judge_res = [x for x in res_list if x >= 1]
		if judge_res:
			show_res = [{'create_time' : x.create_time.strftime("%Y-%m-%d"), 'res' : float(x.res), 'rpm' : int(x.rpm)} for x in range_list.filter(method_id=method).order_by('create_time') if x.res]
			try:
				source = Method.objects.get(id=method)
			except:
				continue
			my_dict = {
				'method':source.method,
				'des':source.des,
				'version':source.version,
				'type':source.type,
				'time':show_res,
				}
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

@login_required
def single(request):
	intID = request.GET['id']
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
		date_from = datetime.datetime(week_ago.year, week_ago.month, week_ago.day)
		date_to = datetime.datetime(now.year, now.month, now.day)
	range_list = Datas.objects.filter(method_id=intID).filter(create_time__range=(date_from, date_to))
	time_label = [ x['create_time'] for x in range_list.values('create_time').distinct().order_by('create_time')]
	# 确定接口范围
	show_list = []
	# 过滤接口，检测响应时间有没有>= 1的，如果有就保留，去掉都是毫毛级的稳定接口
	res_list = [x.res for x in range_list if x.res]
	if res_list:
		show_res = [{'create_time' : x.create_time.strftime("%Y-%m-%d"), 'res' : float(x.res), 'rpm' : int(x.rpm)} for x in range_list.order_by('create_time') if x.res]
		source = Method.objects.get(id=intID)
		my_dict = {
			'method':source.method,
			'des':source.des,
			'version':source.version,
			'type':source.type,
			'time':show_res,
			}
		show_list.append(my_dict)
	else:
		pass
	return render(request, 'single.html', locals())

@login_required
def project(request):
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
		date_from = datetime.datetime(week_ago.year, week_ago.month, week_ago.day)
		date_to = datetime.datetime(now.year, now.month, now.day)
	range_list = Projects.objects.filter(day__range=(date_from, date_to))
	time_origle = [x['day'] for x in range_list.values('day').distinct().order_by('day')]
	time_label = [x.strftime("%Y-%m-%d") for x in time_origle]
	pName_list = [x['pName'] for x in range_list.values('pName').distinct().order_by('pName')]
	show_list = {}
	for x in pName_list:
		show_list[x] = [{'day':y,'count':sum([z.count for z in range_list.filter(pName=x).filter(day=y)])} for y in time_origle]

	return render(request, 'project.html', locals())
