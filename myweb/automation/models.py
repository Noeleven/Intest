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

class myConfig(models.Model):
    caseStr = models.TextField()
    device = models.CharField(max_length=100)
    modify_time = models.DateTimeField(blank=True, default=datetime.datetime.now)

class caseList(models.Model):
    caseName = models.CharField(max_length=300)
    type_field = models.ForeignKey(caseType)
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

class controlList(models.Model):
    controlName = models.CharField(max_length=100)
    controlFiled = models.CharField(max_length=100)
    TYPE_CHOICE = (('0', 'Android'), ('1', 'IOS'), ('2', 'M'))
    controlType = models.CharField(max_length=2,
        choices=TYPE_CHOICE,
        default='0')
    TYPE = models.CharField(max_length=100, default='action')

class caseTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name', 'type_field', 'modify_time')
    list_per_page = 30
    search_fields = ['type_name', 'type_field', 'modify_time']

class caseListAdmin(admin.ModelAdmin):
    list_display = ('caseName', 'type_field', 'plantform', 'version', 'owner', 'des', 'in_use', 'modify_time')
    list_per_page = 30
    search_fields = ['caseName', 'type_field', 'plantform', 'owner', 'version', 'des']

class controlListAdmin(admin.ModelAdmin):
    list_display = ('controlName', 'controlFiled', 'controlType','TYPE')
    list_per_page = 30
    search_fields = ['controlName', 'controlFiled', 'controlType','TYPE']

admin.site.register(caseType, caseTypeAdmin)
admin.site.register(caseList, caseListAdmin)
admin.site.register(controlList, controlListAdmin)
