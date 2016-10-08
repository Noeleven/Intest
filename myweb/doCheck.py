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

getAddress = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.getAddress&version=1.0.0&lvsessionid=92ebe3a7-f763-43fb-96d7-bcec0872dd9d"
delAddress = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.deleteAddress&version=1.0.0&lvsessionid=92ebe3a7-f763-43fb-96d7-bcec0872dd9d&addressNo="
addressNo = []


def do_address():
	c = pycurl.Curl() #创建一个同libcurl中的CURL处理器相对应的Curl对象
	#写的回调
	b = io.BytesIO()
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.setopt(pycurl.FOLLOWLOCATION, 1) #参数有1、2
	#最大重定向次数,可以预防重定向陷阱
	c.setopt(pycurl.MAXREDIRS, 5)
	#连接超时设置
	c.setopt(pycurl.CONNECTTIMEOUT, 20) #链接超时
	c.setopt(pycurl.CUSTOMREQUEST, 'GET') #get or post
	c.setopt(pycurl.HTTPHEADER,['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	#模拟浏览器
	c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")
	c.setopt(pycurl.VERBOSE,0)
	#先处理常用地址
	c.setopt(pycurl.URL, getAddress)
	c.perform() #执行上述访问网址的操作
	#解析返回的json数据
	htmlString = b.getvalue().decode('UTF-8')
	html_json = json.loads(htmlString)
	for x in html_json['data']:
		if x['address'] == "宝山区666路":
			addressNo.append(x['addressNo'])
	for y in addressNo:
		delAdd = delAddress + y
		c.setopt(pycurl.URL, delAdd)
		c.perform()
	b.close()
	c.close()
	return
	
def do_contact():
	getContact = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.getContact&version=1.0.0&receiversType=Address&lvsessionid=92ebe3a7-f763-43fb-96d7-bcec0872dd9d"
	delContact = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.removeContact&version=1.0.0&receiversType=Address&lvsessionid=92ebe3a7-f763-43fb-96d7-bcec0872dd9d&receiverId="
	contactNo = []
	c = pycurl.Curl() #创建一个同libcurl中的CURL处理器相对应的Curl对象
	#写的回调
	b = io.BytesIO()
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.setopt(pycurl.FOLLOWLOCATION, 1) #参数有1、2
	#最大重定向次数,可以预防重定向陷阱
	c.setopt(pycurl.MAXREDIRS, 5)
	#连接超时设置
	c.setopt(pycurl.CONNECTTIMEOUT, 20) #链接超时
	c.setopt(pycurl.CUSTOMREQUEST, 'GET') #get or post
	c.setopt(pycurl.HTTPHEADER,['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	#模拟浏览器
	c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")
	c.setopt(pycurl.VERBOSE,0)
	#处理联系人
	c.setopt(pycurl.URL, getContact)
	c.perform()
	#解析返回的json数据
	htmlString = b.getvalue().decode('UTF-8')
	html_json = json.loads(htmlString)
	for x in html_json['data']:
		if x['mobileNumber'] == "13621998464":
			contactNo.append(x['receiverId'])
	for y in contactNo:
		delCon = delContact + y
		c.setopt(pycurl.URL, delCon)
		c.perform()

	b.close()
	c.close()
	return

if __name__ == '__main__':
	do_address()
	do_contact()
