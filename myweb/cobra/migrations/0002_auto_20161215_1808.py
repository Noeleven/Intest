# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-12-15 18:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cobra', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datas',
            name='res',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='datas',
            name='rpm',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True),
        ),
    ]