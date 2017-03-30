# -*- coding: utf-8 -*-

from django.conf.urls import url
from automation.views import *

urlpatterns = [
	url(r'^$', auto_search, name='auto_search'),	# 默认全部列表
	# url(r'^auto_list$', auto_list, name='auto_list'),	# 按品类分的列表
	url(r'^auto_list/(.+)/$', auto_list, name='auto_list'),	# 按品类分的列表
	url(r'^auto_edit_save/(.+)/$', auto_edit_save, name='auto_edit_save'),	# 编辑保存
	url(r'^auto_config$', auto_config, name='auto_config'),	# 点击构建
	url(r'^auto_response$', auto_response, name='auto_response'),	# jenkins调用
	url(r'^auto_del$', auto_del, name='auto_del'),	# 删除
	url(r'^auto_copy$', auto_copy, name='auto_copy'),	# 复制
	url(r'^new_add$', new_add, name='new_add'),	# 添加
	url(r'^new_save$', new_save, name='new_save'),	# 保存用例
	url(r'^new_edit/(.+)/$', new_edit, name='new_edit'),	# 编辑页面
	url(r'^auto_caseJson$', auto_caseJson, name='auto_caseJson'),	# IOS接口
	url(r'^test_list$', test_list, name='test_list'),	# 测试报告
	url(r'^auto_search$', auto_search, name='auto_search'),	# 搜索页面
	url(r'^search_result$', search_result, name='search_result'),	# 搜索接口
]
