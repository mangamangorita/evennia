# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-06 20:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('objects', '0008_auto_20170705_1736'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='objectdb',
            name='db_player',
        ),
    ]
