# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-09-15 15:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0047_auto_20170915_1531'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testrecording',
            name='createTime',
        ),
    ]
