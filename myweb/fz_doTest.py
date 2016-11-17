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



def do_url(login_url):
	c = pycurl.Curl() 
	b = io.BytesIO()
	c.setopt(pycurl.URL, login_url) 
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.setopt(pycurl.FOLLOWLOCATION, 1) 
	c.setopt(pycurl.MAXREDIRS, 5)
	c.setopt(pycurl.CONNECTTIMEOUT, 20) 
	c.setopt(pycurl.CUSTOMREQUEST, 'GET') 
	c.setopt(pycurl.HTTPHEADER,['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")
	c.setopt(pycurl.VERBOSE,0)
	try:
		c.perform()
	except:
		print('url error: %s' % login_url)
	result = b.getvalue()
	b.close()
	c.close()
	return result

def do_session(result):
	try:
		htmlString = result.decode('UTF-8')
		print(htmlString)
		html_json = json.loads(htmlString)
		lvsession = html_json['lvsessionId']
		lvsessionid = ("&lvsessionid=%s" % lvsession)
	except:
		print('====>do session error')
		sys.exit()
	return lvsessionid

def do_intcurl(n, req_url, url_method="GET", method_name="未定义名称", url_api="未定义接口"):
	start = time.time()
	c = pycurl.Curl() 
	b = io.BytesIO()
	c.setopt(pycurl.URL, req_url) 
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.setopt(pycurl.FOLLOWLOCATION, 1) 
	c.setopt(pycurl.MAXREDIRS, 5)
	c.setopt(pycurl.CONNECTTIMEOUT, 20)
	c.setopt(pycurl.CUSTOMREQUEST, url_method)
	c.setopt(pycurl.HTTPHEADER,['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")
	c.setopt(pycurl.VERBOSE,0)
	try:
		c.perform() 
	except:
		print('url error: %s' % req_url)

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
	login_url = 'http://192.168.0.227/t_login.htm?firstChannel=TOUCH&secondChannel=LVMM&username=eXV6aGliaW5nMw%3D%3D&password=MTExMTEx'
	method_list = Ints.objects.filter(inuse='1').values('method_version').order_by('method_version').distinct()
	source_list = Ints.objects.all()
	n = 1
	# 如果无验证码则可行
	# url_string = do_url(login_url)
	# lvsessionid = do_session(url_string)
	# 目前每天手动获取一下吧 需要登录session
	# lvsessionid = '&lvsessionid=78d4a411-87f2-41d0-8598-e86a39887f1a'
	for x in method_list:
		i = Ints.objects.all().filter(method_version=x['method_version']).order_by('-timestamp')[0]
		method_name = i.name
		url_api = i.method_version
		# 处理lvsessionid
		# if 'lvsessionid' in i.params:
			# position = i.params.find('&lvsessionid')
			# url_params = i.params.replace(i.params[position:(position+49)], '')
		# else:
			# url_params = i.params
		url_params = i.params
		lvsessionid = ''
		
		if i.isget.lower() == "get":
			url_method = "GET"
		else:
			url_method = "POST"
			
		if 'http://' in url_params or 'https://' in url_params:
			req_url = url_params + lvsessionid
		else:
			if i.ishttp.lower() == "http":
				url_http = "http://"
			else:
				url_http = "https://"
			req_url = url_http + url_path + url_api + url_params + lvsessionid
			
		n += 1
		j.apply_async(do_intcurl, args=(n, req_url, url_method, method_name, url_api))
		
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

