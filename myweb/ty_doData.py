import configparser
import datetime
import json
import re
import time
import os
import django
import logging
import argparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from bs4 import BeautifulSoup
from selenium import webdriver
from tyblog.models import *
from django.db.models import Q

# 日志模块
logger = logging.getLogger('myLogger')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('ty.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
# ch = logging.StreamHandler()
# ch.setLevel(logger.DEBUG)
# ch.setFormatter(formatter)
# logger.addHandler(ch)
parser = argparse.ArgumentParser(description='I print messages')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Enable debug info')

args = parser.parse_args()
if args.verbose:
	logger.setLevel(logging.DEBUG)
else:
	logger.setLevel(logging.INFO)

# 通过selenium获取数据
def get_data(urls):
	cf = configparser.ConfigParser()
	cf.read('/rd/pystudy/conf')
	username = cf.get('TY', 'username')
	password = cf.get('TY', 'password')

	driver = webdriver.PhantomJS(executable_path='/bin/phantomjs')
	driver.get(
		"https://account.tingyun.com/cas/login?service=https%3A%2F%2F"
		"saas.tingyun.com%2Fj_acegi_cas_security_check%3FloginView%3DcasLoginTingyun")
	driver.find_element_by_id("username").send_keys(username)
	driver.find_element_by_id("password").send_keys(password)
	driver.find_element_by_class_name("mty-btn-blue").click()
	time.sleep(3)
	for k, v in urls.items():
		driver.get(v)
		html = driver.page_source
		soup = BeautifulSoup(html, "html.parser")
		content = soup.pre.string
		save_datas(k, content)
	time.sleep(3)
	driver.quit()

# 保存数据
def save_datas(name, content):
	with open(('/rd/pystudy/Intest/myweb/tyblog/src/%s' % name), 'w', encoding='utf-8', errors='ignore') as f:
		f.write(content)

# 拼接URL
def get_urls():
	d = datetime.datetime.now()
	this_year = d.year
	this_month = d.month
	last_month = (d - datetime.timedelta(days=d.day)).month
	this_day = d.day

	url0 = 'https://report.tingyun.com/mobile/mobileApplication/selectFilter/'
	if int(this_day) < 15:
		url1 = ('&endTime=%s-%s-%s%%2023%%3A59' % (this_year, last_month, '28'))
		url2 = ('&endTime=%s-%s-%s+23%%3A59' % (this_year, last_month, '28'))
		url3 = ('&endTime=%s-%s-%s+23%%3A59' % (this_year, last_month, '21'))
	else:
		url1 = ('&endTime=%s-%s-%s%%2000%%3A00' % (this_year, this_month, '15'))
		url2 = ('&endTime=%s-%s-%s+00%%3A00' % (this_year, this_month, '15'))
		url3 = ('&endTime=%s-%s-%s+00%%3A00' % (this_year, this_month, '08'))

	urls = {'res_api3g2_a': url0 + 'http/host/uri.json?&mobileAppId=9573&mobileAppVersionFilterId=&timeType=2'
								   '&timePeriod=20160&baseonId=1&searchKey=api3g2&reqType=2&pageNo=1&pageSize=5000'
								   '&hostId=424892' + url1,
			'res_api3g_a': url0 + 'http/host/uri.json?&mobileAppId=9573&mobileAppVersionFilterId=&timeType=2'
								  '&timePeriod=20160&baseonId=1&searchKey=api3g&reqType=2&pageNo=1&pageSize=1000'
								  '&hostId=424891' + url1,
			'res_lvmm_a': url0 + 'http/host/uri.json?&mobileAppId=9573&mobileAppVersionFilterId=&timeType=2'
								 '&timePeriod=20160&baseonId=1&searchKey=lvmama&reqType=2&pageNo=1&pageSize=1000'
								 '&hostId=41699' + url1,
			'res_api3g2_ios': url0 + 'http/host/uri.json?&mobileAppId=9568&mobileAppVersionFilterId=&timeType=2'
									 '&timePeriod=20160&baseonId=1&searchKey=api3g2&reqType=2&pageNo=1&pageSize=5000'
									 '&hostId=424892' + url1,
			'res_api3g_ios': url0 + 'http/host/uri.json?&mobileAppId=9568&mobileAppVersionFilterId=&timeType=2'
									'&timePeriod=20160&baseonId=1&searchKey=api3g&reqType=2&pageNo=1&pageSize=1000'
									'&hostId=424891' + url1,
			'res_lvmm_ios': url0 + 'http/host/uri.json?&mobileAppId=9568&mobileAppVersionFilterId=&timeType=2'
								   '&timePeriod=20160&baseonId=1&searchKey=lvmama&reqType=2&pageNo=1&pageSize=1000'
								   '&hostId=41699' + url1,
			'rpm_api3g2_a': url0 + 'http/host/uri.json?&mobileAppId=9573&mobileAppVersionFilterId=&timeType=2'
								   '&timePeriod=20160&baseonId=3&searchKey=lvmama&reqType=2&pageNo=1&pageSize=5000'
								   '&hostId=424892' + url1,
			'rpm_api3g_a': url0 + 'http/host/uri.json?&mobileAppId=9573&mobileAppVersionFilterId=&timeType=2'
								  '&timePeriod=20160&baseonId=3&searchKey=lvmama&reqType=2&pageNo=1&pageSize=1000'
								  '&hostId=424891' + url1,
			'rpm_lvmm_a': url0 + 'http/host/uri.json?&mobileAppId=9573&mobileAppVersionFilterId=&timeType=2'
								 '&timePeriod=20160&baseonId=3&searchKey=lvmama&reqType=2&pageNo=1&pageSize=1000'
								 '&hostId=41699' + url1,
			'rpm_api3g2_ios': url0 + 'http/host/uri.json?&mobileAppId=9568&mobileAppVersionFilterId=&timeType=2'
									 '&timePeriod=20160&baseonId=3&searchKey=lvmama&reqType=2&pageNo=1&pageSize=5000'
									 '&hostId=424892' + url1,
			'rpm_api3g_ios': url0 + 'http/host/uri.json?&mobileAppId=9568&mobileAppVersionFilterId=&timeType=2'
									'&timePeriod=20160&baseonId=3&searchKey=lvmama&reqType=2&pageNo=1&pageSize=1000'
									'&hostId=424891' + url1,
			'rpm_lvmm_ios': url0 + 'http/host/uri.json?&mobileAppId=9568&mobileAppVersionFilterId=&timeType=2'
								   '&timePeriod=20160&baseonId=3&searchKey=lvmama&reqType=2&pageNo=1&pageSize=1000'
								   '&hostId=41699' + url1,
			'err_a': url0 + 'error.json?&mobileAppId=9573&mobileAppVersionFilterId='
							'&timeType=2&timePeriod=20160&baseonId=1' + url2,
			'err_ios': url0 + 'error.json?&mobileAppId=9568&mobileAppVersionFilterId='
							  '&timeType=2&timePeriod=20160&baseonId=1' + url2,
			'res_a': url0 + 'http/host.json?&mobileAppId=9573&mobileAppVersionFilterId='
							'&timeType=2&timePeriod=20160&baseonId=1&reqType=1' + url2,
			'res_ios': url0 + 'http/host.json?&mobileAppId=9568&mobileAppVersionFilterId='
							  '&timeType=2&timePeriod=20160&baseonId=1&reqType=1' + url2,
			'view_a': url0 + 'interactionView.json?&mobileAppId=9573&mobileAppVersionFilterId='
							 '&timeType=2&timePeriod=20160&baseonId=14' + url2,
			'view_ios': url0 + 'interactionView.json?&mobileAppId=9568&mobileAppVersionFilterId='
							   '&timeType=2&timePeriod=20160&baseonId=14' + url2,
			'crash_a_one':	 url0 + 'crash/list.json?&mobileAppId=9573&mobileAppVersionFilterId='
			'&timeType=2&timePeriod=10080&baseonId=2' + url3,
			'crash_a_two':	 url0 + 'crash/list.json?&mobileAppId=9573&mobileAppVersionFilterId='
			'&timeType=2&timePeriod=10080&baseonId=2' + url2,
			'crash_ios_one': url0 + 'crash/list.json?&mobileAppId=9568&mobileAppVersionFilterId='
			'&timeType=2&timePeriod=10080&baseonId=2' + url3,
			'crash_ios_two': url0 + 'crash/list.json?&mobileAppId=9568&mobileAppVersionFilterId='
			'&timeType=2&timePeriod=10080&baseonId=2' + url2}
	return urls

# 获取主机名和平台
def judge_host(s):
	if 'api3g2' in s.split('_'):
		hostid = 'api3g2'
	elif 'lvmm' in s.split('_'):
		hostid = 'm'
	else:
		hostid = 'api3g'
	if 'ios' in s.split('_'):
		plantform = 'ios'
	else:
		plantform = 'android'
	return hostid, plantform

#获取时间描述信息
def time_des():
	d = datetime.datetime.now()
	this_year = d.year
	this_month = d.month
	last_month = (d - datetime.timedelta(days=d.day)).month
	if d.day < 15:
		des = str(this_year) + str(last_month) + "月下"
		crash_one = str(this_year) + str(last_month) + "第3周"
		crash_two = str(this_year) + str(last_month) + "第4周"
	else:
		des = str(this_year) + str(this_month) + "月上"
		crash_one = str(this_year) + str(last_month) + "第1周"
		crash_two = str(this_year) + str(last_month) + "第2周"
	return des, crash_one, crash_two

#储存数据库
def do_db():
	res_file = ['res_api3g2_a', 'res_api3g2_ios', 'res_api3g_a', 'res_api3g_ios', 'res_lvmm_a', 'res_lvmm_ios']
	rpm_file = ['rpm_api3g2_a', 'rpm_api3g2_ios', 'rpm_api3g_a', 'rpm_api3g_ios', 'rpm_lvmm_a', 'rpm_lvmm_ios']
	err_file = ['err_a', 'err_ios']
	view_file = ['view_a', 'view_ios']
	resite_file = ['res_a', 'res_ios']
	crash_file = ['crash_a_one', 'crash_ios_one', 'crash_a_two', 'crash_ios_two']
	Rpm.objects.all().filter(time=time_des()[0]).delete()
	Res.objects.all().filter(time=time_des()[0]).delete()
	errs.objects.all().filter(des=time_des()[0]).delete()
	views.objects.all().filter(des=time_des()[0]).delete()
	reses.objects.all().filter(des=time_des()[0]).delete()
	crashes.objects.all().filter(des=time_des()[1]).delete()
	crashes.objects.all().filter(des=time_des()[2]).delete()
	for i in res_file:
		with open(('tyblog/src/%s' % i), 'r', encoding='utf-8') as f:
			b = json.loads(f.read())
			newb = [dict(name=x['name'], value=x['value'], ) for x in b]
			host_id = judge_host(i)[0]
			plantform = judge_host(i)[1]
			for x in newb:
				if 'method=' in x['name']:
					if 'productId' not in x['name'] or 'keyword' not in x['name']:
						src = x['name'].replace('&', '|').replace('?', '|').replace(' ', '|').replace('%', '|') + '|'
						p = Res(hostId=host_id)
						logger.debug('api3g2 xname=%s' % x['name'])
						logger.debug('api3g2 src=%s' % src)
						method = re.findall(r"method=(.+?)\|", src)[0]
						logger.debug('api3g2 method=%s' % method)
						p.method = method
						if 'POST' in src:
							p.isGet = 'Post'
						else:
							p.isGet = 'Get'
						if 'https' in src:
							p.isHttp = 'Https'
						else:
							p.isHttp = 'Http'
						if 'lvversion' in src:
							p.lvversion = re.findall(r"lvversion=(.+?)\|", src)[0]
						else:
							p.lvversion = ''
						if '|version' in src:
							p.version = re.findall(r"\|version=(.+?)\|", src)[0]
						else:
							p.version = ''
						p.plantform = plantform
						p.time = time_des()[0]
						p.response = x['value']
						try:
							p.des = Ints.objects.filter(method=method).values('des')[0]['des']
						except:
							p.des = ''
						p.save()
					else:
						continue
				elif 'clutter/client' in x['name']:
					src = x['name'].replace('&', '|').replace('?', '|').replace(' ', '|').replace('%', '|') + '|'
					p = Res(hostId=host_id)
					method = re.findall(r"/clutter(.+?)\|", src)[0]
					p.method = method
					logger.debug('api3g src=%s' % src)
					logger.debug('api3g method=%s' % method)
					if 'POST' in src:
						p.isGet = 'Post'
					else:
						p.isGet = 'Get'
					if 'https' in src:
						p.isHttp = 'Https'
					else:
						p.isHttp = 'Http'
					p.lvversion = ''
					p.version = ''
					p.plantform = plantform
					p.time = time_des()[0]
					p.response = x['value']
					try:
						p.des = Ints.objects.filter(method=method).values('des')[0]['des']
					except:
						p.des = ''
					p.save()
				elif 's='  in x['name'] or 'toPay' in x['name'] or 'clutter' in x['name'] or '*.' in x['name']:
					if 'udid' in x['name'] or 'product-' in x['name']:
						continue
					else:
						src = x['name'].replace('&', '|').replace(' ', '|').replace('%', '|') + '|'
						p = Res(hostId=host_id)
						if 'POST' in src:
							p.isGet = 'Post'
							method = src.split('|')[1]
							p.method = method
						else:
							p.isGet = 'Get'
							method = src.split('|')[0]
							p.method = method
						logger.debug('m src=%s' % src)
						logger.debug('m method=%s' % method)
						if 'https' in src:
							p.isHttp = 'Https'
						else:
							p.isHttp = 'Http'
						p.lvversion = ''
						p.version = ''
						p.plantform = plantform
						p.response = x['value']
						try:
							p.des = Ints.objects.filter(method=method).values('des')[0]['des']
						except:
							p.des = ''
						p.time = time_des()[0]
						p.save()
				else:
					continue
	for i in rpm_file:
		with open(('tyblog/src/%s' % i), 'r', encoding='utf-8') as f:
			b = json.loads(f.read())
			newb = [dict(name=x['name'], value=x['value'], ) for x in b]
			host_id = judge_host(i)[0]
			plantform = judge_host(i)[1]
			for x in newb:
				if 'method=' in x['name']:
					src = x['name'].replace('&', '|').replace('?', '|').replace(' ', '|').replace('%', '|') + '|'
					p = Rpm(hostId=host_id)
					method = re.findall(r'method=(.+?)\|', src)[0]
					p.method = method
					logger.debug('api3g2 src=%s' % src)
					logger.debug('api3g2 method=%s' % method)
					if 'POST' in src:
						p.isGet = 'Post'
					else:
						p.isGet = 'Get'
					if 'https' in src:
						p.isHttp = 'Https'
					else:
						p.isHttp = 'Http'
					if 'lvversion' in src:
						p.lvversion = re.findall(r'lvversion=(.+?)\|', src)[0]
					else:
						p.lvversion = ''
					if '|version' in src:
						p.version = re.findall(r"\|version=(.+?)\|", src)[0]
					else:
						p.version = ''
					p.plantform = plantform
					p.rpm = x['value']
					p.time = time_des()[0]
					try:
						p.des = Ints.objects.filter(method=method).values('des')[0]['des']
					except:
						p.des = ''
					p.save()
				elif 'clutter/client' in x['name']:
					src = x['name'].replace('&', '|').replace('?', '|').replace(' ', '|').replace('%', '|') + '|'
					p = Rpm(hostId=host_id)
					method = re.findall(r"/clutter(.+?)\|", src)[0]
					p.method = method
					logger.debug('api3g src=%s' % src)
					logger.debug('api3g method=%s' % method)
					if 'POST' in src:
						p.isGet = 'Post'
					else:
						p.isGet = 'Get'
					if 'https' in src:
						p.isHttp = 'Https'
					else:
						p.isHttp = 'Http'
					p.lvversion = ''
					p.version = ''
					p.plantform = plantform
					p.rpm = x['value']
					p.time = time_des()[0]
					p.save()
				elif 's='  in x['name'] or 'toPay' in x['name'] or 'clutter' in x['name'] or '*.' in x['name']:
					src = x['name'].replace('&', '|').replace(' ', '|').replace('%', '|') + '|'
					p = Rpm(hostId=host_id)
					if 'POST' in src:
						p.isGet = 'Post'
						if 'udid' in x['name']:
							method = src.split('|')[1].replace(re.findall(r'(udid=.+)\|', src)[0], '')
							p.method = method
						else:
							method = src.split('|')[1]
							p.method = method
					else:
						p.isGet = 'Get'
						if 'udid' in x['name']:
							method = src.split('|')[0].replace(re.findall(r'(udid=.+)\|', src)[0], '')
							p.method = method
						else:
							method = src.split('|')[0]
							p.method = method
					logger.debug('m src=%s' % src)
					logger.debug('m method=%s' % method)
					if 'https' in src:
						p.isHttp = 'Https'
					else:
						p.isHttp = 'Http'
					p.lvversion = ''
					p.version = ''
					p.plantform = plantform
					p.time = time_des()[0]
					p.rpm = x['value']
					try:
						p.des = Ints.objects.filter(method=method).values('des')[0]['des']
					except:
						p.des = ''
					p.save()
				else:
					continue
	for i in err_file:
		with open(('tyblog/src/%s' % i), 'r', encoding='utf-8') as f:
			b = json.loads(f.read())
			newb = [dict(name=x['name'], value=x['value'], ) for x in b]
			host_list = ['pic.lvmama.com', 'iguide.lvmama.com', 'api3g.lvmama.com', 'api3g2.lvmama.com', 'm.lvmama.com',
						 'login.lvmama.com', 'www.lvmama.com', 'zt1.lvmama.com', 'alog.umeng.com',
						 'loc.map.baidu.com', 'resolver.gslb.mi-idc.com', 'sapi.map.baidu.com', 'api.weixin.qq.com',
						 'collect.dsp.chinanetcenter.com', 'mauth.chinanetcenter.com', 'm.api.baifengdian.com',
						 'data.cn.coremetrics.com', 'api.weibo.com', 'pingma.qq.com', 'api.share.mob.com']
			for x in newb:
				for y in host_list:
					if y == x['name']:
						p = errs(name=y)
						p.des = time_des()[0]
						p.plantform = judge_host(i)[1]
						p.value = x['value']
						p.save()
	for i in view_file:
		with open(('tyblog/src/%s' % i), 'r', encoding='utf-8') as f:
			b = json.loads(f.read())
			newb = [dict(name=x['name'], value=x['value'], ) for x in b]
			host_list = ['WelcomeActivity', 'MainActivity', 'V5IndextFragment', 'LvmmWebIndexFragment',
						 'WebViewIndexActivity', 'Filter2ViewController', 'RouteSearchTableViewController',
						 'LVMMTabBarController', 'IndexSearchViewController', 'LVNavigationController',
						 'StartUpViewController']
			for x in newb:
				for y in host_list:
					if y in x['name']:
						p = views(name=y)
						p.des = time_des()[0]
						p.plantform = judge_host(i)[1]
						p.value = x['value']
						p.save()
	for i in resite_file:
		with open(('tyblog/src/%s' % i), 'r', encoding='utf-8') as f:
			b = json.loads(f.read())
			newb = [dict(name=x['name'], value=x['value'], ) for x in b]
			host_list = ['pic.lvmama.com', 'iguide.lvmama.com', 'api3g.lvmama.com', 'api3g2.lvmama.com', 'm.lvmama.com',
						 'login.lvmama.com', 'zt1.lvmama.com', 'super.lvmama.com', 'alog.umeng.com',
						 'loc.map.baidu.com', 'resolver.gslb.mi-idc.com', 'sapi.map.baidu.com', 'api.weixin.qq.com',
						 'collect.dsp.chinanetcenter.com', 'mauth.chinanetcenter.com', 'm.api.baifengdian.com',
						 'data.cn.coremetrics.com', 'api.weibo.com', 'pingma.qq.com', 'api.share.mob.com',
						 'api.share.mob.com:80']
			for x in newb:
				for y in host_list:
					if y in x['name']:
						p = reses(name=y)
						p.des = time_des()[0]
						p.plantform = judge_host(i)[1]
						p.value = x['value']
						p.save()
	for i in crash_file:
		with open(('tyblog/src/%s' % i), 'r', encoding='utf-8') as f:
			b = json.loads(f.read())
			newb = [dict(name=x['name'], value=x['value'],) for x in b]
			for x in newb:
				if re.findall(r'\d', x['name']):
					p = crashes(name=x['name'])
					if 'one' in i:
						p.des = time_des()[1]
					else:
						p.des = time_des()[2]
					p.plantform = judge_host(i)[1]
					p.value = x['value']
					p.save()
				else:
					continue
#计算接口占比
def do_rates():
	x = Res.objects.all().filter(hostId='api3g2').filter(time=time_des()[0]) #过滤这期所有api3g2的res数据
	x_a = x.filter(plantform='android') # 安卓的所有数据
	x_ios = x.filter(plantform='ios') # ios的所有数据
	# 取最新的2个版本号
	z = x.values('lvversion').distinct().order_by('-lvversion')
	first_version = z[0]['lvversion']
	second_version = z[1]['lvversion']
	#将最新的2个版本数据汇总，包含android和ios
	all_list = x.filter(Q(lvversion=first_version)|Q(lvversion=second_version)).values('response')
	ms_count = len([x for x in all_list if x['response'] < 1])
	one_count = len([x for x in all_list if 1 <= x['response'] < 2])
	two_count = len([x for x in all_list if 2 <= x['response'] < 3])
	three_count = len([x for x in all_list if 3 <= x['response'] < 4])
	four_count = len([x for x in all_list if 4 <= x['response'] < 5])
	five_count = len([x for x in all_list if x['response'] >=5])
	all_list = len(all_list)
	try:
		Rates.objects.all().filter(des=time_des()[0]).delete()
		p = Rates(des=time_des()[0])
		p.zero_level = round(ms_count / all_list * 100)
		p.one_level = round(one_count / all_list * 100)
		p.two_level = round(two_count / all_list * 100)
		p.three_level = round(three_count / all_list * 100)
		p.four_level = round(four_count / all_list * 100)
		p.five_level = round(five_count / all_list * 100)
		p.save()
	except:
		print("计算占比出错")
# 合并res和rpm数据
def do_count():
	pass
	
	
if __name__ == '__main__':
	# urls = get_urls() #拼接URL
	# get_data(urls) #通过听云获取数据
	# do_db() # 存储数据库
	do_rates() # 计算接口占比 
