#!/usr/bin/env python
# -*- coding:utf-8 -*-

import requests
import datetime
import django
import requests, os
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from automation.models import *

'''
自动化每日自动构建发邮件
'''
# 需要区分自动跑的还是手动跑的 flag=1自动构建flag=0手动构建

today = datetime.datetime.now()
timeStamp = testRecording.objects.filter(flag='1').filter(create_time=today).values('timeStamp', 'Version','groupId').distinct()
print(timeStamp)
for x in timeStamp:
	name = caseGroup.objects.get(id=x['groupId']).groupName
	url = ('http://127.0.0.1:8000/auto/sendMail?timeStamp=%s&ver=%s&name=%s' %
		(x['timeStamp'], x['Version'], name))
	r = requests.get(url)


# 来清理下2个月前的老报告、老用例集
date_from = today - datetime.timedelta(days=30)
toClear = allBookRecording.objects.filter(create_time__lt=date_from)
toClear1 = caseGroup.objects.filter(groupName__contains='ReTest').filter(create_time__lt=date_from)
toClear.delete()
toClear1.delete()


'''自动更新用例执行时间'''

# 确认用例范围

caseSource = caseList.objects.filter(in_use='1')
bookSource = allBookRecording.objects.filter(status='success').order_by('-create_time')

def changeTime(aa):
	t = 0
	if 'm' in aa:
		t += int(aa.split('m')[0]) * 60
		if 's' in aa:
			t += int(aa.split('m')[1].split('s')[0])
	elif 's' in aa:
		t = int(aa.split('s')[0])
	else:
		pass
	return t

# 获取每个用例前一次构建成功的时长，转换更新
for x in caseSource:
	timeSource = bookSource.filter(caseID=str(x.id))
	if timeSource:
		buildTime = changeTime(timeSource[0].usedTime)
		x.buildTime = buildTime
		x.save()
