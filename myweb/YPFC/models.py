from django.db import models
from django.contrib import admin
from django import forms
import datetime


# Create your models here.
class member(models.Model):
    name = models.CharField(max_length=20,default="name")
    both = models.DateField(auto_now=False,default="1980-01-01")
    position = models.CharField(max_length=20,default="GK")
    weight = models.IntegerField(null=True,blank=True)
    height = models.IntegerField(null=True,blank=True)
    phone = models.CharField(max_length=11,null=True,blank=True)
    address = models.CharField(max_length=200,null=True,blank=True)
    number = models.CharField(max_length=10,null=True,blank=True)
    like = models.TextField(null=True,blank=True)
    saying = models.TextField(null=True,blank=True)
    BOOL_CHOICES = (('1', '在队'), ('0', '离队'))
    status = models. CharField(max_length=2,
        choices=BOOL_CHOICES,
        default='1')

# everyone's cashflow
class cash(models.Model):
    member_id = models.CharField(max_length=20)
    income = models.DecimalField(max_digits=5,decimal_places=1)
    pay = models.DecimalField(max_digits=5,decimal_places=1)
    timestamp = models.DateField(auto_now=False)

# mark workflow
class mark(models.Model):
    income = models.DecimalField(max_digits=5,decimal_places=1)
    pay = models.DecimalField(max_digits=5,decimal_places=1)
    des = models.TextField(null=True,blank=True)
    timestamp = models.DateField(auto_now=False)

class YPFCAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'phone', 'status')
    list_per_page = 30
    search_fields = ['name', 'number', 'phone', 'status']

class myFrom(forms.Form):
    data = forms.DateField(initial=datetime.date.today)
    income = forms.DecimalField(help_text='总收入.')
    income_mem = forms.ChoiceField(label="收入来源")
    pay = forms.DecimalField(help_text='总支出.')
    pay_mem = forms.MultipleChoiceField(label=u'支出参与人员', widget=forms.CheckboxSelectMultiple())
    mark = forms.CharField(widget=forms.Textarea)

admin.site.register(member, YPFCAdmin)
