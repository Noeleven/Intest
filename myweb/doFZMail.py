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
from fz.models import *

def _format_addr(s):
	name, addr = parseaddr(s)
	return formataddr((Header(name, 'utf-8').encode(), addr))

def err_list():
	today = time.strftime('%Y-%m-%d',time.localtime(time.time()) )
	y = int(today.split('-')[0])
	m = int(today.split('-')[1])
	d = int(today.split('-')[2])
	date_from = datetime.datetime(y,m,d, 0, 0)
	date_to = datetime.datetime(y,m,d, 23, 59)
	err_500 = Sdata.objects.values('name', 'method_version', 'url', 'code', 'log_code', 'debugmsg', 'error', 'message').filter(timestamp__range=(date_from,date_to)).filter(code='500').order_by('name').distinct().order_by('name')
	err_200 = Sdata.objects.values('name', 'method_version', 'url', 'code', 'log_code', 'debugmsg', 'error', 'message').filter(timestamp__range=(date_from,date_to)).filter(code='200').exclude(log_code='1').order_by('name').distinct().order_by('name')
	succ_200 = Sdata.objects.values('name', 'method_version', 'url', 'code', 'log_code', 'error', 'message').filter(timestamp__range=(date_from,date_to)).filter(log_code='1').order_by('name').distinct().order_by('name')
	err_list = []
	if err_500 or err_200:	#没有错误就跳出程序吧
		err_list.append(err_500)
		err_list.append(err_200)
		err_list.append(succ_200)
		return err_list
	else:
		sys.exit(0)
	
def do_contents():
	my_lists = err_list()
	html_string0 = "<h3><font face='微软雅黑'>以下是今天仿真环境产生的错误列表，测试时间为今天3点到4点，每隔15分钟检测一次</font></h3><h4><span style='background-color: rgba(0, 0, 0, 0); font-family: 微软雅黑; font-size: 16px;'>&nbsp; &nbsp;&nbsp;</span><span style='font-weight: normal;'><font face='微软雅黑'>-- 返回值500、404说明仿真环境接口服务挂了或网络不稳定<br></font></span><span style='font-family: 微软雅黑; font-size: 16px; color: rgb(0, 0, 0); background-color: rgba(0, 0, 0, 0); font-weight: normal;'>&nbsp; &nbsp;&nbsp;</span><span style='font-weight: normal;'><font face='微软雅黑'>-- 返回200，日志code不是1的，请根据error或message信息判断<br></font></span><span style='font-family: 微软雅黑; font-size: 16px; color: rgb(0, 0, 0); background-color: rgba(0, 0, 0, 0); font-weight: normal;'>&nbsp; &nbsp;&nbsp;</span><span style='font-weight: normal;'><font face='微软雅黑'>-- 需要修改请求参数的请挪步 <a href='http://10.113.1.35:8000/admin/fz/ints/' target='_blank'>仿真测试接口管理</a><br></font></span><span style='font-family: 微软雅黑; font-size: 16px; color: rgb(0, 0, 0); background-color: rgba(0, 0, 0, 0); font-weight: normal;'>&nbsp; &nbsp;&nbsp;</span><span style='font-weight: normal;'><font face='微软雅黑'>-- 错误提供WEB页面查看 <a href='http://10.113.1.35:8000/fz' target='_blank'>仿真接口监控</a></font></span></h4>"
	
	# 500的部分
	
	html_string111 = ""
	if len(my_lists[0]) is 0:
		html_string1 = ''
	else:
	# 获取PID
		html_string11 = ("<h3>500错误:%s</h3><table border=1 width=100%%><tr style=\'background-color:cadetblue\'><th>HttpCode</th><th>Name</th><th>Method</th><th>ProductId</th><th>URL</th></tr>\n\r" % len(my_lists[0]))
		for x in my_lists[0]:
			temp_list = x['url'].split('&')
			for z in temp_list:
				if str(z).startswith('productId'):
					pId = z.split('=')[1]
					break
				else:
					pId = 'null'
		# 拼html
			html_string111 += ("<tr><td>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td>%s</td><td><a href='%s'>url</a></td></tr>\n\r" %(  x['code'], x['name'], x['method_version'], pId, x['url']))
		patterns = []
		for line in html_string111.split("\n\r"):
			if line not in patterns:
				patterns.append(line)
		html_string111 = ''.join(patterns)
		html_string1 = html_string11 + html_string111 + "</table>"
		
	#200返回错误的部分
	
	html_string222 = ''
	if len(my_lists[1]) is 0:
		html_string2 = ''
	else:
	# 获取PID
		html_string22 = ("<h3>接口返回错误:%s</h3><table border=1 width=100%%><tr style=\'background-color:cadetblue\'><th>HttpCode</th><th>Name</th><th>Method</th><th>LogCode</th><th>debugMsg</th><th>Error</th><th>Message</th><th>ProductId</th><th>URL</th></tr>\n\r" % len(my_lists[1]))
		for x in my_lists[1]:
			temp_list = x['url'].split('&')
			for z in temp_list:
				if str(z).startswith('productId'):
					pId = z.split('=')[1]
					break
				else:
					pId = 'null'
		# 拼html
			html_string222 += ("<tr><td>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td style='word-break:break-all'>%s</td><td style='word-break:break-all'>%s</td><td>%s</td><td><a href='%s'>url</a></td></tr>\n\r" %( x['code'], x['name'], x['method_version'], x['log_code'], x['debugmsg'],x['error'], x['message'], pId, x['url']))
		patterns = []
		for line in html_string222.split("\n\r"):
			if line not in patterns:
				patterns.append(line)
		html_string222 = ''.join(patterns)
		html_string2 = html_string22 + html_string222 + "</table>"
		
	# 成功的列表
	html_string333 = ''
	if len(my_lists[2]) is 0:
		html_string3 = ''
	else:
	# 获取PID
		html_string33 = ("<h3>成功:%s</h3><table border=1 width=100%%><tr style=\'background-color:cadetblue\'><th>HttpCode</th><th>Name</th><th>Method</th><th>LogCode</th><th>Error</th><th>Message</th><th>ProductId</th><th>URL</th></tr>\n\r" % len(my_lists[2]))
		for x in my_lists[2]:
			temp_list = x['url'].split('&')
			for z in temp_list:
				if str(z).startswith('productId'):
					pId = z.split('=')[1]
					break
				else:
					pId = 'null'
		# 拼html
			html_string333 += ("<tr><td>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td style='word-break:break-all'>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td style='word-break:break-all'>%s</td><td><a href='%s'>url</a></td></tr>\n\r" %(  x['code'], x['name'], x['method_version'], x['log_code'], x['error'], x['message'], pId, x['url']))
		patterns = []
		for line in html_string333.split("\n\r"):
			if line not in patterns:
				patterns.append(line)
		html_string333 = ''.join(patterns)
		html_string3 = html_string33 + html_string333 + "</table>"
		
	html_string = html_string0 + html_string1 + html_string2 + html_string3
	return html_string
	
def do_mail():
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	sender = cf.get('mail', 'username')
	receiverlist = [x for x in cf.get('mail', 'FZreceiverlist').split(',')] 
	subject = "[仿真环境 接口测试]--错误日志"
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
