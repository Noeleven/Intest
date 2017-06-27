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
# 循环读取今天所有的timestamp,并去重


today = datetime.datetime.now()
timeStamp = testRecording.objects.filter(createTime=today).values('timeStamp', 'Version','groupId').distinct()
for x in timeStamp:
	name = caseGroup.objects.get(id=json.loads(x['groupId'])[0]).groupName
	url = ('http://127.0.0.1:8000/auto/api_report?timeStamp=%s&ver=%s&name=%s' %
		(x['timeStamp'], x['Version'], name))
	print(name)
	r = requests.get(url)
