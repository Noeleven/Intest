#! /bin/bash python3
# -*- coding:utf-8 -*-
# 用于将interface表中的接口更新到intest ints表中
import os
import django
import json
import copy
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from automation.models import *


# 读取用例集对应的用例ID
ids = json.loads(caseGroup.objects.get(id=11).caseID)
# 筛选条件filter对应的分别是在用，android平台，796的用例
# origin = caseList.objects.filter(in_use='1').filter(plantform='Android').filter(version='7.9.6') 
origin = [caseList.objects.get(id=x) for x in ids]
for x in origin:
	b = copy.deepcopy(x)
	b.id = None
	b.des = ''
	b.version = '7.10.0'
	b.save()
# copy 设备
#origin = deviceList.objects.filter(in_use='1').get(id=16)
#for x in range(8):
#    b = copy.deepcopy(origin)
#    b.id = None
#    b.save()
