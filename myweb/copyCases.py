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

# 读取用例，循环并生成新的case
origin = caseList.objects.filter(in_use='1').filter(plantform='Android')
for x in origin:
    b = copy.deepcopy(x)
    b.version = '7.9.6'
    b.id = None
    b.save()
