# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-08-18 10:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cobra', '0004_channel_projects'),
    ]

    operations = [
        migrations.CreateModel(
            name='DayIndex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.CharField(default='', max_length=50)),
                ('status', models.CharField(default='0', max_length=1)),
            ],
        ),
    ]
