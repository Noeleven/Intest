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
	server = [
		{'url':'http://10.115.1.74:8080'},
		{'url':'http://10.115.1.77:8080'},
		{'url':'http://10.115.1.78:8080'},
		{'url':'http://10.115.1.75:8080'},
		]
	job_name = 'AbortAndroidUITest'
	for x in server:
		server = jenkins.Jenkins(x['url'])
		server.build_job(job_name)
	return HttpResponseRedirect('/auto/test_list')

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
			'sType':[]
		}
		for y in secondType.objects.all():
			Ftype = x['id']
			tmpDict2 = {
				'type':y.second_Type,
				'num':caseList.objects.filter(type_field=Ftype).filter(in_use='1').filter(second_Type=y.id).count()
			}
			tmpDict['sType'].append(tmpDict2)
		nav_list.append(tmpDict)
	# 废弃的
	trashDict = {
		'type':'废弃',
		'num':caseList.objects.filter(in_use='0').count(),
	}
	nav_list.append(trashDict)
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
def trans_me(aname, type, ptype, ver):
	plist = {'android':'0','ios':'1','m':'2'}
	cc = plist[ptype.lower()]
	targetRange = controlList.objects.filter(controlType=cc).filter(TYPE=type).filter(versionStr__versionStr=ver)
	# 中文 到 英文
	try:
		if targetRange.filter(controlName=aname):
			bname = targetRange.get(controlName=aname).controlFiled
		# 英到中
		elif targetRange.filter(controlFiled=aname):
			bname = targetRange.get(controlFiled=aname).controlName
		else:
			bname = aname
		return bname
	except TypeError as e:
		logger.info('翻译%s' % aname)
		logger.info('err:%s' % e)

# 报告翻译
def trans_report_list(x):
	plant = caseList.objects.get(id=x['id']).plantform
	ver = caseList.objects.get(id=x['id']).version
	for y in x['jsonStory']:
		y['where'] = trans_me(y['where'], 'where', plant, ver)
		y['enterActivity'] = trans_me(y['enterActivity'], 'where', plant, ver)
		for z in y['checkString']:
			z['checkType'] = trans_me(z['checkType'], 'checkString', plant, ver)
			if z.get('enterActivity'):
				z['enterActivity'] = trans_me(z['enterActivity'], 'where', plant, ver)
			if z.get('elementName'):
				z['elementName'] = trans_me(z['elementName'], 'targetName', plant, ver)
		for z in y['action']:
			z['actionCode'] = trans_me(z['actionCode'], 'action', plant, ver)
			z['target']['targetName'] = trans_me(z['target']['targetName'], 'targetName', plant, ver)
	return x


### 各PAGE ###
# 导航list
def auto_list(request):
	try:
		my_type = request.GET['my_type']
	except:
		my_type='全部'
	else:
		f_type = my_type.split('_')[0]
		if f_type == "全部":
			show_list = caseList.objects.filter(in_use='1')
		elif f_type == '废弃':
			show_list = caseList.objects.filter(in_use='0')
		else:
			s_type = my_type.split('_')[1]
			try:
				type_id = caseType.objects.filter(type_name=f_type)[0].id
				s_type_id = secondType.objects.filter(second_Type=s_type)[0].id
			except:
				show_list = ''
			else:
				show_list = caseList.objects.filter(in_use='1').filter(type_field=type_id).filter(second_Type=s_type_id)
	finally:
		device_list = deviceList.objects.exclude(in_use='0')
		nav_list = navList()
		return render(request, 'auto_list.html', locals())

# 编辑保存
def auto_edit_save(request, id):
	my_form = dict(request.GET)
	logger.info(my_form)
	case_obj = caseList.objects.get(id=id)
	try:
		caseName = case_obj.caseName
		csType = caseType.objects.get(type_name=my_form.get('type')[0]).type_field
		caseVersion = my_form.get('version')[0]
		casePlantform = my_form.get('plantform')[0]
		caseStatus = my_form.get('canUse')[0]
		caseDes = my_form.get('caseDes')[0]
		owner = my_form.get('owner')[0]
		s_Type = my_form.get('second_Type')[0]
	except TypeError as e:
		logger.info('获取用例信息出错： %s' % e)
	caseStatus = '1' if caseStatus=='use' else '0'

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
				"where":trans_me(my_form.get('where')[bgSub], 'where', casePlantform, caseVersion),
				'action':[],
				"enterActivity":trans_me(my_form.get('enterActivity')[bgSub], 'where', casePlantform, caseVersion),
				"checkString":[],
				}
			# 预期列表，处理checkString
			expendlist = [x for x in my_form.get('index_expend') if x.split('-')[0] == str(bgSub + 1)]

			for smExpend in range(expendIndex, expendIndex + len(expendlist)):
				cType = my_form.get('checkType')[smExpend]
				eName = my_form.get('elementname')[smExpend]
				expendDict = {
					"checkType": trans_me(cType, 'checkString', casePlantform, caseVersion),
					"expeted": my_form.get('expeted')[smExpend],
					"elementName": trans_me(eName, 'targetName', casePlantform, caseVersion),
				}
				bgElement['checkString'].append(expendDict)

			# 动作列表['1-1','1-2','2-1']
			steplist = [x for x in my_form.get('index_step') if x.split('-')[0] == str(bgSub + 1)]
			# 循环小步下标，获取数值
			for smSub in range(startIndex, startIndex + len(steplist)):
				actionDict = {
					"actionCode": trans_me(my_form.get('actionCode')[smSub], 'action', casePlantform, caseVersion),
					"behaviorPara":{
						"inputValue":my_form.get('inputValue')[smSub],
						},
					"target": {
						"targetName": trans_me(my_form.get('targetName')[smSub], 'targetName', casePlantform, caseVersion),
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
				'action':trans_me(my_form.get('actionCode')[bgSub], 'action', casePlantform, caseVersion),
				'typeText':myInput,
				'value':trans_me(my_form.get('targetName')[bgSub], 'targetName', casePlantform, caseVersion),
				}
			json_home['jsonStory'].append(bgElement)
		my_case = json.dumps(json_home, ensure_ascii=False)
	else:
		logger.info('编辑保存用例 平台版本：%s' % casePlantform)
	# logger.info(('*' * 20 + '\n' + '%s') % my_case)
	# 存储DB
	p = case_obj
	p.case = my_case
	p.caseName = caseName
	p.type_field = caseType.objects.get(id=caseType.objects.filter(type_field=csType)[0].id)
	p.plantform = casePlantform
	p.version = caseVersion
	p.owner = owner
	p.des = caseDes
	p.in_use = caseStatus
	p.second_Type_id = str(secondType.objects.get(second_Type=s_Type).id)  # todo 增加二类型选择
	p.modify_time = datetime.datetime.now()
	p.save()
	# 判断动作
	return HttpResponseRedirect("/auto/auto_list?my_type=%s_%s" % (my_form.get('type')[0], secondType.objects.get(second_Type=s_Type).second_Type))

# 构建用例，生成配置，吊起Jenkins，存储报告
def auto_config(request):
	# 取参数
	ids = request.GET['vals'].split(',')    # 获取用例或集合的ID
	device = request.GET['device']  # 获取类型是AD、ios还是M
	mytype = request.GET['type']	# 标识用例还是用例集
	isDay = request.GET['isDay']	# 标记日常还是测试

	# 整理待测用例ID
	cases = []
	if mytype == 'group':
		groupVersion = caseGroup.objects.get(id=ids[0]).versionStr.versionStr	# 获取用例集版本
		groupId = ids
		# 汇总用例集所有用例 在均分
		casetmp = []
		for x in ids:
			casetmp += json.loads(caseGroup.objects.get(id=x).caseID)
	else:
		casetmp = [int(x) for x in ids]
	filter_id = set(casetmp)	# 用例集去重

	# 过滤无效，终用例列表newid
	newid = []
	for y in filter_id:
		if caseList.objects.filter(in_use='1').filter(id=y):
			cases.append(caseList.objects.filter(in_use='1').filter(id=y)[0].caseName)
			newid.append(y)
		else:
			continue
	logger.debug('cases:%s caseid:%s' % (cases, newid))

	# 确认设备,可用+平台+对应用例版本，用例集使用AD iOS M来标记，非用例集使用设备名来标记
	if device == 'AD':
		mydevice = deviceList.objects.filter(in_use='1').filter(platformName='Android').filter(appVersion=groupVersion).order_by('-deviceName')
	elif device == 'M':
		mydevice = deviceList.objects.filter(in_use='1').filter(platformName='M')  # M站不用带版本
	elif device == 'iOS':
		mydevice = deviceList.objects.filter(in_use='1').filter(platformName='iOS').filter(appVersion=groupVersion).order_by('-deviceName')
	else:
		mydevice = deviceList.objects.filter(deviceName=device)  # 单台

	# 分发用例
	if len(mydevice) == 0:
		logger.info('构建用例：然而没有设备')
	else:
		# 分发用例-计算用例步长
		if len(newid) >= len(mydevice):
			if (len(newid) % len(mydevice)) == 0:
				mdl = len(newid) // len(mydevice)
			else:
				if (len(newid) % len(mydevice)) >= (len(mydevice) // 2):
					mdl = len(newid) // len(mydevice) + 1
				else:
					mdl = len(newid) // len(mydevice)
		else:
			mdl = 1
		logger.info('dev:%s dev数量:%s 步长:%s' % (mydevice, len(mydevice) ,mdl))
		# 分发用例-用例集所有设备用同一个标志，故循环之前
		groupTime = 'autoTestIn' + datetime.datetime.now().strftime('%Y%m%d') + str(random.randint(10000,99999))
		# 分发用例-分配给每台设备
		start = end = numb = 0
		for x in mydevice:
			end += mdl
			numb += 1
			if start < len(newid):
				# 确认存瑞myconfig的json结构，各平台不一样
				if x.platformName == 'iOS':
					jsonStr = {
						"deviceName": x.deviceName,    # 设备:ip
						"deviceIP": x.deviceIP,
						"appVersion": x.appVersion,  #   app版本
						"platformVersion": x.platformVersion,    # 操作系统版本
						"platformName": x.platformName,  # iOS
						"webDriverAgentUrl": x.webDriverAgentUrl,  # iOS
						"bundleId": x.bundleId,  # iOS
						"appPackage": x.appPackage,
						}
				else:
					jsonStr = {
						"APPIUMSERVERSTART": x.APPIUMSERVERSTART,
						"appiumServicePath": x.appiumServicePath,
						"appiumServicePort": x.appiumServicePort,
						"appVersion": x.appVersion,
						"deviceName": x.deviceName,
						"deviceIP":x.deviceIP,
						"platformVersion": x.platformVersion,
						"platformName": x.platformName,
						"lvsessionid": x.lvsessionid,
						"timeout": x.timeWait,
						"appPackage": x.appPackage,
						"appLaunchActivity": x.appLaunchActivity,
						}

				# 确认timestamp
				if mytype == 'group':
					jsonStr['timeStamp'] = groupTime
					tt = testRecording(timeStamp=jsonStr['timeStamp'])
					tt.Version = groupVersion
					tt.groupId = json.dumps(groupId)
					tt.save()
				else:
					singleTime = 'autoTestIn' + str(int(time.time())) + str(random.randint(10000,99999))
					jsonStr['timeStamp'] = singleTime

				# 具体分配用例
				if end > len(newid):	# end + 步长 超过就不要在分了，结束
					jsonStr["testCaseSQL"] = newid[start:]
					logger.debug(newid[start:])
				elif (end + mdl) > len(newid) and numb == len(mydevice):
					jsonStr["testCaseSQL"] = newid[start:]
				else:
					jsonStr["testCaseSQL"] = newid[start:end]
					logger.debug(newid[start:end])

				# 判断有没有该设备，并存入config表供jenkins调用，但不需要timeStamp的ids
				hasD = myConfig.objects.filter(device=x.deviceName)
				if hasD:
					hasD[0].caseStr = json.dumps(jsonStr, ensure_ascii=False)
					hasD[0].save()
				else:
					p = myConfig(device=x.deviceName)
					p.caseStr = json.dumps(jsonStr, ensure_ascii=False)
					p.save()

				# 定义存report的名称，貌似可以简化掉了
				if end >= len(newid):
					time_case = jsonStr['timeStamp'] + '_' + ('_').join([str(x) for x in list(newid)[start:]])
				else:
					time_case = jsonStr['timeStamp'] + '_' + ('_').join([str(x) for x in list(newid)[start:end]])

				# 驱动jenkins
				server = jenkins.Jenkins(x.url, username=x.username, password=x.password)
				job_name = x.job_name
				try:
					server.build_job(job_name, {'deviceName':x.deviceName})  # 执行构建
					build_number = server.get_job_info(job_name)['lastBuild']['number']
				except:
					build_number = 0
					logger.info('未获取到buildNumber,置为%s' % build_number)
				finally:
					pp = reportsList(timeStamp=time_case)
					if build_number != 0:
						pp.buildNUM = '#' + str(build_number + 1)
						pp.status = str(server.get_build_info(job_name, build_number)['building'])
					if device == 'iOS':
						pp.reportURL = ('http://10.113.1.193:8001/%s/report.html' % (build_number + 1))
					else:
						pp.reportURL = ("/auto/api_report_page?timeStamp=" + "%s" % jsonStr['timeStamp'])
					pp.deviceName = deviceList.objects.get(deviceName=x.deviceName)
					pp.save()

				start += mdl

	return HttpResponse('OK')

# jenkins调用接口，返回接口配置
def auto_response(request):
	try:
		deviceN = request.GET['deviceName']
		jsonStr = myConfig.objects.get(device=deviceN).caseStr
		return HttpResponse(jsonStr, content_type="application/json")
	except:
		return HttpResponse('No Such Device')

# iOS 用例返回json	废弃
# def auto_caseJson(request):
# 	"""调取参数:平台+timeStamp"""
# 		# 从config里读取ios的用例编号
# 		# caseName = request.GET['caseName']
# 	try:
# 		plantform = request.GET['plantform']
# 		if plantform == 'Android':
# 			casetimeStamp = request.GET['timeStamp']
# 		else:
# 			casetimeStamp = ''
# 		# 从reportlist里取timestamp对应的case_id
# 		try:
# 			if plantform == 'Android':
# 				# 这里有个BUG，如果timestamp存在包含关系，就嗝屁了
# 				ids = reportsList.objects.filter(timeStamp__contains=casetimeStamp)[0].timeStamp.split('_')[1:]
# 			else:
# 				iosID = deviceList.objects.get(deviceName='iOS').id
# 				ids = reportsList.objects.filter(deviceName_id=iosID).order_by('-create_time')[0].timeStamp.split('_')[1:]
# 			cases = []
# 			for x in ids:
# 				caseD = {
# 					"caseType": caseList.objects.get(id=x).type_field.type_field,
# 					"jsonStory": json.loads(caseList.objects.get(id=x).case),
# 				}
# 				# logger.info(x)
# 				cases.append(caseD)
# 			jsonStr = {
# 				"code": "1",
# 				"message": "",
# 				"data": cases
# 			}
# 		except:
# 			jsonStr = {
# 				"code": "-2",
# 				"message":"用例不存在"
# 			}
# 	except:
# 		jsonStr = {
# 			"code": "-1",
# 			"message":"参数错误,需要plantform和timeStamp"
# 		}
# 	finally:
# 		jsonStr = json.dumps(jsonStr, ensure_ascii=False)
# 		return HttpResponse(jsonStr, content_type="application/json")

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
	s_type_all = secondType.objects.all().order_by('second_Type')
	type_list = [x for x in type_all]
	second_type_list = [x for x in s_type_all]
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
		caseName = request.POST['caseName']
		csType = caseType.objects.get(type_name=request.POST['type']).type_field
		caseVersion = request.POST['version']
		casePlantform = request.POST['plantform']
		caseStatus = request.POST['canUse']
		caseDes = request.POST['caseDes']
		owner = request.POST['owner']
		s_Type = request.POST['second_Type']

		caseStatus = '1' if caseStatus=='use' else '0'
		if casePlantform == 'iOS':
			defaultCase = '{"jsonStory":[{"des":"", "index":1, "value":"", "action":"click", "typeText":""}], "caseType":"" }'
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
		p.second_Type_id = str(secondType.objects.get(second_Type=s_Type).id)  # todo 增加二类型选择
		p.save()
		# 获取当前用例ID
		myID = caseList.objects.filter(plantform=casePlantform).filter(caseName=caseName).values('id')[0]['id']
		return HttpResponseRedirect("/auto/new_edit/%s" % myID)
	except TypeError as e:
		# data = ()
		logger.info('新建保存用例出错了 %s' % e)
		return

# 新增用例action
def new_edit(request, id):
	# 反向解析json存入表单 首先从DB获取json字符串，并解析成数据类型
	if caseList.objects.filter(id=id).exists():
		json_dict = caseList.objects.filter(id=id).values()[0]
		# 转义品类名称
		try:
			# 开始解析用例
			json_dict['type_field_id'] = caseType.objects.get(id=json_dict['type_field_id']).type_name
			json_dict['second_Type_id'] = secondType.objects.get(id=json_dict['second_Type_id']).second_Type
			# 取case部分转为数据格式

			# json_dict.pop('case')
			myPlantform = json_dict['plantform']

			# 基本信息里下拉列表
			type_all = caseType.objects.all().order_by('type_name')
			s_type_all = secondType.objects.all().order_by('second_Type')
			type_list = [x for x in type_all]
			second_type_list = [x for x in s_type_all]
			user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
			versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
			plant = ['Android','iOS','M']
			nav_list = navList()

			# define 元素 起点 终点列表 iOS没有
			targetname = []
			elementname = []

			if myPlantform == 'Android' or myPlantform == 'M':
				where = []
				enterActivity = []
				wait_list = ['等待','不等待']
				BgStep = json.loads(json_dict['case'])
				for x in BgStep:
					x['enterActivity'] = trans_me(x['enterActivity'],'where',json_dict['plantform'], json_dict['version'])
					x['where'] = trans_me(x['where'],'where',json_dict['plantform'], json_dict['version'])
					where.append(x['where'])
					enterActivity.append(x['enterActivity'])
					ai = ci = 1
					for y in x['action']:
						y['target']['targetName'] = trans_me(y['target']['targetName'],'targetName',json_dict['plantform'], json_dict['version'])
						targetname.append(y['target']['targetName'])
						y['actionCode'] = trans_me(y['actionCode'],'action',json_dict['plantform'], json_dict['version'])
						if y['needWait'] == True:
							y['needWait'] = '等待'
						else:
							y['needWait'] ='不等待'
						y['index'] = str(x['index']) + '-' + str(ai)
						ai += 1
					for y in x['checkString']:
						y['elementName'] = trans_me(y['elementName'],'targetName',json_dict['plantform'], json_dict['version'])
						elementname.append(y['elementName'])
						y['index'] = str(x['index']) + '-' + str(ci)
						ci += 1
						y['checkType'] = trans_me(y['checkType'],'checkString',json_dict['plantform'], json_dict['version'])
					control_list = new_select_list('action', json_dict['plantform'], json_dict['version'])
					where_list = new_select_list('where', json_dict['plantform'], json_dict['version'])
					target_list = new_select_list('targetName', json_dict['plantform'], json_dict['version'])
					checkType_list = new_select_list('checkString', json_dict['plantform'])
				return render(request, 'new_edit.html',locals())
			else:
				BgStep = json.loads(json_dict['case'])['jsonStory']
				ai = 1
				for x in BgStep:
					x['index'] = str(ai)
					ai += 1
					x['action'] = trans_me(x['action'],'action',json_dict['plantform'], json_dict['version'])
					targetname.append(trans_me(x['value'],'targetName',json_dict['plantform'], json_dict['version']))
					control_list = new_select_list('action', json_dict['plantform'], json_dict['version'])
					target_list = new_select_list('targetName', json_dict['plantform'], json_dict['version'])
				return render(request, 'ios_edit.html', locals())
		except AttributeError as e:
			logger.info("new_edit:%s" % e)
	else:
		logger.info("用例id %s 不存在" % id)
		return HttpResponseRedirect('/auto/new_add')

# 测试报告页
def test_list(request):
	# 右侧对应品类的用例列表
	iosdev = deviceList.objects.filter(in_use='1').filter(platformName='iOS').order_by('deviceName')  #设备列表
	addev = deviceList.objects.exclude(in_use='0').filter(platformName='Android').order_by('deviceName')   #设备列表
	mdev = deviceList.objects.filter(in_use='1').filter(platformName='M').order_by('deviceName')   #设备列表
	nav_list = navList()
	groupReports = testRecording.objects.order_by('-createTime').values('timeStamp', 'Version', 'createTime', 'groupId').distinct()[:20]
	for x in groupReports:
		x['url'] = '/auto/api_report_page?timeStamp=' + x['timeStamp']
		# x['name'] = [caseGroup.objects.get(id=y).groupName for y in json.loads(x['groupId'])]
		x['name'] = caseGroup.objects.get(id=json.loads(x['groupId'])[0]).groupName
		try:
			x['createTime'] = reportsList.objects.filter(timeStamp__contains=x['timeStamp'])[0].create_time
		except IndexError as e:
			logger.info('test_list error:%s' % e)
	return render(request, 'test_list.html',locals())

# 首页查询
def auto_search(request):
	# 需要品类、二品类、版本、所属人、平台
	type_all = caseType.objects.all().order_by('type_name')
	s_type_all = secondType.objects.all().order_by('second_Type')
	type_list = [x for x in type_all]
	second_type_list = [x for x in s_type_all]
	user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
	versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
	plant = ['Android','iOS','M']
	device_list = deviceList.objects.exclude(in_use='0')
	nav_list = navList()
	casegroup = caseGroup.objects.all()
	return render(request, 'auto_search.html', locals())

# 动态查询结果返回
def search_result(request):
	myRequest = dict(request.GET)
	logger.debug('search:myRequest %s' % myRequest)
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
				elif m == 'secondType':
					if_list[m] += origin.filter(second_Type__second_Type__contains=x)
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
			# 发邮件
			myUrl = ("http://10.115.1.73:8000/auto/api_report_page?timeStamp=%s" % timeTarget)
			err_list = cases.filter(status='danger')
			pass_list = cases.filter(status='success')
			groupNum = len(json.loads(caseGroup.objects.get(groupName=name).caseID))
			allNum = cases.count()
			passNum = pass_list.count()
			failNum = err_list.count()
			if groupNum > allNum:
				warnNum = groupNum - allNum
			else:
				warnNum = 0
			passRate = round((passNum / allNum * 100),2)
			# email发送
			html_string0 = "<h3>UI自动化报告</h3><h4><p>用例集名称:%s | 用例总数:%s <br>| 本次测试用例数:%s | 通过:%s | 失败:%s | 测试异常:%s | 版本:%s</p><p>通过率:%s %%</p><span><a href=%s target=_blank><font color='#008080'>点击查看错误详情和截图</font></a></span></h4>" % (name, groupNum, allNum, passNum, failNum, warnNum, vver, passRate, myUrl)
			html_string1 = ""
			html_string3 = "</table>"
			if err_list:
				html_string1 = "<h3 style='color:IndianRed'>错误列表</h3><table border=1 width=100%><tr style='background-color:DarkSalmon'><th>ID</th><th>品类</th><th>用例名称</th><th>状态</th><th>耗时</th><th>创建人</th></tr>\n\r"
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
		return HttpResponse(result, content_type="application/json")

# 根据url参数返回报表页面
def api_report_page(request):
	timeTarget = request.GET['timeStamp']
	rec = allBookRecording.objects.filter(timeStamp=timeTarget)
	if rec:
		# 计算测试时长
		time = rec.values('create_time')
		if time:
			sTime = time.order_by('create_time')[0]['create_time']
			eTime = time.order_by('-create_time')[0]['create_time']
			m,s = divmod((eTime - sTime).seconds, 60)
			testTime = '%s分%s秒' % (m,s)
		# 重构列表
		cases = []
		plats = []
		for x in rec:
			doc = json.loads(x.testResultDoc)
			tmp = {
				'runAt':doc['runAt'],
				'storySize':doc['storySize'],
				'caseTestTime':doc['caseTestTime'],
				# 'caseTestTime':x.usedTime,
				'info':caseList.objects.get(id=doc['id']),
				'status':x.status,
				'id':x.id,
			}
			cases.append(tmp)
			plats.append(doc["platformName"])
		plat = set(plats)
		version = set([x['info'].version for x in cases])
		# 计算其让指标
		pass_list = [x for x in cases if x['status'] == 'success']
		err_list = [x for x in cases if x['status'] == 'danger']
		# if it's group,求差集
		try:
			all_list = json.loads(caseGroup.objects.get(id=json.loads(testRecording.objects.filter(timeStamp=timeTarget)[0].groupId)[0]).caseID)
			run_list = [x['info'].id for x in cases]
			no_list = [caseList.objects.get(id=x) for x in list(set(all_list).difference(set(run_list)))]
		except IndexError as e:
			no_list = []
			logger.info('api_report_page error:%s' % e)
		# 计算各种结果
		allNum = len(cases)
		passNum = len(pass_list)
		failNum = len(err_list)
		passRate = round((passNum / allNum) * 100, 2)
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
	casegroup = caseGroup.objects.all()
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
	logger.debug('%s' % allCase[:10])
	return render(request, 'group_edit.html', locals())

# 用例集保存
def group_save(request):
	try:
		groupId = request.POST.get('ID')
		group = caseGroup.objects.get(id=groupId)
		group.des = request.POST.get('des')
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
