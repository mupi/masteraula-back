# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-08-04 23:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0068_auto_20200731_1344'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stationmaterial',
            old_name='name',
            new_name='name_station',
        ),
    ]