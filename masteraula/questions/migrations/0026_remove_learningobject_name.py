# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-10-24 14:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0025_auto_20180806_1149'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='learningobject',
            name='name',
        ),
    ]