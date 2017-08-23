#! /bin/bash python3
# -*- coding:utf-8 -*-
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from intest.models import Ints
from cobra.models import Method, Datas


'''
用于将cobra表中的接口更新到intest ints表中
'''

cobra = Method.objects.filter(enabled=1)
ints = Ints.objects.all()

for x in cobra:
    myName = x.method + '&version=' + x.version
    target = [x.method_version for x in ints]
    if myName in target:
        p = Ints.objects.get(method_version=myName)
    else:
        p = Ints(method_version=myName)
    try:
        p.name = x.des
        p.type = x.type
        p.inuse = str(x.enabled)
        rmpL = Datas.objects.filter(method_id=x.id).order_by('-create_time')
        if rmpL:
            p.rpm = int(rmpL[0].rpm)
        p.save()
    except:
        print(myName)
