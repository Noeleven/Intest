# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-08-23 15:12
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0039_casetag_type_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='myconfig',
            name='timeStamp',
            field=models.TextField(default=datetime.datetime(2017, 8, 23, 15, 12, 0, 666162)),
            preserve_default=False,
        ),
    ]