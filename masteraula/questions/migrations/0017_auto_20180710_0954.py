# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-07-10 12:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0016_auto_20180710_0943'),
    ]

    operations = [
        migrations.RenameField(
            model_name='documentheader',
            old_name='subject_name',
            new_name='discipline_name',
        ),
    ]