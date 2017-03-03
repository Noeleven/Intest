from django.shortcuts import render,render_to_response
from automation.models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.forms.models import model_to_dict
from decimal import Decimal
import time
import json
import mysql.connector
import datetime


# Create your views here.
# 定义品类列表
def nav_list():
    nav_list = []
    all = {
        'type':'全部',
        'num':len(caseList.objects.filter(in_use='1')),
    }
    nav_list.append(all)
    for t in caseType.objects.all():
        show_type = {
            'type':t.type_name,
            'num':len(caseList.objects.filter(type_field=t.id).filter(in_use='1')),
        }
        nav_list.append(show_type)
    nouse = {
        'type':'废弃',
        'num':len(caseList.objects.filter(in_use='0')),
    }

    nav_list.append(nouse)
    return nav_list
# 定义下拉内容
def select_list(controlListType):
    # 设置目标元素列表
    target_all = controlList.objects.filter(TYPE=controlListType).order_by('controlName')
    target_list = [x for x in target_all]
    return target_list
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
def auto_list(request, my_type='全部'):
    # 右侧对应品类的用例列表
    if my_type == '废弃':
        show_list = caseList.objects.filter(in_use='0')
    elif my_type != '全部':
        type_id = caseType.objects.filter(type_name=my_type)[0].id
        show_list = caseList.objects.filter(in_use='1').filter(type_field=type_id)
    else:
        show_list = caseList.objects.filter(in_use='1')

    navList = nav_list()
    return render(request, 'auto_list.html',{
        'show_list':show_list,
        'nav_list':navList,
        'my_type':my_type,
        })
# 添加页面list
def auto_add(request):
    type_all = caseType.objects.all().order_by('type_name')
    type_list = [x for x in type_all]
    casenames = [x['caseName'] for x in caseList.objects.filter(in_use='1').values('caseName')]

    return render(request, 'auto_add.html',{
        'type_list':type_list,
        'control_list':select_list('action'),
        'where_list':select_list('where'),
        'target_list':select_list('targetName'),
        'nav_list':nav_list(),
        'checkType_list':select_list('checkString'),
        'casenames':casenames
    })
# 添加保存
def auto_save(request):
    my_form = dict(request.POST)
    print(my_form)
    try:
        caseName = my_form.get('caseName')[0]
        csType = caseType.objects.get(type_name=my_form.get('type')[0]).type_field
        caseVersion = my_form.get('version')[0]
        casePlantform = 'Android'
        caseStatus = my_form.get('canUse')[0]
        caseDes = my_form.get('caseDes')[0]
        owner = my_form.get('owner')[0]
    except TypeError as e:
        print('oh my god!! %s' % e)

    caseStatus = '1' if caseStatus=='use' else '0'
    # 处理生成json,等json格式，根据plantform类型生成不同的json
    json_home = []
    # 统计有多少大步
    bigstep = len(set([x.split('-')[0] for x in my_form.get('index_step')]))
    #起始下标
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
        expendIndex += len(expendlist)
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
        json_home.append(bgElement)

    my_case = json.dumps(json_home, ensure_ascii=False)
    print(('*' * 20 + '\n' + '%s') % my_case)
    # 存储DB
    mydbList = [caseName, bigstep, my_case, caseStatus, csType, caseVersion]
    doDB('insert', mydbList)

    p = caseList(caseName=caseName)
    p.type_field = caseType.objects.get(id=caseType.objects.filter(type_field=csType)[0].id)
    p.plantform = casePlantform
    p.version = caseVersion
    p.case = my_case
    p.des = caseDes
    p.in_use = caseStatus
    p.owner = owner
    p.save()
    # 判断动作
    return HttpResponseRedirect("/auto/auto_list/%s" % my_form.get('type')[0])
# 编辑页面list
def auto_edit(request, id):
    # 反向解析json存入表单
    try:
        # 首先从DB获取json字符串，并解析成数据类型
        json_dict = caseList.objects.filter(id=id).values()[0]
        # 转义品类名称
        json_dict['type_field_id'] = caseType.objects.get(id=json_dict['type_field_id']).type_name
        # 取case部分转为数据格式
        BgStep = json.loads(json_dict['case'])
        # 去掉case部分，避免数据重复导致的性能下降
        json_dict.pop('case')
        # 依次 什么元素 是否校验 校验类型 是否页面 是否元素 是否等待
        targetname = []
        elementname = []

        # print(BgStep)
        # 转义json字符串中的字符串为中文
        for x in BgStep:
            x['enterActivity'] = trans_me(x['enterActivity'],'where',json_dict['plantform'])
            x['where'] = trans_me(x['where'],'where',json_dict['plantform'])
            ai = 1
            ci = 1
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

        type_all = caseType.objects.all().order_by('type_name')
        type_list = [x for x in type_all]
        wait_list = ['等待','不等待']
        return render(request, 'auto_edit.html',{
            'type_list':type_list,
            'control_list':select_list('action'),
            'where_list':select_list('where'),
            'target_list':select_list('targetName'),
            'checkType_list':select_list('checkString'),
            'nav_list':nav_list(), 'json_dict':json_dict,
            'BgStep':BgStep,
            'id':id,"targetname":targetname, 'elementname':elementname,
            'wait_list':wait_list,
        })
    except KeyError as e:
        print("===%s" % e)
        return HttpResponseRedirect('/auto/auto_add')
# 编辑保存
def auto_edit_save(request, id):
    my_form = dict(request.GET)
    case_obj = caseList.objects.filter(id=id)[0]
    try:
        caseName = case_obj.caseName
        csType = caseType.objects.get(type_name=my_form.get('type')[0]).type_field
        caseVersion = my_form.get('version')[0]
        casePlantform = 'Android'
        caseStatus = my_form.get('canUse')[0]
        caseDes = my_form.get('caseDes')[0]
        owner = my_form.get('owner')[0]
    except TypeError as e:
        print('oh my god!! %s' % e)

    caseStatus = '1' if caseStatus=='use' else '0'
    # 处理生成json,等json格式，根据plantform类型生成不同的json
    json_home = []
    # 统计有多少大步
    bigstep = len(set([x.split('-')[0] for x in my_form.get('index_step')]))
    #起始下标
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
    print(('*' * 20 + '\n' + '%s') % my_case)
    # 存储DB
    mydbList = [caseName, bigstep, my_case, caseStatus, csType, caseVersion]
    conn = mysql.connector.connect(user='root', password='lvmama', database='lmmpicTest', host='127.0.0.1')
    cursor = conn.cursor(buffered=True)
    inputTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('select * from testStory where caseName=%s', (caseName,))
    values = cursor.fetchall()
    if values:
        doDB('update', mydbList)
    else:
        doDB('insert', mydbList)
    conn.commit()
    cursor.close()
    conn.close()
    p = case_obj
    p.case = my_case
    p.type_field = caseType.objects.get(id=caseType.objects.filter(type_field=csType)[0].id)
    p.plantform = casePlantform
    p.version = caseVersion
    p.owner = owner
    p.des = caseDes
    p.in_use = caseStatus
    p.modify_time = datetime.datetime.now()
    p.save()
    # 判断动作
    return HttpResponseRedirect("/auto/auto_list/%s" % my_form.get('type')[0])
# 点击生成配置
def auto_config(request):
    # 转为id列表
    ids = request.GET['vals'].split(',')
    device = request.GET['device']
    print(device)
    if device == '62001':
        device = '127.0.0.1:62001'
        APPIUMSERVERSTART = "D:\\nodejs\\appium.cmd -a 10.113.2.70 -p 47231 -bp 47241 --chromedriver-port 19515 --command-timeout 300"
        appiumServicePort = 47231
        lvsessionid = "a69161be-91ec-4e29-8815-36273fdef8d5"
    else:
        APPIUMSERVERSTART = "D:\\nodejs\\appium.cmd -a 10.113.2.70 -p 47232 -bp 47242 --chromedriver-port 29515 --command-timeout 300"
        device = '127.0.0.1:62025'
        appiumServicePort = 47232
        lvsessionid = "2763ca61-9bd0-44b6-86a3-a3cffcaa78bf"
    cases = []
    # 转为用例名称列表
    for x in caseList.objects.values('id','caseName'):
        if str(x['id']) in ids:
            cases.append(x['caseName'])
    jsonStr = {
        "APPIUMSERVERSTART": APPIUMSERVERSTART,
        "appiumServicePath": "10.113.2.70",
        "appiumServicePort": appiumServicePort,
        "appVersion": "7.8.5",
        "deviceName": device,
        "platformVersion": "4.4.2",
        "platformName": "Android",
        "lvsessionid": lvsessionid,
        "timeout": 30,
        "appPackage": "com.gift.android",
        "appLaunchActivity": "com.gift.android.activity.splash.WelcomeActivity",
        "testCaseSQL": cases,
    }
    hasD = myConfig.objects.filter(device=device)
    if hasD:
        hasD[0].caseStr = json.dumps(jsonStr, ensure_ascii=False)
        hasD[0].save()
    else:
        p = myConfig(device=device)
        p.caseStr = json.dumps(jsonStr, ensure_ascii=False)
        p.save()
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
        id = request.GET['id']
        myCase = caseList.objects.get(id=id)
        caseName = myCase.caseName
        myList = [caseName]
        doDB('delete', myList)
        myCase.delete()
        data = 'success'
        return HttpResponse(data)
    except IOError as e:
        data = 'err'
        print('删除失败，请联系管理员查看.err:%s' % e)
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
                p.save()
                bgstep = len(json.loads(sorceCase.case))
                mydbList = [cName, bgstep, sorceCase.case, sorceCase.in_use, sorceCase.type_field.type_field, sorceCase.version]
                doDB('insert',mydbList)
                data = '1' # 用例名OK
        else:
            data = '3' # 没输入
        return HttpResponse(data)
    except IOError as e:
        data = '2'
        print('复制失败，请联系管理员查看.err:%s' % e)
        return HttpResponse(data)
