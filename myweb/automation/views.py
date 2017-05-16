from django.shortcuts import render,render_to_response
from automation.models import *
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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

def _format_addr(s):
	name, addr = parseaddr(s)
	return formataddr((Header(name, 'utf-8').encode(), addr))

# 定义导航
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

# 定义下拉内容
def new_select_list(controlListType, plantform, version='all'):
	# 设置目标元素列表
	plist = {'Android':'0','IOS':'1','M':'2'}
	if version == 'all':
		target_all = controlList.objects.filter(TYPE=controlListType).filter(controlType=plist[plantform]).order_by('controlName')
	else:
		target_all = controlList.objects.filter(TYPE=controlListType).filter(controlType=plist[plantform]).filter(versionStr__versionStr=version).order_by('controlName')
	target_list = [x for x in target_all]
	return target_list

# 接口签名（未用）
def user_sign(request):
	# 判断时间差，5分钟
	client_time = request.POST['TimeStr']
	signId = request.POST['signId']
	server_time = str(time.time()).split('.')[0]
	time_sub = int(server_time) - int(client_time)
	if time_sub > 300:
		return 'timeout'
	else:
		md5 = hashlib.md5()
		sign_str = (client_time + '@djangoSign').encode(encoding='utf-8')
		md5.update(sign_str)
		result = md5.hexdigest()
		if result == signId:
			return 'success'
		else:
			return 'error'

# controllist翻译 save时只正向翻译，只有显示和report时才反向翻译
def trans_meA(aname, type, ptype):
	plist = {'android':'0','ios':'1','m':'2'}
	cc = plist[ptype.lower()]
	targetRange = controlList.objects.filter(controlType=cc).filter(TYPE=type)
	if targetRange.filter(controlName=aname):
		bname = targetRange.get(controlName=aname).controlFiled
	else:
		bname = aname
	return bname

def trans_me(aname, type, ptype):
	plist = {'android':'0','ios':'1','m':'2'}
	cc = plist[ptype.lower()]
	targetRange = controlList.objects.filter(controlType=cc).filter(TYPE=type)
	if targetRange.filter(controlName=aname):
		bname = targetRange.get(controlName=aname).controlFiled
	elif targetRange.filter(controlFiled=aname):
		bname = targetRange.get(controlFiled=aname).controlName
	else:
		bname = aname
	return bname


def trans_report_list(myList):
	for x in myList:
		plant = caseList.objects.get(id=x['id']).plantform
		for y in x['jsonStory']:
			y['where'] = trans_me(y['where'], 'where', plant)
			y['enterActivity'] = trans_me(y['enterActivity'], 'where', plant)
			for z in y['checkString']:
				z['checkType'] = trans_me(z['checkType'], 'checkString', plant)
				if z.get('enterActivity'):
					z['enterActivity'] = trans_me(z['enterActivity'], 'where', plant)
				if z.get('elementName'):
					z['elementName'] = trans_me(z['elementName'], 'targetName', plant)
			for z in y['action']:
				z['actionCode'] = trans_me(z['actionCode'], 'action', plant)
				z['target']['targetName'] = trans_me(z['target']['targetName'], 'targetName', plant)
	return myList

# NORMAL DB
def doDB(method, myList):
	# myList = [caseName, bigstep, my_case, caseStatus, csType, caseVersion]
	conn = mysql.connector.connect(user='root', password='lvmama', database='lmmpicTest', host='127.0.0.1')
	cursor = conn.cursor()
	cursor = conn.cursor(buffered=True)
	inputTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	if method == 'insert':
		cursor.execute('insert into bookShelf (caseName, needTest, inputTime, classType, appVersion) values (%s, %s, %s, %s, %s)', [myList[0], myList[3], inputTime, myList[4], myList[5]])
		cursor.execute('insert into testStory (caseName, caseLength, jsonStory, caseUpdateTime, caseType) values (%s, %s,%s, %s,%s)', [myList[0], myList[1], myList[2], inputTime, myList[4]])
	elif method == 'update':
		cursor.execute('update bookShelf set needTest=%s, classType=%s, appVersion=%s where caseName=%s', [myList[3], myList[4], myList[5], myList[0]])
		cursor.execute('update testStory set caseLength=%s, jsonStory=%s, caseUpdateTime=%s, caseType=%s where caseName=%s', [myList[1], myList[2], inputTime, myList[4], myList[0]])
	elif method == 'delete':
		cursor.execute('delete from bookShelf where caseName=%s', [myList[0]])
		cursor.execute('delete from testStory where caseName=%s', [myList[0]])
	else:
		logger.info('doDB unknow!')
	conn.commit()
	cursor.close()
	conn.close()

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
		device_list = deviceList.objects.filter(in_use='1')
		nav_list = navList()
		return render(request, 'auto_list.html', locals())

# 编辑保存
def auto_edit_save(request, id):
	my_form = dict(request.GET)
	# logger.info(my_form)
	case_obj = caseList.objects.filter(id=id)[0]
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
		logger.info('编辑保存用例出错： %s' % e)
	caseStatus = '1' if caseStatus=='use' else '0'
	# 处理生成json,等json格式，根据plantform类型生成不同的json
	json_home = []
	# 统计有多少大步
	bigstep = len(set([x.split('-')[0] for x in my_form.get('index_step')]))
	#起始下标
	if casePlantform == 'Android' or casePlantform == 'M':
		startIndex = expendIndex = 0
		for bgSub in range(bigstep):
			# 大步字典
			bgElement = {
				"storyDescription":my_form.get('storyDescription')[bgSub],
				"index":bgSub + 1,
				"where":trans_meA(my_form.get('where')[bgSub],'where',casePlantform),
				'action':[],
				"enterActivity":trans_meA(my_form.get('enterActivity')[bgSub],'where',casePlantform),
				"checkString":[],
				}
			# 预期列表，处理checkString
			expendlist = [x for x in my_form.get('index_expend') if x.split('-')[0] == str(bgSub + 1)]

			for smExpend in range(expendIndex, expendIndex + len(expendlist)):
				cType = my_form.get('checkType')[smExpend]
				eName = my_form.get('elementname')[smExpend]
				expendDict = {
					"checkType": trans_meA(cType, 'checkString', casePlantform),
					"expeted": my_form.get('expeted')[smExpend],
					"elementName": trans_meA(eName, 'targetName', casePlantform),
				}
				bgElement['checkString'].append(expendDict)

			# 动作列表['1-1','1-2','2-1']
			steplist = [x for x in my_form.get('index_step') if x.split('-')[0] == str(bgSub + 1)]
			# 循环小步下标，获取数值
			for smSub in range(startIndex, startIndex + len(steplist)):
				actionDict = {
					"actionCode": trans_meA(my_form.get('actionCode')[smSub], 'action', casePlantform),
					"behaviorPara":{
						"inputValue":my_form.get('inputValue')[smSub],
						},
					"target": {
						"targetName": trans_meA(my_form.get('targetName')[smSub], 'targetName', casePlantform),
						},
					"needWait": (bool(1) if my_form.get('needWait')[smSub] == '等待' else bool(0)),
					}
				bgElement['action'].append(actionDict)
			# 下标自增，供下一大步作为起始下标
			startIndex += len(steplist)
			expendIndex += len(expendlist)
			json_home.append(bgElement)
		my_case = json.dumps(json_home, ensure_ascii=False)
		mydbList = [caseName, bigstep, my_case, caseStatus, csType, caseVersion]
		conn = mysql.connector.connect(user='root', password='lvmama', database='lmmpicTest', host='127.0.0.1')
		cursor = conn.cursor(buffered=True)
		cursor.execute('select * from testStory where caseName=%s', (caseName,))
		values = cursor.fetchall()
		if values:
			doDB('update', mydbList)
		else:
			doDB('insert', mydbList)
		conn.commit()
		cursor.close()
		conn.close()
	elif casePlantform == 'IOS':
		for bgSub in range(bigstep):
			# 大步字典
			bgElement = {
				"des":my_form.get('storyDescription')[bgSub],
				"index":bgSub + 1,
				'action':trans_meA(my_form.get('actionCode')[bgSub], 'action', casePlantform),
				'type':trans_meA(my_form.get('typeCode')[bgSub], 'type', casePlantform),
				'typeText':my_form.get('inputValue')[bgSub],
				'label':my_form.get('targetName')[bgSub],
				}
			json_home.append(bgElement)
		my_case = json.dumps(json_home, ensure_ascii=False)
	else:
		logger.info('编辑保存用例 平台版本：%s' % casePlantform)
	# logger.info(('*' * 20 + '\n' + '%s') % my_case)
	# 存储DB
	p = case_obj
	p.case = my_case
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

# 点击生成配置
def auto_config(request):
	ids = request.GET['vals'].split(',')    # 待测id列表
	device = request.GET['device']  # 待测设备
	mytype = request.GET['type']	# 用例还是用例集
	isDay = request.GET['isDay']	# 用例还是用例集
	cases = []
	logger.debug('%s##%s##%s' %(ids,device,mytype))
	if mytype == 'group':
		# 汇总用例集所有用例 在均分
		casetmp = []
		for x in ids:
			casetmp += json.loads(caseGroup.objects.get(id=x).caseID)
	else:	# id就是用例
		casetmp = ids
	logger.debug(set(casetmp))
	filter_id = set(casetmp)
	newid = []
	# 过滤无效用例
	for y in filter_id:
		if caseList.objects.filter(in_use='1').filter(id=y):
			cases.append(caseList.objects.filter(in_use='1').filter(id=y)[0].caseName)
			newid.append(y)
		else:
			continue
	logger.debug('cases:%s caseid:%s' % (cases, newid))
	# device:IOS,AD,62001,62025,M,chrome之类，如果ios直接存
	if device == 'IOS':
		#IOS jenkins
		mydevice = deviceList.objects.filter(deviceName=device)[0]  #待测设备属性
		server = jenkins.Jenkins(mydevice.url, username=mydevice.username, password=mydevice.password)
		myTime = int(time.time())
		jsonStr = {
			"deviceName": mydevice.deviceName,    # 设备:ip
			"deviceIP": mydevice.deviceIP,
			"appVersion": mydevice.appVersion,  #   app版本
			"platformVersion": mydevice.platformVersion,    # 操作系统版本
			"platformName": mydevice.platformName,  # IOS
			"timeStamp": str(myTime),
		}
		job_name = mydevice.job_name
		# 判断有没有该设备，并存入config表供jenkins调用，但不需要timeStamp的ids
		hasD = myConfig.objects.filter(device=mydevice.deviceName)
		if hasD:
			hasD[0].caseStr = json.dumps(jsonStr, ensure_ascii=False)
			hasD[0].save()
		else:
			p = myConfig(device=mydevice.deviceName)
			p.caseStr = json.dumps(jsonStr, ensure_ascii=False)
			p.save()

		server.build_job(job_name)  # 执行构建
		build_number = server.get_job_info(job_name)['lastBuild']['number']
		# 报告存入report，需要ids
		time_case = jsonStr['timeStamp'] + '_' + ('_').join(casetmp)
		pp = reportsList(timeStamp=time_case)
		pp.buildNUM = '#' + str(build_number + 1)
		pp.reportURL = ('%s/%s/report.html' % (mydevice.url,(build_number + 1)))
		logger.info('保存报告url：%s' % pp.reportURL)
		pp.status = str(server.get_build_info(job_name,build_number)['building'])
		pp.deviceName = deviceList.objects.get(deviceName=device)
		pp.save()
	else:
		# jenkins
		if device == 'AD':
			mydevice = deviceList.objects.filter(in_use='1').filter(platformName='Android')  # 多台
		elif device == 'M':
			mydevice = deviceList.objects.filter(in_use='1').filter(platformName='M')  # M站多台
		else:
			mydevice = deviceList.objects.filter(deviceName=device)  # 单台
		# 步长计算
		if len(cases) >= len(mydevice):
			if (len(cases) % len(mydevice)) == 0:
				mdl = len(cases) // len(mydevice)
			else:
				if (len(cases) % len(mydevice)) >= (len(mydevice) // 2):
					mdl = len(cases) // len(mydevice) + 1
				else:
					mdl = len(cases) // len(mydevice)
		else:
			mdl = 1
		start = end = 0
		logger.info('dev:%s 步长:%s' % (mydevice, mdl))
		for x in mydevice:
			end += mdl
			myTime = int(time.time())
			if start < len(cases):
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
				logger.info('是否每日构建：%s' % isDay)
				if isDay == 'yes':
					jsonStr['timeStamp'] = 'autoTestIn' + datetime.datetime.now().strftime('%Y%m%d')
				else:
					jsonStr['timeStamp'] = str(myTime)
				if end > len(cases):	# end + 步长 超过就不要在分了，直接结束
					jsonStr["testCaseSQL"] = cases[start:]
					logger.debug(cases[start:])
				else:
					jsonStr["testCaseSQL"] = cases[start:end]
					logger.debug(cases[start:end])
				job_name = x.job_name
				# 判断有没有该设备，并存入config表供jenkins调用，但不需要timeStamp的ids
				hasD = myConfig.objects.filter(device=x.deviceName)
				if hasD:
					hasD[0].caseStr = json.dumps(jsonStr, ensure_ascii=False)
					hasD[0].save()
				else:
					p = myConfig(device=x.deviceName)
					p.caseStr = json.dumps(jsonStr, ensure_ascii=False)
					p.save()
				server = jenkins.Jenkins(x.url, username=x.username, password=x.password)
				server.build_job(job_name)  # 执行构建
				build_number = server.get_job_info(job_name)['lastBuild']['number']
				# 报告存入report，需要ids
				if end >= len(cases):	# end + 步长超过就不要在分了，直接结束
					time_case = jsonStr['timeStamp'] + '_' + ('_').join([str(x) for x in list(newid)[start:]])
				else:
					time_case = jsonStr['timeStamp'] + '_' + ('_').join([str(x) for x in list(newid)[start:end]])

				pp = reportsList(timeStamp=time_case)
				pp.buildNUM = '#' + str(build_number + 1)
				pp.reportURL = ("http://10.113.1.35:8000/auto/api_report_page?timeStamp=" + "%s" % jsonStr['timeStamp'])
				pp.status = str(server.get_build_info(job_name,build_number)['building'])
				pp.deviceName = deviceList.objects.get(deviceName=x.deviceName)
				pp.save()
				start += mdl
			else:
				break
	return HttpResponse('OK')

# 返回接口配置
def auto_response(request):
	try:
		deviceN = request.GET['deviceName']
		jsonStr = myConfig.objects.get(device=deviceN).caseStr
		return HttpResponse(jsonStr, content_type="application/json")
	except:
		return HttpResponse('No Such Device')

# 定义删除
def auto_del(request):
	try:
		id = request.GET['id'].split(',')
		for x in id:
			myCase = caseList.objects.get(id=x)
			doDB('delete', [x for x in myCase.caseName])
			myCase.in_use = '0'
			myCase.save()
		data = 'success'
	except KeyError as e:
		data = ('ERR:删除失败，请联系管理员查看\n:%s' % e)
	finally:
		return HttpResponse(data)


def auto_copy(request):
	try:
		id = request.GET['id']
		cName = request.GET['cName']
		if cName:
			if caseList.objects.filter(caseName=cName):
				data = '0' # 重复名称
			else:
				sorceCase = caseList.objects.get(id=id)
				p = caseList(caseName=cName)
				p.type_field = sorceCase.type_field
				p.plantform = sorceCase.plantform
				p.version = sorceCase.version
				p.case = sorceCase.case
				p.des = sorceCase.des
				p.in_use = sorceCase.in_use
				p.owner = sorceCase.owner
				p.second_Type_id = '1'
				p.save()
				bgstep = len(json.loads(sorceCase.case))
				mydbList = [cName, bgstep, sorceCase.case, sorceCase.in_use, sorceCase.type_field.type_field, sorceCase.version]
				doDB('insert',mydbList)
				data = '1' # 用例名OK
		else:
			data = '3' # 没输入
	except KeyError as e:
		data = '2'
		logger.info('ERR:复制失败，请联系管理员查看.\n%s' % e)
	finally:
		return HttpResponse(data)


def new_add(request):
	type_all = caseType.objects.all().order_by('type_name')
	s_type_all = secondType.objects.all().order_by('second_Type')
	type_list = [x for x in type_all]
	second_type_list = [x for x in s_type_all]
	# 为了校验用例名
	casenames = [x['caseName'] for x in caseList.objects.filter(in_use='1').values('caseName')]
	# 用户list 和 版本list
	user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
	versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
	plant = ['Android','IOS','M']
	nav_list = navList()
	return render(request, 'new_add.html', locals())

# todo
def new_save(request):
	my_form = dict(request.POST)
	try:
		caseName = my_form.get('caseName')[0]
		csType = caseType.objects.get(type_name=my_form.get('type')[0]).type_field
		caseVersion = my_form.get('version')[0]
		casePlantform = my_form.get('plantform')[0]
		caseStatus = my_form.get('canUse')[0]
		caseDes = my_form.get('caseDes')[0]
		owner = my_form.get('owner')[0]
		s_Type = my_form.get('second_Type')[0]
		caseStatus = '1' if caseStatus=='use' else '0'
		if casePlantform == 'IOS':
			defaultCase = '[{"type":"buttons","label":"","typeText":"","action":"click","des":""}]'
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
		if casePlantform == 'Android':
			mydbList = [caseName, 1, defaultCase, caseStatus, csType, caseVersion]
			doDB('insert', mydbList)
		# 获取当前用例ID
		myID = caseList.objects.filter(plantform=casePlantform).filter(caseName=caseName).values('id')[0]['id']
		return HttpResponseRedirect("/auto/new_edit/%s" % myID)
	except TypeError as e:
		data = ('Oh my god!!出错啦 %s' % e)
		logger.info(data)
		return HttpResponse(data)


def new_edit(request, id):
	# 反向解析json存入表单 首先从DB获取json字符串，并解析成数据类型
	if caseList.objects.filter(id=id).exists():
		json_dict = caseList.objects.filter(id=id).values()[0]
		# logger.info(json_dict)
		# 转义品类名称
		try:
			json_dict['type_field_id'] = caseType.objects.get(id=json_dict['type_field_id']).type_name
			json_dict['second_Type_id'] = secondType.objects.get(id=json_dict['second_Type_id']).second_Type
			# 取case部分转为数据格式
			BgStep = json.loads(json_dict['case'])
			json_dict.pop('case')
			targetname = []
			elementname = []
			where = []
			enterActivity = []
			# 判断plantform
			myPlantform = json_dict['plantform']
			# 转义json字符串中的字符串为中文
			type_all = caseType.objects.all().order_by('type_name')
			s_type_all = secondType.objects.all().order_by('second_Type')
			type_list = [x for x in type_all]
			second_type_list = [x for x in s_type_all]
			user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
			versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
			plant = ['Android','IOS','M']
			nav_list = navList()
			if myPlantform == 'Android' or myPlantform == 'M':
				wait_list = ['等待','不等待']
				for x in BgStep:
					x['enterActivity'] = trans_me(x['enterActivity'],'where',json_dict['plantform'])
					x['where'] = trans_me(x['where'],'where',json_dict['plantform'])
					where.append(x['where'])
					enterActivity.append(x['enterActivity'])
					ai = ci = 1
					for y in x['action']:
						y['target']['targetName'] = trans_me(y['target']['targetName'],'targetName',json_dict['plantform'])
						targetname.append(y['target']['targetName'])
						y['actionCode'] = trans_me(y['actionCode'],'action',json_dict['plantform'])
						if y['needWait'] == True:
							y['needWait'] = '等待'
						else:
							y['needWait'] ='不等待'
						y['index'] = str(x['index']) + '-' + str(ai)
						ai += 1
					for y in x['checkString']:
						y['elementName'] = trans_me(y['elementName'],'targetName',json_dict['plantform'])
						elementname.append(y['elementName'])
						y['index'] = str(x['index']) + '-' + str(ci)
						ci += 1
						y['checkType'] = trans_me(y['checkType'],'checkString',json_dict['plantform'])
					control_list = new_select_list('action', json_dict['plantform'], json_dict['version'])
					where_list = new_select_list('where', json_dict['plantform'], json_dict['version'])
					target_list = new_select_list('targetName', json_dict['plantform'], json_dict['version'])
					checkType_list = new_select_list('checkString', json_dict['plantform'])
				return render(request, 'new_edit.html',locals())
			else:
				ai = 1
				for x in BgStep:
					x['index'] = str(ai)
					ai += 1
					x['action'] = trans_me(x['action'],'action',json_dict['plantform'])
					x['type'] = trans_me(x['type'],'type',json_dict['plantform'])
					targetname.append(x['label'])
					target_type_list = new_select_list('type', json_dict['plantform'], json_dict['version'])
					control_list = new_select_list('action', json_dict['plantform'], json_dict['version'])
					target_list = new_select_list('targetName', json_dict['plantform'], json_dict['version'])
				return render(request, 'ios_edit.html', locals())
		except AttributeError as e:
			logger.info("new_edit:%s" % e)
	else:
		logger.info("用例id %s 不存在" % id)
		return HttpResponseRedirect('/auto/new_add')

# IOS定义用例返回json
def auto_caseJson(request):
	"""调取参数:平台+timeStamp"""
		# 从config里读取ios的用例编号
		# caseName = request.GET['caseName']
	try:
		plantform = request.GET['plantform']
		if plantform == 'Android':
			casetimeStamp = request.GET['timeStamp']
		else:
			casetimeStamp = ''
		# 从reportlist里取timestamp对应的case_id
		try:
			if plantform == 'Android':
				# 这里有个BUG，如果timestamp存在包含关系，就嗝屁了
				ids = reportsList.objects.filter(timeStamp__contains=casetimeStamp)[0].timeStamp.split('_')[1:]
			else:
				iosID = deviceList.objects.get(deviceName='IOS').id
				ids = reportsList.objects.filter(deviceName_id=iosID).order_by('-create_time')[0].timeStamp.split('_')[1:]
			cases = []
			for x in ids:
				caseD = {
					"caseType": caseList.objects.get(id=x).type_field.type_field,
					"jsonStory": json.loads(caseList.objects.get(id=x).case),
				}
				# logger.info(x)
				cases.append(caseD)
			jsonStr = {
				"code": "1",
				"message": "",
				"data": cases
			}
		except:
			jsonStr = {
				"code": "-2",
				"message":"用例不存在"
			}
	except:
		jsonStr = {
			"code": "-1",
			"message":"参数错误,需要plantform和timeStamp"
		}
	finally:
		jsonStr = json.dumps(jsonStr, ensure_ascii=False)
		return HttpResponse(jsonStr, content_type="application/json")


@cache_page(15)
def test_list(request):
	# 右侧对应品类的用例列表
	dList = deviceList.objects.filter(in_use='1')   #设备列表
	testResults = []
	for x in dList:
		server = jenkins.Jenkins(x.url, username=x.username, password=x.password)
		rList = reportsList.objects.filter(deviceName__deviceName=x.deviceName).order_by('-create_time')[:20]    #结果列表
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
		testResults.append(x)
	return render(request, 'test_list.html',{
		'nav_list':navList(),
		'testResults':testResults,
		})

# 查询页面
def auto_search(request):
	# 需要品类、二品类、版本、所属人、平台
	type_all = caseType.objects.all().order_by('type_name')
	s_type_all = secondType.objects.all().order_by('second_Type')
	type_list = [x for x in type_all]
	second_type_list = [x for x in s_type_all]
	user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
	versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
	plant = ['Android','IOS','M']
	device_list = deviceList.objects.filter(in_use='1')
	nav_list = navList()
	casegroup = caseGroup.objects.all()
	return render(request, 'auto_search.html', locals())

#动态查询结果返回
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
	origin = caseList.objects.all()
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

# 当日报表邮件接口
def api_report(request):
	try:
		timeTarget = request.GET['timeStamp']
	except:
		jsonStr = {
			"code": "-1",
			"message":"参数错误,需要timeStamp"
		}
	else:
		cases = allBookRecording.objects.filter(timeStamp=timeTarget)
		# allin = testRecording.objects.filter(timeStamp=timeTarget)
		if cases:
			# 返回一个报告页面 URL，通过此url可以访问对应的数据构造页面
			jsonStr = {
				"code": "1",
				"data":[x.caseName for x in cases]
			}
			# 发邮件
			myUrl = ("http://10.113.1.35:8000/auto/api_report_page?timeStamp=%s" % timeTarget)
			err_list = cases.filter(status='danger')
			pass_list = cases.filter(status='success')
			allNum = cases.count()
			passNum = pass_list.count()
			failNum = err_list.count()
			passRate = round((passNum / allNum * 100),2)
			# sTime = allin.values('testStartDate').order_by('testStartDate')[0]['testStartDate']
			# eTime = allin.values('testDuration').order_by('-testDuration')[0]['testDuration']
			# testTime = (eTime - sTime).seconds
			# email发送
			html_string0 = "<h3>UI自动化报告</h3><h4><p>用例总数:%s | 通过:%s | 失败:%s</p><p>通过率:%s %%</p><p><a href=%s target=_blank>点击查看错误详情和截图</a></p></h4>" % (allNum, passNum, failNum, passRate, myUrl)
			html_string1 = ""
			html_string3 = "</table>"
			if err_list:
				html_string1 = "<h3 style='color:IndianRed'>错误列表</h3><table border=1 width=100%><tr style='background-color:DarkSalmon'><th>ID</th><th>品类</th><th>用例名称</th><th>状态</th><th>耗时</th><th>创建人</th></tr>\n\r"
				html_string2 = ""
				build_list = []
				for x in err_list:
					tmp = {
						'id':caseList.objects.filter(caseName=x.caseName)[0].id,
						'type':caseList.objects.filter(caseName=x.caseName)[0].type_field.type_name,
						'caseName':x.caseName,
						'status':x.status,
						'usedTime':x.usedTime,
						'user':caseList.objects.filter(caseName=x.caseName)[0].owner
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
		else:
			jsonStr = {
				"code": "-2",
				"message":"查无此人"
			}
	finally:
		result = json.dumps(jsonStr, ensure_ascii=False)
		return HttpResponse(result, content_type="application/json")

# 根据url参数返回报表页面
@cache_page(30)
def api_report_page(request):
	try:
		timeTarget = request.GET['timeStamp']
	except:
		message = "参数错误,需要timeStamp"
	else:
		Acases = allBookRecording.objects.filter(timeStamp=timeTarget).filter(testResultDoc__contains='platformName":"Android"')
		if Acases:
			Apass_list = [json.loads(x['testResultDoc']) for x in Acases.filter(status='success').values('testResultDoc')]
			Aerr_list = [json.loads(x['testResultDoc']) for x in Acases.filter(status='danger').values('testResultDoc')]
			AallNum = int(Acases.count())
			ApassNum = len(Apass_list)
			AfailNum = len(Aerr_list)
			Apass_list = trans_report_list(Apass_list)
			Aerr_list = trans_report_list(Aerr_list)
			if AallNum != 0:
				ApassRate = round((ApassNum / AallNum) * 100, 2)
			Atime = Acases.values('create_time')
			if Atime:
				AsTime = Atime.order_by('create_time')[0]['create_time']
				AeTime = Atime.order_by('-create_time')[0]['create_time']
				AtestTime = (AeTime - AsTime).seconds
		else:
			Amessage = '没有匹配内容'
		Mcases = allBookRecording.objects.filter(timeStamp=timeTarget).filter(testResultDoc__contains='platformName":"M"')
		if Mcases:
			Mpass_list = [json.loads(x['testResultDoc']) for x in Mcases.filter(status='success').values('testResultDoc')]
			Merr_list = [json.loads(x['testResultDoc']) for x in Mcases.filter(status='danger').values('testResultDoc')]
			MallNum = int(Mcases.count())
			MpassNum = len(Mpass_list)
			MfailNum = len(Merr_list)
			Mpass_list = trans_report_list(Mpass_list)
			Merr_list = trans_report_list(Merr_list)
			if MallNum != 0:
				MpassRate = round((MpassNum / MallNum) * 100, 2)
			Mtime = Mcases.values('create_time')
			if Mtime:
				MsTime = Mtime.order_by('create_time')[0]['create_time']
				MeTime = Mtime.order_by('-create_time')[0]['create_time']
				MtestTime = (MeTime - MsTime).seconds
		else:
			Mmessage = '没有匹配内容'
	finally:
		return render_to_response('report.html', locals())


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
			case = caseList.objects.filter(in_use='1').get(caseName=x.caseName)
			if user in case.owner:
				if x.status == 'danger':
					logger.info('search_report %s' % x.caseName)
					Aerr_list.append(json.loads(x.testResultDoc))
				else:
					Apass_list.append(json.loads(x.testResultDoc))
		for x in Mcases:
			case = caseList.objects.filter(in_use='1').get(caseName=x.caseName)
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

# 修改controlList同步修改用例case接口
def change_case(request):
	try:
		old = request.GET['old']
		new = request.GET['new']
	except:
		jsonStr = {
			"code": "-1",
			"message":"参数错误 need old,new"
		}
	else:
		cases = caseList.objects.filter(case__contains=old)
		if cases:
			for x in cases:
				x.case = x.case.replace(old,new)
				x.save()
			jsonStr = {
				'code':'1',
				'data':[x.caseName for x in cases]
			}
		else:
			jsonStr = {
				"code": "-2",
				"message":"没有匹配"
			}
	finally:
		result = json.dumps(jsonStr, ensure_ascii=False)
		return HttpResponse(result, content_type="application/json")

# 添加用例集
def auto_makeGroup(request):
	try:
		ids = [int(x) for x in request.GET['id'].split(',')]
		# ids = request.GET['id']
		groupName = request.GET['groupName']
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
			temp.save()
		data = 'success'
	except TypeError as e:
		logger.info('添加用例集报错：%s' % e)
		data = 'failed'
	finally:
		logger.info('添加用例集状态：%s' % data)
		return HttpResponse(data)

# group列表页
def auto_group(request):
	casegroup = caseGroup.objects.all()
	nav_list = navList()
	return render(request, 'case_group.html', locals())


# group编辑
def group_edit(request):
	groupID = request.GET.get('groupID')
	# 需要获取group信息、所有用例名信息、当前用例集用例名信息
	groupInfo = caseGroup.objects.get(id=groupID)
	gourpIDS = json.loads(groupInfo.caseID)
	allCase = caseList.objects.filter(in_use='1').values('id', 'caseName', 'des', 'owner').order_by('caseName')
	for x in allCase:
		if x['id'] in gourpIDS:
			x['sta'] = 'checked'
		else:
			x['sta'] = 'unchecked'
	nav_list = navList()
	logger.debug('%s' % allCase[:10])
	return render(request, 'group_edit.html', locals())


# 用例集编辑保存
def group_save(request):
	try:
		groupId = request.POST.get('ID')
		group = caseGroup.objects.get(id=groupId)
		group.des = request.POST.get('des')
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

def many_many(request):
	v = caseVersion.objects.all()
	c = controlList.objects.all()
	back = []
	for x in c:
		if not x.versionStr.all():
			for y in v:
				x.versionStr.add(y)
			x.save()
			back.append(x.controlName)
		else:
			continue
	back = json.dumps(back, ensure_ascii=False)
	return HttpResponse(back, content_type="application/json")


def sync_allbook(request):
	source_list = allBookRecording.objects.filter(timeStamp__contains='autoTestIn')
	other_list = allBookRecording.objects.exclude(timeStamp__contains='est')
	ok_list = []
	for x in source_list:
		try:
			ctime = datetime.datetime.strptime(x.timeStamp.split('autoTestIn')[1],'%Y%m%d').strftime('%Y-%m-%d %H:%M:%S')
			x.create_time = ctime
			x.save()
			ok_list.append(x.id)
		except:
			pass
	for x in other_list:
		try:
			ctime = datetime.datetime.fromtimestamp(int(x.timeStamp)).strftime('%Y-%m-%d %H:%M:%S')
			x.create_time = ctime
			x.save()
			ok_list.append(x.id)
		except:
			pass
	back = json.dumps({'code':'1','oklist':ok_list})
	return HttpResponse(back, content_type="application/json")
