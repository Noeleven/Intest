# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-12-15 19:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cobra', '0002_auto_20161215_1808'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datas',
            name='create_time',
            field=models.DateField(),
        ),
    ]
