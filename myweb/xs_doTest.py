#!/usr/bin/env python
# -*- coding:utf8 -*-
import django
import os, io, json, pycurl, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from intest.models import *
from multiprocessing import Pool
from django.db.models import Q

def do_curl(n, req_url, url_method="GET", method_name="未定义名称", url_api="未定义接口"):
	# print ('Run task %s (%s)...' % ((req_url.split('api.com.',2)[1]).split('&',1)[0], os.getpid()))
	start = time.time()
	b = io.BytesIO()
	c = pycurl.Curl()
	c.setopt(pycurl.URL, req_url.encode('UTF-8'))
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.setopt(pycurl.FOLLOWLOCATION, 1)
	# 最大重定向次数,可以预防重定向陷阱
	c.setopt(pycurl.MAXREDIRS, 5)
	# 连接超时设置
	c.setopt(pycurl.CONNECTTIMEOUT, 20)
	c.setopt(pycurl.CUSTOMREQUEST, url_method)  # get or post
	c.setopt(pycurl.HTTPHEADER, ['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	# 模拟浏览器
	c.setopt(pycurl.USERAGENT,
			 "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) "
			 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")
	c.setopt(pycurl.VERBOSE, 0)
	try:
		c.perform()
	except pycurl.error as e:
		print('%s: %s' % (e, req_url))
		end = time.time()
		print('%s XXX URL出错 XXX runs %0.2f S' % (n, (end - start)))
	else:
		if c.getinfo(c.HTTP_CODE) == 200:
			p = Sdata(method_version=url_api)
			# 这里要确认 响应信息有json数据、html数据、图片二进制数据，仅json可以decode
			try:
				# 如果解析正常 就不是图片 可能是html
				html_string = b.getvalue().decode('UTF-8')
				html_json = json.loads(html_string)
				m = 0
			except:
				html_string = b.getvalue()[-199:]
				m = 1
			if m == 0:
				p.log_code = html_json['code']
				if p.log_code is '1':
					p.name = method_name
					p.url = req_url
					p.code = c.getinfo(c.HTTP_CODE)
					p.dns_time = round(c.getinfo(c.NAMELOOKUP_TIME), 2)
					p.tcp_time = round((c.getinfo(c.CONNECT_TIME) - c.getinfo(c.NAMELOOKUP_TIME)), 2)
					p.up_time = round((c.getinfo(c.PRETRANSFER_TIME) - c.getinfo(c.CONNECT_TIME)), 2)
					p.server_time = round((c.getinfo(c.STARTTRANSFER_TIME) - c.getinfo(c.PRETRANSFER_TIME)), 2)
					p.download_time = round((c.getinfo(c.TOTAL_TIME) - c.getinfo(c.STARTTRANSFER_TIME)), 2)
					p.download_size = round(((c.getinfo(c.SIZE_DOWNLOAD) / 8) / 1024), 2)
					p.total_time = round(c.getinfo(c.TOTAL_TIME), 2)
					try:
						debug_msg = html_json['debugMsg']
						if debug_msg == '':				
							p.log_time = 0
						else:
							p.log_time = round((int((debug_msg.split('costTime:', 1)[1]).split('ms', 1)[0]) / 1000), 2)
					except:
						print('no debugmsg')
					p.save()
				else:
					e = Errs(method_version=url_api)
					e.name = method_name
					e.url = req_url
					e.httpcode = c.getinfo(c.HTTP_CODE)
					e.log_code = html_json['code']
					try:
						e.error = html_json['errorMessage'][:198]
						e.message = html_json['message'][:198]
					except KeyError as ee:
						e.error = b.getvalue()[-199:]
					finally:
						e.save()
			else:
				p.name = method_name
				p.url = req_url
				p.code = c.getinfo(c.HTTP_CODE)
				p.dns_time = round(c.getinfo(c.NAMELOOKUP_TIME), 2)
				p.tcp_time = round((c.getinfo(c.CONNECT_TIME) - c.getinfo(c.NAMELOOKUP_TIME)), 2)
				p.up_time = round((c.getinfo(c.PRETRANSFER_TIME) - c.getinfo(c.CONNECT_TIME)), 2)
				p.server_time = round((c.getinfo(c.STARTTRANSFER_TIME) - c.getinfo(c.PRETRANSFER_TIME)), 2)
				p.download_time = round((c.getinfo(c.TOTAL_TIME) - c.getinfo(c.STARTTRANSFER_TIME)), 2)
				p.download_size = round(((c.getinfo(c.SIZE_DOWNLOAD) / 8) / 1024), 2)
				p.total_time = round(c.getinfo(c.TOTAL_TIME), 2)
				p.log_time = 0
				p.save()
		else:
			# 返回不是200的 都是错的
			e = Errs(method_version=url_api)
			e.name = method_name
			e.url = req_url
			e.httpcode = c.getinfo(c.HTTP_CODE)
			e.error = b.getvalue()[-199:]
			e.save()
		end = time.time()
		print('%s %s 执行完毕 runs %0.2f S' % (n, method_name, (end - start)))
	finally:
		b.close()
		c.close()
	return


def do_db():
	url_path = "api3g2.lvmama.com/api/router/rest.do?method="
	method_list = Ints.objects.values('method_version').order_by('method_version').distinct()
	n = 1
	# lvsessionid = '&lvsessionid=7c204ec3-04ef-4ed9-8643-4ed64ac3f5fe'
	for x in method_list:
		# 这里也顺便维护下DB，我们保留最新和最老的数据，其他的都删除
		todel = Ints.objects.all().filter(method_version=x['method_version']).order_by('timestamp')
		if len(todel) > 2:
			first = todel[0].id
			last = todel.reverse()[0].id
			todel.exclude(Q(id=first)|Q(id=last)).delete()
		# 只取最新的一个数据做测试
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
		j.apply_async(do_curl, args=(n, req_url, url_method, method_name, url_api))
	print("=====")
	return


if __name__ == '__main__':
	print("parent process is %s" % os.getpid())
	for t in range(1):
		j = Pool(4)
		do_db()
		j.close()
		j.join()
		print('All subprocesses done.')
