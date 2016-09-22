#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import django
import os, sys, io, json, pycurl, time, datetime, multiprocessing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
import string,smtplib,os
import configparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import Header
import time,datetime
from intest.models import *

def err_list():
	yesday = time.strftime('%Y-%m-%d',time.localtime(time.time() - 24*60*60) )
	y = int(yesday.split('-')[0])
	m = int(yesday.split('-')[1])
	d = int(yesday.split('-')[2])
	date_from = datetime.datetime(y,m,d, 0, 0)
	date_to = datetime.datetime(y,m,d, 23, 59)
	error_list = Errs.objects.all().filter(timestamp__range=(date_from,date_to))
	if error_list:	#没有错误就跳出程序吧
	#	print (error_list)
		return error_list
	else:
#		print ("+++")
		sys.exit(0)
	
def do_contents():
	error_list = err_list()
	html_string0 = "<h3>以下是昨天产生的错误列表，请根据错误内容调整接口参数，保证测试有效性。<a href="http://10.113.1.35:8000/admin/intest/ints/" target=_blank>接口管理地址</a></h3><table border=1><tr><th>名称</th><th>接口</th><th>HTTP响应码</th><th>code</th><th>error</th><th>message</th></tr>\n\r"
	html_string1 = ""
	for x in error_list:
		html_string1 += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n\r" %(x.name, x.method_version, x.httpcode, x.log_code, x.error, x.message))
	patterns = []
	for line in html_string1.split("\n\r"):
		if line not in patterns:
			patterns.append(line)
	html_string2 = "".join(patterns)
	html_string3="</table>"
	html_string = html_string0 + html_string2 + html_string3
	print(html_string)
	return html_string
	
def do_mail():
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	sender = cf.get('mail', 'username')
	receiverlist = [x for x in cf.get('mail', 'receiverlist').split(',')] 
	subject = "[接口性能自动化]--接口错误"
	smtpserver = cf.get('mail','smtpserver') 
	username = cf.get('mail','username') 
	password = cf.get('mail','password') 

	html_string = do_contents()
	
	msg=MIMEText(html_string,'html','utf-8')
	msg['From'] = sender 
	#msg['to'] = ','.join(receiverlist)
	msg['Subject'] = subject

	smtp = smtplib.SMTP()
	smtp.connect(smtpserver)
	smtp.ehlo()
	#smtp.set_debuglevel(1)
	smtp.login(username, password)
	#smtp.sendmail(msg['From'],msg['to'],msg.as_string())
	smtp.sendmail(msg['From'],receiverlist,msg.as_string())
	smtp.quit()
	
if __name__ == '__main__':
	do_mail()
