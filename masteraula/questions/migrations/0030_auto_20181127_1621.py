# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-11-27 18:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0029_header'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='class_indicator',
        ),
        migrations.RemoveField(
            model_name='document',
            name='date_indicator',
        ),
        migrations.RemoveField(
            model_name='document',
            name='discipline_name',
        ),
        migrations.RemoveField(
            model_name='document',
            name='institution_name',
        ),
        migrations.RemoveField(
            model_name='document',
            name='professor_name',
        ),
        migrations.RemoveField(
            model_name='document',
            name='score_indicator',
        ),
        migrations.RemoveField(
            model_name='document',
            name='student_indicator',
        ),
    ]
