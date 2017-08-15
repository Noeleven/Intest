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
# 老听云项目
# def tyreport(request):
	# return render(request, 'TYreport.html')

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
@cache_page(5)
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


# 版本分
@login_required
@cache_page(300)
def ty_Android_All(request):
	username = request.session.get('user', '')
	check = request.GET
	try:
		params = check['checkall']
		if params == '1':
			datas = count_All('android', 0)
		else:
			datas = count_All('android', 3)
	except:
		datas = count_All('android', 3)

	return render_to_response('ty_Android_All.html', {'datas':datas,})


@login_required
@cache_page(300)
def ty_IOS_All(request):
	check = request.GET
	try:
		params = check['checkall']
		if params == '1':
			datas = count_All('ios', 0)
		else:
			datas = count_All('ios', 3)
	except:
		datas = count_All('ios', 3)

	return render_to_response('ty_IOS_All.html', {'datas':datas,})


# 主机分布
@login_required
@cache_page(300)
def ty_siteApi3g2(request):
	check = request.GET
	try:
		params = check['checkall']
		if params == '1':
			datas = RR.objects.filter(hostId='Api3g2')
		else:
			datas = RR.objects.filter(hostId='Api3g2').filter(response__gt=2).filter(rpm__gt=100)
	except:
		datas = RR.objects.filter(hostId='Api3g2').filter(response__gt=2).filter(rpm__gt=100)
	return render_to_response('ty_siteApi3g2.html', {'datas':datas,})


@login_required
@cache_page(300)
def ty_siteApi3g(request):
	datas = RR.objects.filter(hostId='Api3g')
	return render_to_response('ty_siteApi3g.html', {'datas':datas,})


@login_required
@cache_page(300)
def ty_siteM(request):
	datas = RR.objects.filter(hostId='siteM')
	return render_to_response('ty_siteM.html', {'datas':datas,})


# 汇总
@login_required
@cache_page(300)
def ty_rpmAll(request):
	src = RR.objects.values('method', 'version', 'lvversion').distinct()
	datas = []
	for x in src:
		data_list = RR.objects.filter(method=x['method']).filter(version=x['version']).filter(lvversion=x['lvversion'])
		res = round(sum([x.response for x in data_list]) / len(data_list), 2)
		rpm = round(sum([x.rpm for x in data_list]) * 24 * 60)
		dict = {
					"hostId": data_list[0].hostId,
					"method" : x['method'],
					"version": x['version'],
					"lvversion": x['lvversion'],
					"des": data_list[0].des,
					"res": res,
					"rpm": rpm,
		}
		datas.append(dict)
	return render_to_response('ty_rpmAll.html', {'datas':datas,})


@login_required
@cache_page(300)
def ty_fullLists(request):
	datas = RR.objects.all().filter(time=time_des())
	return render_to_response('ty_fullLists.html', {'datas':datas,})


#关键元素
@login_required
def ty_keyElements(request):
	return render(request, 'ty_keyElements.html')
