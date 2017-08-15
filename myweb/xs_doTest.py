#!/usr/bin/env python
# -*- coding:utf8 -*-
import django
import io,os,time,datetime,sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from intest.models import *
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import pycurl
import random
import configparser
# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.
try:
	import signal
	from signal import SIGPIPE,SIG_ING
	signal.signal(signal.SIGPIPE,signal.SIG_IGN)
except ImportError:
	pass

# read conf
cf = configparser.ConfigParser()
cf.read("/rd/pystudy/conf")
new = cf.get('header', 'lvse')
header = cf.get('header', 'key') + ':' + cf.get('header', 'sign')
# get urls
def getUrls():
	sourceLists = Ints.objects.filter(inuse=1)
	# sourceLists = Ints.objects.filter(method_version='api.com.route.order.showContract&version=2.0.0')
	urls = []
	# new = "7bef8d03-99d4-4b88-871a-5025340ed3f5"
	for x in sourceLists:
		tmp = {
			'method_version':x.method_version,
			'protocol':x.ishttp.upper(),
			'method':x.isget.upper(),
			'des':x.name,
			'type':x.type
		}

		# config url
		if 'http' in x.params:
			tmp['url'] = x.params
		else:
			# 其实拆分了工程以后，并不是都是router，还有nticket nsso other trip pay ==
			print('...[!]url need protect id:%s method:%s' % (x.id, x.method_version))
			tmp['url'] = 'https://m.lvmama.com/api/router/rest.do?method=' + x.method_version + x.params

		# 处理lvsessionid
		if 'lvsessionid' in x.params:
			strNum = x.params.find('lvsessionid') + 12
			tmp['url'] = tmp['url'].replace(x.params[strNum:strNum + 36], new)
		else:
			tmp['url'] += '&lvsessionid=%s' % new

		urls.append(tmp)
	# print(urls)
	return urls

# define work
def doWork(myUrl):
	b = io.BytesIO()
	c = pycurl.Curl()
	c.setopt(pycurl.URL, myUrl['url'].encode('UTF-8'))
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.setopt(pycurl.FOLLOWLOCATION, 1)
	c.setopt(pycurl.MAXREDIRS, 5)
	# ssl，目前是不校验,这一步很耗时？
	# 	c.setopt(pycurl.SSL_VERIFYPEER, 0)
	# 	c.setopt(pycurl.SSL_VERIFYHOST, 0)
	c.setopt(pycurl.NOSIGNAL,1)	# 解决多线程崩溃问题
	# 连接超时设置
	c.setopt(pycurl.CONNECTTIMEOUT, 20)
	c.setopt(pycurl.CUSTOMREQUEST, myUrl['method'])
	c.setopt(pycurl.HTTPHEADER, [header])
	# 模拟浏览器
	c.setopt(pycurl.USERAGENT,
			 "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) "
			 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")
	c.setopt(pycurl.VERBOSE, 0)
	result = myUrl
	# 请求尝试3次，失败做个记录
	n = 1
	while n < 4:
		try:
			result['requesTime'] = datetime.datetime.now()
			c.perform()
			result['status'] = '1'
			result['HTTP_CODE'] = c.getinfo(c.HTTP_CODE)
			result['NAMELOOKUP_TIME'] = c.getinfo(c.NAMELOOKUP_TIME)
			result['CONNECT_TIME'] = c.getinfo(c.CONNECT_TIME)
			result['APPCONNECT_TIME'] = c.getinfo(c.APPCONNECT_TIME)
			result['REDIRECT_TIME'] = c.getinfo(c.REDIRECT_TIME)
			result['PRETRANSFER_TIME'] = c.getinfo(c.PRETRANSFER_TIME)
			result['STARTTRANSFER_TIME'] = c.getinfo(c.STARTTRANSFER_TIME)
			result['SIZE_DOWNLOAD'] = round(((c.getinfo(c.SIZE_DOWNLOAD) / 8) / 1024), 2)	#KB
			result['TOTAL_TIME'] = c.getinfo(c.TOTAL_TIME)
			result['SPEED_DOWNLOAD'] = round(((c.getinfo(c.SPEED_DOWNLOAD) / 8) / 1024), 2)
			# print(c.getinfo(c.CONTENT_TYPE))

			if 'json' in c.getinfo(c.CONTENT_TYPE):
				result['HTML'] = b.getvalue().decode('UTF-8')
			elif 'image' in c.getinfo(c.CONTENT_TYPE):
				urlPath = '/static/codeImg/'
				fileName = str(int(time.time())) + str(random.randint(00000, 99999)) + '.jpg'
				rootPath = '/rd/pystudy/Intest/myweb/intest/static/codeImg/' + fileName
				result['HTML'] = {'url':urlPath + fileName,'type':'image'}
				open(rootPath,'wb').write(b.getvalue())
			else:
				result['HTML'] = b.getvalue().decode('UTF-8')
		except TypeError as e:
			print('...%s error, try  %sth times\n%s' % (myUrl['method_version'],n,e))
		except:
			print("Unexpected error:", sys.exc_info()[0])
			print("%s" % myUrl['url'])
		else:
			# print(result['HTML'])
			break
		finally:
			n += 1
	b.close()
	c.close()
	return result

def doSave(result):
	for x in result:
		# 必有：URL，品类，接口，版本，请求方法，请求时间
		p = Sdata(method_version=x['method_version'])
		p.name = x['des']
		p.url = x['url']
		p.ci = x['type']
		p.method = x['method']
		# 请求成功才有
		if x['status'] == '1':
			# 时间都是微秒
			p.httpCode = x['HTTP_CODE']
			p.requesTime = x['requesTime']
			p.dnsTime = x['NAMELOOKUP_TIME']
			p.conneTime = x['CONNECT_TIME'] - x['NAMELOOKUP_TIME']
			p.sslTime = x['APPCONNECT_TIME'] - x['CONNECT_TIME']
			p.serverTime = x['STARTTRANSFER_TIME'] - x['PRETRANSFER_TIME']
			p.downloadTime = x['TOTAL_TIME'] - x['STARTTRANSFER_TIME']
			p.total_time = x['TOTAL_TIME']
			p.size = x['SIZE_DOWNLOAD']
			p.speed = x['SPEED_DOWNLOAD']
		# 判断返回类型，图片，正常格式，500错误
		# if x['HTML']:
		# 	p.code = x['']
		p.response = x['HTML']
		p.save()
		print('...%s save done' % x['method_version'])

if __name__ == '__main__':
	start = time.time()
	urls = getUrls()
	second = time.time()
	print('...time costs:%s' % (second - start))
	print('...urls ready num:%s' % len(urls))
	j = Pool(4)
	results = j.map(doWork, urls)
	j.close()
	j.join()
	end = time.time()
	print('...time costs:%s' % (end - second))
	print('...All subprocesses done. Do save work')
	# print(results)
	doSave(results)
