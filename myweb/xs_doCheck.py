#!/usr/bin/env python
# -*- coding:utf8 -*-
import django
import os, sys, io, json, pycurl, time, datetime, multiprocessing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from intest.models import *
from io import StringIO
from multiprocessing import Process, Pool

'''
消灭线上下的单，添加的游玩人等
'''
#UIautomation for clear_add
lvse='b81abf32-4277-42eb-87e9-0feaeca5eca0'
#APIautomation for clear_order
llse = "f4591872-54c4-427a-a6bb-751cb5330f4b"
addressNo = []
orderNo = []


def do_curl(a):
	c = pycurl.Curl()
	b = io.BytesIO()
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.setopt(pycurl.FOLLOWLOCATION, 1)
	c.setopt(pycurl.MAXREDIRS, 5)
	c.setopt(pycurl.CONNECTTIMEOUT, 20) #链接超时
	c.setopt(pycurl.CUSTOMREQUEST, 'GET') #get or post
	c.setopt(pycurl.HTTPHEADER,['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36 NetType/WIFI Language/zh_CN")
	c.setopt(pycurl.VERBOSE,0)
	c.setopt(pycurl.URL, a)
	c.perform()
	htmlString = b.getvalue().decode('UTF-8')
	html_json = json.loads(htmlString)
	b.close()
	c.close()
	return html_json


def get_order(orderNo):
	getOrderAdd = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.order.getOrderList&version=1.0.0&osVersion=6.0.1&lvversionCode=68&lvversion=7.8.2&page=1&pageSize=10&queryType=WAIT_PAY&lvsessionid=" + llse
	html_json = do_curl(getOrderAdd)
	try:
		for x in html_json['data']['list']:
			orderNo.append(x['orderId'])
	except:
		print("get_order failed")
	print(orderNo)
	return orderNo


def cancel_Order(orderNo):
	cancelOrderAdd = 'http://api3g2.lvmama.com/api/router/rest.do?method=api.com.order.cancellOrder&version=1.0.0&osVersion=6.0.1&lvversionCode=65&lvversion=7.7.3&lvsessionid=' + llse
	c = pycurl.Curl()
	c.setopt(pycurl.FOLLOWLOCATION, 1)
	c.setopt(pycurl.MAXREDIRS, 5)
	c.setopt(pycurl.CONNECTTIMEOUT, 20)
	c.setopt(pycurl.CUSTOMREQUEST, 'GET')
	c.setopt(pycurl.HTTPHEADER,['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")
	c.setopt(pycurl.VERBOSE,0)
	for i in orderNo:
		order_str = ('&orderId=%s' % i)
		c.setopt(pycurl.URL, (cancelOrderAdd + order_str))
		c.perform()
	c.close()


def do_address():
	getAddress = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.getAddress&version=1.0.0&lvsessionid=" + lvse
	delAddress = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.deleteAddress&version=1.0.0&lvsessionid=" + lvse + "&addressNo="
	html_json = do_curl(getAddress)
	try:
		for x in html_json['data']:
			if x['address'] == "宝山区666路":
				addressNo.append(x['addressNo'])
		for y in addressNo:
			delAdd = delAddress + y
			# print(delAdd)
			do_curl(delAdd)
	except:
		print("do_address failed")


def do_contact():
	getContact = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.getContact&version=1.0.0&receiversType=Address&lvsessionid=" + lvse
	delContact = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.removeContact&version=1.0.0&receiversType=Address&lvsessionid=" + lvse + "&receiverId="
	contactNo = []
	html_json = do_curl(getContact)
	try:
		for x in html_json['data']:
			if x['mobileNumber'] == "13621998464":
				contactNo.append(x['receiverId'])
		for y in contactNo:
			delCon = delContact + y
			print(delCon)
			do_curl(delCon)
	except:
		print("do_contact failed")
	return


def sign_in():
	now = datetime.datetime.now()
	day = now.strftime("%a")
	month = now.strftime("%b")
	UA = "Mozilla/5.0 (Linux; Android 6.0.1; MI 5 Build/MXB48T) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/37.0.0.0 Mobile MQQBrowser/6.8 TBS/036887 Safari/537.36 MicroMessenger/6.3.31.940 NetType/WIFI Language/zh_CN"
	target = ("http://wechatlh.chujian.com/dosignin.page?t=%s%%20%s%%2012%%202016%%2006%%3A30%%3A30%%20GMT%%200800%%20%%28CST%%29&qid=51c8442a87fd6df6" % (day, month))

	c = pycurl.Curl()
	c.setopt(pycurl.FOLLOWLOCATION, 1)
	c.setopt(pycurl.MAXREDIRS, 5)
	c.setopt(pycurl.CONNECTTIMEOUT, 20) #链接超时
	c.setopt(pycurl.CUSTOMREQUEST, 'GET') #get or post
	c.setopt(pycurl.HTTPHEADER,['Referer:http://wechatlh.chujian.com/signin.page?qid=51c8442a87fd6df6'])
	c.setopt(pycurl.USERAGENT, UA)
	c.setopt(pycurl.VERBOSE,0)
	c.setopt(pycurl.URL, target)
	c.perform()
	c.close()
	pass


if __name__ == '__main__':
	# 清理添加的地址
	do_address()
	# 清理添加的联系人
	do_contact()
	# 清理订单
	get_order(orderNo)
	cancel_Order(orderNo)
