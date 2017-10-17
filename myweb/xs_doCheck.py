#!/usr/bin/env python
# -*- coding:utf8 -*-
import django
import os, sys, io, json, pycurl, time, datetime, multiprocessing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from django.http import HttpResponse
from intest.models import *
import configparser
import requests

'''
消灭线上下的单
'''

cf = configparser.ConfigParser()
cf.read("/rd/pystudy/conf")
# new = cf.get('header', 'lvse')
key = cf.get('header', 'key')
val = cf.get('header', 'sign')
header = {key:val}
lvses = [x for x in cf.get('header', 'lvses').split(',')]

def cancelOrder():
	for x in lvses:
		orderNo = []
		# getOrder = "https://m.lvmama.com/api/router/rest.do?method=api.com.order.getOrderList&page=1&pageSize=30&queryType=UNPAY&version=2.0.0&lvversion=7.10.1&firstChannel=ANDROID&formate=json&secondChannel=LVMM&lvsessionid=" + x
		getOrder = "https://m.lvmama.com/api/router/rest.do?method=api.com.order.getOrderList&page=1&pageSize=30&queryType=WAIT_APPROVE&version=1.0.0&lvsessionid=" + x
		getOrder1 = "https://m.lvmama.com/api/router/rest.do?method=api.com.order.getOrderList&page=1&pageSize=30&queryType=WAIT_PAY&version=1.0.0&lvsessionid=" + x
		canOrder = 'https://m.lvmama.com/api/router/rest.do?method=api.com.order.cancellOrder&version=1.0.0&firstChannel=ANDROID&osVersion=6.0.1&lvversion=7.10.1&lvsessionid=' + x
		r = requests.get(getOrder, headers=header)
		rr = requests.get(getOrder1, headers=header)
		result = r.json()
		for y in result['data']['list']:
			orderNo.append(y['orderId'])
		result1 = rr.json()
		for y in result1['data']['list']:
			orderNo.append(y['orderId'])
			
		for z in orderNo:
			url = canOrder + '&orderId=%s' % z
			r = requests.get(url, headers=header)
			print(z,r.status_code)


cancelOrder()
