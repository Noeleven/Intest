# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-03-17 20:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0015_devicelist_secondtype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='devicelist',
            name='APPIUMSERVERSTART',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
