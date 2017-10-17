import os
import sys
import io
import json
import pycurl
import time
import datetime
import multiprocessing
import decimal

from io import StringIO
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.db import connection
from tyblog.models import *
from decimal import Decimal
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.views.decorators.cache import cache_page

def time_des():
	d =  datetime.datetime.now()
	this_year = d.year
	last_year = (d - datetime.timedelta(days=d.day)).year
	this_month = d.month
	last_month = (d - datetime.timedelta(days=d.day)).month
	if this_month < 10:
		this_month = '0' + str(this_month)
	if last_month < 10:
		last_month = '0' + str(last_month)
	if d.day < 15:
		des = str(last_year) + str(last_month) + "月下"
	else:
		des = str(this_year) + str(this_month) + "月上"
	return des


def count_All(a, b):
	#a 平台 b 版本数量
	if b > 0:
		try:
			version_src = RR.objects.filter(plantform=a).values('lvversion').filter(time=time_des()).distinct().order_by('-lvversion')[:b]
		except:
			version_src = RR.objects.filter(plantform=a).values('lvversion').filter(time=time_des()).distinct().order_by('-lvversion')
	else:
		version_src = RR.objects.filter(plantform=a).values('lvversion').filter(time=time_des()).distinct().order_by('-lvversion')
	version_list = [x['lvversion'] for x in version_src]
	datas = {}
	for x in version_list:
		data = RR.objects.filter(plantform=a).filter(time=time_des()).filter(lvversion=x)
		if data:
			datas[x] = data
		else:
			continue
	return datas

# Create your views here.

# 总导航页
def index(request):
	return render(request, 'index.html')

# 登录页面
def login(request):
	return render(request, 'login.html')


def ty_login(request):
	if request.method == 'POST':
		username = request.POST.get('username', '')
		password = request.POST.get('password', '')
		user = auth.authenticate(username=username, password=password)
		print(user)
		if user is not None:
			auth.login(request, user)
			request.session['user'] = username
			response = HttpResponseRedirect('/tyblog/ty_Overview')
			return response
		else:
			return render(request, 'login.html', {'error' : '用户密码错误'})


def logout(request):
	try:
		del request.session['user']
		print('yes')
	except KeyError as e:
		print(e)
	return render(request, 'login.html')

# 概览
@login_required
# @cache_page(28800)
def ty_Overview(request):
	# 响应占比
	ints_rate_all = Rates.objects.all().order_by('-des')
	show_list = [x for x in ints_rate_all]
	show_list.reverse()
	show_t_label = [x.des for x in show_list] # 时间标签，适用于错误，交互，响应
	# 崩溃率
	version_a = [x['name'] for x in crashes.objects.all().filter(plantform='android').values('name').distinct()]
	version_a.sort(key=lambda x:tuple(int(v) for v in x.split('.'))) #android前5个版本
	crash_version_a = version_a[-5:]
	version_ios = [x['name'] for x in crashes.objects.all().filter(plantform='ios').values('name').distinct()]
	version_ios.sort(key=lambda x:tuple(int(v) for v in x.split('.')))
	crash_version_ios = version_ios[-5:]

	crash_v_a = [x for x in crash_version_a]
	crash_v_ios = [x for x in crash_version_ios]
	#取最近12周标签
	crash_time = crashes.objects.all().values('des').order_by('-des').distinct()[:12]
	crash_t_list = [x['des'] for x in crash_time]
	crash_t_list.reverse()
	# 开始过滤
	other_list = ['alog.umeng.com', 'loc.map.baidu.com','data.de.coremetrics.com','v.admaster.com.cn','beacon.tingyun.com','api.geetest.com',
		'uop.umeng.com','api.map.baidu.com']
	crash_show_a = {}
	crash_show_ios = {}
	for x in crash_v_a:
		datas = []
		for y in crash_t_list:
			value = crashes.objects.all().filter(plantform='android').filter(name=x).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				datas.append('0')
		crash_show_a[x] = datas
	for x in crash_v_ios:
		datas = []
		for y in crash_t_list:
			value = crashes.objects.all().filter(plantform='ios').filter(name=x).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				datas.append('0')
		crash_show_ios[x] = datas

	#错误率
	err_sub_a = errs.objects.all().filter(plantform='android').values('name').distinct().order_by('name')
	err_sub_ios = errs.objects.all().filter(plantform='ios').values('name').distinct().order_by('name')
	err_show_a_self = {}
	err_show_a_other = {}
	err_show_ios_self = {}
	err_show_ios_other = {}
	for x in err_sub_a:
		datas=[]
		for y in show_t_label:
			value = errs.objects.all().filter(plantform='android').filter(name=x['name']).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				datas.append('0')
		self_list = ['pic.lvmama.com', 'api3g2.lvmama.com', 'm.lvmama.com', 'api3g.lvmama.com', 'pics.lvjs.com.cn', 'zt1.lvmama.com']
		if x['name'] in self_list:
			err_show_a_self[x['name']] = datas
		elif x['name'] in other_list:
			err_show_a_other[x['name']] = datas
	for x in err_sub_ios:
		datas=[]
		for y in show_t_label:
			value = errs.objects.all().filter(plantform='ios').filter(name=x['name']).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				datas.append('0')
		self_list = ['pic.lvmama.com', 'api3g2.lvmama.com', 'm.lvmama.com', 'api3g.lvmama.com', 'pics.lvjs.com.cn', 'zt1.lvmama.com']

		if x['name'] in self_list:
			err_show_ios_self[x['name']] = datas
		elif x['name'] in other_list:
			err_show_ios_other[x['name']] = datas
	#主机响应
	res_sub_a = reses.objects.all().filter(plantform='android').values('name').distinct().order_by('name')
	res_sub_ios = reses.objects.all().filter(plantform='ios').values('name').distinct().order_by('name')
	res_show_a_self = {}
	res_show_a_other = {}
	res_show_ios_self = {}
	res_show_ios_other = {}
	for x in res_sub_a:
		datas=[]
		for y in show_t_label:
			value = reses.objects.all().filter(plantform='android').filter(name=x['name']).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				datas.append('0')
		self_list = ['pic.lvmama.com', 'api3g2.lvmama.com', 'm.lvmama.com', 'rhino.lvmama.com', 'api3g.lvmama.com', 'pics.lvjs.com.cn',
						# 'iguide.lvmama.com', 'login.lvmama.com', 'www.lvmama.com', 'zt1.lvmama.com'
						]
		if x['name'] in self_list:
			res_show_a_self[x['name']] = datas
		elif x['name'] in other_list:
			res_show_a_other[x['name']] = datas
	for x in res_sub_ios:
		datas=[]
		for y in show_t_label:
			value = reses.objects.all().filter(plantform='ios').filter(name=x['name']).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				datas.append('0')
		self_list = ['pic.lvmama.com', 'api3g2.lvmama.com', 'm.lvmama.com', 'rhino.lvmama.com', 'api3g.lvmama.com', 'pics.lvjs.com.cn',
						# 'iguide.lvmama.com', 'login.lvmama.com', 'www.lvmama.com', 'zt1.lvmama.com'
						]
		if x['name'] in self_list:
			res_show_ios_self[x['name']] = datas
		elif x['name'] in other_list:
			res_show_ios_other[x['name']] = datas
	#应用交互
	view_sub_a = views.objects.all().filter(plantform='android').values('name').distinct().order_by('name')
	view_sub_ios = views.objects.all().filter(plantform='ios').values('name').distinct().order_by('name')
	view_show_a = {}
	view_show_ios = {}
	for x in view_sub_a:
		datas=[]
		for y in show_t_label:
			value = views.objects.all().filter(plantform='android').filter(name=x['name']).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				pass
		view_show_a[x['name']] = datas
	for x in view_sub_ios:
		datas=[]
		for y in show_t_label:
			value = views.objects.all().filter(plantform='ios').filter(name=x['name']).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				pass
		view_show_ios[x['name']] = datas
	return render_to_response('ty_overview.html', locals())

@login_required
# @cache_page(28800)
def newCrash(request):
	dateto = datetime.datetime.now()
	datefrom = dateto - datetime.timedelta(days=30)
	# 数据源
	source = newData.objects.filter(date__range=(datefrom, dateto)).filter(type='crash')
	# 时间表
	dateList = [x['date'].strftime("%Y-%m-%d") for x in source.values('date').distinct().order_by('date')]

	# AD崩溃率
	ADcrash = source.filter(platform='AD')
	iOScrash = source.filter(platform='iOS')
	ADver = [x['name'].split('(')[0] for x in ADcrash.values('name').distinct()]
	ADver.sort(key=lambda x:tuple(int(v) for v in x.split('.')))
	ADver = ADver[-3:]

	result = []
	for x in ADver:
		value,iOSvalue = [],[]
		for y in dateList:
			have = ADcrash.filter(date=y).filter(name__contains=x)
			iOShave = iOScrash.filter(date=y).filter(name__contains=x)
			if have:
				value.append(str(have[0].value))
			else:
				value.append('')
			if iOShave:
				iOSvalue.append(str(iOShave[0].value))
			else:
				iOSvalue.append('')
		tmp = {
			'name':x,
			'value':value,
			'iOSvalue':iOSvalue
		}
		result.append(tmp)

	return render_to_response('newCrash.html', locals())

@login_required
# @cache_page(28800)
def newErr(request):
	dateto = datetime.datetime.now()
	datefrom = dateto - datetime.timedelta(days=30)
	# 数据源
	source = newData.objects.filter(date__range=(datefrom, dateto)).filter(type='error')
	# 时间表
	dateList = [x['date'].strftime("%Y-%m-%d") for x in source.values('date').distinct().order_by('date')]
	# nameList,太多了 手工指定吧
	nameList = source.exclude(name__contains='_').values('name','platform').distinct()

	# nameList = [
	# 	{'name': 'api3g.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'api3g.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'm.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'm.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'api3g2.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'api3g2.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'static.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'static.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'pic.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'pic.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'api3g2.lvmama.com:443', 'platform': 'AD'},
	# 	{'name': 'api3g2.lvmama.com:443', 'platform': 'iOS'},
	# 	{'name': 'm.lvmama.com:443', 'platform': 'AD'},
	# 	{'name': 'm.lvmama.com:443', 'platform': 'iOS'},
	# 	{'name': 'loc.map.baidu.com', 'platform': 'AD'},
	# 	{'name': 'api.map.baidu.com', 'platform': 'AD'},
	# 	{'name': 'data.de.coremetrics.com', 'platform': 'AD'},
	# 	{'name': 'data.de.coremetrics.com', 'platform': 'iOS'},
	# 	{'name': 'alog.umeng.com', 'platform': 'AD'},
	# 	{'name': 'alogs.umeng.com', 'platform': 'iOS'},
	# 	{'name': 'v.admaster.com.cn', 'platform': 'AD'},
	# 	{'name': 'v.admaster.com.cn', 'platform': 'iOS'},
	# 	{'name': 'uop.umeng.com', 'platform': 'AD'},
	# ]

	# result
	result = []
	for x in nameList:
		if x['platform'] == 'AD':
			if 'lvmama' in x['name']:
				myType = 'ADself'
			else:
				myType = 'ADthird'
		else:
			if 'lvmama' in x['name']:
				myType = 'IOSself'
			else:
				myType = 'IOSthird'

		# 填入每天的数据
		valueList = []
		for y in dateList:
			iHave = source.filter(name=x['name']).filter(platform=x['platform']).filter(date=y)
			if iHave:
				myValue = str(iHave[0].value)
			else:
				myValue = ''
			valueList.append(myValue)

		tmp = {
			'name':x['name'],
			'type':myType,
			'value':valueList,
		}
		result.append(tmp)

	return render_to_response('newErr.html', locals())

@login_required
# @cache_page(28800)
def newRes(request):
	dateto = datetime.datetime.now()
	datefrom = dateto - datetime.timedelta(days=30)
	# 数据源
	source = newData.objects.filter(date__range=(datefrom, dateto)).filter(type='response')
	# 时间表
	dateList = [x['date'].strftime("%Y-%m-%d") for x in source.values('date').distinct().order_by('date')]
	# nameList
	nameList = source.values('name','platform').distinct()
	# nameList = [
	# 	{'name': 'api3g.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'api3g.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'm.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'm.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'api3g2.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'api3g2.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'static.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'static.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'pic.lvmama.com', 'platform': 'AD'},
	# 	{'name': 'pic.lvmama.com', 'platform': 'iOS'},
	# 	{'name': 'api3g2.lvmama.com:443', 'platform': 'AD'},
	# 	{'name': 'api3g2.lvmama.com:443', 'platform': 'iOS'},
	# 	{'name': 'm.lvmama.com:443', 'platform': 'AD'},
	# 	{'name': 'm.lvmama.com:443', 'platform': 'iOS'},
	# 	{'name': 'loc.map.baidu.com', 'platform': 'AD'},
	# 	{'name': 'api.map.baidu.com', 'platform': 'AD'},
	# 	{'name': 'data.de.coremetrics.com', 'platform': 'AD'},
	# 	{'name': 'data.de.coremetrics.com', 'platform': 'iOS'},
	# 	{'name': 'alog.umeng.com', 'platform': 'AD'},
	# 	{'name': 'alogs.umeng.com', 'platform': 'iOS'},
	# 	{'name': 'v.admaster.com.cn', 'platform': 'AD'},
	# 	{'name': 'v.admaster.com.cn', 'platform': 'iOS'},
	# 	{'name': 'uop.umeng.com', 'platform': 'AD'},
	# ]
	# result
	result = []
	for x in nameList:
		if x['platform'] == 'AD':
			if 'lvmama' in x['name']:
				myType = 'ADself'
			else:
				myType = 'ADthird'
		else:
			if 'lvmama' in x['name']:
				myType = 'IOSself'
			else:
				myType = 'IOSthird'


		# 填入每天的数据
		valueList = []
		for y in dateList:
			iHave = source.filter(name=x['name']).filter(platform=x['platform']).filter(date=y)
			if iHave:
				myValue = str(iHave[0].value)
			else:
				myValue = ''
			valueList.append(myValue)

		tmp = {
			'name':x['name'],
			'type':myType,
			'value':valueList,
		}
		result.append(tmp)

	return render_to_response('newRes.html', locals())

@login_required
# @cache_page(28800)
def newView(request):
	dateto = datetime.datetime.now()
	datefrom = dateto - datetime.timedelta(days=30)
	# 数据源
	source = newData.objects.filter(date__range=(datefrom, dateto)).filter(type='view')
	# 时间表
	dateList = [x['date'].strftime("%Y-%m-%d") for x in source.values('date').distinct().order_by('date')]
	# nameList
	nameList = source.values('name','platform').distinct()
	legend = [x['name'] for x in nameList]
	# result
	result = []
	for x in nameList:
		if x['platform'] == 'AD':
			myType = 'AD'
		else:
			myType = 'IOS'
		# 填入每天的数据
		valueList = []
		for y in dateList:
			iHave = source.filter(name=x['name']).filter(platform=x['platform']).filter(date=y)
			if iHave:
				myValue = str(iHave[0].value)
			else:
				myValue = ''
			valueList.append(myValue)
		# 过滤平均值小于0.5的数据，否则太多了
		valid = [float(z) for z in valueList if z]
		try:
			avg = sum(valid) / len(valid)
		except:
			pass
		else:
			if avg > 0.5:
				tmp = {
					'name':x['name'],
					'type':myType,
					'value':valueList,
				}
				result.append(tmp)

	return render_to_response('newView.html', locals())
