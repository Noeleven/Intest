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
	error_list = Errs.objects.all().filter(timestamp__range=(date_from,date_to)).order_by('name')
	if error_list:	#没有错误就跳出程序吧
		return error_list
	else:
		sys.exit(0)
	
def do_contents():
	my_lists = err_list()
	html_string0 = "<h3>以下是今天产生的错误列表，测试组童鞋 还请查看有日志返回的错误异常信息，验证线上产品是否有异常</h3><br /><h4>响应码非200的接口说明线上服务有几率会挂。参数错误（如产品下架等）导致的，可以访问<a href='http://10.113.1.35:8000/admin/intest/ints/' target=_blank>接口管理地址</a>修改参数，也可以等管理员修改。</h4><table border=1 width=100%><tr style='background-color:cadetblue'><th>HttpCode</th><th>Name</th><th>Method</th><th>LogCode</th><th>Error</th><th>Message</th><th>ProductId</th><th>URL</th><th>Time</th></tr>\n\r"
	html_string1 = ""
	
	for x in my_lists:
		temp_list = x.url.split('&')
		for z in temp_list:
			if str(z).startswith('productId'):
				pId = z.split('=')[1]
				break
			else:
				pId = 'null'
		html_string1 += ("<tr><td>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><a href='%s'>url</a></td><td>%s</td></tr>\n\r" %( x.httpcode, x.name, x.method_version, x.log_code, x.error, x.message, pId, x.url, x.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
	patterns = []
	#去重
	for line in html_string1.split("\n\r"):
		if line not in patterns:
			patterns.append(line)
	html_string2 = "".join(patterns)
	html_string3="</table><h4><a href='http://10.113.1.35:8000/' target=_blank>性能监控平台</a></h4>"
	html_string = html_string0 + html_string2 + html_string3
	#print (html_string)
	return html_string
	
def do_mail():
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	sender = cf.get('mail', 'username')
	receiverlist = [x for x in cf.get('mail', 'receiverlist').split(',')] 
	subject = "[接口性能自动化]--错误日志"
	smtpserver = cf.get('mail','smtpserver') 
	username = cf.get('mail','username') 
	password = cf.get('mail','password') 

	html_string = do_contents()
	
	msg=MIMEText(html_string,'html','utf-8')
	msg['From'] = _format_addr("管理员 <%s>" % sender) 
	msg['to'] = '%s' % ','.join([_format_addr('<%s>' % x) for x in receiverlist])
	msg['Subject'] = Header("%s" % subject , 'utf-8').encode()

	smtp = smtplib.SMTP()
	smtp.connect(smtpserver)
	smtp.ehlo()
	#smtp.set_debuglevel(1)
	smtp.login(username, password)
	smtp.sendmail(msg['From'],receiverlist,msg.as_string())
	smtp.quit()
	
if __name__ == '__main__':
	do_mail()
