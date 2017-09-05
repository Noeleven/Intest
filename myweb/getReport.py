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
# 需要区分自动跑的还是手动跑的 flag=1自动构建flag=0手动构建

today = datetime.datetime.now()
timeStamp = testRecording.objects.filter(flag='1').filter(createTime=today).values('timeStamp', 'Version','groupId').distinct()
for x in timeStamp:
	name = caseGroup.objects.get(id=x['groupId']).groupName
	url = ('http://127.0.0.1:8000/auto/api_report?timeStamp=%s&ver=%s&name=%s' %
		(x['timeStamp'], x['Version'], name))
	
	r = requests.get(url)
