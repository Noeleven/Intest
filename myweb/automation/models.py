from django.db import models
from django.contrib import admin
import datetime


# Create your models here.
class caseType(models.Model):
    type_name = models.CharField(blank=True, max_length=100)
    type_field = models.CharField(blank=True, max_length=100)
    modify_time = models.DateTimeField(blank=True, default=datetime.datetime.now)

    def __str__(self):
        return self.type_field

class secondType(models.Model):
    second_Type = models.CharField(max_length=100, default='测试')
    modify_time = models.DateTimeField(blank=True, default=datetime.datetime.now)

    def __str__(self):
        return self.second_Type

class deviceList(models.Model):
    deviceName = models.CharField(max_length=100)
    deviceIP = models.CharField(blank=True, max_length=100, default='127.0.0.1:port')
    APPIUMSERVERSTART = models.CharField(blank=True, max_length=200)
    appiumServicePort = models.IntegerField(blank=True)
    lvsessionid = models.CharField(blank=True, max_length=100)
    job_name = models.CharField(blank=True, max_length=100, default='AndroidAppiumAutoTest')
    appiumServicePath = models.CharField(blank=True, default='10.113.2.70', max_length=20)
    appVersion = models.CharField(blank=True, default='7.8.5', max_length=10)
    appPackage = models.CharField(blank=True, default='com.gift.android', max_length=20)
    platformVersion = models.CharField(blank=True, default='4.4.2', max_length=10)
    platformName = models.CharField(blank=True, default='Android', max_length=10)
    appLaunchActivity = models.CharField(blank=True, default='com.gift.android.activity.splash.WelcomeActivity', max_length=100)
    timeWait = models.IntegerField(blank=True, default=30)
    USE_CHOICE = (('1', '启用'), ('0', '禁用'))
    in_use = models.CharField(max_length=2,
        choices=USE_CHOICE,
        default='1')
    def __str__(self):
        return self.deviceName

class myConfig(models.Model):
    caseStr = models.TextField()
    device = models.CharField(max_length=100)
    modify_time = models.DateTimeField(blank=True, default=datetime.datetime.now)

class caseList(models.Model):
    caseName = models.CharField(max_length=300)
    type_field = models.ForeignKey(caseType)
    second_Type = models.ForeignKey(secondType)
    plantform = models.CharField(max_length=100)
    version = models.CharField(max_length=100)
    case = models.TextField()
    des = models.TextField(blank=True,)
    USE_CHOICE = (('1', '在用'), ('0', '废弃'))
    in_use = models.CharField(max_length=2,
        choices=USE_CHOICE,
        default='1')
    modify_time = models.DateTimeField(default=datetime.datetime.now)
    owner = models.CharField(max_length=100)

class caseVersion(models.Model):
    versionStr = models.CharField(max_length=10)
    des = models.TextField(blank=True,)
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
    versionStr = models.ForeignKey(caseVersion)

class caseUser(models.Model):
    userName = models.CharField(max_length=100)
    loginName = models.CharField(max_length=100,blank=True,)
    TYPE_CHOICE = (('0', '无效'), ('1', '有效'))
    userStatus = models.CharField(max_length=2,
        choices=TYPE_CHOICE,
        default='1')
    des = models.TextField(blank=True,)

class reportsList(models.Model):
    timeStamp = models.TextField()
    buildNUM = models.CharField(max_length=20,blank=True)
    reportURL = models.CharField(max_length=200,blank=True)
    status = models.CharField(max_length=50,blank=True)
    deviceName = models.ForeignKey(deviceList)
    create_time = models.DateTimeField(default=datetime.datetime.now)

class testRecording(models.Model):
    testStartDate = models.DateTimeField()
    testCondition = models.CharField(max_length=100)
    testDuration = models.DateTimeField()
    testAppVersion = models.CharField(max_length=100)
    timeStamp = models.CharField(max_length=100)

class allBookRecording(models.Model):
    caseName = models.CharField(max_length=300)
    status = models.CharField(max_length=50,blank=True)
    testResultDoc = models.TextField()
    timeStamp = models.CharField(max_length=100)
    usedTime = models.CharField(max_length=100, default='0')


class caseTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name', 'type_field', 'modify_time')
    list_per_page = 30
    search_fields = ['type_name', 'type_field', 'modify_time']

class caseListAdmin(admin.ModelAdmin):
    list_display = ('caseName', 'type_field', 'plantform', 'version', 'owner', 'des', 'in_use', 'modify_time')
    list_per_page = 30
    search_fields = ['caseName', 'type_field__type_field', 'plantform', 'owner', 'version', 'des']

class controlListAdmin(admin.ModelAdmin):
    list_display = ('controlName', 'controlFiled', 'controlType','TYPE', 'versionStr')
    list_per_page = 30
    search_fields = ['controlName', 'controlFiled', 'controlType','TYPE', 'versionStr__versionStr']

class caseUserAdmin(admin.ModelAdmin):
    list_display = ('userName', 'loginName', 'userStatus','des')
    list_per_page = 30
    search_fields = ['userName', 'loginName', 'userStatus','des']

class caseVersionAdmin(admin.ModelAdmin):
    list_display = ('versionStr', 'des')
    list_per_page = 30
    search_fields = ['versionStr', 'des']

class secondTypeAdmin(admin.ModelAdmin):
    list_display = ('second_Type','modify_time')
    list_per_page = 30
    search_fields = ['second_Type','modify_time']

class deviceListAdmin(admin.ModelAdmin):
    list_display = ('deviceName','deviceIP','job_name','appVersion','platformVersion')
    list_per_page = 30
    search_fields = ['deviceName','deviceIP','job_name','appVersion','platformVersion']

class reportsListAdmin(admin.ModelAdmin):
    list_display = ('buildNUM','status','deviceName', 'create_time','timeStamp')
    list_per_page = 30
    search_fields = ['timeStamp','buildNUM','status','deviceName__deviceName','create_time']


admin.site.register(caseType, caseTypeAdmin)
admin.site.register(caseList, caseListAdmin)
admin.site.register(controlList, controlListAdmin)
admin.site.register(caseUser, caseUserAdmin)
admin.site.register(caseVersion, caseVersionAdmin)
admin.site.register(secondType, secondTypeAdmin)
admin.site.register(deviceList, deviceListAdmin)
admin.site.register(reportsList, reportsListAdmin)
