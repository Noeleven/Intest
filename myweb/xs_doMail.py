#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import django
import os, sys, io, time, datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
import string,smtplib
import configparser
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import Header
from email.utils import	parseaddr, formataddr
from intest.models import *

def _format_addr(s):
	name, addr = parseaddr(s)
	return formataddr((Header(name, 'utf-8').encode(), addr))

def err_list():
	#yesday = time.strftime('%Y-%m-%d',time.localtime(time.time() - 24*60*60) )
	today = time.strftime('%Y-%m-%d',time.localtime(time.time()) )
	y = int(today.split('-')[0])
	m = int(today.split('-')[1])
	d = int(today.split('-')[2])
	date_from = datetime.datetime(y,m,d, 0, 0)
	date_to = datetime.datetime(y,m,d, 23, 59)
	reportlist = Sdata.objects.filter(recordTime__range=(date_from, date_to))
	err = reportlist.exclude(httpCode='200')
	if err:
		return err
	else:	# 没有错误就跳出程序吧
		sys.exit(0)

def do_contents():
	my_lists = err_list()
	html_string0 = "<h3>今天请求错误的接口</h3><br /><h4><a href='http://10.115.1.73:8000/intest/int_report' target=_blank>接口报告</a></h4><table border=1 width=100%><tr style='background-color:cadetblue'><th>HttpCode</th><th>Type</th><th>Name</th><th>Method</th><th>ProductId</th><th>URL</th></tr>\n\r"
	html_string1 = ""

	for x in my_lists:
		temp_list = x.url.split('&')
		for z in temp_list:
			if str(z).startswith('productId'):
				pId = z.split('=')[1]
				break
			else:
				pId = 'null'
		html_string1 += ("<tr><td>%s</td><td>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td>%s</td><td><a href='%s'>url</a></td></tr>\n\r" %( x.httpCode, x.ci, x.name, x.method_version, pId, x.url))
	patterns = []
	#去重
	for line in html_string1.split("\n\r"):
		if line not in patterns:
			patterns.append(line)
	html_string2 = "".join(patterns)
	html_string3="</table>"
	html_string = html_string0 + html_string2 + html_string3
	return html_string

def do_mail():
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	sender = cf.get('mail', 'username')
	receiverlist = [x for x in cf.get('mail', 'receiverlist').split(',')]
	subject = "[接口检测]--线上环境"
	smtpserver = cf.get('mail','smtpserver')
	username = cf.get('mail','username')
	password = cf.get('mail','password')

	html_string = do_contents()

	msg=MIMEText(html_string,'html','utf-8')
	msg['From'] = _format_addr("接口测试 <%s>" % sender)
	msg['to'] = '%s' % ','.join([_format_addr('<%s>' % x) for x in receiverlist])
	msg['Subject'] = Header("%s" % subject , 'utf-8').encode()

	smtp = smtplib.SMTP()
	smtp.connect(smtpserver)
	smtp.ehlo()
	smtp.set_debuglevel(1)
	smtp.login(username, password)
	smtp.sendmail(msg['From'],receiverlist,msg.as_string())
	smtp.quit()

if __name__ == '__main__':
	do_mail()
