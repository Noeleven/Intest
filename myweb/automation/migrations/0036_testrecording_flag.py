# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-07-27 11:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0035_auto_20170725_1026'),
    ]

    operations = [
        migrations.AddField(
            model_name='testrecording',
            name='flag',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]