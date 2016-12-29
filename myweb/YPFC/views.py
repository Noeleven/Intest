from django.shortcuts import render
from YPFC.models import *
from django.http import HttpResponse, HttpResponseRedirect
from decimal import Decimal
import time

# Create your views here.

# memberList
def memView(request):
	# 计算表中每个id的总收入和支出，在求余额、状态等信息
	datas = []
	name_list = [x['name'] for x in member.objects.values('name')]
	for name in name_list:
		mem_content = {}
		id = member.objects.get(name=name).id
		mem_content['name'] = name
		mem_content['income'] = sum([x['income'] for x in cash.objects.filter(member_id=id).values('income')])
		mem_content['pay'] = sum([x['pay'] for x in cash.objects.filter(member_id=id).values('pay')])
		mem_content['balance'] = mem_content['income'] - mem_content['pay']
		if mem_content['balance'] > 0:
			mem_content['status'] = '正常'
		elif mem_content['balance'] == 0:
			mem_content['status'] = '待缴费'
		else:
			mem_content['status'] = '欠费'
		datas.append(mem_content)
	return render(request, 'memView.html', {'datas':datas})

# cash write
def cashView(request):
	# 需要给页面提供人员名单
	name_list = [x['name'] for x in member.objects.values('name')]
	if request.method == 'POST': # 如果表单被提交
		form = myFrom(request.POST) # 获取Post表单数据
		if form.is_valid(): # 验证表单
			return HttpResponseRedirect('/') # 跳转
	else:
		form = myFrom() #获得表单对象

	return render(request, 'cashView.html', {'name_list':name_list, 'form':form})

# 汇总
def Summary(request):
	incomeAll = sum([x['income'] for x in cash.objects.values('income')])
	payAll = sum([x['pay'] for x in cash.objects.values('pay')])
	summary_dict = {
		'incomeAll': str(incomeAll),
		'payAll': str(payAll),
		'balance': str(incomeAll - payAll),
		'memNum': len(member.objects.filter(status='1').values('name').distinct().order_by('name')),
	}
	range = mark.objects.all().order_by('-timestamp')
	datas = []
	for i in range:
		tmp_dict = {
			'income':str(i.income),
			'pay':str(i.pay),
			'des':i.des,
			'timestamp':i.timestamp.strftime("%Y-%m-%d"),
		}
		datas.append(tmp_dict)
	print(summary_dict, datas)
	return render(request, 'Summary.html',{'summary_dict':summary_dict,
											'datas':datas,})

def saveDate(request):
	inputData = request.POST.get('inputData')
	income = request.POST.get('income')
	income_mem = request.POST.getlist('income_mem')
	income_self = request.POST.getlist('income_self')
	pay = request.POST.get('pay')
	pay_mem = request.POST.getlist('pay_mem')
	des = request.POST.get('des')

	# initial
	y,m,d = time.strptime(inputData, "%Y-%m-%d ")[:3]
	inputData = datetime.datetime(y, m, d)
	income = Decimal(income)
	pay = Decimal(pay)

	# mark in db
	ma = mark(income=income)
	ma.pay = pay
	ma.des = des
	ma.timestamp = inputData
	ma.save()
	# counts
	income_dict = dict(zip(income_mem,income_self))
	single_pay = round(pay / len(pay_mem), 1)
	print(income_dict)
	#everyone's in db
	name_list = set(income_mem + pay_mem)
	for name in name_list:
		if name in income_mem:
			income = Decimal(income_dict[name])
		else:
			income = 0
		if name in pay_mem:
			pay = single_pay
		else:
			pay = 0
		if income > 0 or pay > 0:
			p = cash(member_id=getID(name))
			p.income = income
			p.pay = pay
			p.timestamp = inputData
			p.save()

	return HttpResponseRedirect('/YPFC/memView')

def getID(name):
	id = member.objects.get(name=name).id
	return id

def cashDetail(request, name):
	member_id = getID(name)
	print(member_id)
	datas = []
	range = cash.objects.filter(member_id=member_id).order_by('-timestamp')
	print(range)
	for i in range:
		try:
			des = mark.objects.filter(timestamp=i.timestamp)[0].des
		except:
			des = ''
		tmp_dict = {
			'income':str(i.income),
			'pay':str(i.pay),
			'des':des,
			'timestamp':i.timestamp.strftime("%Y-%m-%d"),
		}
		datas.append(tmp_dict)
	return render(request, 'cashDetail.html',{'datas':datas,'name':name})
