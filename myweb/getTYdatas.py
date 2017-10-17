import configparser
import datetime, time
import json
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from bs4 import BeautifulSoup
from selenium import webdriver
from tyblog.models import *

'''
新版获取听云线上数据
'''


# 通过selenium获取数据
def get_data(urls):
	for k, v in urls.items():
		driver.get(v)
		html = driver.page_source
		soup = BeautifulSoup(html, "html.parser")
		content = soup.pre.string
		datas = json.loads(content)

		for x in datas:
			p = newData(tid=x['id'])
			p.value = x['value']
			p.platform = k.split('_')[0]
			p.date = yestoday
			p.type = k.split('_')[1]
			p.name = x['name']
			p.save()

# 拼接URL
def get_urls():
	baseUrl = 'https://report.tingyun.com/mobile/mobileApplication/selectFilter/'

	AD_crash = baseUrl + 'crash/list.json?&mobileAppId=9573&hideLowerThroughtput=1&mobileAppVersionFilterId=&timeType=2&timePeriod=1440&endTime=%s+00%%3A00&baseonId=2' % yestoday
	AD_error = baseUrl + 'error.json?mobileAppId=9573&hideLowerThroughtput=1&mobileAppVersionFilterId=&timeType=2&timePeriod=1440&endTime=%s+00%%3A00&baseonId=1' % yestoday
	AD_response = baseUrl + 'http/host.json?mobileAppId=9573&hideLowerThroughtput=1&mobileAppVersionFilterId=&timeType=2&timePeriod=1440&endTime=%s+00%%3A00&baseonId=1&reqType=1' % yestoday
	AD_view = baseUrl + 'interactionView.json?mobileAppId=9573&hideLowerThroughtput=1&mobileAppVersionFilterId=&timeType=2&timePeriod=1440&endTime=%s+00%%3A00&baseonId=14' % yestoday

	iOS_crash = baseUrl + 'crash/list.json?&mobileAppId=9568&hideLowerThroughtput=1&mobileAppVersionFilterId=&timeType=2&timePeriod=1440&endTime=%s+00%%3A00&baseonId=2' % yestoday
	iOS_error = baseUrl + 'error.json?mobileAppId=9568&hideLowerThroughtput=1&mobileAppVersionFilterId=&timeType=2&timePeriod=1440&endTime=%s+00%%3A00&baseonId=1' % yestoday
	iOS_response = baseUrl + 'http/host.json?mobileAppId=9568&hideLowerThroughtput=1&mobileAppVersionFilterId=&timeType=2&timePeriod=1440&endTime=%s+00%%3A00&baseonId=1&reqType=1' % yestoday
	iOS_view = baseUrl + 'interactionView.json?mobileAppId=9568&hideLowerThroughtput=1&mobileAppVersionFilterId=&timeType=2&timePeriod=1440&endTime=%s+00%%3A00&baseonId=14' % yestoday

	urls = {
		'AD_crash':AD_crash,
		'AD_error':AD_error,
		'AD_response':AD_response,
		'AD_view':AD_view,
		'iOS_crash':iOS_crash,
		'iOS_error':iOS_error,
		'iOS_response':iOS_response,
		'iOS_view':iOS_view,
	}
	# print(urls)
	return urls

# 区分版本有巨坑，首先ad和ios线上最新版本不一致，其次每天取最新版本的数据，会造成数据偏离版本
def getVersion():
	url = [
		"https://report.tingyun.com/mobile/mobileApp/9573/versionList",
		"https://report.tingyun.com/mobile/mobileApp/9568/versionList"
	]
	verId = []
	for x in url:
		driver.get(x)
		html = driver.page_source
		soup = BeautifulSoup(html, "html.parser")
		content = soup.pre.string
		datas = json.loads(content)
		print(datas['data'][0]['id'],datas['data'][0]['name'])
		verId.append(datas['data'][0]['id'])

	return verId


if __name__ == '__main__':
	cf = configparser.ConfigParser()
	cf.read('/rd/pystudy/conf')
	username = cf.get('TY', 'username')
	password = cf.get('TY', 'password')

	driver = webdriver.PhantomJS(executable_path='/bin/phantomjs')
	driver.get(
		"https://account.tingyun.com/cas/login?service=https%3A%2F%2Fsaas.tingyun.com%2Fj_acegi_cas_security_check%3FloginView%3DcasLoginTingyun")
	driver.find_element_by_id("username").send_keys(username)
	driver.find_element_by_id("password").send_keys(password)
	driver.find_element_by_class_name("mty-btn-blue").click()
	time.sleep(3)

	# 确定起始日期，持续时间，循环获取数据
	from_date = datetime.datetime(2017, 8, 1, 0, 0, 1, 000000)
	today = datetime.datetime.now()
	dulartion = (today - from_date).days

	# verId = getVersion()

	for x in range(dulartion):
		yestoday = from_date.strftime("%Y-%m-%d")
		print(yestoday)
		if not newData.objects.filter(date=yestoday):
			urls = get_urls() # 拼接URL
			get_data(urls) # 获取数据
		from_date += datetime.timedelta(days=1)

	driver.quit()
