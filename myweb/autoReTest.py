#!/usr/bin/env python
# -*- coding:utf-8 -*-

import requests
import datetime
import django
import jenkins
import json
import requests, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()
from automation.models import *

'''
仅针对自动构建
    自动构建 不会有人cancleJob(没有status=0),不会改变buildNum
testRecording状态说明
    (0-取消；1-进行中；2-重测中,3-完成)
crontab 定时任务
    每天4点到7点 每分钟一次 一共检查180次
'''

# 检查testRecording表中需要重跑的用例集状态 当天的，flag=1 status!=0,3
# dnow = datetime.datetime(2017, 9, 17)
checkRange = testRecording.objects.filter(create_time=datetime.datetime.now()).filter(flag='1').exclude(status='0').exclude(status='3')
if checkRange:
    for x in checkRange:    # 遍历每个测试中用例集
        # 获取相关设备
        deviceNa = myConfig.objects.filter(timeStamp=x.timeStamp)
        deviceL = [deviceList.objects.get(deviceName=y.device) for y in deviceNa]
        deviceNum = len(deviceL)
        vers = deviceL[0].appVersion # 获取平台和版本
        plat = deviceL[0].platformName
        # 检查设备构建状态，全部停的话就可以重构了
        m = 0
        for z in deviceL:
            # print(z.deviceName)
            server = jenkins.Jenkins(z.url, username=z.username, password=z.password)
            # 获取当前设备job的构建状态

            Num = server.get_job_info(z.job_name)['lastBuild']['number']
            # print(Num)
            if server.get_build_info(z.job_name,Num)['actions'][0]['parameters'][0]['value'].split('_')[1] == x.timeStamp:   # 确实是当前任务
                if server.get_build_info(z.job_name,Num)['building']:
                    break
                else:
                    m += 1
            else:
                print(server.get_build_info(z.job_name,Num), x.timeStamp)
                print('时间戳不匹配')
                break

        if m == deviceNum:
            # 全部设备都停止了，状态1开始重构，状态2发邮件
            print('设备已就绪')
            if x.status == '1': # if状态为1在跑，获取错误列表，重新构建一次
                print('开始重跑')
                allBook = allBookRecording.objects.filter(timeStamp=x.timeStamp)
                # get error ids
                errList = allBook.filter(status='danger')
                ids = list(set([int(aa.caseID) for aa in errList]))
                # 跑的的ID
                run_id = [int(y.caseID) for y in allBook]
                # 所有的ID
                all_id = json.loads(caseGroup.objects.get(id=x.groupId).caseID)
                # 求差集，就是没跑的ID
                ids += list(set(all_id).difference(set(run_id)))

                # 新建一个group
                name = 'ReTest' + str(x.timeStamp)
                tg = caseGroup(groupName=name)
                tg.caseID = ids
                tg.des = '失败用例重测'
                tg.status = '1'
                tg.platform = plat
                tg.versionStr = caseVersion.objects.get(versionStr=vers)
                tg.save()

                url = 'http://127.0.0.1:8000/auto/auto_config?vals=%s&type=group&timeStamp=%s' % (tg.id, x.timeStamp)
                r = requests.get(url)
                x.status = '2'  # 标记用例集状态为重测中
                x.save()
            else:   # 如果构建状态完成，发邮件
                print('已重跑完')
                name = caseGroup.objects.get(id=x.groupId).groupName
                url = ('http://127.0.0.1:8000/auto/sendMail?timeStamp=%s&ver=%s&name=%s' %
                (x.timeStamp, x.Version, name))
                # print(url)
#                r = requests.get(url)
        else:   # 有设备没完成，跳出该用例集检查
            continue
