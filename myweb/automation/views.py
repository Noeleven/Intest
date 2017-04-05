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


# Create your views here.
def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

def nav_list():
    nav_list = []
    # 大分类
    someList = []
    for x in caseType.objects.values('id','type_name'):
        bDict = {}
        bDict['type'] = x['type_name']
        bDict['sq'] = caseList.objects.filter(type_field=x['id']).filter(in_use='1')
        someList.append(bDict)
    someList.append({'type':'废弃','sq':caseList.objects.filter(in_use='0')})
    # 小分类
    for y in someList:
        aDict = {
            'type':y['type'],
            'num':len(y['sq']),
            'sType':[]
        }
        for tt in secondType.objects.all():
            tDict = {}
            Stype = tt.second_Type
            tDict['type'] = Stype
            if y['type'] == "废弃":
                Ftype = ''
                tDict['num'] = len(caseList.objects.filter(in_use='0').filter(second_Type=tt.id))
            else:
                Ftype = caseType.objects.get(type_name=y['type']).id
                tDict['num'] = len(caseList.objects.filter(type_field=Ftype).filter(in_use='1').filter(second_Type=tt.id))
            aDict['sType'].append(tDict)
        nav_list.append(aDict)
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
# 接口签名
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

# controllist翻译
def trans_me(aname, type, ptype):
    # 转换controlList函数，要注意controlType是0,1
    if ptype.lower() == 'android':
        cc = '0'
    elif ptype.lower() == 'ios':
        cc = '1'
    else:
        cc = '2'
    targetRange = controlList.objects.filter(controlType=cc).filter(TYPE=type)
    if targetRange.filter(controlName=aname):
        bname = targetRange.get(controlName=aname).controlFiled
    elif targetRange.filter(controlFiled=aname):
        bname = targetRange.get(controlFiled=aname).controlName
    else:
        bname = aname
    return bname
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
        print('doDB unknow!')
    conn.commit()
    cursor.close()
    conn.close()
# 导航list
def auto_list(request):
    try:
        my_type = request.GET['my_type']
    except KeyError as e:
        print(e)
        my_type='全部'
    f_type = my_type.split('_')[0]  #出境
    if f_type == "全部":
        show_list = caseList.objects.filter(in_use='1')
    elif f_type == '废弃':
        show_list = caseList.objects.filter(in_use='0')
    else:
        s_type = my_type.split('_')[1]
        type_id = caseType.objects.filter(type_name=f_type)[0].id
        s_type_id = secondType.objects.filter(second_Type=s_type)[0].id
        show_list = caseList.objects.filter(in_use='1').filter(type_field=type_id).filter(second_Type=s_type_id)
    device_list = deviceList.objects.filter(in_use='1').values('deviceName')
    navList = nav_list()
    return render(request, 'auto_list.html',{
        'show_list':show_list,
        'nav_list':navList,
        'my_type':my_type,
        'device_list':device_list
        })
# 编辑保存
def auto_edit_save(request, id):
    my_form = dict(request.GET)
    # print(my_form)
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
        print('oh my god!! %s' % e)
    caseStatus = '1' if caseStatus=='use' else '0'
    # 处理生成json,等json格式，根据plantform类型生成不同的json
    json_home = []
    # 统计有多少大步
    bigstep = len(set([x.split('-')[0] for x in my_form.get('index_step')]))
    #起始下标
    if casePlantform == 'Android':
        startIndex = expendIndex = 0
        for bgSub in range(bigstep):
            # 大步字典
            bgElement = {
                "storyDescription":my_form.get('storyDescription')[bgSub],
                "index":bgSub + 1,
                "where":trans_me(my_form.get('where')[bgSub],'where',casePlantform),
                'action':[],
                "enterActivity":trans_me(my_form.get('enterActivity')[bgSub],'where',casePlantform),
                "checkString":[],
                }
            # 预期列表，处理checkString
            expendlist = [x for x in my_form.get('index_expend') if x.split('-')[0] == str(bgSub + 1)]

            for smExpend in range(expendIndex, expendIndex + len(expendlist)):
                cType = my_form.get('checkType')[smExpend]
                eName = my_form.get('elementname')[smExpend]
                expendDict = {
                    "checkType": trans_me(cType, 'checkString', casePlantform),
                    "expeted": my_form.get('expeted')[smExpend],
                    "elementName": trans_me(eName, 'targetName', casePlantform),
                }
                bgElement['checkString'].append(expendDict)

            # 动作列表['1-1','1-2','2-1']
            steplist = [x for x in my_form.get('index_step') if x.split('-')[0] == str(bgSub + 1)]
            # 循环小步下标，获取数值
            for smSub in range(startIndex, startIndex + len(steplist)):
                actionDict = {
                    "actionCode": trans_me(my_form.get('actionCode')[smSub], 'action', casePlantform),
                    "behaviorPara":{
                        "inputValue":my_form.get('inputValue')[smSub],
                        },
                    "target": {
                        "targetName": trans_me(my_form.get('targetName')[smSub], 'targetName', casePlantform),
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
                'action':trans_me(my_form.get('actionCode')[bgSub], 'action', casePlantform),
                'type':trans_me(my_form.get('typeCode')[bgSub], 'type', casePlantform),
                'typeText':my_form.get('inputValue')[bgSub],
                'label':my_form.get('targetName')[bgSub],
                # 'sub':{
                #     'type':'',
                #     'label':'',
                #     },
                }
            json_home.append(bgElement)
        my_case = json.dumps(json_home, ensure_ascii=False)
    else:
        pass
    # print(('*' * 20 + '\n' + '%s') % my_case)
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
    device = request.GET['device']  #   待测设备
    mydevice = deviceList.objects.filter(deviceName=device)[0]  #待测设备属性
    myTime = int(time.time())   # 取时间串
    if device == 'IOS':
        #IOS jenkins
        server = jenkins.Jenkins('http://10.113.1.193:8080', username='autotest', password='111111')
        jsonStr = {
            "deviceName": mydevice.deviceIP,    # 设备:ip
            "appVersion": mydevice.appVersion,  #   app版本
            # "appiumServicePath": mydevice.appiumServicePath, # ip：端口
            "platformVersion": mydevice.platformVersion,    # 操作系统版本
            "platformName": mydevice.platformName,  # AD还是IOS
            # "lvsessionid": mydevice.lvsessionid,
            "timeStamp": str(myTime),
        }
    else:
        # jenkins
        server = jenkins.Jenkins('http://10.113.2.70:8080/jenkins', username='admin', password='111111')
        cases = []
        for x in caseList.objects.values('id','caseName'):
            if str(x['id']) in ids:
                cases.append(x['caseName'])
        jsonStr = {
            "APPIUMSERVERSTART": mydevice.APPIUMSERVERSTART,
            "appiumServicePath": mydevice.appiumServicePath,
            "appiumServicePort": mydevice.appiumServicePort,
            "appVersion": mydevice.appVersion,
            "deviceName": mydevice.deviceIP,
            "platformVersion": mydevice.platformVersion,
            "platformName": mydevice.platformName,
            "lvsessionid": mydevice.lvsessionid,
            "timeout": mydevice.timeWait,
            "appPackage": mydevice.appPackage,
            "appLaunchActivity": mydevice.appLaunchActivity,
            "testCaseSQL": cases,   # 待改
            "timeStamp": str(myTime),
        }
    job_name = mydevice.job_name
    # 判断有没有该设备，并存入config表供jenkins调用，但不需要timeStamp的ids
    hasD = myConfig.objects.filter(device=mydevice.deviceIP)
    if hasD:
        hasD[0].caseStr = json.dumps(jsonStr, ensure_ascii=False)
        hasD[0].save()
    else:
        p = myConfig(device=mydevice.deviceIP)
        p.caseStr = json.dumps(jsonStr, ensure_ascii=False)
        p.save()
    server.build_job(job_name)  # 执行构建
    build_number = server.get_job_info(job_name)['lastBuild']['number']
    # 报告存入report，需要ids
    time_case = jsonStr['timeStamp'] + '_' + ('_').join(ids)
    pp = reportsList(timeStamp=time_case)
    pp.buildNUM = '#' + str(build_number + 1)
    if device == 'IOS':
        pp.reportURL = ('http://10.113.1.193:8001/%s/report.html' % (build_number + 1))
        print(pp.reportURL)
    else:
        pp.reportURL = ("http://10.113.2.70:8080/htmlReport/AndroidAutoTest/autoTest" + "%s.html" % str(myTime))
    pp.status = str(server.get_build_info(job_name,build_number)['building'])
    pp.deviceName = deviceList.objects.get(deviceName=device)
    pp.save()
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
            caseName = myCase.caseName
            myList = [caseName]
            doDB('delete', myList)
            # myCase.delete()
            myCase.in_use = '0'
            myCase.save()
        data = 'success'
        return HttpResponse(data)
    except KeyError as e:
        data = ('ERR:删除失败，请联系管理员查看\n:%s' % e)
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
        return HttpResponse(data)
    except KeyError as e:
        data = '2'
        print('ERR:复制失败，请联系管理员查看.\n%s' % e)
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
    return render(request, 'new_add.html',{
        'type_list':type_list,
        'nav_list':nav_list(),
        'casenames':casenames,
        'user_list':user_list,
        'versionList':versionList,
        'plant':plant,
        'second_type_list':second_type_list
    })
# todo
def new_save(request):
    my_form = dict(request.POST)
    # print(my_form)
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
        if casePlantform == 'Android':
            defaultCase = '[{"enterActivity":"","index":1,"storyDescription":"","action":[{"target":{"targetName":""},"actionCode":"click","behaviorPara":{"inputValue":""},"needWait":true}],"where":"","checkString":[{"checkType":"","elementName":"","expeted":""}]}]'
        elif casePlantform == 'IOS':
            defaultCase = '[{"type":"buttons","label":"","typeText":"","action":"click","des":""}]'
        else:
            defaultCase == ''
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
        print(data)
        return HttpResponse(data)


def new_edit(request, id):
    # 反向解析json存入表单
    try:
        # 首先从DB获取json字符串，并解析成数据类型
        json_dict = caseList.objects.filter(id=id).values()[0]
        # print(json_dict)
        # 转义品类名称
        json_dict['type_field_id'] = caseType.objects.get(id=json_dict['type_field_id']).type_name
        json_dict['second_Type_id'] = secondType.objects.get(id=json_dict['second_Type_id']).second_Type
        # 取case部分转为数据格式
        BgStep = json.loads(json_dict['case'])
        json_dict.pop('case')
        targetname = []
        elementname = []
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
        if myPlantform == 'Android' or myPlantform == 'M':
            wait_list = ['等待','不等待']
            for x in BgStep:
                x['enterActivity'] = trans_me(x['enterActivity'],'where',json_dict['plantform'])
                x['where'] = trans_me(x['where'],'where',json_dict['plantform'])
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
            return render(request, 'new_edit.html',{
                'type_list':type_list,
                'second_type_list':second_type_list,
                'control_list':new_select_list('action', json_dict['plantform'], json_dict['version']),
                'where_list':new_select_list('where', json_dict['plantform'], json_dict['version']),
                'target_list':new_select_list('targetName', json_dict['plantform'], json_dict['version']),
                'checkType_list':new_select_list('checkString', json_dict['plantform']),
                'nav_list':nav_list(),
                'json_dict':json_dict,
                'BgStep':BgStep,
                'id':id,
                "targetname":targetname,
                'elementname':elementname,
                'wait_list':wait_list,
                'user_list':user_list,
                'versionList':versionList,
                'plant':plant
            })
        else:
            ai = 1
            for x in BgStep:
                x['index'] = str(ai)
                ai += 1
                x['action'] = trans_me(x['action'],'action',json_dict['plantform'])
                x['type'] = trans_me(x['type'],'type',json_dict['plantform'])
                targetname.append(x['label'])
            return render(request, 'ios_edit.html', {
                'type_list':type_list,
                'second_type_list':second_type_list,
                'target_type_list':new_select_list('type', json_dict['plantform'], json_dict['version']),
                'control_list':new_select_list('action', json_dict['plantform'], json_dict['version']),
                'target_list':new_select_list('targetName', json_dict['plantform'], json_dict['version']),
                'nav_list':nav_list(),
                'json_dict':json_dict,
                'BgStep':BgStep,
                'id':id,
                "targetname":targetname,
                'user_list':user_list,
                'versionList':versionList,
                'plant':plant
            })
    except KeyError as e:
        print("===%s" % e)
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
                print(x)
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
    dList = deviceList.objects.filter(in_use='1').values('deviceName','job_name')   #设备列表
    testResults = []


    for x in dList:
        if x['deviceName'] == 'IOS':
            server = jenkins.Jenkins('http://10.113.1.193:8080/', username='autotest', password='111111')
        else:
            server = jenkins.Jenkins('http://10.113.2.70:8080/jenkins', username='admin', password='111111')
        xDict = x
        rList = reportsList.objects.filter(deviceName__deviceName=x['deviceName']).order_by('-create_time')[:20]    #结果列表
        xDict['buildLog'] = []
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
            # myDict['status'] = 'False'
            try:
                myDict['status'] = str(server.get_build_info(xDict['job_name'], int(y.buildNUM[1:]))['result'])
            except:
                myDict['status'] = 'queue'
            # print(myDict['status'])
            xDict['buildLog'].append(myDict)
        testResults.append(xDict)
    # queue_num = len(server.get_queue_info())
    return render(request, 'test_list.html',{
        'nav_list':nav_list(),
        'testResults':testResults,
        # 'queue_num':queue_num
        })

def auto_search(request):
    # 需要品类、二品类、版本、所属人、平台
    type_all = caseType.objects.all().order_by('type_name')
    s_type_all = secondType.objects.all().order_by('second_Type')
    type_list = [x for x in type_all]
    second_type_list = [x for x in s_type_all]
    user_list = [x['userName'] for x in caseUser.objects.filter(userStatus=1).values('userName').order_by('userName')]
    versionList = [x['versionStr'] for x in caseVersion.objects.values('versionStr').order_by('-versionStr')]
    plant = ['Android','IOS','M']
    device_list = deviceList.objects.filter(in_use='1').values('deviceName')
    return render(request, 'auto_search.html',{
        'type_list':type_list,
        'nav_list':nav_list(),
        'user_list':user_list,
        'versionList':versionList,
        'plant':plant,
        'second_type_list':second_type_list,
        'device_list':device_list
    })

def search_result(request):
    myrequest = dict(request.GET)
    # 处理下key带[]的问题
    for k,v in myrequest.items():
        if '[]' in k:
            k1 = k.replace('[]','')
            myrequest.pop(k)
            myrequest[k1] = v
    # print(myrequest)
    # 每个key值循环取并集，最后取交集
    origin = caseList.objects.all()
    if_list = {'ids':[],'names':[],'types':[],'secs':[],'vers':[],'plans':[],'owns':[],'dess':[]}
    num = 0
    for m,n in myrequest.items():
        if n[0] == '':  # 参数没值就pass
            num += 1
            pass
        else:   # 有值就循环遍历
            for x in n:
                if m == 'caseId':
                    if_list['ids'] += origin.filter(id__contains=x)
                elif m == 'caseName':
                    if_list['names'] += origin.filter(caseName__contains=x)
                elif m == 'caseType':
                    if_list['types'] += origin.filter(type_field__type_name__contains=x)
                elif m == 'secondType':
                    if_list['secs'] += origin.filter(second_Type__second_Type__contains=x)
                elif m == 'plantform':
                    if_list['plans'] += origin.filter(plantform__contains=x)
                elif m == 'version':
                    if_list['vers'] += origin.filter(version__contains=x)
                elif m == 'note':
                    if_list['dess'] += origin.filter(des__contains=x)
                elif m == 'owner':
                    if_list['owns'] += origin.filter(owner__contains=x)
                else:
                    continue
    print(num)
    if num == 8:
        show_list = origin
        return render_to_response('auto_ajax.html', locals())
    else:
        # 现在不一定每个list都有值，需要判断过滤掉没有的值，首先清空没有值的形成一个list
        result = [y for x,y in if_list.items() if y]
        # 遍历这个list 并求交集
        try:
            show_list = set(result[0])
            for x in result[1:]:
                show_list &= set(x)
            # show_list = [x for x in show_list]
            response = HttpResponse()
            response['Content-Type'] = "text/json"
            return render_to_response('auto_ajax.html', locals())
        except Exception as e:
            print(e)
            return render_to_response('auto_ajax.html', locals())
