# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-07-27 16:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0036_testrecording_flag'),
    ]

    operations = [
        migrations.AddField(
            model_name='devicelist',
            name='udid',
            field=models.CharField(blank=True, default='iOS use', max_length=40),
        ),
    ]
