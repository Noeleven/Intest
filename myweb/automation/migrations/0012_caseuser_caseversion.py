# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-03-03 11:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0011_myconfig_device'),
    ]

    operations = [
        migrations.CreateModel(
            name='caseUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('userName', models.CharField(max_length=100)),
                ('loginName', models.CharField(blank=True, max_length=100)),
                ('userStatus', models.CharField(choices=[('0', '无效'), ('1', '有效')], default='1', max_length=2)),
                ('des', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='caseVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('versionStr', models.CharField(max_length=10)),
                ('des', models.TextField(blank=True)),
            ],
        ),
    ]
