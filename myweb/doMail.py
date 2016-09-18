#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import django
import os, sys, io, json, pycurl, time, datetime, multiprocessing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
import string,smtplib,os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import Header
import time,datetime
from intest.models import *

def err_list():
	yesday = time.strftime('%Y-%m-%d',time.localtime(time.time() - 24*60*60) )
	y = yesday.split('-')[0]
	m = yesday.split('-')[1]
	d = yesday.split('-')[2]
	date_from = datetime.datetime(time.localtime().tm_year,time.localtime().tm_mon,time.localtime().tm_mday, 0, 0)
	date_to = datetime.datetime(time.localtime().tm_year,time.localtime().tm_mon,time.localtime().tm_mday, 23, 59)
	error_list = Errs.objects.all().filter(timestamp__range=(date_from,date_to))
	# error_list = Errs.objects.all().filter(timestamp__range=(datetime.datetime(2016,9,1,0,0),datetime.datetime(2016,9,1,23,59)))
	if error_list:	#没有错误就跳出程序吧
		print (error_list)
		return error_list
	else:
		print ("+++")
		sys.exit(0)
	
def do_contents():
	error_list = err_list()
	html_string0 = "<table border=1><tr><th>名称</th><th>接口</th><th>HTTP响应码</th><th>code</th><th>error</th><th>message</th></tr>"
	html_string1 = ""
	for x in error_list:
		html_string1 += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %(x.name, x.method_version, x.httpcode, x.log_code, x.error, x.message))
	html_string2="</table>"
	html_string = html_string0 + html_string1 + html_string2
	return html_string
	
def do_mail():
	sender = 'zhangqiang@lvmama.com'
	receiverlist = ["zhangqiang@lvmama.com"]
	subject = "接口性能--报错列表"
	smtpserver = 'smtp.exmail.qq.com'
	username = 'zhangqiang@lvmama.com'
	password = '851206Sqq'

	html_string = do_contents()
	
	msg=MIMEText(html_string,'html','utf-8')
	msg['From'] = 'zhangqiang@lvmama.com'
	msg['to'] = ','.join(receiverlist)
	msg['Subject'] = subject

	smtp = smtplib.SMTP()
	smtp.connect(smtpserver)
	smtp.ehlo()
	# smtp.set_debuglevel(1)
	smtp.login(username, password)
	smtp.sendmail(msg['From'],msg['to'],msg.as_string())
	smtp.quit()
	
if __name__ == '__main__':
	do_mail()