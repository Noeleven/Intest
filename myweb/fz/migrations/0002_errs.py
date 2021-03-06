# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-19 10:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fz', '0001_initial'),
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
    ]
