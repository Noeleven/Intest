from django.test import TestCase, Client
from automation.models import *

# Create your tests here.
class autoConfig(TestCase):
    fixtures = ['au.json']
    """测试构建方法"""
    def setup(self):
        pass

    def test_errParams(self):
        """参数错误"""
        response = self.client.get('/auto/auto_config')
        self.assertEqual(response.status_code, 200)
        self.assertIn('参数错误', response.json()['message'])

    def test_noCases(self):
        """没有用例"""
        # 没用例
        response = self.client.get('/auto/auto_config?vals=1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('没有可用用例', response.json()['message'])
        # 没参数值
        response = self.client.get('/auto/auto_config?vals')
        self.assertEqual(response.status_code, 200)
        self.assertIn('没有用例', response.json()['message'])
        # 用例集不存在
        response = self.client.get('/auto/auto_config?vals=5555,6666&type=group')
        self.assertEqual(response.status_code, 200)
        self.assertIn('没有可用用例', response.json()['message'])
        # 多用例集 没设备
        response = self.client.get('/auto/auto_config?vals=1,7&type=group')
        self.assertEqual(response.status_code, 200)
        self.assertIn('没有可用用例', response.json()['message'])

    def test_noParamsNum(self):
        """未指定设备，没有设备 5014 7103"""
        response = self.client.get('/auto/auto_config?vals=5014')
        self.assertEqual(response.status_code, 200)
        self.assertIn('没有可用设备', response.json()['message'])

    def test_noCaseGroup(self):
        """发射成功"""
        # 用例可用
        response = self.client.get('/auto/auto_config?vals=4481')
        self.assertEqual(response.status_code, 200)
        self.assertIn('装弹完毕，准备发射', response.json()['message'])
        # 用例集一个可用
        response = self.client.get('/auto/auto_config?vals=1,8&type=group')
        self.assertEqual(response.status_code, 200)
        self.assertIn('装弹完毕，准备发射', response.json()['message'])
        # 用例集2个可用
        response = self.client.get('/auto/auto_config?vals=8,40740&type=group')
        self.assertEqual(response.status_code, 200)
        self.assertIn('装弹完毕，准备发射', response.json()['message'])

    def test_noDev(self):
        """指定设备不存在"""
        response = self.client.get('/auto/auto_config?vals=4481&device=xxx123')
        self.assertEqual(response.status_code, 200)
        self.assertIn('设备不存在', response.json()['message'])

        # 混杂版本用例 5014没设备
        response = self.client.get('/auto/auto_config?vals=5013,5015,5014,5008')
        self.assertEqual(response.status_code, 200)
        self.assertIn('没有可用设备', response.json()['message'])

        # 指定设备，混杂用例
        response = self.client.get('/auto/auto_config?vals=5013,5015,5014,5008&device=Mauto32')
        self.assertEqual(response.status_code, 200)
        self.assertIn('设备不匹配', response.json()['message'])

# class pageRequest(TestCase):
#     """测试页面返回"""
    # def setup(self):
    #     caseList.objects.all()
    # def test_getProgress(self):

    # http://10.115.1.73:7000/auto/testProgress?tt=1513800020869140

    # def test_main_page(self):
    #     """auto首页"""
    #     response = Client().get('/auto')
    #     self.assertEqual(response.status_code, 301)
    #
    # def test_list_page(self):
    #     """按品类分的列表"""
    #     response = Client().get('/auto/auto_list')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'auto_list.html')
    #
    # def test_jenkins_page(self):
    #     """jenkins调用"""
    #     response = Client().get('/auto/auto_response?deviceName=127.0.0.1:62001')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn(b'Device', response.content)
    #
    # def test_del_page(self):
    #     """删除"""
    #     response = Client().get('/auto/auto_del')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn(b'ERR', response.content)
    #
    #
    # def test_copy_page(self):
    #     """复制"""
    #     response = Client().get('/auto/auto_copy')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn(b'2', response.content)
    #
    # def test_add_page(self):
    #     """添加"""
    #     response = Client().get('/auto/new_add')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'new_add.html')
    #
    # def test_new_page(self):
    #     """新建"""
    #     response = Client().get('/auto/new_save')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn(b'Oh my god', response.content)
    #
    # def test_ios_page(self):
    #     """IOS接口"""
    #     response = Client().get('/auto/auto_caseJson?plantform=IOS')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn(b'message', response.content)
    #
    # def test_report_page(self):
    #     """测试报告"""
    #     response = Client().get('/auto/test_list')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'test_list.html')
    #
    # def test_search_page(self):
    #     """搜索页面"""
    #     response = Client().get('/auto/auto_search')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'auto_search.html')
    #
    # def test_sapi_page(self):
    #     """搜索接口"""
    #     response = Client().get('/auto/search_result')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'auto_ajax.html')
