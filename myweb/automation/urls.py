# -*- coding: utf-8 -*-

from django.conf.urls import url
from automation.views import *

urlpatterns = [
	url(r'^$', autoSearch, name='autoSearch'),
	url(r'^autoSearch$', autoSearch, name='autoSearch'),	# 搜索页面
	url(r'^getDeviceStatus$', getDeviceStatus, name='getDeviceStatus'),	# 获取设备状态
	url(r'^searchResult$', searchResult, name='searchResult'),	# 搜索接口
	url(r'^showCaseList$', showCaseList, name='showCaseList'),	# 用例列表
	url(r'^auto_config$', auto_config, name='auto_config'),	# 构建引擎
	url(r'^auto_response$', auto_response, name='auto_response'),	# jenkins调用返回设备信息
	url(r'^addCase$', addCase, name='addCase'),	# 新建用例
	url(r'^saveCaseBaseInfo$', saveCaseBaseInfo, name='saveCaseBaseInfo'),	# 保存用例基本信息
	url(r'^caseConfirm/(.+)/$', caseConfirm, name='caseConfirm'),	# 编辑用例 确认版本平台
	url(r'^editCaseStep$', editCaseStep, name='editCaseStep'),	# 编辑用例
	url(r'^saveCaseStep$', saveCaseStep, name='saveCaseStep'),	# 保存用例步骤信息
	url(r'^auto_del$', auto_del, name='auto_del'),	# 删除用例
	url(r'^auto_ex$', auto_ex, name='auto_ex'),	# 用例重置为过期
	url(r'^auto_copy$', auto_copy, name='auto_copy'),	# 用例复制
	url(r'^reportList$', reportList, name='reportList'),	# 测试报告列表
	url(r'^reportDetail$', reportDetail, name='reportDetail'),	# 报告详情页
	url(r'^testProgress$', testProgress, name='testProgress'),	# 获取测试用例进度
	url(r'^reportFilter$', reportFilter, name='reportFilter'),	# 报告页面根据owner过滤
	url(r'^getDevBuildHistory$', getDevBuildHistory, name='getDevBuildHistory'),	# 获取设备构建历史
	url(r'^snapshot$', snapshot, name='snapshot'),	# 单条用例详情
	url(r'^sendMail$', sendMail, name='sendMail'),	# 发邮件
	url(r'^change_case$', change_case, name='change_case'),	# 修改用例json由于变更controList
	url(r'^autoMakeGroup$', autoMakeGroup, name='autoMakeGroup'),	# 添加到用例集
	url(r'^groupList$', groupList, name='groupList'),	# 用例集列表
	url(r'^groupEdit$', groupEdit, name='groupEdit'),	# 编辑用例集
	url(r'^groupSave$', groupSave, name='groupSave'),	# 用例集保存
	url(r'^getGroupHistory$', getGroupHistory, name='getGroupHistory'),	# 用例集操作历史
	url(r'^many_many$', many_many, name='many_many'),	# 控制列表对应关系一键处理
	url(r'^stopJenkins$', stopJenkins, name='stopJenkins'),	# 停止jenkins
	url(r'^retry$', retry, name='retry'),	# 重测失败用例
	url(r'^tagSearch$', tagSearch, name='tagSearch'),	# 用例列表标签
	url(r'^cancleOrder$', cancleOrder, name='cancleOrder'),	# 手动取消订单
	url(r'^autoReport$', autoReport, name='autoReport'),	# 数据分析报告
	url(r'^getBuildTimes$', getBuildTimes, name='getBuildTimes'),	# 数据分析查询构建次数
	url(r'^memGroupList$', memGroupList, name='memGroupList'),	# 小组列表
	url(r'^memGroupEdit$', memGroupEdit, name='memGroupEdit'),	# 小组编辑
	url(r'^memGroupSave$', memGroupSave, name='memGroupSave'),	# 小组保存
]
