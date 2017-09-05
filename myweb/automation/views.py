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


### TOOLS ###
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


# 一键停止构建
def stop_jenkins(request):
	# server = [
	# 	{'url':'http://10.115.1.74:8080'},
	# 	{'url':'http://10.115.1.77:8080'},
	# 	{'url':'http://10.115.1.78:8080'},
	# 	{'url':'http://10.115.1.75:8080'},
	# 	{'url':'http://10.115.1.79:8080'},
	# 	]
	# job_name = 'AbortAndroidUITest'
	# for x in server:
	# 	try:
	# 		server = jenkins.Jenkins(x['url'])
	# 		server.build_job(job_name)
	# 	except:
	# 		pass
	device = deviceList.objects.filter(in_use='1')
	stopList = []
	for x in device:
		server = jenkins.Jenkins(x.url, username=x.username, password=x.password)
		server.disable_job(x.job_name)
		time.sleep(1)
		server.enable_job(x.job_name)
		stopList.append(x.deviceName)

	result = {
		'message':'停止jenkins任务完成',
		'deviceList':stopList
	}
	return HttpResponse(json.dumps(result), content_type="application/json")

# 邮件格式化地址
def _format_addr(s):
	name, addr = parseaddr(s)
	return formataddr((Header(name, 'utf-8').encode(), addr))

# 导航
def navList():
	nav_list = []
	for x in caseType.objects.values('id','type_name'):
		tmpDict = {
			'type':x['type_name'],
			'num':caseList.objects.filter(type_field=x['id']).filter(in_use='1').count(),
		}
		nav_list.append(tmpDict)
	# 废弃的
	trashDict = {
		'type':'废弃',
		'num':caseList.objects.filter(in_use='0').count(),
	}
	# 过期的
	exDict = {
		'type':'过期',
		'num':caseList.objects.filter(in_use='2').count(),
	}
	nav_list.append(trashDict)
	nav_list.append(exDict)
	return nav_list

# 下拉内容
def new_select_list(controlListType, plantform, version='all'):
	# 设置目标元素列表
	plist = {'Android':'0','iOS':'1','M':'2'}
	if version == 'all':
		target_all = controlList.objects.filter(TYPE=controlListType).filter(controlType=plist[plantform]).order_by('controlName')
	else:
		target_all = controlList.objects.filter(TYPE=controlListType).filter(controlType=plist[plantform]).filter(versionStr__versionStr=version).order_by('controlName')
	target_list = [x for x in target_all]
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
		logger.info('err:%s' % sys.exc_info()[0])


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
	td = caseGroup.objects.get(groupName=name)
	url = 'http://127.0.0.1:8000/auto/auto_config?vals=%s&type=group&isDay=' % (td.id)

	r = requests.get(url)
	# 删除用例集
	td.status = '0'
	td.save()
	message = '测试已启动，请关注用例集报告'
	return HttpResponse(message)

def myprint(mess):
	print("[%s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mess))

### 各PAGE ###
# 导航list
def auto_list(request):
	try:
		my_type = request.GET['my_type']
	except:
		my_type='全部'
	else:
		if my_type == "全部":
			show_list = caseList.objects.filter(in_use='1')
		elif my_type == '废弃':
			show_list = caseList.objects.filter(in_use='0')
		elif my_type == '过期':
			show_list = caseList.objects.filter(in_use='2')
		else:
			try:
				type_id = caseType.objects.filter(type_name=my_type)[0].id
			except:
				show_list = ''
			else:
				show_list = caseList.objects.filter(in_use='1').filter(type_field=type_id)
	finally:
		device_list = deviceList.objects.exclude(in_use='0')
		for x in device_list:
			try:
				server = jenkins.Jenkins(x.url, username=x.username, password=x.password)
				x.status = [y for y in server.get_running_builds() if y['name'] == x.job_name]	# 执行状态
				x.queue = [y for y in server.get_queue_info() if y['task']['name'] == x.job_name]	# 队列
			except:
				x.broken = ['1']
		nav_list = navList()
		tag_list = caseTag.objects.filter(type_field__type_name=my_type)
		return render(request, 'auto_list.html', locals())

# 编辑保存
def auto_edit_save(request, id):
	my_form = dict(request.GET)
	logger.info(my_form)
	case_obj = caseList.objects.get(id=id)
	try:
		caseName = my_form.get('caseName')[0]
		csType = caseType.objects.get(type_name=my_form.get('type')[0]).type_field
		caseVersion = my_form.get('version')[0]
		casePlantform = my_form.get('platform')[0]
		caseStat = my_form.get('canUse')[0]
		caseDes = my_form.get('caseDes')[0]
		owner = my_form.get('owner')[0]
		myTag = my_form.get('caseTag')
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
		json_home = {'jsonStory':[], 'caseType':csType, 'caseTag':myTag}
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
	# logger.debug(('*' * 20 + '\n' + '%s') % my_case)
	# 存储DB
	p = case_obj
	p.case = my_case
	p.caseName = caseName
	p.type_field = caseType.objects.get(id=caseType.objects.filter(type_field=csType)[0].id)
	p.plantform = casePlantform
	p.version = caseVersion
	p.owner = owner
	p.des = caseDes
	if myTag:
		p.case_tag = json.dumps([caseTag.objects.get(tagName=x).id for x in myTag])
	p.in_use = caseStatus
	p.modify_time = datetime.datetime.now()
	p.save()
	# 判断动作
	return HttpResponseRedirect("/auto/auto_list?my_type=%s" % my_form.get('type')[0])

# 构建用例，生成配置，吊起Jenkins，存储报告
def auto_config(request):
	# 取参数, isDay 和 device看情况传
	ids = request.GET['vals'].split(',')    # 获取用例或集合的ID
	mytype = request.GET['type']	# 标识用例还是用例集

	# get caseGroup
	cGroup = []
	message = ''
	if mytype == 'group':
		for x in ids:
			groupVersion = caseGroup.objects.get(id=x).versionStr.versionStr
			groupPlat = caseGroup.objects.get(id=x).platform
			mydevice = deviceList.objects.filter(in_use='1').filter(platformName=groupPlat).filter(appVersion=groupVersion).order_by('-deviceName')
			if mydevice:
				cases = [caseList.objects.get(id=x) for x in json.loads(caseGroup.objects.get(id=x).caseID)]
				tmp = {
					'version':groupVersion,
					'devices':mydevice,
					'cases':cases,
					'groupId':x,
				}
				cGroup.append(tmp)
			message += '用例集%s 构建中 </br>' % x
	else:
		device = deviceList.objects.filter(deviceName=request.GET['device'])
		cases = [caseList.objects.get(id=x) for x in ids]
		if device[0].platformName == 'M':
			tmp = {
				'version':'',
				'devices':device,
				'cases':cases,
			}
			cGroup.append(tmp)
			message += '用例构建中 </br>'
		else:
			caseVersion = set([caseList.objects.get(id=x).version for x in ids])
			deviceVer = device[0].appVersion
			for x in caseVersion:
				if x == deviceVer:
					tmp = {
						'version':x,
						'devices':device,
						'cases':[y for y in cases if y.version == deviceVer],
					}
					cGroup.append(tmp)
					message += '用例构建中</br>'
				else:
					notIds = [y.id for y in cases if y.version== x]
					if notIds:
						message += '所选用例id%s未构建, 其版本为%s，与所选设备%s版本不同 </br>' % (notIds, x, device[0].deviceName)

	# myprint(cGroup)
	if cGroup:
		for x in cGroup:
			# 算步长
			if len(x['devices']) == 0:
				print('用例id %s 没有可用设备' % [y.id for y in x['cases']])
				continue
			elif len(x['devices']) == 1:
				mdl = len(x['cases'])
			else:
				if len(x['cases']) >= len(x['devices']):
					if (len(x['cases']) % len(x['devices'])) == 0:
						mdl = len(x['cases']) // len(x['devices'])
					else:
						if (len(x['cases']) % len(x['devices'])) >= (len(x['devices']) // 2):
							mdl = len(x['cases']) // len(x['devices']) + 1
						else:
							mdl = len(x['cases']) // len(x['devices'])
				else:
					mdl = 1
			logger.info('用例数量:%s 设备数量:%s 步长:%s 设备名%s' % (len(x['cases']), len(x['devices']), mdl, x['devices']))

			# 确定唯一标志
			TimeTime = str(int(time.time())) + str(random.randint(100000,999999))

			# 用例集存testRecording
			if mytype == 'group':
				tt = testRecording(timeStamp=TimeTime)
				tt.Version = x['version']
				tt.groupId = x['groupId']
				isDay = request.GET['isDay']	# yes表示自动构建，空表示手工构建
				if isDay == 'yes':
					tt.flag = '1'
				else:
					tt.flag = '0'
				tt.save()

			# 标记开始和结束、步长标志
			start = end = numb = 0
			for y in x['devices']:
				end += mdl
				numb += 1
				if start < len(x['cases']):
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
							}

					# 具体分配用例 end + 步长 超过就不要在分了，结束
					if end > len(x['cases']):
						jsonStr["testCaseSQL"] = [xx.id for xx in x['cases'][start:]]
					elif (end + mdl) > len(x['cases']) and numb == len(x['devices']):
						jsonStr["testCaseSQL"] = [xx.id for xx in x['cases'][start:]]
					else:
						jsonStr["testCaseSQL"] = [xx.id for xx in x['cases'][start:end]]

					# save myConfig
					p = myConfig(device=y.deviceName)
					p.timeStamp = TimeTime
					p.caseStr = json.dumps(jsonStr, ensure_ascii=False)
					p.save()

					# 驱动jenkins
					server = jenkins.Jenkins(y.url, username=y.username, password=y.password)
					job_name = y.job_name
					# try:
					# server.build_job(job_name, {'deviceName':y.deviceName,'timeStamp':TimeTime})  # 执行构建
					server.build_job(job_name, {'deviceName':y.deviceName + '_' + TimeTime})
					build_number = server.get_job_info(job_name)['lastBuild']['number']
						# build_number = 0
					# except:
					# 	build_number = 0
					# 	logger.info('获取buildNumber失败, 人工置为%s' % build_number)
					# finally:
					# 存储构建记录 reportList
					if end >= len(x['cases']):
						time_case = str(TimeTime) + '_' + ('_').join([str(z.id) for z in x['cases'][start:]])
					else:
						time_case = str(TimeTime) + '_' + ('_').join([str(z.id) for z in x['cases'][start:end]])
					pp = reportsList(timeStamp=time_case)
					if build_number != 0:
						pp.buildNUM = '#' + str(build_number + 1)
						pp.status = str(server.get_build_info(job_name, build_number)['building'])

					if y.platformName == 'iOS':
						pp.reportURL = ('http://10.113.1.193:8001/%s/report.html' % (build_number + 1))
					else:
						pp.reportURL = ("/auto/api_report_page?timeStamp=" + "%s" % TimeTime)

					pp.deviceName = deviceList.objects.get(deviceName=y.deviceName)
					pp.save()

					start += mdl
	else:
		message += '没有用例执行'
	if message:
		myprint(message)

	return HttpResponse(message)

# jenkins调用接口，返回接口配置
def auto_response(request):
	try:
		deviceNa = request.GET['deviceName'].split('_')[0]
		times = request.GET['deviceName'].split('_')[1]
		print(deviceNa, times)
		jsonStr = myConfig.objects.filter(timeStamp=times).get(device=deviceNa).caseStr
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
			myCase.save()
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
		cName = request.GET['cName']
		if cName:
			if caseList.objects.filter(caseName=cName):
				data = '0' # 重复名称
			else:
				a = caseList.objects.get(id=id)
				b = copy.deepcopy(a)
				b.id = None
				b.des = ''
				b.caseName = cName
				b.save()
				data = '1' # 用例名OK
		else:
			data = '3' # 没输入
	except KeyError as e:
		data = '2'
		logger.info('ERR:复制失败，请联系管理员查看.\n%s' % e)
	finally:
		return HttpResponse(data)

# 新增用例页面
def new_add(request):
	# 各选项list
	type_all = caseType.objects.all().order_by('type_name')
	case_tag = caseTag.objects.all()
	type_list = [x for x in type_all]
	# 为了校验用例名
	casenames = [x['caseName'] for x in caseList.objects.filter(in_use='1').values('caseName')]
	# 用户list 和 版本list
	user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
	versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
	plant = ['Android','iOS','M']
	nav_list = navList()
	return render(request, 'new_add.html', locals())

# 新增用例保存，预设json结构
def new_save(request):
	try:
		caseName = request.GET['caseName']
		csType = caseType.objects.get(type_name=request.GET['type']).type_field
		caseVersion = request.GET['version']
		casePlantform = request.GET['plantform']
		caseStatus = request.GET['canUse']
		caseDes = request.GET['caseDes']
		owner = request.GET['owner']
		myTag = request.GET.getlist('caseTag')
		print(request.GET,myTag)

		caseStatus = '1' if caseStatus=='use' else '0'
		if casePlantform == 'iOS':
			defaultCase = '{"jsonStory":[{"des":"", "index":1, "value":"", "action":"click", "typeText":""}], "caseType":"" ,"caseTag":""}'
		else:
			defaultCase = '[{"enterActivity":"","index":1,"storyDescription":"","action":[{"target":{"targetName":""},"actionCode":"click","behaviorPara":{"inputValue":""},"needWait":true}],"where":"","checkString":[{"checkType":"","elementName":"","expeted":""}]}]'
		# 存储DB
		p = caseList(caseName=caseName)
		p.type_field = caseType.objects.get(id=caseType.objects.filter(type_field=csType)[0].id)
		p.plantform = casePlantform
		p.version = caseVersion
		p.case = defaultCase
		p.des = caseDes
		p.in_use = caseStatus
		p.owner = owner
		p.case_tag = json.dumps([caseTag.objects.get(tagName=x).id for x in myTag])
		p.save()
		# 获取当前用例ID
		myID = caseList.objects.filter(plantform=casePlantform).filter(caseName=caseName).values('id')[0]['id']
		return HttpResponseRedirect("/auto/ver_confirm/%s" % myID)
	except TypeError as e:
		logger.info('新建保存用例出错了 %s' % e)
		return

# 确认版本
def ver_confirm(request, id):
	case = caseList.objects.get(id=id)
	versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
	plant = ['Android','iOS','M']
	nav_list = navList()
	return render(request, 'ver_confirm.html', locals())

# 新增用例action
def new_edit(request):
	id = request.GET['caseID']
	version = request.GET['version']
	myPlantform = request.GET['platform']
	# 反向解析json存入表单 首先从DB获取json字符串，并解析成数据类型
	if caseList.objects.filter(id=id).exists():
		json_dict = caseList.objects.filter(id=id).values()[0]
		try:
			# 基本信息确认
			json_dict['type_field_id'] = caseType.objects.get(id=json_dict['type_field_id']).type_name	# 品类
			if json_dict['case_tag']:
				myTag = [caseTag.objects.get(id=x).tagName  for x in json.loads(json_dict['case_tag'])]	# 标签

			# 下拉列表
			type_all = caseType.objects.all().order_by('type_name')
			type_list = [x for x in type_all]
			user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
			versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
			plant = ['Android','iOS','M']
			case_tag = caseTag.objects.filter(type_field__type_name=json_dict['type_field_id'])
			# print(json_dict['type_field_id'])
			nav_list = navList()

			# 元素 起点 终点列表 iOS没有
			targetname = []
			elementname = []

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
				return render(request, 'new_edit.html',locals())
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
				return render(request, 'ios_edit.html', locals())
		except AttributeError as e:
			logger.info("new_edit:%s" % e)
	else:
		logger.info("用例id %s 不存在" % id)
		return HttpResponseRedirect('/auto/new_add')

# 测试报告页
def test_list(request):
	# 右侧对应品类的用例列表
	device_list = deviceList.objects.exclude(in_use='0')
	nav_list = navList()
	groupReports = testRecording.objects.order_by('-createTime').values('timeStamp', 'Version', 'createTime', 'groupId', 'flag').distinct()[:20]
	for x in groupReports:
		x['url'] = '/auto/api_report_page?timeStamp=' + x['timeStamp']
		try:
			x['name'] = caseGroup.objects.get(id=x['groupId']).groupName
		except:
			# x['name'] = caseGroup.objects.get(id=json.loads(x['groupId'])[0]).groupName
			x['name'] = '未知'
		try:
			x['createTime'] = reportsList.objects.filter(timeStamp__contains=x['timeStamp'])[0].create_time
		except IndexError as e:
			logger.info('test_list error:%s' % e)
	return render(request, 'test_list.html',locals())

# 首页查询
def auto_search(request):
	# 需要品类、二品类、版本、所属人、平台
	type_all = caseType.objects.all().order_by('type_name')
	type_list = [x for x in type_all]
	user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
	versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
	plant = ['Android','iOS','M']
	device_list = deviceList.objects.exclude(in_use='0')
	for x in device_list:
		try:
			server = jenkins.Jenkins(x.url, username=x.username, password=x.password)
			x.status = [y for y in server.get_running_builds() if y['name'] == x.job_name]	# 执行状态
			x.queue = [y for y in server.get_queue_info() if y['task']['name'] == x.job_name]	# 队列
		except:
			x.broken = ['1']
	nav_list = navList()
	casegroup = caseGroup.objects.all()
	return render(request, 'auto_search.html', locals())

# 动态查询结果返回
def search_result(request):
	myRequest = dict(request.GET)
	logger.info('search:myRequest %s' % myRequest)
	# 处理下key带[]的问题
	myrequest = {}
	for k,v in myRequest.items():
		if '[]' in k:
			k1 = k.replace('[]','')
			myrequest[k1] = v
	# 每个key值循环取并集，最后取交集
	logger.debug('search:myrequest %s' % myrequest)
	origin = caseList.objects.filter(in_use='1')
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

	response = HttpResponse()
	response['Content-Type'] = "text/json"
	return render_to_response('auto_ajax.html', locals())

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

def tag_search(request):
	mixChan = request.GET['mixChan']
	fChannel = caseType.objects.get(type_name=mixChan.split('_')[0])
	sChannel = caseTag.objects.get(tagName=mixChan.split('_')[1])
	result = caseList.objects.filter(type_field=fChannel).filter(case_tag__contains=sChannel.id)
	return render_to_response('tag_search.html', locals())

### 报表相关 ###
# 当日报表邮件接口
def api_report(request):
	try:
		timeTarget = request.GET['timeStamp']
		vver = request.GET['ver']
		name = request.GET['name']
	except:
		jsonStr = {
			"code": "-1",
			"message":"参数错误"
		}
	else:
		cases = allBookRecording.objects.filter(timeStamp=timeTarget)
		if cases:
			# 返回一个报告页面 URL，通过此url可以访问对应的数据构造页面
			# 计算执行时间
			time = cases.values('create_time')
			if time:
				sTime = time.order_by('create_time')[0]['create_time']
				eTime = time.order_by('-create_time')[0]['create_time']
				m,s = divmod((eTime - sTime).seconds, 60)
				testTime = '%s分%s秒' % (m,s)
			# 发邮件
			myUrl = ("http://10.115.1.73:8000/auto/api_report_page?timeStamp=%s" % timeTarget)
			err_list = cases.filter(status='danger')
			pass_list = cases.filter(status='success')
			groupNum = len(json.loads(caseGroup.objects.get(groupName=name).caseID))	# 用例集总数
			allNum = cases.count()
			passNum = pass_list.count()
			failNum = err_list.count()
			if groupNum > allNum:
				warnNum = groupNum - allNum	# 没跑的
			else:
				warnNum = 0
			passRate = round((passNum / allNum * 100),2)
			# email发送
			html_string0 = "<h3>UI自动化报告</h3><h4>[用例集名称:%s]</h4><br><table border=1><tbody><tr><td>版本</td><td>%s</td><td>测试时长</td><td>%s</td></tr><tr><td>用例总数</td><td>%s</td><td>成功率</td><td>%s %%</td></tr><tr><td>本次测试用例数</td><td>%s</td><td>异常</td><td>%s</td></tr><tr><td>通过</td><td>%s</td><td>失败</td><td>%s</td></tr></tbody></table><hr><span><h4><a href=%s target=_blank><font color='DarkSalmon' size='4'>看报告请点点点点点点点点我!!!</font></a></span></h4>" % (name, vver, testTime, groupNum, passRate, allNum, warnNum, passNum, failNum, myUrl)
			html_string1 = ""
			html_string3 = "</table>"
			if err_list:
				html_string1 = "<h3>错误列表</h3><table border=1 width=100%><tr style='background-color:cadetblue'><th>ID</th><th>品类</th><th>用例名称</th><th>状态</th><th>耗时</th><th>创建人</th></tr>\n\r"
				html_string2 = ""
				build_list = []
				for x in err_list:
					sou = json.loads(x.testResultDoc)
					tmp = {
						'id':sou['id'],
						'type':caseList.objects.get(id=sou['id']).type_field.type_name,
						'caseName':x.caseName,
						'status':x.status,
						'usedTime':x.usedTime,
						'user':sou['owner'],
					}
					build_list.append(tmp)
				build_list = sorted(build_list, key = lambda x:x['type'])
				for x in build_list:
					status = '通过'
					if x['status'] == 'danger':
						status = '失败'
					html_string2 += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n\r" % (x['id'], x['type'], x['caseName'], status, x['usedTime'], x['user']))
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
			jsonStr = {
				"code": "-2",
				"message":"没有符合条件的结果"
			}
	finally:
		result = json.dumps(jsonStr, ensure_ascii=False)
		logger.info(result)
		return HttpResponse(result, content_type="application/json")

# 根据url参数返回报表页面
def api_report_page(request):
	timeTarget = request.GET['timeStamp']
	# 每条报告
	rec = allBookRecording.objects.filter(timeStamp=timeTarget)
	if rec:
		# 计算测试时长
		time = rec.values('create_time')
		if time:
			sTime = time.order_by('create_time')[0]['create_time']
			eTime = time.order_by('-create_time')[0]['create_time']
			if (eTime - sTime).seconds > 0:
				m,s = divmod((eTime - sTime).seconds, 60)
				testTime = '%s分%s秒' % (m,s)
			else:
				testTime = rec[0].usedTime
		# 统计所有符合条件的用例table展示数据
		cases = []	# 所有用例列表
		plats = []	# 平台列表
		for x in rec:
			doc = json.loads(x.testResultDoc)
			tmp = {
				'runAt':doc['runAt'],
				'storySize':doc['storySize'],
				'caseTestTime':doc['caseTestTime'],
				'info':caseList.objects.get(id=doc['id']),
				'status':x.status,
				'id':x.id,
			}
			cases.append(tmp)
			plats.append(doc["platformName"])

		plat = set(plats)
		version = set([x['info'].version for x in cases])

		# 指标计算
		pass_list = [x for x in cases if x['status'] == 'success']
		err_list = [x for x in cases if x['status'] == 'danger']

		# for retry err包含 失败的和未跑的
		err_ids = [x['info'].id for x in err_list]
		vver = [x for x in version][-1]
		platt = [x for x in plat][0]

		# if it's group,求差集nono，没跑no，废弃del，错误err
		if testRecording.objects.filter(timeStamp=timeTarget):
			groupID = testRecording.objects.get(timeStamp=timeTarget).groupId
			groupName = caseGroup.objects.get(id=groupID).groupName
			all_list = json.loads(caseGroup.objects.get(id=groupID).caseID)
			run_list = [x['info'].id for x in cases]
			nono_list = [caseList.objects.get(id=x) for x in list(set(all_list).difference(set(run_list)))]
			no_list = [x for x in nono_list if x.in_use == '1']
			err_ids += [x.id for x in no_list]
			delList = [x for x in nono_list if nono_list and x.in_use != '1']
		else:
			myprint('report: not group!')
			no_list = []
			delList = []
			all_list = rec

		# 计算各种结果
		allNum = len(all_list)
		passNum = len(pass_list)
		failNum = len(err_list)
		passRate = round((passNum / (passNum + failNum)) * 100, 2)	# 成功率不算没跑的
	else:
		Amessage = '没有结果'
	return render_to_response('report.html', locals())

# 单条用例报告
def snapshot(request):
	bid = request.GET['id']
	book = trans_report_list(json.loads(allBookRecording.objects.get(id=bid).testResultDoc))
	return render(request, 'snapshot.html', locals())

# 报告筛选功能
def search_report(request):
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
					logger.info('search_report %s' % x.caseName)
					Aerr_list.append(json.loads(x.testResultDoc))
				else:
					Apass_list.append(json.loads(x.testResultDoc))
		for x in Mcases:
			cid = json.loads(x.testResultDoc)['id']
			case = caseList.objects.filter(in_use='1').get(id=cid)
			if user in case.owner:
				if x.status == 'danger':
					logger.info('search_report %s' % x.caseName)
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


### 用例集 ###
# 添加用例集
def auto_makeGroup(request):
	try:
		ids = [int(x) for x in request.GET['id'].split(',')]
		# ids = request.GET['id']
		groupName = request.GET['groupName']
		groupVersion = request.GET['groupVersion']
		# 判断用例集是否存在
		if caseGroup.objects.filter(groupName=groupName).exists():
			temp = caseGroup.objects.get(groupName=groupName)
			origin = json.loads(temp.caseID)
			new = list(set(origin + ids))
			temp.caseID = json.dumps(new)
			logger.info('%s\n %s'% (origin,new))
			temp.save()
		else:
			temp = caseGroup(groupName=groupName)
			temp.caseID = json.dumps(ids)
			if groupVersion:
				temp.versionStr = caseVersion.objects.get(versionStr=groupVersion)
			else:
				temp.versionStr = caseVersion.objects.order_by('-versionStr')[0]
			temp.save()
		data = 'success'
	except TypeError as e:
		logger.info('添加用例集报错：%s' % e)
		data = 'failed'
	finally:
		logger.info('添加用例集状态：%s' % data)
		return HttpResponse(data)

# 用例集列表页
def auto_group(request):
	casegroup = caseGroup.objects.exclude(des='失败用例重测').filter(status='1')
	nav_list = navList()
	cf = configparser.ConfigParser()
	cf.read("/rd/pystudy/conf")
	Aid = cf.get('automation', 'AgroupID')
	Mid = cf.get('automation', 'MgroupID')
	return render(request, 'case_group.html', locals())

# 用例集编辑
def group_edit(request):
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
	platform = {'Android', 'iOS', 'M'}
	logger.debug('%s' % allCase[:10])
	return render(request, 'group_edit.html', locals())

# 用例集保存
def group_save(request):
	try:
		groupId = request.POST.get('ID')
		group = caseGroup.objects.get(id=groupId)
		group.des = request.POST.get('des')
		group.platform = request.POST.get('plat')
		group.versionStr = caseVersion.objects.get(versionStr=request.POST.get('version'))
		group.groupName = request.POST.get('groupName')
		if request.POST.get('groupListBox'):
			group.caseID = json.dumps([int(x.split('-')[1]) for x in request.POST.getlist('groupListBox')])
		else:
			group.caseID = json.dumps([])
		group.save()
	except TypeError as e:
		logger.info('用例集编辑保存出错:%s e:%s' % (request.POST, e))
	finally:
		return HttpResponseRedirect('/auto/auto_group')

# 用例报告结果
def test_ajax(request):
	# 右侧对应品类的用例列表
	dev = request.GET['device']
	testResults = []
	x = deviceList.objects.get(deviceName=dev)
	server = jenkins.Jenkins(x.url, username=x.username, password=x.password)
	rList = reportsList.objects.filter(deviceName__deviceName=x.deviceName).order_by('-create_time')[:10]    #结果列表
	x.buildLog = []
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
	nav_list = navList()
	return render(request, 'test_ajax.html',locals())

# 报表
def autoReport(request):
	nav_list = navList()
	# 版本用例趋势 M站只有一个用例集，永远都是一条线

	source = caseGroup.objects.filter(status='1').filter(groupName__contains='[回归]')
	ver = list(set([x.versionStr.versionStr for x in source]))
	ver.sort(key=lambda x:tuple(int(v) for v in x.split('.')))
	vers = ver[-5:]
	now = vers[-1]
	# line
	result = []
	# rada
	area = []
	#
	typeLi = []
	for v in ['Android', 'iOS', 'M']:
		tmp = {
			'name':v,
			'result':[]
			}
		areatmp = {
			'name':v,
			'result':[],
			}
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
					cases = [caseList.objects.get(id=x) for x in json.loads(backage[0].caseID)]
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
	return render(request, 'autoReport.html', locals())

def getBuildTimes(request):
	date_from = datetime.datetime.now()
	date_to = date_from - datetime.timedelta(days=7)
	source = allBookRecording.objects.filter(create_time__range=(date_to, date_from))
	# 构建次数
	num = source.values('timeStamp').distinct().count()
	result = {'count':num}

	# auto成功率 区分AD M iOS, 仅自动构建
	timeList = [x['timeStamp'] for x in testRecording.objects.filter(flag='1').filter(createTime__range=(date_to, date_from)).values('timeStamp').distinct()]
	Apass, Aall, Mpass, Mall, Ipass, Iall, errList, top, errTypeRe = [], [], [], [], [], [], [], [], []
	for x in source:
		if x.timeStamp in timeList:
			# 成功率
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
			else:
				# 错误用例统计
				if x.status == 'danger':
					errList.append(json.loads(x.testResultDoc)['id'])

	if request.GET['data'] == '1':
		# 通过率计算
		if Apass:
			result['Arate'] = str(round(len(Apass) * 100 / len(Aall), 2)) + '%'
		if Mpass:
			result['Mrate'] = str(round(len(Mpass) * 100 / len(Mall), 2)) + '%'
		if Ipass:
			result['Irate'] = str(round(len(Ipass) * 100 / len(Iall), 2)) + '%'

		return HttpResponse(json.dumps(result), content_type="application/json")
	else:
		# TOP5 用例计算
		finalTop = set(errList)
		for x in finalTop:
			tmp = {
				'id':caseList.objects.get(id=x).id,
				'caseName':caseList.objects.get(id=x).caseName,
				'type':caseList.objects.get(id=x).type_field.type_name,
				'plat':caseList.objects.get(id=x).plantform,
				'ver':caseList.objects.get(id=x).version,
				'times':errList.count(x),
			}
			top.append(tmp)
		top.sort(key=lambda x:x['times'])
		topTable = top[-5:]

		return render(request, 'autoReportAjax.html', locals())
