# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-03-22 13:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0006_auto_20170317_1644'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='year_level',
            new_name='education_level',
        ),
    ]