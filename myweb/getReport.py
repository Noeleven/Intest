#!/usr/bin/env python
# -*- coding:utf-8 -*-

import requests
import datetime
import django
import requests, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from automation.models import testRecording
# 循环读取今天所有的timestamp,并去重


today = datetime.datetime.now()
timeStamp = testRecording.objects.filter(createTime=today).values('timeStamp', 'Version').distinct()
for x in timeStamp:
    url = 'http://10.113.1.35:8000/auto/api_report?timeStamp=%s&ver=%s' % (x['timeStamp'], x['Version'])
    r = requests.get(url)
