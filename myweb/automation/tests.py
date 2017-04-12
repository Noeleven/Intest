from django.test import TestCase, Client

# Create your tests here.
class pageRequest(TestCase):
    """测试页面返回"""
    def setup(self):
        caseList.objects.create(id=1, caseName='测试用例', type_field_id='10', second_Type_id='1', plantform='Android', version='7.8.5', case='', des='测试数据', in_use='1', modify_time='2017-02-28 15:26:31.549726', owner='测试')

    def test_main_page(self):
        """auto首页"""
        response = Client().get('/auto')
        self.assertEqual(response.status_code, 301)

    def test_list_page(self):
        """按品类分的列表"""
        response = Client().get('/auto/auto_list')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auto_list.html')

    def test_jenkins_page(self):
        """jenkins调用"""
        response = Client().get('/auto/auto_response?deviceName=127.0.0.1:62001')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Device', response.content)

    def test_del_page(self):
        """删除"""
        response = Client().get('/auto/auto_del')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ERR', response.content)


    def test_copy_page(self):
        """复制"""
        response = Client().get('/auto/auto_copy')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'2', response.content)

    def test_add_page(self):
        """添加"""
        response = Client().get('/auto/new_add')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'new_add.html')

    def test_new_page(self):
        """新建"""
        response = Client().get('/auto/new_save')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Oh my god', response.content)

    def test_ios_page(self):
        """IOS接口"""
        response = Client().get('/auto/auto_caseJson?plantform=IOS')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'message', response.content)

    def test_report_page(self):
        """测试报告"""
        response = Client().get('/auto/test_list')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'test_list.html')

    def test_search_page(self):
        """搜索页面"""
        response = Client().get('/auto/auto_search')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auto_search.html')

    def test_sapi_page(self):
        """搜索接口"""
        response = Client().get('/auto/search_result')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auto_ajax.html')
