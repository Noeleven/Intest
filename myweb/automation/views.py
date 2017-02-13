from django.shortcuts import render,render_to_response
from automation.models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.forms.models import model_to_dict
from decimal import Decimal
import time
import json
import mysql.connector
import datetime
# 定义品类列表
def nav_list():
    nav_list = []
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

def select_list():
    # 设置品类列表
    type_all = caseType.objects.all().order_by('type_name')
    type_list = [x for x in type_all]

    # 设置动作列表
    control_all = controlList.objects.filter(TYPE='action')
    control_list = [x for x in control_all]
    where_all = controlList.objects.filter(TYPE='where')
    where_list = [x for x in where_all]
    return type_list, control_list, where_list
# Create your views here.
def auto_list(request, my_type='all'):
    # 右侧对应品类的用例列表
    if my_type == '废弃':
        show_list = caseList.objects.filter(in_use='0')
    elif my_type != 'all':
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

def auto_add(request):
    return render(request, 'auto_add.html',{
        'type_list':select_list()[0],
        'control_list':select_list()[1],
        'where_list':select_list()[2],
        'nav_list':nav_list(),
    })

def auto_edit(request, id):
    # 反向解析json存入表单
    try:
        # 首先从DB获取json字符串，并解析成数据类型
        json_dict = caseList.objects.filter(id=id).values()[0]
        # 转义
        json_dict['type_field_id'] = caseType.objects.filter(id=json_dict['type_field_id'])[0].type_name
        # 大步骤确认
        BgStep = json.loads(json_dict['case'])
        # 去掉完整json里的case部门，避免数据重复导致的性能下降
        json_dict.pop('case')
        # 获取where列表 校验方法和进入目标页的描述
        where = [x['where'] for x in BgStep]
        checkType = []
        for x in BgStep:
            print(type(x['checkString']['checkType']))
            if x['checkString']['checkType'] == 'enterActivity':
                somecheck = '是否进入目标页面'
            else:
                somecheck = '是否是指定元素'
            checkType.append(somecheck)
        # 获取needCheck描述
        needCheck = []
        for x in BgStep:
            print(type(x['checkString']['needCheck']))
            if x['checkString']['needCheck'] == True:
                somecheck = '校验'
            else:
                somecheck = '不校验'
            needCheck.append(somecheck)
        enterActivity = [x['checkString']['enterActivity'] for x in BgStep]

        #
        # testcase = [
        #     {
        #     "checkString":{
        #         "enterActivity": "门票频道页",
        #         "checkType": "enterActivity",
        #         "needCheck": "true"},
        #     "action": [{
        #         "behaviorPara": {"inputValue": ""},
        #         "needTarget": "true",
        #         "target": {
        #             "elementName": "定位代码1",
        #             "itemName": "",
        #             "targetName": "目标元素名1",
        #             "selectorType": "id"},
        #         "needWait": "false",
        #         "actionCode": "enter"
        #         }],
        #     },

        return render(request, 'auto_edit.html',{
            'type_list':select_list()[0],
            'control_list':select_list()[1],
            'where_list':select_list()[2],
            'nav_list':nav_list(), 'json_dict':json_dict,
            'BgStep':BgStep, 'where':where,
            'needCheck':needCheck, 'enterActivity':enterActivity, 'checkType':checkType,
        })
    except KeyError as e:
        print("===%s" % e)
        return HttpResponseRedirect('/auto/auto_add')


def auto_save(request):
    my_form = dict(request.POST)
    # 获取表单信息
    print(my_form)
    try:
        caseName = my_form.get('caseName')[0]
        csType = caseType.objects.filter(type_name=my_form.get('type')[0])[0].type_field
        caseVersion = my_form.get('version')[0]
        casePlantform = my_form.get('plantform')[0]
        PlantformDict = {'Android':'0', 'IOS':'1', 'M':'2'}
        PlantformNum = PlantformDict[casePlantform]
        caseStatus = my_form.get('canUse')[0]
        caseDes = my_form.get('caseDes')[0]
    except TypeError as e:
        print('oh my god!! %s' % e)

    if caseStatus == 'use':
        caseStatus = '1'
    else:
        caseStatus = '0'
    # 处理生成json,等json格式，根据plantform类型生成不同的json
    json_home = []
    # 统计有多少大步
    bigstep = len(set([x.split('-')[0] for x in my_form.get('index_1_1')]))
    #起始下标
    startIndex = 0
    for bgSub in range(bigstep):
        checkType = controlList.objects.filter(controlName=my_form.get('checkType')[bgSub]).filter(controlType=PlantformNum)[0]
        # 大步字典
        bgElement = {
            "storyDescription":my_form.get('storyDescription')[bgSub],
            "index":bgSub + 1,
            "where":my_form.get('where')[bgSub],
            'action':[],
            "expeted":my_form.get('expeted')[bgSub],
            "checkString":{
                "checkType":checkType.controlFiled,
                "needCheck":(bool(1) if my_form.get('needCheck')[bgSub] == '校验' else bool(0)),
                },
            }
        # 判断校验类型
        if bgElement['checkString']['checkType'] == 'enterActivity':
            bgElement['checkString']['enterActivity'] = my_form.get('enterActivity')[bgSub]
            bgElement['checkString']['elementName'] = ''
        elif bgElement['checkString']['checkType'] == 'elementName':
            bgElement['checkString']['elementName'] = my_form.get('elementname')[bgSub]
            bgElement['checkString']['enterActivity'] = ''
        else:
            pass

        # 小步列表['1-1','1-2','2-1']
        steplist = [x for x in my_form.get('index_1_1') if x.split('-')[0] == str(bgSub + 1)]
        # 循环小步下标，获取数值
        for smSub in range(startIndex, startIndex + len(steplist)):
            # 取DB里动作中文对应的字段
            actionCode = controlList.objects.filter(controlName=my_form.get('actionCode')[smSub]).filter(controlType=PlantformNum)[0]
            actionDict = {
                "actionCode": actionCode.controlFiled,
                "behaviorPara":{
                    "inputValue":my_form.get('inputValue')[smSub],
                    },
                "needTarget": (bool(1) if my_form.get('targetName')[smSub] else bool(0)),
                "target": {
                    "targetName": my_form.get('targetName')[smSub],
                    "selectorType": my_form.get('selectorType')[smSub].lower(),
                    "elementName": my_form.get('elementName')[smSub],
                    "itemName": my_form.get('itemName')[smSub],
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
    # 测试库
    conn = mysql.connector.connect(user='root', password='lvmama', database='lmmpicTest', host='127.0.0.1')
    cursor = conn.cursor()
    inputTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('insert into bookShelf (caseName, needTest, inputTime, classType, appVersion) values (%s, %s, %s, %s, %s)', [caseName, caseStatus, inputTime, csType, caseVersion])
    cursor.execute('insert into testStory (caseName, caseLength, jsonStory, caseUpdateTime, caseType) values (%s, %s,%s, %s,%s)', [caseName, bigstep, my_case, inputTime, csType])
    conn.commit()
    cursor.close()
    conn.close()
    p = caseList(caseName=caseName)
    p.type_field = caseType.objects.get(id=caseType.objects.filter(type_field=csType)[0].id)
    p.plantform = casePlantform
    p.version = caseVersion
    p.case = my_case
    p.des = caseDes
    p.in_use = caseStatus
    p.save()
    message = "提交成功"
    # 判断动作
    return HttpResponseRedirect("/auto/")
    # return render(request, 'auto_list.html')
