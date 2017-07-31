# -*- coding: utf-8 -*-

from django.conf.urls import url
from automation.views import *

urlpatterns = [
	url(r'^$', auto_search, name='auto_search'),	# 默认全部列表
	url(r'^auto_list$', auto_list, name='auto_list'),	# 按品类分的列表
	url(r'^auto_edit_save/(.+)/$', auto_edit_save, name='auto_edit_save'),	# 编辑保存
	url(r'^auto_config$', auto_config, name='auto_config'),	# 点击构建
	url(r'^auto_response$', auto_response, name='auto_response'),	# jenkins调用
	url(r'^auto_del$', auto_del, name='auto_del'),	# 删除
	url(r'^auto_ex$', auto_ex, name='auto_ex'),	# 重置为过期
	url(r'^auto_copy$', auto_copy, name='auto_copy'),	# 复制
	url(r'^new_add$', new_add, name='new_add'),	# 添加
	url(r'^new_save$', new_save, name='new_save'),	# 保存用例
	url(r'^ver_confirm/(.+)/$', ver_confirm, name='ver_confirm'),	# 保存用例
	url(r'^new_edit$', new_edit, name='new_edit'),	# 编辑页面
	# url(r'^auto_caseJson$', auto_caseJson, name='auto_caseJson'),	# IOS接口
	url(r'^test_list$', test_list, name='test_list'),	# 测试报告
	url(r'^auto_search$', auto_search, name='auto_search'),	# 搜索页面
	url(r'^search_result$', search_result, name='search_result'),	# 搜索接口
	url(r'^api_report$', api_report, name='api_report'),	# 发邮件接口
	url(r'^api_report_page$', api_report_page, name='api_report_page'),	# 测试报告接口
	url(r'^search_report$', search_report, name='search_report'),	# 报告页面查询
	url(r'^change_case$', change_case, name='change_case'),	# 修改用例对应关系
	url(r'^auto_makeGroup$', auto_makeGroup, name='auto_makeGroup'),	# 添加用例集接口
	url(r'^auto_group$', auto_group, name='auto_group'),	# 用例集列表页
	url(r'^group_edit$', group_edit, name='group_edit'),	# 编辑用例集
	url(r'^group_save$', group_save, name='group_save'),	# 用例集保存
	url(r'^many_many$', many_many, name='many_many'),	# 控制列表对应关系一键处理
	url(r'^test_ajax$', test_ajax, name='test_ajax'),	# 普通报告ajax请求
	url(r'^snapshot$', snapshot, name='snapshot'),	# 单条报告ajax请求
	url(r'^stop_jenkins$', stop_jenkins, name='stop_jenkins'),	# 停止jenkins
	url(r'^retry$', retry, name='retry'),	# 重测
]
