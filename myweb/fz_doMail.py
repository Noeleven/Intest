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
	range_list = Sdata.objects.values('method_version', 'url', 'code', 'log_code', 'error', 'message').filter(timestamp__range=(date_from,date_to))
	succ_200 = range_list.filter(log_code='1').order_by('method_version').distinct()
	# 由于sessionId问题，过滤-3需要登录的信息
	err_200 = range_list.filter(code='200').exclude(log_code='1').exclude(log_code='-3').order_by('method_version').distinct()
	err_500_list = range_list.exclude(code='200').order_by('method_version').distinct()

	succ_list = [x['method_version'] for x in succ_200]
	# 过滤请求成功过的接口
	err_500 = [x for x in err_500_list if x['method_version'] not in succ_list]

	err_list = []
	if err_500 or err_200:	#没有错误就跳出程序吧
		err_list.append(err_500)
		err_list.append(err_200)
		err_list.append(succ_200)
		err_list.append(range_list)
		for show in err_list:
			for x in show:
				home = Ints.objects.filter(method_version=x['method_version'])
				x['name'] = home[0].name
				x['type'] = home[0].type
		return err_list
	else:
		sys.exit(0)

def do_contents():
	my_lists = err_list() # 0123分别是500,200非1,200&1,范围列表
	all_num = len(Ints.objects.filter(inuse='1'))
	succ_num = len(my_lists[2])
	err_num = all_num - len(my_lists[2])
	# 品类列表
	type_list = [x['type'] for x in  Ints.objects.filter(inuse='1').values('type').distinct().order_by('type')]
	src_list = my_lists[3]
	summary_list = []
	for type in type_list:
		summ = {
			'type':type,
			'num':len([x for x in src_list if x['type'] == type]),
			'succ':len([x for x in src_list if x['type'] == type and x['log_code'] == '1']),
			'err':len([x for x in src_list if x['type'] == type and x['log_code'] != '1']),
		}
		summary_list.append(summ)

	html_string0 = ("<h4>接口测试报告<hr><font face='微软雅黑'>环境：仿真<br>用例：%s<br>成功：%s<br>失败：%s</font><br><span style='font-weight:normal;'><a href='http://10.113.3.46:8000/admin/fz/ints/' target='_blank'>配置后台</a><a href='http://10.113.3.46:8000/fz/' target='_blank'>监控平台</a></span></h4><table border=1><tr style=\'background-color:cadetblue\'><td>品类</td>" % (all_num, succ_num, err_num))

	html_string0 += ''.join([('<td>%s</td>' % x['type']) for x in summary_list]) + '</tr><tr><td>用例总数</td>'
	html_string0 += ''.join([('<td>%s</td>' % x['num']) for x in summary_list]) + '</tr><tr style=\'background-color:Aquamarine\'><td>成功的</td>'
	html_string0 += ''.join([('<td>%s</td>' % x['succ']) for x in summary_list]) + '</tr><tr style=\'background-color:salmon\'><td>失败的</td>'
	html_string0 += ''.join([('<td>%s</td>' % x['err']) for x in summary_list]) + '</tr></table>'

	# 500的部分

	html_string111 = ""
	if len(my_lists[0]) is 0:
		html_string1 = ''
	else:
	# 获取PID
		html_string11 = ("<h3>【网络错误:%s -- 仿真环境接口服务挂了或网络不稳定，各组点击 URL 链接再确认一下】</h3><table border=1 width=100%%><tr style=\'background-color:cadetblue\'><th>HttpCode</th><th>Type</th><th>Name</th><th>Method</th><th>ProductId</th><th>URL</th></tr>\n\r" % len(my_lists[0]))
		for x in my_lists[0]:
			temp_list = x['url'].split('&')
			for z in temp_list:
				if str(z).startswith('productId'):
					pId = z.split('=')[1]
					break
				else:
					pId = 'null'
		# 拼html
			html_string111 += ("<tr><td style='background-color:yellow'>%s</td><td>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td>%s</td><td><a href='%s'>url</a></td></tr>\n\r" %(x['code'],x['type'], x['name'], x['method_version'], pId, x['url']))
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
		html_string22 = ("<h3>【接口返回错误:%s -- 仿真环境重新验证下】</h3><table border=1 width=100%%><tr style=\'background-color:cadetblue\'><th>HttpCode</th><th>Type</th><th>Name</th><th>Method</th><th>LogCode</th><th>debugMsg</th><th>Error</th><th>Message</th><th>ProductId</th><th>URL</th></tr>\n\r" % len(my_lists[1]))
		for x in my_lists[1]:
			temp_list = x['url'].split('&')
			for z in temp_list:
				if str(z).startswith('productId'):
					pId = z.split('=')[1]
					break
				else:
					pId = 'null'
		# 拼html
			html_string222 += ("<tr><td>%s</td><td>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td style='background-color:salmon'>%s</td><td style='word-break:break-all'>%s</td><td style='word-break:break-all'>%s</td><td>%s</td><td><a href='%s'>url</a></td></tr>\n\r" %( x['code'], x['type'], x['name'], x['method_version'], x['log_code'],x['error'], x['message'], pId, x['url']))
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
		html_string33 = ("<h3>【成功:%s】</h3><table border=1 width=100%%><tr style=\'background-color:cadetblue\'><th>HttpCode</th><th>Type</th><th>Name</th><th>Method</th><th>LogCode</th><th>ProductId</th><th>URL</th></tr>\n\r" % len(my_lists[2]))
		for x in my_lists[2]:
			temp_list = x['url'].split('&')
			for z in temp_list:
				if str(z).startswith('productId'):
					pId = z.split('=')[1]
					break
				else:
					pId = 'null'
		# 拼html
			html_string333 += ("<tr><td style='background-color:Aquamarine'>%s</td><td>%s</td><td>%s</td><td style='word-break:break-all'>%s</td><td style='word-break:break-all'>%s</td><td style='word-break:break-all'>%s</td><td><a href='%s'>url</a></td></tr>\n\r" %(x['code'], x['type'], x['name'], x['method_version'], x['log_code'], pId, x['url']))
		patterns = []
		for line in html_string333.split("\n\r"):
			if line not in patterns:
				patterns.append(line)
		html_string333 = ''.join(patterns)
		html_string3 = html_string33 + html_string333 + "</table>"

	html_string = html_string0 + html_string1 + html_string2 + html_string3
	# print(html_string)
	return html_string

def do_mail():
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	sender = cf.get('mail', 'username')
	receiverlist = [x for x in cf.get('mail', 'FZreceiverlist').split(',')]
	subject = "[仿真接口测试]"
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
	do_contents()
	do_mail()
