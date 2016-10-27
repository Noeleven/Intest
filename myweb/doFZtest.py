#!/usr/bin/env python
# -*- coding:utf8 -*-
import django
import os, sys, io, json, pycurl, time, datetime, multiprocessing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from fz.models import *
from io import StringIO
from multiprocessing import Process, Pool

def do_curl(n, req_url, url_method="GET", method_name="未定义名称", url_api="未定义接口"):
	#print ('Run task %s (%s)...' % ((req_url.split('api.com.',2)[1]).split('&',1)[0], os.getpid()))
	start = time.time()
	c = pycurl.Curl() #创建一个同libcurl中的CURL处理器相对应的Curl对象
	b = io.BytesIO()
	c.setopt(pycurl.URL, req_url) #设置要访问的网址 url = "http://www.cnn.com"
	#写的回调
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.setopt(pycurl.FOLLOWLOCATION, 1) #参数有1、2
	#最大重定向次数,可以预防重定向陷阱
	c.setopt(pycurl.MAXREDIRS, 5)
	#连接超时设置
	c.setopt(pycurl.CONNECTTIMEOUT, 20) #链接超时
	c.setopt(pycurl.CUSTOMREQUEST, url_method) #get or post
	c.setopt(pycurl.HTTPHEADER,['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	#模拟浏览器
	c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")
	c.setopt(pycurl.VERBOSE,0)
	try:
		c.perform() #执行上述访问网址的操作
	except:
		print('url error: %s' % req_url)
	#解析返回的json数据
	p = Sdata(method_version = url_api)
	p.name = method_name
	p.url = req_url
	p.code =  c.getinfo(c.HTTP_CODE)
	try:
		htmlString = b.getvalue().decode('UTF-8')	
		if c.getinfo(c.HTTP_CODE) == 200:
			try:
				html_json = json.loads(htmlString)
				p.log_code =  html_json['code']
				if p.log_code is '1':
					p.debugmsg = html_json['debugMsg'][:90]
				else:
					p.log_code = html_json['code']
					try:
						p.error = html_json['errorMessage']
						p.message = html_json['message']
					except:
						print(html_json)
				p.save()
			except:
				print(htmlString)
		else:
			p.save()
	except:
		htmlString = b.getvalue()
		p.message = htmlString

	b.close()
	c.close()
	end = time.time()
	print ('%s docurl %s 执行完毕 runs %0.2f seconds.' % (n, p.name, (end - start)))
	return
	
def do_db(task):
	print ('第%s次循环开始' % task)
	url_path = "192.168.0.227/api/router/rest.do?method="
	#获取DB所有接口信息
	source_list = Ints.objects.all()
	n = 1
	#循环组合测试各个数据存入数据库
	for i in source_list:
		method_name = i.name
		url_api = i.method_version
		url_params = i.params
		if i.ishttp.lower() == "http":
			url_http = "http://"
		else:
			url_http = "https://"
		if i.isget.lower() == "get":
			url_method = "GET"
		else:
			url_method = "POST"
		req_url = url_http + url_path + url_api + url_params
		n += 1
		j.apply_async(do_curl, args=(n, req_url, url_method, method_name, url_api))
	print ("=====")
	return

if __name__ == '__main__':
	print ("parent process is %s" % os.getpid()) 
	for t in range(1):
		j = Pool(4)
		do_db(t)
		j.close()
		j.join()
		print('All subprocesses done.')
		# time.sleep(10)
