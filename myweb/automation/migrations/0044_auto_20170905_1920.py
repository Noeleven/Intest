# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-09-05 19:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0043_history'),
    ]

    operations = [
        migrations.RenameField(
            model_name='history',
            old_name='operton',
            new_name='opertion',
        ),
    ]
