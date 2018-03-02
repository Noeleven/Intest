from django.shortcuts import render,render_to_response
from automation.models import *
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from django.views.decorators.cache import cache_page
from django.template import loader
from decimal import Decimal
import time
import json
import mysql.connector
import datetime
import jenkins
import hashlib
import smtplib
import configparser
import logging
import copy
import random
import requests
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import Header
from email.utils import	parseaddr, formataddr

# Create your views here.
logger = logging.getLogger('auto')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('auto.log')
sh = logging.StreamHandler()
fh.setLevel(logging.INFO)
sh.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s File:%(filename)s Line:%(lineno)s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)

'''version=3.0.0'''
''' TOOLS '''
# controlList对应关系处理，入参 渠道类型channel，版本号ver，增加原版本origin输入
def many_many(request):
	try:
		channel = request.GET['channel']
		ver = request.GET['ver']
		origin = request.GET['origin']
	except:
		back = {'code':'-1','message':'参数错误, channel,ver'}
		return HttpResponse(json.dumps(back, ensure_ascii=False), content_type="application/json")
	else:
		verTrans = {'Android':'0','M':'2','iOS':'1'}
		# 获取指定渠道的clist
		cid = controlList.objects.filter(controlType=verTrans[channel])
		vid = caseVersion.objects.get(versionStr=ver).id
		back = {'code':'1','data':
			{'channel':channel,'sourceVersion':origin, 'originLens':0, 'targetVersion':ver, 'successLens':0, 'allreadyIn':0}}
		succ = err = allin = 0
		# 如果有指定原版本号，重新筛选列表
		if origin:
			nid = [x for x in cid if x.versionStr.filter(versionStr=origin)]
		else:
			nid = cid
		# 遍历添加关系
		for x in nid:
			if x.id in x.versionStr.all():
				allin += 1
			else:
				x.versionStr.add(vid)
				x.save()
				succ += 1

		back['data']['successLens'] = succ
		back['data']['allreadyIn'] = allin
		back['data']['originLens'] = len(nid)
		back = json.dumps(back, ensure_ascii=False)
		return HttpResponse(back, content_type="application/json")

# 修改controlList同步修改用例case接口
def change_case(request):
	try:
		old = request.GET['old']
		new = request.GET['new']
		ver = request.GET['ver']
	except:
		jsonStr = {
			"code": "-1",
			"message":"参数错误 we need 'old,new,ver'"
		}
	else:
		cases = caseList.objects.filter(version=ver).filter(case__contains=old)
		if cases:
			for x in cases:
				x.case = x.case.replace(old,new)
				x.save()
			jsonStr = {
				'code':'1',
				'data':[x.caseName for x in cases],
				'message':"匹配到以上用例"
			}
		else:
			jsonStr = {
				"code": "-2",
				"message":"sorry, no cases find"
			}
	finally:
		result = json.dumps(jsonStr, ensure_ascii=False)
		return HttpResponse(result, content_type="application/json")

# 记录操作历史
def operationSave(ip,message):
	p = history(remoteIp=ip)
	p.operation = message
	p.save()

# 一键停止构建
def stopJenkins(request):
	device = deviceList.objects.filter(in_use='1')
	stopList = []
	for x in device:
		server = jenkins.Jenkins(x.url, username=x.username, password=x.password)
		# 检查队列
		queue = server.get_queue_info()
		if queue:
			for y in queue:
				server.cancel_queue(y['id'])
		# 取消当前构建
		runNum = server.get_running_builds()
		for y in runNum:
			try:
				server.stop_build(x.job_name, int(y['number']))	# 有异常！
				stopList.append(x.deviceName)
			except:
				print(x.deviceName)
	result = {
		'message':'停止jenkins任务完成',
		'deviceList':stopList
	}

	return HttpResponse(json.dumps(result), content_type="application/json")

# 邮件格式化地址
def _format_addr(s):
	name, addr = parseaddr(s)
	return formataddr((Header(name, 'utf-8').encode(), addr))

# 下拉内容
def new_select_list(controlListType, plantform, version='all'):
	# 设置目标元素列表
	plist = {'Android':'0', 'iOS':'1', 'M':'2', 'PC':'3'}
	if version == 'all':
		target_list = controlList.objects.filter(TYPE=controlListType).filter(controlType=plist[plantform]).order_by('controlName')
	else:
		target_list = controlList.objects.filter(TYPE=controlListType).filter(controlType=plist[plantform]).filter(versionStr__versionStr=version).order_by('controlName')

	return target_list

# 编辑翻译，controllist 保存用例，展示用例，展示报告都需要带版本一一对应
def trans_me(aname, type, ptype, ver, road):
	plist = {'android':'0','ios':'1','m':'2'}
	cc = plist[ptype.lower()]
	targetRange = controlList.objects.filter(controlType=cc).filter(TYPE=type).filter(versionStr__versionStr=ver)

	try:
		# 区分中到英还是英到中 toE toC
		if road == 'toE':
			if targetRange.filter(controlName=aname):
				bname = targetRange.get(controlName=aname).controlFiled
			else:
				bname = aname
		else:
			if targetRange.filter(controlFiled=aname):
				bname = targetRange.get(controlFiled=aname).controlName
			else:
				bname = aname
		return bname
	except:
		logger.info('翻译%s' % aname)
		# logger.info('err:%s' % sys.exc_info()[0])

# 报告翻译
def trans_report_list(x):
	plant = caseList.objects.get(id=x['id']).plantform
	ver = caseList.objects.get(id=x['id']).version
	for y in x['jsonStory']:
		y['where'] = trans_me(y['where'], 'where', plant, ver, 'toC')
		y['enterActivity'] = trans_me(y['enterActivity'], 'where', plant, ver, 'toC')
		for z in y['checkString']:
			z['checkType'] = trans_me(z['checkType'], 'checkString', plant, ver, 'toC')
			if z.get('enterActivity'):
				z['enterActivity'] = trans_me(z['enterActivity'], 'where', plant, ver, 'toC')
			if z.get('elementName'):
				z['elementName'] = trans_me(z['elementName'], 'targetName', plant, ver, 'toC')
		for z in y['action']:
			z['actionCode'] = trans_me(z['actionCode'], 'action', plant, ver, 'toC')
			z['target']['targetName'] = trans_me(z['target']['targetName'], 'targetName', plant, ver, 'toC')
	return x

# 重构失败用例
def retry(request):
	ids = request.GET['ids']
	plat = request.GET['plat']
	if ids:
		# 临时保存测试用例集
		name = 'ReTest' + str(int(time.time()))
		tg = caseGroup(groupName=name)
		tg.caseID = ids
		tg.des = '失败用例重测'
		tg.status = '1'
		tg.platform = plat
		tg.versionStr = caseVersion.objects.get(versionStr=request.GET['version'])
		tg.save()
		# 驱动测试
		url = 'http://127.0.0.1:8000/auto/auto_config?vals=%s&type=group' % (tg.id)

		r = requests.get(url)
		# 删除用例集
		tg.status = '0'
		tg.save()
		message = '测试已启动，请关注用例集报告'
	else:
		message = '没有需要测试的case'
	return HttpResponse(message)

# 发邮件
def do_mail(htmlStr):
	html_string = htmlStr
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	sender = cf.get('mail', 'username')
	receiverlist = [x for x in cf.get('mail', 'test_receiver').split(',')]
	subject = "[UI自动化测试报告]"
	smtpserver = cf.get('mail','smtpserver')
	username = cf.get('mail','username')
	password = cf.get('mail','password')
	msg=MIMEText(html_string,'html','utf-8')
	msg['From'] = _format_addr("Admin <%s>" % sender)
	msg['to'] = '%s' % ','.join([_format_addr('<%s>' % x) for x in receiverlist])
	msg['Subject'] = Header("%s" % subject , 'utf-8').encode()
	smtp = smtplib.SMTP()
	smtp.connect(smtpserver)
	smtp.ehlo()
	# smtp.set_debuglevel(1)
	smtp.login(username, password)
	smtp.sendmail(msg['From'],receiverlist,msg.as_string())
	smtp.quit()

# 取消订单
def cancleOrder(request):
	# get config
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	key = cf.get('header', 'key')
	val = cf.get('header', 'sign')
	header = {key:val}
	lvses = [x for x in cf.get('header', 'lvses').split(',')]
	# getOrderList
	data = {'content':''}
	for x in lvses:
		orderNo = []
		getOrder = cf.get('url', 'getOrder') + x
		getOrder1 = cf.get('url', 'getOrder1') + x
		canOrder =cf.get('url', 'canOrder') + x
		r = requests.get(getOrder, headers=header)
		rr = requests.get(getOrder1, headers=header)
		result = r.json()

		try:
			for y in result['data']['list']:
				orderNo.append(y['orderId'])
			result1 = rr.json()
			for y in result1['data']['list']:
				orderNo.append(y['orderId'])
			data['content'] += 'lvsessionid:%s \n\r' % x
			for z in orderNo:
				url = canOrder + '&orderId=%s' % z
				r = requests.get(url, headers=header)
				print(z,r.status_code)
				data['content'] += '订单号%s 取消状态%s\n\r' % (z,r.status_code)

		except:
			print(result)
			data['content'] += 'lvsessionid:%s 订单取消失败\n\r' % x
	# cancle Order

	return HttpResponse(json.dumps(data), content_type="application/json")

'''首页'''
# 导航
def navList():
	# 废弃的
	trashDict = caseList.objects.filter(in_use='0').count()
	# 过期的
	exDict = caseList.objects.filter(in_use='2').count()

	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	Aid = cf.get('automation', 'AgroupID')
	Mid = cf.get('automation', 'MgroupID')
	runId = (Aid + ',' + Mid).split(',')
	groupShow = [x for x in caseGroup.objects.filter(status='1') if str(x.id) in runId]

	nav_list = {
		'trashDict':trashDict,
		'exDict':exDict,
		'groupShow':groupShow
	}
	return nav_list

# 获取设备状态
def getDeviceStatus(request):
	device_list = deviceList.objects.exclude(in_use='0')
	for x in device_list:
		if 'qingyang' in x.deviceName:
			pass
		else:
			try:
				server = jenkins.Jenkins(x.url, username=x.username, password=x.password, timeout=5)
				x.status = [y for y in server.get_running_builds() if y['name'] == x.job_name]	# 执行状态
				x.queue = [y for y in server.get_queue_info() if y['task']['name'] == x.job_name]	# 队列
			except:
				print('获取设备状态出错：%s' % x.deviceName)
				x.broken = ['1']

	return render(request,'getDeviceStatus.html', locals())

# 首页查询
def autoSearch(request):
	# 查询选项
	type_all = caseType.objects.all().order_by('type_name')		# 品类
	user_list = caseUser.objects.filter(userStatus=1).order_by('userName')	# 用户
	versionList = caseVersion.objects.values('versionStr').order_by('-versionStr')
	platform = ['Android', 'iOS', 'M', 'PC']	# 平台
	device_list = deviceList.objects.exclude(in_use='0')	# 设备
	nav_list = navList()	# 导航树
	memGroup = userGroup.objects.all()	# 小组信息

	# 添加用例集
	casegroup = caseGroup.objects.exclude(groupName__contains='ReTest')		#用例集

	return render(request, 'autoSearch.html', locals())

# 动态查询结果返回
def searchResult(request):
	myRequest = dict(request.GET)
	logger.info('search:myRequest %s' % myRequest)
	# 处理下key带[]的问题
	myrequest = {}
	for k,v in myRequest.items():
		if '[]' in k:
			k1 = k.replace('[]','')
			myrequest[k1] = v
	origin = caseList.objects.filter(in_use='1')
	# 对于小组，找出组员，把名字添加到owner列表中即可
	try:
		if myrequest['memGroup']:
			for x in myrequest['memGroup']:
				groupUser = [caseUser.objects.get(id=z).userName for z in  json.loads(userGroup.objects.get(id=x).groupUser)]
				if 'owner' in myrequest:
					myrequest['owner'] += groupUser
				else:
					myrequest['owner'] = groupUser
			del myrequest['memGroup']
	except Exception as e:
		logger.info('search:%s' % e)
	# 每个key值循环取并集，最后取交集
	# logger.info('search:myrequest %s' % myrequest)

	if myrequest:
		if_list = {}
		# 根据条件遍历查询
		for m,n in myrequest.items():
			if_list[m] = []
			for x in n:
				if m == 'caseId':
					if_list[m] += origin.filter(id__contains=x)
				elif m == 'caseName':
					if_list[m] += origin.filter(caseName__contains=x)
				elif m == 'caseType':
					if_list[m] += origin.filter(type_field__type_name__contains=x)
				elif m == 'plantform':
					if_list[m] += origin.filter(plantform__contains=x)
				elif m == 'version':
					if_list[m] += origin.filter(version__contains=x)
				elif m == 'note':
					if_list[m] += origin.filter(des__contains=x)
				elif m == 'owner':
					if_list[m] += origin.filter(owner__contains=x)
				else:
					logger.info('search:未知参数 %s' % m)
					break

		# 现在不一定每个list都有值，需要判断过滤掉没有的值，首先清空没有值的形成一个list
		result = [y for x,y in if_list.items()]

		# 遍历这个list 并求交集
		if result:
			try:
				show_list = set(result[0])
				if result[1:]:
					for x in result[1:]:
						show_list &= set(x)
			except Exception as e:
				logger.info("search:%s %s" % (x,e))
	else:
		show_list = origin

	for x in show_list:
		if x.groupId:
			groupRange = json.loads(x.groupId)
			x.caseGroup = [caseGroup.objects.get(id=y).groupName for y in groupRange]
	return render(request,'searchResult.html', locals())

'''用例管理'''
def delFromCaseGroup(id):
	sourceGroup = caseGroup.objects.filter(groupName__contains='[回归]')
	myGroup = sourceGroup.filter(caseID__contains=int(id))
	for y in myGroup:
		oldCaseId = json.loads(y.caseID)
		if int(id) in oldCaseId:
			oldCaseId.remove(int(id))
			y.caseID = json.dumps(oldCaseId)
			y.save()

# 用例列表
def showCaseList(request):
	device_list = deviceList.objects.exclude(in_use='0')
	nav_list = navList()
	userGroupList = userGroup.objects.all()
	# 检索列表
	show_list = []
	try:
		group = caseGroup.objects.get(id=request.GET['groupId'])
		if group.caseID:
			caseIDS = json.loads(group.caseID)
			for x in caseList.objects.filter(in_use='1'):
				if x.id in caseIDS:
					if x.groupId:
						groupRange = json.loads(x.groupId)
						x.caseGroup = [caseGroup.objects.get(id=y).groupName for y in groupRange]
					show_list.append(x)
	except:
		myType = request.GET['type']
		if myType == 'ex':
			show_list = caseList.objects.filter(in_use='2')
		else:
			show_list = caseList.objects.filter(in_use='0')
		# 用例集信息
		for x in show_list:
			if x.groupId:
				groupRange = json.loads(x.groupId)
				x.caseGroup = [caseGroup.objects.get(id=y).groupName for y in groupRange]

	show_list_id = [x.id for x in show_list]

	return render(request, 'showCaseList.html', locals())

# 构建函数
def goOn(case, device, TimeTime):
	# 预估时间 产出totalTime
	totalTime = 0	# 预估用例总时长
	for x in case:
		if x.buildTime:
			totalTime += x.buildTime
		else:
			totalTime += 60		# 预估每条用例60秒

	# 时间步长，产出mtl步长
	if len(device) == 1:
		mtl = totalTime
	else:
		mtl = totalTime // len(device)

	# 按照时间步长，组装用例列表，平均分配给每台机器
	alList, smList = [], []	# 装用例的 大表 小表
	t, n = 0, 0	# 累积计时,用例条数
	for x in case:
		n += 1
		if x.buildTime:
			t += x.buildTime	# 时间累积
		else:
			t += 60	# 默认用例执行60秒

		if t <= mtl:	# 小于阀值 列表继续追加 循环继续
			smList.append(x.id)
			if n == len(case): # 如果是最后一条用例，也加入大表
				alList.append(smList)
		else:	# 超过阀值，列表生成
			smList.append(x.id)
			alList.append(smList)
			t, smList = 0, []	# 完成后初始化，继续循环
	logger.info('设备%s 构建大表%s' % ([x.deviceName for x in device], alList))

	# 分配用例
	t = 0      # 取用例参考的角标
	caseHome = []      #
	# 遍历设备，执行构建了
	for y in device:
		if (t + 1) > len(alList):	# 当前角标超过大表长度，用例分配完了, 中断
			logger.info('中断%s' % y.deviceName)
			break
		else:	# 如果大表还有
			if y.platformName == 'iOS':
				jsonStr = {
					"deviceName": y.deviceName,    # 设备:ip
					"deviceIP": y.deviceIP,
					"appVersion": y.appVersion,  #   app版本
					"platformVersion": y.platformVersion,    # 操作系统版本
					"platformName": y.platformName,  # iOS
					"webDriverAgentUrl": y.webDriverAgentUrl,  # iOS
					"bundleId": y.bundleId,  # iOS
					"udid": y.udid,  # iOS
					"appPackage": y.appPackage,
					"timeStamp": TimeTime,
					"testCaseSQL":alList[t]
					}
			else:
				jsonStr = {
					"APPIUMSERVERSTART": y.APPIUMSERVERSTART,
					"appiumServicePath": y.appiumServicePath,
					"appiumServicePort": y.appiumServicePort,
					"appVersion": y.appVersion,
					"deviceName": y.deviceName,
					"deviceIP":y.deviceIP,
					"platformVersion": y.platformVersion,
					"platformName": y.platformName,
					"lvsessionid": y.lvsessionid,
					"timeout": y.timeWait,
					"adbPort": y.adbPort,
					"appPackage": y.appPackage,
					"appLaunchActivity": y.appLaunchActivity,
					"timeStamp": TimeTime,
					"testCaseSQL":alList[t]
					}

			# save myConfig
			p = myConfig(device=y.deviceName)
			p.timeStamp = TimeTime
			p.caseStr = json.dumps(jsonStr, ensure_ascii=False)
			p.save()

			# 驱动jenkins
			server = jenkins.Jenkins(y.url, username=y.username, password=y.password)
			job_name = y.job_name
			try:
				server.build_job(job_name, {'deviceName':y.deviceName + '_' + TimeTime})
				# logger.info('假设我驱动成功了')
			except:
				# 失败了记录一下
				logger.info('用例%s构建失败，设备%s连接超时' % (alList[t], y.deviceName))
			else:
				build_number = server.get_job_info(job_name)['lastBuild']['number']
				# 存储构建记录 reportList
				time_case = str(TimeTime) + '_' + ('_').join([str(x) for x in alList[t]])

				pp = reportsList(timeStamp=time_case)
				if build_number != 0:
					pp.buildNUM = '#' + str(build_number + 1)
					pp.status = str(server.get_build_info(job_name, build_number)['building'])

				if y.platformName == 'iOS':
					pp.reportURL = ('http://10.113.1.193:8001/%s/report.html' % (build_number + 1))
				else:
					pp.reportURL = ("/auto/reportDetail?timeStamp=" + "%s" % TimeTime)

				pp.deviceName = deviceList.objects.get(deviceName=y.deviceName)
				pp.save()
		t += 1

	return mtl

# 构建用例，生成配置，吊起Jenkins，存储报告，多个用例/用例集同时构建，前端循环调取，后端不处理
def auto_config(request):
	# 确认参数 timeStamp
	try:
		if request.GET['timeStamp']:
			TimeTime = request.GET['timeStamp']
		else:
			TimeTime = str(int(time.time())) + str(random.randint(100000,999999))
	except:
		TimeTime = str(int(time.time())) + str(random.randint(100000,999999))

	try:
		if request.GET['device']:
			mydevice = request.GET['device']	# 设备
	except:
		mydevice = ''

	try:
		if request.GET['isDay'] == 'yes':
			myisDay = request.GET['isDay']	# isDay 自动构建
		else:
			myisDay = 'no'
	except:
		myisDay = 'no'

	try:
		if request.GET['type'] == 'group':
			mytype = request.GET['type']	# 类型
		else:
			mytype = 'single'
	except:
		mytype = 'single'

	# 确认用例
	try:
		myid = request.GET['vals']    # 用例或集合的ID must
	except:
		code = '-3'
		message = '参数错误'
	else:
		if myid:
			cases = []
			if mytype == 'group':	# 用例集
				for x in myid.split(','):
					group = caseGroup.objects.filter(status=1).filter(id=x)
					if group:
						mygroup = group[0]
						cases += [caseList.objects.get(id=x) for x in json.loads(mygroup.caseID.replace("'",'')) if caseList.objects.filter(in_use='1').filter(id=x)]

						# 用例集构建存储
						tt = testRecording(timeStamp=TimeTime)
						tt.Version = mygroup.versionStr.versionStr
						tt.groupId = mygroup.id
						if myisDay == 'yes':		# yes表示自动构建，0表示手工构建
							tt.flag = '1'
						else:
							tt.flag = '0'
						tt.status = '1'	# 构建用例添加状态 1进行中 2重测中 0取消 3完成
						tt.save()
						logger.info('用例集testRecording预存完毕')
					else:
						logger.info('用例集%s不存在' % x)
			else:
				noExist = []
				for x in myid.split(','):
					if caseList.objects.filter(in_use='1').filter(id=x):
						cases.append(caseList.objects.get(id=x))
					else:
						noExist.append(x)
				if noExist:
					logger.info('这些用例不存在了 %s\n' % noExist)

			# logger.info('用例为%s' % cases)
			if cases:
				message = ''
				timeList = []
				# 组装设备平台清单, 产出allDiv
				allCom = set([(x.version + '_' + x.plantform) for x in cases])
				allDiv = {}		# 清单，以v_p为key，以用例为value
				for com in allCom:
					allDiv[com] = []

				for x in cases:
					# 设备平台清单赋值
					v_p = x.version + '_' + x.plantform
					allDiv[v_p].append(x)
				logger.info('组装清单%s\n' % allDiv.keys())
				# 确认设备，产出设备和用例
				if mydevice:	# 有指定
					mydev = deviceList.objects.filter(deviceName=mydevice)
					if mydev:
						device = mydev[0]
						myv_p = device.appVersion + '_' + device.platformName
						# 未命中的，回头打印出来
						misCase = []
						for x, y in allDiv.items():
							if x != myv_p:
								misCase += y
						if misCase:
							message += '部分用例与所选设备不匹配:%s' % [x.id for x in misCase]

						hitCase = allDiv[myv_p]
						timeList.append(goOn(hitCase, [device,], TimeTime))
					else:
						message += '%s该设备不存在' % mydevice
				else:
					# 遍历清单，分别执行job
					for k,v in allDiv.items():
						ppla = k.split('_')[1]
						vver = k.split('_')[0]
						device = deviceList.objects.filter(in_use='1').filter(platformName=ppla).filter(appVersion=vver).order_by('-deviceName')

						if device:
							timeList.append(goOn(v, device, TimeTime))
						else:
							message += '用例:%s, 没有可用设备\n\r<br/>' % [x.id for x in v]

				# 每次构建返回一个执行最长时间
				if timeList:
					preTime = max(timeList)
					message += '装弹完毕，准备发射, 预计需要%s分钟<br/>' % (round(preTime/60,1))
					message += "<a class='btn btn-sm btn-default' href='/auto/reportDetail?timeStamp=%s' target=_blank>测试报告</a><br/>" % TimeTime
					code = '1'
				else:
					code = '-1'
			else:
				code = '-1'
				message = '没有可用用例'
		else:
			code = '-1'
			message = '没有用例，over'
	finally:
		logger.info(message)
		result = {'code':code, 'message':message, 'timeStamp': TimeTime}
		return HttpResponse(json.dumps(result), content_type="application/json")

# jenkins调用接口，返回接口配置
def auto_response(request):
	deviceNa = request.GET['deviceName'].split('_')[0]
	try:
		times = request.GET['deviceName'].split('_')[1]
		jsonStr = myConfig.objects.filter(timeStamp=times).get(device=deviceNa).caseStr
		return HttpResponse(jsonStr, content_type="application/json")
	except:
		try:
			jsonStr = myConfig.objects.filter(device=deviceNa).order_by('-create_time')[0].caseStr
			return HttpResponse(jsonStr, content_type="application/json")
		except:
			return HttpResponse('No Such Device')

# 删除用例
def auto_del(request):
	try:
		id = request.GET['id'].split(',')
		for x in id:
			myCase = caseList.objects.get(id=x)
			myCase.in_use = '0'
			myCase.groupId = ''	# 废弃后移除所有所在用例集标记
			myCase.save()
			# 废弃用例同时在用例集中删除
			delFromCaseGroup(x)
		data = 'success'
	except KeyError as e:
		data = ('ERR:删除失败，请联系管理员查看\n:%s' % e)
	finally:
		return HttpResponse(data)

# 置为过期
def auto_ex(request):
	try:
		id = request.GET['id'].split(',')
		for x in id:
			myCase = caseList.objects.get(id=x)
			# 0是废弃 1是在用 2是过期
			myCase.in_use = '2'
			myCase.save()
		data = 'success'
	except KeyError as e:
		data = ('操作失败\n:%s' % e)
	finally:
		return HttpResponse(data)

# copy用例
def auto_copy(request):
	try:
		id = request.GET['id']
		a = caseList.objects.get(id=id)
		b = copy.deepcopy(a)
		b.id = None
		b.des = ''
		# b.case_tag = ''
		b.groupId = ''
		b.save()
		data = "复制成功，用例ID%s" % b.id
	except KeyError as e:
		data = '复制失败,囧'
	finally:
		return HttpResponse(data)

# 新增用例页面
def addCase(request):
	# 各选项list
	type_list = caseType.objects.all().order_by('type_name')
	user_list = caseUser.objects.filter(userStatus=1).order_by('userName')
	versionList = caseVersion.objects.order_by('-versionStr')
	plat = ['Android', 'iOS', 'M', 'PC']
	nav_list = navList()
	# 为了校验用例名
	casenames = [x.caseName for x in caseList.objects.filter(in_use='1')]

	try:
		groupId = request.GET['groupId']
		caseGroupList = caseGroup.objects.filter(id=groupId)
	except:
		caseGroupList = caseGroup.objects.exclude(groupName__contains='ReTest')

	return render(request, 'addCase.html', locals())

# 新增用例保存，预设json结构
def saveCaseBaseInfo(request):
	try:
		# 取参数
		caseName = request.GET['caseName']
		csType = caseType.objects.get(type_name=request.GET['type'])
		caseVersion = request.GET['version']
		casePlantform = request.GET['plantform']
		caseStatus = request.GET['canUse']
		caseDes = request.GET['caseDes']
		owner = request.GET['owner']
		caseStatus = '1' if caseStatus=='use' else '0'
		groupId = []
		try:
			groupId.append(int(request.GET['groupId']))
		except:
			logger.debug('没有选用例集')

		# 初始化caseJson结构
		if casePlantform == 'iOS':
			defaultCase = '{"jsonStory":[{"des":"", "index":1, "value":"", "action":"click", "typeText":""}], "caseType":"" ,"caseTag":""}'
		else:
			defaultCase = '[{"enterActivity":"","index":1,"storyDescription":"","action":[{"target":{"targetName":""},"actionCode":"click","behaviorPara":{"inputValue":""},"needWait":true}],"where":"","checkString":[{"checkType":"","elementName":"","expeted":""}]}]'
		# 存用例
		p = caseList(caseName=caseName)
		# p.type_field = caseType.objects.get(id=caseType.objects.filter(type_field=csType)[0].id)
		p.type_field = csType
		p.plantform = casePlantform
		p.version = caseVersion
		p.case = defaultCase
		p.des = caseDes
		p.in_use = caseStatus
		p.owner = owner
		p.groupId = json.dumps(groupId)
		p.save()

		# 给用例集里加id
		try:
			group = caseGroup.objects.get(id=groupId[0])
			if group.caseID:
				oldCaseId = json.loads(group.caseID)
			else:
				oldCaseId = []
			oldCaseId.append(p.id)
			group.caseID = json.dumps(oldCaseId)
			group.save()
		except:
			logger.debug('没有选用例集')

		return HttpResponseRedirect("/auto/caseConfirm/%s?New=yes" % p.id)
	except TypeError as e:
		logger.info('新建保存用例出错了 %s' % e)
		return

# 确认用例版本
def caseConfirm(request, id):
	case = caseList.objects.get(id=id)
	versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
	plant = ['Android','iOS','M']
	nav_list = navList()
	try:
		isNew = request.GET['New']
	except:
		isNew = 'no'


	try:
		forzt = request.GET['zt']
	except:
		return render(request, 'caseConfirm.html', locals())
	else:
		print(request.GET)
		return render(request, 'caseConfirm4zt.html', locals())

# 新增用例action
def editCaseStep(request):
	id = request.GET['caseID']
	version = request.GET['version']
	myPlantform = request.GET['platform']
	# 反向解析json存入表单 首先从DB获取json字符串，并解析成数据类型
	if caseList.objects.filter(id=id).exists():
		json_dict = caseList.objects.filter(id=id).values()[0]
		try:
			# 基本信息确认
			nav_list = navList()
			json_dict['type_field_id'] = caseType.objects.get(id=json_dict['type_field_id']).type_name	# 品类
			# 用例集
			caseGroupList = caseGroup.objects.exclude(groupName__contains='ReTest')
			if json_dict['groupId']:
				myGroup = []
				for x in json.loads(json_dict['groupId']):
					if caseGroup.objects.filter(id=x).exists():
						myGroup.append(caseGroup.objects.get(id=x).id)
					else:
						# 顺便维护下用例
						nowCase = caseList.objects.get(id=id)
						oldGroup = json.loads(nowCase.groupId)
						oldGroup.remove(x)
						nowCase.groupId = json.dumps(oldGroup)
						nowCase.save()
			# 下拉列表
			type_all = caseType.objects.all().order_by('type_name')
			type_list = [x for x in type_all]
			user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
			versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
			plant = ['Android','iOS','M']
			# case_tag = caseTag.objects.filter(type_field__type_name=json_dict['type_field_id']) | caseTag.objects.filter(type_field__type_field='other')
			# case_tag.distinct()

			# 元素 起点 终点列表 iOS没有
			targetname = []
			elementname = []
			# 是否新建的用例，用于判断是否走向自关闭页面close.html
			isNew = request.GET['isNew']
			# 解析caseJSON，虽然改了平台和版本，但是caseJSON还是不变的，因此翻译时需要注意区分，原有的还是caseJSON里的，下拉列表才是new的
			if myPlantform == 'Android' or myPlantform == 'M':
				where = []
				enterActivity = []
				wait_list = ['等待','不等待']
				BgStep = json.loads(json_dict['case'])
				for x in BgStep:
					x['enterActivity'] = trans_me(x['enterActivity'],'where',json_dict['plantform'], json_dict['version'], 'toC')
					x['where'] = trans_me(x['where'],'where',json_dict['plantform'], json_dict['version'], 'toC')
					where.append(x['where'])
					enterActivity.append(x['enterActivity'])
					ai = ci = 1
					for y in x['action']:
						y['target']['targetName'] = trans_me(y['target']['targetName'],'targetName',json_dict['plantform'], json_dict['version'], 'toC')
						targetname.append(y['target']['targetName'])
						y['actionCode'] = trans_me(y['actionCode'],'action',json_dict['plantform'], json_dict['version'], 'toC')
						if y['needWait'] == True:
							y['needWait'] = '等待'
						else:
							y['needWait'] ='不等待'
						y['index'] = str(x['index']) + '-' + str(ai)
						ai += 1
					for y in x['checkString']:
						y['elementName'] = trans_me(y['elementName'],'targetName',json_dict['plantform'], json_dict['version'], 'toC')
						elementname.append(y['elementName'])
						y['index'] = str(x['index']) + '-' + str(ci)
						ci += 1
						y['checkType'] = trans_me(y['checkType'],'checkString',json_dict['plantform'], json_dict['version'], 'toC')
					control_list = new_select_list('action', myPlantform, version)
					where_list = new_select_list('where', myPlantform, version)
					target_list = new_select_list('targetName', myPlantform, version)
					checkType_list = new_select_list('checkString', myPlantform)
				return render(request, 'editCaseStep.html',locals())
			else:
				BgStep = json.loads(json_dict['case'])['jsonStory']
				ai = 1
				for x in BgStep:
					x['index'] = str(ai)
					ai += 1
					x['action'] = trans_me(x['action'],'action',json_dict['plantform'], json_dict['version'], 'toC')
					targetname.append(trans_me(x['value'],'targetName',json_dict['plantform'], json_dict['version'], 'toC'))
					control_list = new_select_list('action', myPlantform, version)
					target_list = new_select_list('targetName', myPlantform, version)
				return render(request, 'editCaseStepIos.html', locals())
		except AttributeError as e:
			logger.info("editCaseStep:%s" % e)
	else:
		logger.info("用例id %s 不存在" % id)
		return HttpResponseRedirect('/auto/addCase')

# 编辑保存
def saveCaseStep(request):
	id = request.POST.get('id')
	my_form = dict(request.POST)
	print(my_form)
	case_obj = caseList.objects.get(id=id)
	try:
		caseName = my_form.get('caseName')[0]
		csType = caseType.objects.get(id=my_form.get('type')[0])
		caseVersion = my_form.get('version')[0]
		casePlantform = my_form.get('platform')[0]
		caseStat = my_form.get('canUse')[0]
		caseDes = my_form.get('caseDes')[0]
		owner = my_form.get('owner')[0]
		myGroup = my_form.get('groupId')
		# myTag = my_form.get('caseTag')
	except TypeError as e:
		logger.info('获取用例信息出错： %s' % e)

	if caseStat == 'use':
		caseStatus = '1'
	elif caseStat == 'nouse':
		caseStatus = '0'
	elif caseStat == 'ex':
		caseStatus = '2'
	else:
		caseStatus = '3'	# 未知

	# 统计有多少大步
	bigstep = len(set([x.split('-')[0] for x in my_form.get('index_step')]))
	#起始下标
	if casePlantform == 'Android' or casePlantform == 'M':
		json_home = []
		startIndex = expendIndex = 0
		for bgSub in range(bigstep):
			# 大步字典
			bgElement = {
				"storyDescription":my_form.get('storyDescription')[bgSub],
				"index":bgSub + 1,
				"where":trans_me(my_form.get('where')[bgSub], 'where', casePlantform, caseVersion, 'toE'),
				'action':[],
				"enterActivity":trans_me(my_form.get('enterActivity')[bgSub], 'where', casePlantform, caseVersion, 'toE'),
				"checkString":[],
				}
			# 预期列表，处理checkString
			expendlist = [x for x in my_form.get('index_expend') if x.split('-')[0] == str(bgSub + 1)]

			for smExpend in range(expendIndex, expendIndex + len(expendlist)):
				cType = my_form.get('checkType')[smExpend]
				eName = my_form.get('elementname')[smExpend]
				expendDict = {
					"checkType": trans_me(cType, 'checkString', casePlantform, caseVersion, 'toE'),
					"expeted": my_form.get('expeted')[smExpend],
					"elementName": trans_me(eName, 'targetName', casePlantform, caseVersion, 'toE'),
				}
				bgElement['checkString'].append(expendDict)

			# 动作列表['1-1','1-2','2-1']
			steplist = [x for x in my_form.get('index_step') if x.split('-')[0] == str(bgSub + 1)]
			# 循环小步下标，获取数值
			for smSub in range(startIndex, startIndex + len(steplist)):
				actionDict = {
					"actionCode": trans_me(my_form.get('actionCode')[smSub], 'action', casePlantform, caseVersion, 'toE'),
					"behaviorPara":{
						"inputValue":my_form.get('inputValue')[smSub],
						},
					"target": {
						"targetName": trans_me(my_form.get('targetName')[smSub], 'targetName', casePlantform, caseVersion, 'toE'),
						},
					"needWait": (bool(1) if my_form.get('needWait')[smSub] == '等待' else bool(0)),
					}
				bgElement['action'].append(actionDict)
			# 下标自增，供下一大步作为起始下标
			startIndex += len(steplist)
			expendIndex += len(expendlist)
			json_home.append(bgElement)
		my_case = json.dumps(json_home, ensure_ascii=False)
	elif casePlantform == 'iOS':
		json_home = {'jsonStory':[], 'caseType':csType}
		for bgSub in range(bigstep):
			# 大步字典
			myInput = my_form.get('inputValue')[bgSub] # iOS要求输入框增加\n
			if myInput:
				if '\n' in myInput:
					pass
				else:
					myInput += ' \n'
			bgElement = {
				"des":my_form.get('storyDescription')[bgSub],
				"index":bgSub + 1,
				'action':trans_me(my_form.get('actionCode')[bgSub], 'action', casePlantform, caseVersion, 'toE'),
				'typeText':myInput,
				'value':trans_me(my_form.get('targetName')[bgSub], 'targetName', casePlantform, caseVersion, 'toE'),
				}
			json_home['jsonStory'].append(bgElement)
		my_case = json.dumps(json_home, ensure_ascii=False)
	else:
		logger.info('编辑保存用例 平台版本：%s' % casePlantform)

	# 存储DB
	p = case_obj
	p.case = my_case
	p.caseName = caseName
	# p.type_field = caseType.objects.get(id=caseType.objects.filter(type_field=csType)[0].id)
	p.type_field = csType
	p.plantform = casePlantform
	p.version = caseVersion
	p.owner = owner
	p.des = caseDes
	if myGroup:
		p.groupId = json.dumps([int(x) for x in myGroup])
		# 同步保存到用例集
		for x in myGroup:
			group = caseGroup.objects.get(id=x)
			oldCaseID = json.loads(group.caseID)
			if p.id not in oldCaseID:
				oldCaseID.append(p.id)
				group.caseID = json.dumps(oldCaseID)
				group.save()
	else:
		# 用例集删除用例
		if p.groupId:
			oldGroupId = json.loads(p.groupId)
			for x in oldGroupId:
				group = caseGroup.objects.get(id=x)
				oldCaseID = json.loads(group.caseID)
				if p.id in oldCaseID:
					oldCaseID.remove(p.id)
					group.caseID = json.dumps(oldCaseID)
					group.save()
		# 用例删除用例集ID
		p.groupId = json.dumps([])
	p.in_use = caseStatus
	p.modify_time = datetime.datetime.now()
	p.save()
	message = '提交成功'

	# 判断是否新建过来的
	isNew = request.GET['isNew']
	if isNew == 'yes':
		try:
			ggroupid = [x for x in myGroup]	# 用例可能存在多个用例集中，也可能没有用例集，有仅返回第一个用例集，没有返回search页面
			return HttpResponseRedirect('/auto/showCaseList?groupId=%s' % ggroupid[0])
		except:
			return HttpResponseRedirect('/auto')
	else:
		return render(request,'close.html',locals())

# 用例列表标签/小组
def tagSearch(request):
	memGroupId = request.POST['memGroupId']	# 获取小组ID
	caseIDS = request.POST.getlist('show_list_id[]')

	origin = [caseList.objects.get(id=x) for x in caseIDS]	# 获取用例
	groupUser = [caseUser.objects.get(id=x).userName for x in json.loads(userGroup.objects.get(id=memGroupId).groupUser)]	# 小组成员name
	result = [x for x in origin if x.owner in groupUser]

	for x in result:
		if x.groupId:
			groupRange = json.loads(x.groupId)
			x.caseGroup = [caseGroup.objects.get(id=y).groupName for y in groupRange]
	return render_to_response('tagSearch.html', locals())

'''### 测试报告 ###'''
# 获取测试报告中成功和失败的函数
def getSuccess(timeTarget):
	allbook = allBookRecording.objects.filter(timeStamp=timeTarget)	# 获取所有用例结果
	err_list, pass_list = [], []
	cases = []

	if allbook:
		all_id = allbook.values('caseID').distinct()	# 获取本次测试用例ID
		allNum = len(all_id)	# 获取本次测试总数
		pass_list = allbook.filter(status='success')	# 成功的记录
		pass_id = [int(x.caseID) for x in pass_list]	# 成功的用例ID
		err_list = allbook.filter(status='danger')	# 初始错误记录

		for x in err_list:
			if int(x.caseID) in pass_id:	# 错误id在成功的里面,剔除
				err_list = err_list.exclude(id=x.id)
			if err_list.filter(caseID=x.caseID).count() > 1:	# 错误列表中的重复，留一个
				thisID = [y.id for y in err_list.filter(caseID=x.caseID)]
				for y in thisID[1:]:
					err_list = err_list.exclude(id=y)
	else:
		allNum = 0

	return allNum, pass_list, err_list, allbook

# 当日报表邮件接口
def sendMail(request):
	try:
		timeTarget = request.GET['timeStamp']
		vver = request.GET['ver']
		name = request.GET['name']
	except:
		jsonStr = {
			"code": "-2",
			"message":"参数错误"
		}
	else:
		source = getSuccess(timeTarget)	# 获取用例成功失败列表，运行数量
		cases = source[3]	# 所有成功失败列表
		pass_list = source[1]	# 成功记录列表
		err_list = source[2]	# 错误记录列表

		if cases:
			# 计算测试时长
			time = cases.values('create_time')
			sTime = time.order_by('create_time')[0]['create_time']
			eTime = time.order_by('-create_time')[0]['create_time']
			m,s = divmod((eTime - sTime).seconds, 60)
			testTime = '%s分%s秒' % (m,s)

			# 各项指标
			myUrl = ("http://10.115.1.73:8000/auto/reportDetail?timeStamp=%s" % timeTarget)	# 报告URL
			groupNum = len(json.loads(caseGroup.objects.get(groupName=name).caseID))	# 用例集用例总数
			allNum = source[0]	# 跑了的总数
			passNum = len(pass_list)	# 成功的数量
			failNum = len(err_list)	# 失败的数量
			warnNum = groupNum - allNum
			passRate = round(((passNum / allNum) * 100), 2)	# 成功率

			# email标头
			html_string0 = "<h3>UI自动化报告</h3><h4>[用例集名称:%s]</h4><br><table border=1><tbody><tr><td>版本</td><td>%s</td><td>测试时长</td><td>%s</td></tr><tr><td>用例总数</td><td>%s</td><td>成功率</td><td>%s %%</td></tr><tr><td>本次测试用例数</td><td>%s</td><td>异常</td><td>%s</td></tr><tr><td>通过</td><td>%s</td><td>失败</td><td>%s</td></tr></tbody></table><hr><span><h4><a href=%s target=_blank><font color='DarkSalmon' size='4'>看报告请点点点点点点点点我!!!</font></a></span></h4>" % (name, vver, testTime, groupNum, passRate, allNum, warnNum, passNum, failNum, myUrl)
			html_string1 = ""
			html_string3 = "</table>"

			# 列出错误用例
			if err_list:
				html_string1 = "<h3>错误列表</h3><table border=1 width=100%><tr style='background-color:cadetblue'><th>ID</th><th>品类</th><th>用例名称</th><th>状态</th><th>耗时</th><th>创建人</th></tr>\n\r"
				html_string2 = ""
				build_list = []

				for x in err_list:	# 完善用例集信息
					sou = json.loads(x.testResultDoc)
					if x.status == 'danger':
						status = '失败'
					else:
						status = '成功'
					tmp = {
						'id':x.caseID,
						'type':caseList.objects.get(id=sou['id']).type_field.type_name,
						'caseName':x.caseName,
						'status':status,
						'usedTime':x.usedTime,
						'user':sou['owner'],
					}
					build_list.append(tmp)

				build_list = sorted(build_list, key = lambda x:x['user'])	# 根据人名排序
				for tmp in build_list:	# 填充html
					html_string2 += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n\r" % (tmp['id'], tmp['type'], tmp['caseName'], tmp['status'], tmp['usedTime'], tmp['user']))
			else:
				html_string2 = "<p>恭喜, 全部通过</p>"

			html_string = html_string0 + html_string1 + html_string2 + html_string3
			logger.info('do html ok')
			do_mail(html_string)
			logger.info('do mail ok')
			jsonStr = {
				"code": "1",
				"message":'发送成功'
			}
		else:
			mess = '%s 没有用例报告' % timeTarget
			jsonStr = {
				"code": "-1",
				"message":mess
			}
	finally:
		result = json.dumps(jsonStr, ensure_ascii=False)
		return HttpResponse(result, content_type="application/json")

# 测试报告列表
def reportList(request):
	# 基本信息
	device_list = deviceList.objects.exclude(in_use='0')
	nav_list = navList()

	# 用例集报告
	groupReports = testRecording.objects.order_by('-modify_time').values('timeStamp', 'Version', 'create_time', 'groupId', 'flag').distinct()[:20]

	for x in groupReports:
		x['url'] = '/auto/reportDetail?timeStamp=' + x['timeStamp']
		try:
			x['name'] = caseGroup.objects.get(id=x['groupId']).groupName
		except:
			x['name'] = '未知'
		try:
			x['create_time'] = reportsList.objects.filter(timeStamp__contains=x['timeStamp'])[0].create_time
		except IndexError as e:
			logger.info('test_list error:%s' % e)

	return render(request, 'reportList.html',locals())

# 报告详情
def reportDetail(request):
	timeTarget = request.GET['timeStamp']
	source = getSuccess(timeTarget)	# 获取测试结果记录 0是测试总数，1是成功列表 2是失败列表 3是所有记录
	rec = source[3]	# 所有记录
	if rec:
		pass_list = source[1]	# 成功列表
		err_list = source[2]	# 错误列表
		allNum = source[0]	# 测试总数
		passNum = len(pass_list)	# 成功数量
		failNum = len(err_list)	# 失败数量
		passRate = round(((passNum / allNum) * 100), 2)	# 成功率

		# 获取测试时长
		myTime = rec.values('create_time')
		sTime = myTime.order_by('create_time')[0]['create_time']	# 第一个记录时间
		eTime = myTime.order_by('-create_time')[0]['create_time']	# 最后一个记录时间
		if (eTime - sTime).seconds > 0:
			m,s = divmod((eTime - sTime).seconds, 60)
			testTime = '%s分%s秒' % (m,s)
		else:	# 单用例只有一个记录时间，但是有运行时长
			testTime = rec[0].usedTime

		# 给列表添加报告信息，顺便获取测试的版本、平台
		plats,vers = [],[]
		for x in pass_list:
			doc = json.loads(x.testResultDoc)
			x.runAt = doc['runAt']
			x.storySize = doc['storySize']
			x.caseTestTime = doc['caseTestTime']
			x.info = caseList.objects.get(id=doc['id'])
			plats.append(doc["platformName"])
			vers.append(x.info.version)
		for x in err_list:
			doc = json.loads(x.testResultDoc)
			x.runAt = doc['runAt']
			x.storySize = doc['storySize']
			x.caseTestTime = doc['caseTestTime']
			x.info = caseList.objects.get(id=doc['id'])
			plats.append(doc["platformName"])
			vers.append(x.info.version)
		plat = set(plats) # 获取平台去重
		version = set(vers)	# 获取版本去重

		# 获取错误ID，传给手动重跑函数
		err_ids = [int(x.caseID) for x in err_list]
		# 获取一个平台和版本作为新用例集的参数，前提要求用例集不要存在不同版本和不同平台
		vver = list(version)[-1]
		platt = list(plat)[0]

		# 展示没跑的、废弃的
		if testRecording.objects.filter(timeStamp=timeTarget):
			groupID = testRecording.objects.filter(timeStamp=timeTarget)[0].groupId	# 获取用例集ID
			group = caseGroup.objects.get(id=groupID)	# 获取用例集obj
			cases = pass_list | err_list	# 所有记录
			run_list = [int(x.caseID) for x in cases]	# 所有记录的ID
			all_list = json.loads(group.caseID.replace("'",''))	# 用例集内用例的ID
			totalNum = len(all_list)
			nono_list = [caseList.objects.get(id=x) for x in list(set(all_list).difference(set(run_list)))]	# 没记录的用例
			no_list = [x for x in nono_list if x.in_use == '1']	# 没记录的用例里在用没跑的
			delList = [x for x in nono_list if nono_list and x.in_use != '1']	# 没记录的用例里废弃/过期用例
			err_ids += [x.id for x in no_list]	# 没跑的id也加进重跑列表
		else:
			no_list, delList = [], []

	try:
		forzt = request.GET['zt']
	except:
		return render_to_response('reportDetail.html', locals())
	else:
		return render_to_response('reportDetail4zt.html', locals())

# 获取测试进度
def testProgress(request):
	try:
		tt = request.GET['tt']
	except:
		result = {'code': '-3', 'message': '参数错误'}
	else:
		if tt:
			alList = reportsList.objects.filter(timeStamp__contains=tt)	# 记录在案的测试结果

			if alList:
				# 获取所有记录在案的测试ID
				allID = []
				for x in alList:
					allID += x.timeStamp.split('_')[1:]
				distinctID = set(allID)
				# 考虑到废弃，统计实际会记录的数量
				if distinctID:
					trushNum = len([x for x in distinctID if caseList.objects.get(id=x).in_use != '1'])
					preNum = len(distinctID) - trushNum
				else:
					preNum = len(distinctID)

				# 实际记录的数量
				nowNum = len(set([x.caseID for x in allBookRecording.objects.filter(timeStamp=tt)]))

				# passRate
				recordNum = allBookRecording.objects.filter(timeStamp=tt)
				passNum = recordNum.filter(status='success')
				if passNum.count() == 0:
					passRate = 0
				else:
					passRate = passNum.count() * 100 // recordNum.count()
				# 对于重跑的情况 肯定会大于100
				code = '2'
				if nowNum == 0:
					num = 0
					status = message = '未完成'
				else:
					if preNum == 0:
						num = 100
						message = '没有能够测试的用例'
						status = '未完成'
					else:
						num = round(((nowNum / preNum) * 100), 2)
						if num >= 100:
							num = 100
							code = '1'
							status = message = '已完成'
						else:
							status = message = '未完成'

				result = {'progress':num, 'message': message, 'preNum':preNum, 'code': code, 'nowNum': nowNum, 'passRate':passRate,'status':status}
			else:
				result = {'progress':100, 'message': '没找到测试记录', 'code': '-1'}
		else:
			result = {'progress':100, 'message': '缺少参数', 'code': '-1'}

	return HttpResponse(json.dumps(result), content_type="application/json")

# 设备构建历史
def getDevBuildHistory(request):
	# 基本信息
	dev = request.GET['device']
	nav_list = navList()

	testResults = []
	x = deviceList.objects.get(deviceName=dev)
	server = jenkins.Jenkins(x.url, username=x.username, password=x.password)
	rList = reportsList.objects.filter(deviceName__deviceName=x.deviceName).order_by('-create_time')[:10]    #结果列表
	x.buildLog = []

	# 完善每条构建记录信息
	for y in rList:
		# 若果用例被删除，那就查不到了
		mycase = []
		for z in y.timeStamp.split('_')[1:]:
			try:
				zz = caseList.objects.get(id=z)  # 检查该用例在不在
				zzz = str(zz.id) + ' ' + zz.caseName
			except:
				zzz = '用例已被删除'
			mycase.append(zzz)
		myDict = {}
		myDict['build_case'] = mycase
		myDict['create_time'] = y.create_time.strftime('%Y-%m-%d %H:%M:%S')
		myDict['buildNUM'] = y.buildNUM
		myDict['reportURL'] = y.reportURL
		try:
			myDict['status'] = str(server.get_build_info(x.job_name, int(y.buildNUM[1:]))['result'])
		except:
			myDict['status'] = 'queue'
		x.buildLog.append(myDict)

	return render(request, 'getDevBuildHistory.html',locals())

# 获取用例报告
def snapshot(request):
	bid = request.GET['id']
	book = trans_report_list(json.loads(allBookRecording.objects.get(id=bid).testResultDoc))
	return render(request, 'snapshot.html', locals())

# 报告筛选
def reportFilter(request):
	myrequest = dict(request.GET)
	timeTarget = myrequest['timeT'][0]
	user = myrequest['user'][0]
	Acases = allBookRecording.objects.filter(timeStamp=timeTarget).filter(testResultDoc__contains='platformName":"Android"')
	Mcases = allBookRecording.objects.filter(timeStamp=timeTarget).filter(testResultDoc__contains='platformName":"M"')
	Aerr_list = []
	Apass_list = []
	Merr_list = []
	Mpass_list = []
	if user:
		for x in Acases:
			cid = json.loads(x.testResultDoc)['id']
			case = caseList.objects.filter(in_use='1').get(id=cid)
			if user in case.owner:
				if x.status == 'danger':
					logger.info('reportFilter %s' % x.caseName)
					Aerr_list.append(json.loads(x.testResultDoc))
				else:
					Apass_list.append(json.loads(x.testResultDoc))
		for x in Mcases:
			cid = json.loads(x.testResultDoc)['id']
			case = caseList.objects.filter(in_use='1').get(id=cid)
			if user in case.owner:
				if x.status == 'danger':
					logger.info('reportFilter %s' % x.caseName)
					Merr_list.append(json.loads(x.testResultDoc))
				else:
					Mpass_list.append(json.loads(x.testResultDoc))
	else:
		Aerr_list = [json.loads(x['testResultDoc']) for x in Acases.filter(status='danger').values('testResultDoc')]
		Apass_list = [json.loads(x['testResultDoc']) for x in Acases.filter(status='success').values('testResultDoc')]
		Merr_list = [json.loads(x['testResultDoc']) for x in Mcases.filter(status='danger').values('testResultDoc')]
		Mpass_list = [json.loads(x['testResultDoc']) for x in Mcases.filter(status='success').values('testResultDoc')]
	Apass_list = trans_report_list(Apass_list)
	Aerr_list = trans_report_list(Aerr_list)
	Mpass_list = trans_report_list(Mpass_list)
	Merr_list = trans_report_list(Merr_list)
	return render_to_response('report_ajax.html', locals())

''' 用例集 '''
# 添加用例集
def autoMakeGroup(request):
	# try:
	# 目标用例
	ids = [int(x) for x in request.GET['id'].split(',')]
	myPlat = caseList.objects.get(id=ids[0]).plantform
	groupName = request.GET['groupName']
	# 获取用例集的version，存储包含的用例
	if caseGroup.objects.filter(groupName=groupName).exists():
		group = caseGroup.objects.get(groupName=groupName)	# obj
		groupVersion = group.versionStr.versionStr	# str 7.8.0
		oldCase = json.loads(group.caseID)
		newCase = list(set(oldCase + ids))
		group.caseID = json.dumps(newCase)
		group.platform = myPlat
		group.save()
	else:
		group = caseGroup(groupName=groupName)	# create
		groupVersion = request.GET['groupVersion']
		if groupVersion:
			group.versionStr = caseVersion.objects.get(versionStr=groupVersion)	# 外键存对象
		else:
			# 前端限制了版本必填，万一出现，则给个最新版本
			group.versionStr = caseVersion.objects.order_by('-versionStr')[0]
		group.caseID = json.dumps(ids)
		group.platform = myPlat
		group.save()

	# create tagId, 由于同一个版本可能有多个用例集，使用version会查出多个用例集，故使用用例集name，对应在编辑用例集时，改名字时同步更改tag就好了
	# if caseTag.objects.filter(tagName=groupName).exists():
	# 	tagId = caseTag.objects.get(tagName=groupName).id
	# else:
	# 	newTag = caseTag(tagName=groupName)
	# 	newTag.type_field = caseType.objects.get(type_field='other')
	# 	newTag.save()
	# 	tagId = caseTag.objects.get(tagName=groupName).id

	# 给所选用例增加标签id，增加用例集id
	cases = [caseList.objects.get(id=x) for x in ids]
	for x in cases:
		# 检查tag，有了追加，没有新建
		# if x.case_tag:
		# 	oldTag = json.loads(x.case_tag)
		# 	if tagId not in oldTag:
		# 		oldTag.append(tagId)
		# 		x.case_tag = json.dumps(oldTag)
		# else:
		# 	x.case_tag = json.dumps([tagId])
		# 检查用例集ID是否存在，没有新建
		newGroupId = caseGroup.objects.get(groupName=groupName).id	# 前端应该控制下用例集名称不可重复
		if x.groupId:
			oldGroupIdList = json.loads(x.groupId)
			if newGroupId not in oldGroupIdList:
				oldGroupIdList.append(newGroupId)
				x.groupId = json.dumps(oldGroupIdList)
		else:
			x.groupId = json.dumps([newGroupId])
		x.save()

	data = 'success'
	# except Exception as e:
	# 	logger.info('添加用例集报错：%s' % e)
	# 	data = 'failed'

	return HttpResponse(data)

# 用例集列表页
def groupList(request):
	casegroup = caseGroup.objects.exclude(des='失败用例重测').filter(status='1')
	for x in casegroup:
		x.num = len(json.loads(x.caseID))
	nav_list = navList()
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	Aid = cf.get('automation', 'AgroupID')
	Mid = cf.get('automation', 'MgroupID')

	return render(request, 'groupList.html', locals())

# 用例集编辑
def groupEdit(request):
	groupID = request.GET.get('groupID')
	# 需要获取group信息、所有用例名信息、当前用例集用例名信息
	groupInfo = caseGroup.objects.get(id=groupID)
	gourpIDS = json.loads(groupInfo.caseID)
	allCase = caseList.objects.values('id', 'caseName', 'plantform', 'version', 'des', 'owner','in_use').order_by('caseName')
	for x in allCase:
		if x['id'] in gourpIDS:
			x['sta'] = 'checked'
		else:
			x['sta'] = 'unchecked'
		if x['in_use'] == '1':
			x['in_use'] = '在用'
		else:
			x['in_use'] = '废弃'
	nav_list = navList()
	versionList = caseVersion.objects.all()
	platform = {'Android', 'iOS', 'M', 'PC'}
	logger.debug('%s' % allCase[:10])
	return render(request, 'groupEdit.html', locals())

# 用例集保存
def groupSave(request):
	# 用例id列表
	if request.POST.get('groupListBox'):
		myCaseId = [int(x.split('-')[1]) for x in request.POST.getlist('groupListBox')]
	else:
		myCaseId = []

	# 保存用例集信息
	groupId = int(request.POST.get('ID'))
	group = caseGroup.objects.get(id=groupId)
	# 获取用例集前后信息
	oldName = group.groupName
	oldVer = group.versionStr.versionStr
	oldCase = group.caseID
	oldPlat = group.platform
	newName = request.POST.get('groupName')
	newPlat = request.POST.get('plat')
	newVer = request.POST.get('version')
	newCase = myCaseId
	# 保存其他信息
	group.des = request.POST.get('des')
	group.platform = newPlat
	group.versionStr = caseVersion.objects.get(versionStr=newVer)
	group.groupName = newName
	group.caseID = json.dumps(myCaseId)
	group.save()

	# 检查老名字有没有，新名字有没有，都没有新建
	# if caseTag.objects.filter(tagName=newName).exists():
	# 	tagId = caseTag.objects.get(tagName=newName).id	# 当前用例集的tagId, 有可能用例集已经建好，没有此标签，手动加一个
	# elif caseTag.objects.filter(tagName=oldName).exists():
	# 	oldTag = caseTag.objects.get(tagName=oldName)
	# 	oldTag.tagName = newName
	# 	oldTag.save()
	# 	tagId = oldTag.id
	# else:
	# 	newTag = caseTag(tagName=newName)
	# 	newTag.type_field = caseType.objects.get(type_field='other')
	# 	newTag.save()
	# 	tagId = newTag.id
	# 遍历包含当前用例集id、版本tag的用例，去除包含
	todoCase = caseList.objects.filter(groupId__contains=groupId)
	# | caseList.objects.filter(case_tag__contains=tagId)	# 合并用例组合
	todoCase.distinct()	# 去重

	for x in todoCase:
		if x.groupId:
			oldGroupId = json.loads(x.groupId)
			if groupId in oldGroupId:
				oldGroupId.remove(groupId)
				x.groupId = json.dumps(oldGroupId)
		# if x.case_tag:
		# 	oldTagId = json.loads(x.case_tag)
		# 	if tagId in oldTagId:
		# 		oldTagId.remove(tagId)
		# 		x.case_tag = json.dumps(oldTagId)
		x.save()

	# 遍历目标用例id列表，新增用例集id，标签
	myCase = [caseList.objects.get(id=x) for x in myCaseId]
	for x in myCase:
		# if x.case_tag:
		# 	oldCaseTag = json.loads(x.case_tag)
		# 	if tagId not in oldCaseTag:
		# 		oldCaseTag.append(tagId)
		# 		x.case_tag = json.dumps(oldCaseTag)
		# else:
		# 	x.case_tag = json.dumps([tagId])
		if x.groupId:
			oldGroupId = json.loads(x.groupId)
			if groupId not in oldGroupId:
				oldGroupId.append(groupId)
				x.groupId = json.dumps(oldGroupId)
		else:
			x.groupId = json.dumps([groupId])
		x.save()

	# 记录历史
	oldMess = '用例集名称:%s | 版本:%s | 平台:%s | 用例数量:%s\n\r用例明细:%s' % (oldName,oldVer,oldPlat,len(json.loads(oldCase)),oldCase)
	newMess = '用例集名称:%s | 版本:%s | 平台:%s | 用例数量:%s\n\r用例明细:%s' % (newName,newVer,newPlat,len(newCase),newCase)
	if oldMess != newMess:
		message = ''
		message += '原:\n\r' + oldMess + '\n\r新:\n\r' + newMess
		ip = request.META['REMOTE_ADDR']
		operationSave(ip,message)

	return HttpResponseRedirect('/auto/groupList')

# 用例集操作历史
def getGroupHistory(request):
	# 先取一个月的数据
	date_to = datetime.datetime.now()
	date_from = date_to - datetime.timedelta(days=30)
	result = history.objects.filter(operationTime__range=(date_from,date_to))
	return render(request, 'getGroupHistory.html', locals())

'''一周报表'''
# 报告详情页
def autoReport(request):
	nav_list = navList()
	# 版本用例趋势 M站只有一个用例集，永远都是一条线
	source = caseGroup.objects.filter(status='1').filter(groupName__contains='[回归]')
	ver = list(set([x.versionStr.versionStr for x in source]))
	ver.sort(key=lambda x:tuple(int(v) for v in x.split('.')))
	vers = ver[-5:]
	now = vers[-1]
	# APP趋势 业务覆盖
	result = []
	# 业务覆盖
	area = []
	typeLi = []
	for v in ['Android', 'iOS', 'M']:
		tmp = {'name':v, 'result':[]}
		areatmp = {'name':v, 'result':[]}
		n = 1
		for x in vers:
			# 确定用例集范围
			if v == 'M':
				backage = source.filter(platform=v)
			else:
				backage = source.filter(platform=v).filter(versionStr__versionStr=x)
			if backage:
				value = {
					'version':x,
					'value':len(json.loads(backage[0].caseID)),
					}
				# 确认业务覆盖情况
				if n == 5:
					cases = [caseList.objects.get(id=x) for x in json.loads(backage[0].caseID) if caseList.objects.filter(id=x)]
					typeList = list(set([x.type_field.type_name for x in cases]))
					typeLi += typeList
					for x in typeList:
						areaValue = {
							'type':x,
							'value':len([z for z in cases if z.type_field.type_name == x]),
							}
						areatmp['result'].append(areaValue)
			else:
				value = {
					'version':x,
					'value':0,
					}
			tmp['result'].append(value)
			n += 1

		result.append(tmp)
		area.append(areatmp)

	# 资源分布情况
	resource = []
	dever = [x['appVersion'] for x in deviceList.objects.filter(in_use='1').values('appVersion').distinct()]
	for x in dever:
		plat = deviceList.objects.filter(in_use='1').filter(appVersion=x)[0].platformName
		tmp = {
			'name':plat + ' | ' + x,
			'value':deviceList.objects.filter(in_use='1').filter(appVersion=x).count()
		}
		resource.append(tmp)

	# M站用例趋势
	today = datetime.datetime.now()
	weekAgo = datetime.datetime.now() - datetime.timedelta(days=7)
	dayList,dayNum = [],[]
	for x in range(7):
		da = weekAgo + datetime.timedelta(days=x)
		daa = da.strftime("%Y-%m-%d")
		dayList.append(daa)
		nuu = caseList.objects.filter(plantform='M').filter(in_use='1').filter(groupId__contains='8').filter(create_time__lt=da).count() # 仅保留在用的
		dayNum.append(nuu)

	return render(request, 'autoReport.html', locals())

# 获取构建次数，错误率，成功率，top5
def getBuildTimes(request):
	date_from = datetime.datetime.now()
	date_to = date_from - datetime.timedelta(days=7)
	source = allBookRecording.objects.filter(create_time__range=(date_to, date_from))
	# 构建次数
	num = source.values('timeStamp').distinct().count()
	result = {'count':num}

	# auto成功率 区分AD M iOS, 仅自动构建
	timeList = [x['timeStamp'] for x in testRecording.objects.filter(flag='1').filter(create_time__range=(date_to, date_from)).values('timeStamp').distinct()]	# 近一周 自动构建的所有timeStamp

	Apass, Aall, Mpass, Mall, Ipass, Iall, errList, top, errTypeRe = [], [], [], [], [], [], [], [], []
	for x in source:
		if x.timeStamp in timeList:	# 仅统计自动构建的各平台通过率
			if request.GET['data'] == '1':
				plat = json.loads(x.testResultDoc)['platformName']
				if plat == 'Android':
					Aall.append(x)
					if x.status == 'success':
						Apass.append(x)
				elif plat == 'M':
					Mall.append(x)
					if x.status == 'success':
						Mpass.append(x)
				else:
					Iall.append(x)
					if x.status == 'success':
						Ipass.append(x)
			else:	# 错误用例统计
				if x.status == 'danger':
					errList.append(x.caseID)

	if request.GET['data'] == '1':	# 通过率计算
		if Apass:
			result['Arate'] = str(round(len(Apass) * 100 / len(Aall), 2)) + '%'
		if Mpass:
			result['Mrate'] = str(round(len(Mpass) * 100 / len(Mall), 2)) + '%'
		if Ipass:
			result['Irate'] = str(round(len(Ipass) * 100 / len(Iall), 2)) + '%'

		return HttpResponse(json.dumps(result), content_type="application/json")
	else:	# TOP5 用例计算
		finalTop = set(errList)
		for x in finalTop:
			try:
				theCase = caseList.objects.get(id=x)
			except:
				continue
			else:
				tmp = {
					'id':theCase.id,
					'caseName':theCase.caseName,
					'type':theCase.type_field.type_name,
					'plat':theCase.plantform,
					'ver':theCase.version,
					'times':errList.count(x),
				}
				top.append(tmp)
		top.sort(key=lambda x:x['times'])
		allFailedNum = len(errList)
		topTable = top[-5:]

		return render(request, 'autoReportAjax.html', locals())


'''小组管理'''
# 小组列表
def memGroupList(request):
	memGroup = userGroup.objects.all()
	nav_list = navList()
	for x in memGroup:
		if x.groupUser:
			x.count = len(json.loads(x.groupUser))
		else:
			x.count = 0
	return render(request,'memGroupList.html',locals())

# 小组编辑
def memGroupEdit(request):
	allMem = caseUser.objects.filter(userStatus=1)
	nav_list = navList()
	try:
		groupID = request.GET['groupId']
	except KeyError as e:
		pass
	else:
		if groupID:
			groupID = request.GET['groupId']
			group = userGroup.objects.get(id=groupID)
			if group.groupUser:
				gourpIDS = json.loads(group.groupUser)
				print(gourpIDS)
				for x in allMem:
					if str(x.id) in gourpIDS:
						x.status = 'checked'
					else:
						x.status = 'unchecked'

	return render(request,'memGroupEdit.html',locals())

def memGroupSave(request):
	try:
		groupID = request.POST.get('groupID')
		if groupID:
			r = userGroup.objects.get(id=groupID)
		else:
			r = userGroup(groupName=request.POST.get('groupName'))
	except:
		r = userGroup(groupName=request.POST.get('groupName'))
	finally:
		r.groupName = request.POST.get('groupName')
		r.des = request.POST.get('des')
		if request.POST.get('groupListBox'):
			groupUser = request.POST.getlist('groupListBox')
			r.groupUser = json.dumps(groupUser)
		else:
			r.groupUser = ''
		r.save()
	return HttpResponseRedirect('/auto/memGroupList')
