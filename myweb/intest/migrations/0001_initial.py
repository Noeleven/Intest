# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-09-14 11:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Errs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='未定义接口', max_length=100)),
                ('method_version', models.CharField(max_length=100)),
                ('url', models.TextField()),
                ('httpcode', models.CharField(blank=True, max_length=100, null=True)),
                ('log_code', models.CharField(blank=True, max_length=100, null=True)),
                ('error', models.CharField(blank=True, max_length=200, null=True)),
                ('message', models.CharField(blank=True, max_length=200, null=True)),
                ('timestamp', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Ints',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='接口描述', max_length=100)),
                ('method_version', models.CharField(default='api.com.xxx&version=x.0.0', max_length=100)),
                ('ishttp', models.CharField(default='HTTP', max_length=10)),
                ('isget', models.CharField(default='GET', max_length=10)),
                ('params', models.TextField(default='URL里接口&之后的内容')),
                ('inwhere', models.TextField(default='该接口的出现页面位置')),
                ('timestamp', models.DateField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Sdata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='未定义接口', max_length=100)),
                ('method_version', models.CharField(max_length=100)),
                ('url', models.TextField()),
                ('code', models.CharField(blank=True, max_length=100, null=True)),
                ('log_code', models.CharField(blank=True, max_length=100, null=True)),
                ('log_time', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('dns_time', models.DecimalField(decimal_places=2, max_digits=5)),
                ('tcp_time', models.DecimalField(decimal_places=2, max_digits=5)),
                ('up_time', models.DecimalField(decimal_places=2, max_digits=5)),
                ('server_time', models.DecimalField(decimal_places=2, max_digits=5)),
                ('download_time', models.DecimalField(decimal_places=2, max_digits=5)),
                ('download_size', models.DecimalField(decimal_places=2, max_digits=5)),
                ('total_time', models.DecimalField(decimal_places=2, max_digits=5)),
                ('timestamp', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
