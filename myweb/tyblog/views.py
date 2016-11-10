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

# Create your views here.
# 老听云项目
def tyreport(request):
	return render(request, 'TYreport.html')
	
# 项目首页
def index(request):
	return render(request, 'index.html')
	
# 听云二期首页
def ty_index(request):
	return render(request, 'ty_index.html')
	
def ty_overview(request):
	# 响应占比
	ints_rate_all = Rates.objects.all().order_by('-des')
	show_list = [x for x in ints_rate_all][:10]
	show_list.reverse()
	show_t_label = [x.des for x in show_list] # 时间标签，适用于错误，交互，响应
	# 崩溃率
	crash_version_a = crashes.objects.all().filter(plantform='android').values('name').order_by('-name').distinct()[:5] #android前5个版本
	crash_version_ios = crashes.objects.all().filter(plantform='ios').values('name').order_by('-name').distinct()[:5] #ios前5个版本
	crash_v_a = [x['name'] for x in crash_version_a]
	crash_v_ios = [x['name'] for x in crash_version_ios]
	#取最近12周标签
	crash_time = crashes.objects.all().values('des').order_by('-des').distinct()[:12]
	crash_t_list = [x['des'] for x in crash_time]
	crash_t_list.reverse()
	# 开始过滤
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
		if 'lvmama' in x['name']:
			err_show_a_self[x['name']] = datas
		else:
			err_show_a_other[x['name']] = datas
	for x in err_sub_ios:
		datas=[]
		for y in show_t_label:
			value = errs.objects.all().filter(plantform='ios').filter(name=x['name']).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				datas.append('0')
		if 'lvmama' in x['name']:
			err_show_ios_self[x['name']] = datas
		else:
			err_show_ios_other[x['name']] = datas
	#主机响应
	res_sub_a = reses.objects.all().filter(plantform='android').values('name').distinct().order_by('name')
	res_sub_ios = reses.objects.all().filter(plantform='ios').values('name').distinct().order_by('name')
	res_show_a_self = {}
	res_show_a_other = {}
	res_show_ios_self = {}
	res_show_ios_other = {}
	for x in err_sub_a:
		datas=[]
		for y in show_t_label:
			value = reses.objects.all().filter(plantform='android').filter(name=x['name']).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				datas.append('0')
		if 'lvmama' in x['name']:
			res_show_a_self[x['name']] = datas
		else:
			res_show_a_other[x['name']] = datas
	for x in err_sub_ios:
		datas=[]
		for y in show_t_label:
			value = reses.objects.all().filter(plantform='ios').filter(name=x['name']).filter(des=y)
			if value:
				datas.append(value[0].value)
			else:
				datas.append('0')
		if 'lvmama' in x['name']:
			res_show_ios_self[x['name']] = datas
		else:
			res_show_ios_other[x['name']] = datas
	#应用交互
	return render_to_response('ty_overview.html', {'show_list': show_list,
																	'show_t_label': show_t_label,
																	'crash_v_a': crash_v_a,
																	'crash_v_ios': crash_v_ios,
																	'crash_t_list': crash_t_list,
																	'crash_show_a': crash_show_a,
																	'crash_show_ios': crash_show_ios,
																	'err_show_a_self': err_show_a_self,
																	'err_show_a_other': err_show_a_other,
																	'err_show_ios_self': err_show_ios_self,
																	'err_show_ios_other': err_show_ios_other,
																	'res_show_a_self': res_show_a_self,
																	'res_show_a_other': res_show_a_other,
																	'res_show_ios_self': res_show_ios_self,
																	'res_show_ios_other': res_show_ios_other,
																	})
	
	
def ty_Todo(request):
	return render(request, 'ty_todo.html')
	
	
def ty_fullLists(request):
	return render(request, 'ty_fullLists.html')
	
	
def ty_NewVersion(request):
	return render(request, 'ty_lastInts.html')
	
	
def ty_keyElements(request):
	return render(request, 'ty_keyElements.html')