# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-19 11:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fz', '0003_delete_errs'),
    ]

    operations = [
        migrations.AddField(
            model_name='sdata',
            name='debugmsg',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
