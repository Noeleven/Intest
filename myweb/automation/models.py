from django.db import models
from django.contrib import admin
import datetime


# Create your models here.

class caseType(models.Model):
    """版本"""
    type_name = models.CharField(blank=True, max_length=100)
    # type_field = models.CharField(blank=True, max_length=100)
    # modify_time = models.DateTimeField(blank=True, auto_now=True)
    # create_time = models.DateTimeField(auto_now_add=True,blank=True)

    def __int__(self):
        return self.id

class deviceList(models.Model):
    deviceName = models.CharField(max_length=100)
    deviceIP = models.CharField(blank=True, max_length=100, default='127.0.0.1:port')
    APPIUMSERVERSTART = models.CharField(blank=True, max_length=200, default='AD use')
    appiumServicePort = models.IntegerField(blank=True)
    webDriverAgentUrl = models.CharField(blank=True, max_length=200, default='iOS use')
    bundleId = models.CharField(blank=True, max_length=200, default='iOS use')
    udid = models.CharField(blank=True, max_length=40, default='iOS use')
    lvsessionid = models.CharField(blank=True, max_length=100)
    adbPort = models.CharField(blank=True, max_length=10, default='AD use')
    job_name = models.CharField(blank=True, max_length=100, default='AndroidAppiumAutoTest')
    url = models.CharField(blank=True, max_length=100, default='for jenkins')
    username = models.CharField(blank=True, max_length=100, default='for jenkins')
    password = models.CharField(blank=True, max_length=100, default='for jenkins')
    appiumServicePath = models.CharField(blank=True, default='eg:10.113.2.70', max_length=20)
    appVersion = models.CharField(blank=True, default='7.9.3', max_length=10)
    appPackage = models.CharField(blank=True, default='com.gift.android', max_length=200)
    platformVersion = models.CharField(blank=True, default='4.4.2 or 10.3', max_length=20)
    platformName = models.CharField(blank=True, default='Android or iOS', max_length=20)
    appLaunchActivity = models.CharField(blank=True, default='com.gift.android.activity.splash.WelcomeActivity', max_length=100)
    timeWait = models.IntegerField(blank=True, default=30)
    USE_CHOICE = (('1', '启用'), ('0', '禁用'), ('2', '测试用'))
    in_use = models.CharField(max_length=2,
        choices=USE_CHOICE,
        default='1')
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

    def __str__(self):
        return self.deviceName

class myConfig(models.Model):
    caseStr = models.TextField()
    timeStamp = models.TextField()
    device = models.CharField(max_length=100)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

class caseList(models.Model):
    caseName = models.CharField(max_length=300)
    type_field = models.ForeignKey(caseType)
    # case_tag = models.CharField(max_length=300, blank=True)
    plantform = models.CharField(max_length=100)
    version = models.CharField(max_length=100)
    case = models.TextField()
    des = models.TextField(blank=True,)
    USE_CHOICE = (('1', '在用'), ('0', '废弃'))
    in_use = models.CharField(max_length=2,
        choices=USE_CHOICE,
        default='1')
    groupId = models.CharField(max_length=100, blank=True)
    owner = models.CharField(max_length=100)
    buildTime = models.IntegerField(blank=True, null=True)
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

class caseVersion(models.Model):
    versionStr = models.CharField(max_length=10)
    des = models.TextField(blank=True)
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

    def __str__(self):
        return self.versionStr

class controlList(models.Model):
    controlName = models.CharField(max_length=100)
    controlFiled = models.CharField(max_length=300)
    TYPE_CHOICE = (('0', 'Android'), ('1', 'IOS'), ('2', 'M'))
    controlType = models.CharField(max_length=2,
        choices=TYPE_CHOICE,
        default='0')
    TYPE = models.CharField(max_length=100, default='action')
    versionStr = models.ManyToManyField(caseVersion)
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

class caseUser(models.Model):
    userName = models.CharField(max_length=100)
    loginName = models.CharField(max_length=100,blank=True,)
    TYPE_CHOICE = (('0', '无效'), ('1', '有效'))
    userStatus = models.CharField(max_length=2,
        choices=TYPE_CHOICE,
        default='1')
    des = models.TextField(blank=True)
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

    def __str__(self):
        return self.userName

class reportsList(models.Model):
    timeStamp = models.TextField()
    buildNUM = models.CharField(max_length=20,blank=True)
    reportURL = models.CharField(max_length=200,blank=True)
    status = models.CharField(max_length=50,blank=True)
    deviceName = models.ForeignKey(deviceList)
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

class testRecording(models.Model):
    Version = models.CharField(max_length=10, blank=True)
    timeStamp = models.CharField(max_length=100)
    groupId = models.CharField(max_length=100, blank=True)
    flag = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=10, blank=True, verbose_name='用例集构建状态')
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateField(auto_now_add=True,blank=True)

class allBookRecording(models.Model):
    caseName = models.CharField(max_length=300)
    caseID = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=50,blank=True)
    testResultDoc = models.TextField()
    timeStamp = models.CharField(max_length=100)
    usedTime = models.CharField(max_length=100, default='0')
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

class caseGroup(models.Model):
    groupName = models.CharField(max_length=300)
    caseID = models.TextField()
    versionStr = models.ForeignKey(caseVersion, default=8)
    des = models.TextField()
    platform = models.CharField(max_length=10, default='')
    TYPE_CHOICE = (('0', '禁用'), ('1', '启用'))
    status = models.CharField(max_length=2,
        choices=TYPE_CHOICE,
        default='1')
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

class caseTag(models.Model):
    tagName = models.CharField(blank=True, max_length=100)
    type_field = models.ForeignKey(caseType)
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

    def __str__(self):
        return self.tagName

class history(models.Model):
    operationTime = models.DateTimeField(blank=True, default=datetime.datetime.now)
    remoteIp = models.CharField(blank=True, max_length=100)
    operation = models.TextField(blank=True)

class userGroup(models.Model):
    groupName = models.CharField(max_length=256, verbose_name='组名')
    groupUser = models.TextField(blank=True, null=True, verbose_name='成员')
    des = models.TextField(blank=True, verbose_name='描述')
    modify_time = models.DateTimeField(auto_now=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True,blank=True)

# ListAdmin

class caseTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name',)
    list_per_page = 30
    search_fields = ['type_name',]

class caseListAdmin(admin.ModelAdmin):
    list_display = ('caseName', 'type_field', 'plantform', 'version', 'owner', 'des', 'in_use', 'modify_time')
    list_per_page = 30
    search_fields = ['caseName', 'type_field__type_field', 'plantform', 'owner', 'version', 'des']

class controlListAdmin(admin.ModelAdmin):
    def get_products(self, controlList):
        return ",".join([p.versionStr for p in controlList.versionStr.all()])
    get_products.short_description = 'versionStr'
    list_display = ('controlName', 'controlFiled', 'controlType', 'TYPE', 'get_products')
    list_per_page = 30
    search_fields = ['controlName', 'controlFiled', 'controlType','TYPE']

class caseUserAdmin(admin.ModelAdmin):
    list_display = ('userName', 'loginName', 'userStatus','des')
    list_per_page = 30
    search_fields = ['userName', 'loginName', 'userStatus','des']

class caseVersionAdmin(admin.ModelAdmin):
    list_display = ('versionStr', 'des')
    list_per_page = 30
    search_fields = ['versionStr', 'des']

class deviceListAdmin(admin.ModelAdmin):
    list_display = ('deviceName','url','job_name','appVersion','platformVersion')
    list_per_page = 30
    search_fields = ['deviceName','url','job_name','appVersion','platformVersion']

class reportsListAdmin(admin.ModelAdmin):
    list_display = ('buildNUM','status','deviceName', 'create_time','timeStamp')
    list_per_page = 30
    search_fields = ['timeStamp','buildNUM','status','deviceName__deviceName','create_time']

class caseTagAdmin(admin.ModelAdmin):
    list_display = ('tagName', 'type_field')
    list_per_page = 30
    search_fields = ['tagName', 'type_field']

admin.site.register(caseType, caseTypeAdmin)
admin.site.register(caseList, caseListAdmin)
admin.site.register(controlList, controlListAdmin)
admin.site.register(caseUser, caseUserAdmin)
admin.site.register(caseVersion, caseVersionAdmin)
admin.site.register(deviceList, deviceListAdmin)
admin.site.register(reportsList, reportsListAdmin)
admin.site.register(caseTag, caseTagAdmin)
