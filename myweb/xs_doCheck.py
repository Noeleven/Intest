#!/usr/bin/env python
# -*- coding:utf8 -*-
import django
import os, sys, io, json, pycurl, time, datetime, multiprocessing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from django.http import HttpResponse
from intest.models import *

'''
消灭线上下的单，添加的游玩人等
'''
lvses = ['96d84d8c-eafd-4a2b-a0ee-77532a78f044','3237e799-1b48-47e1-b041-887ddc322640','ef3d2602-7bac-4335-9251-0f1493c64154']
# lvse='87f12558-041f-4028-a27e-f6d9b0460cf1'
addressNo = []

# 返回页面内容
def do_curl(uurl):
	c = pycurl.Curl()
	b = io.BytesIO()
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.setopt(pycurl.FOLLOWLOCATION, 1)
	c.setopt(pycurl.MAXREDIRS, 5)
	if 'https://' in uurl:
		c.setopt(pycurl.SSL_VERIFYPEER, 0)
		c.setopt(pycurl.SSL_VERIFYHOST, 0)
	c.setopt(pycurl.CONNECTTIMEOUT, 20) #链接超时
	c.setopt(pycurl.CUSTOMREQUEST, 'GET') #get or post
	c.setopt(pycurl.HTTPHEADER,['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36 NetType/WIFI Language/zh_CN")
	c.setopt(pycurl.VERBOSE,0)
	c.setopt(pycurl.URL, uurl)
	c.perform()
	htmlString = b.getvalue().decode('UTF-8')
	html_json = json.loads(htmlString)
	b.close()
	c.close()
	return html_json

# 取消订单
def cancel_order():
	c = pycurl.Curl()
	c.setopt(pycurl.FOLLOWLOCATION, 1)
	c.setopt(pycurl.MAXREDIRS, 5)
	c.setopt(pycurl.CONNECTTIMEOUT, 20)
	c.setopt(pycurl.CUSTOMREQUEST, 'GET')
	c.setopt(pycurl.HTTPHEADER,['signal:ab4494b2-f532-4f99-b57e-7ca121a137ca'])
	c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36")
	c.setopt(pycurl.VERBOSE,0)
	# 遍历lvsession
	for lv in lvses:
		orderNo = []
		getOrderAdd = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.order.getOrderList&page=1&pageSize=10&queryType=UNPAY&version=2.0.0&lvversionCode=74&lvversion=7.9.2&firstChannel=ANDROID&formate=json&secondChannel=LVMM&lvsessionid=" + lv
		cancelOrderAdd = 'http://api3g2.lvmama.com/api/router/rest.do?method=api.com.order.cancellOrder&version=1.0.0&firstChannel=ANDROID&osVersion=6.0.1&lvversionCode=65&lvversion=7.7.3&lvsessionid=' + lv
		# 取orderId
		try:
			html_json = do_curl(getOrderAdd)
			for x in html_json['data']['list']:
				orderNo.append(x['orderId'])
			for i in orderNo:
				order_str = ('&orderId=%s' % i)
				c.setopt(pycurl.URL, (cancelOrderAdd + order_str))
				c.perform()
		except TypeError as e:
			print("\n\t ** cancel_Order failed ** \n\t %s" % e)
	c.close()


def do_address():
	for lvse in lvses:
		getAddress = "https://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.getAddress&version=1.0.0&firstChannel=ANDROID&formate=json&osVersion=6.0.1&lvversionCode=72&lvversion=7.9.0&deviceName=MI%2B5&secondChannel=XIAOMI&lvsessionid=" + lvse
		delAddress = "http://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.deleteAddress&version=1.0.0&firstChannel=ANDROID&formate=json&osVersion=6.0.1&lvversionCode=72&lvversion=7.9.0&deviceName=MI%2B5&secondChannel=XIAOMI&lvsessionid=" + lvse + "&addressNo="
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
			print("\n\t ** do_address failed ** \n\t")


def do_contact():
	for lvse in lvses:
		getContact = "https://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.getContact&receiversType=CONTACT&version=1.0.0&firstChannel=ANDROID&formate=json&osVersion=6.0.1&lvversionCode=72&lvversion=7.9.0&deviceName=MI%2B5&secondChannel=XIAOMI&lvsessionid=" + lvse
		delContact = "https://api3g2.lvmama.com/api/router/rest.do?method=api.com.user.removeContact&version=1.0.0&firstChannel=ANDROID&formate=json&osVersion=6.0.1&lvversionCode=72&lvversion=7.9.0&deviceName=MI%2B5&secondChannel=XIAOMI&receiversType=Address&lvsessionid=" + lvse + "&receiverId="
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
			print("\n\t ** do_contact failed ** \n\t")
		return


if __name__ == '__main__':
	# 清理添加的地址
	do_address()
	# 清理添加的联系人
	do_contact()
	# 清理订单
	cancel_order()
