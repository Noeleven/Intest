#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.db import connection
from fz.models import *
import decimal
from decimal import Decimal
import os, sys, io, json, pycurl, time, datetime, multiprocessing
from io import StringIO
from multiprocessing import Pool, Manager

class DecimalJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalJSONEncoder, self).default(o)

	
def fz_home(request):
	if  'from_date' and 'to_date' in request.GET and request.GET['from_date'] is not '' and request.GET['to_date'] is not '':
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
	start = time.time()
	range_list = Sdata.objects.all().filter(timestamp__range=(date_from, date_to))
	
	#请求成功的比例 分为200的1成功比例，和500的比例
	code_500 = range_list.filter(code="500").count()
	code_404 = range_list.filter(code="404").count()
	code_1 = range_list.filter(log_code="1").count()
	code_not1 = range_list.filter(code='200').exclude(log_code='1').count()
	total_value = range_list.count()
	code_other = total_value - code_500 - code_404 - code_1 - code_not1
	if total_value is not 0:
		succ_dict = {}
		succ_dict['code500'] = round((code_500 *100 / total_value),2)
		succ_dict['code404'] = round((code_404 *100 / total_value),2)
		succ_dict['code1'] = round((code_1 *100 / total_value),2)
		succ_dict['codenot1'] = round((code_not1 *100 / total_value),2)
		succ_dict['other'] = round((code_other *100 / total_value),2)
	else:
		succ_dict = {'code500':0, 'code404':0, 'code1':0, 'codenot1':0, 'other':0}
	
	# 分别统计500错误列表、log错误列表、404错误列表
	err_500 = range_list.filter(code="500").distinct().order_by('method_version')
	err_404 = range_list.filter(code="404").distinct().order_by('method_version')
	err_200 = range_list.exclude(log_code="1").distinct().order_by('method_version')
	end = time.time()
	print ('Time: %s' % (end - start))
	return render_to_response('fz_home.html', {'err_500': err_500,'err_404': err_404,'err_200': err_200, 'succ_dict':json.dumps(succ_dict),})
