# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-07-06 12:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0063_activity_task'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='teacher_expectation',
            field=models.TextField(blank=True, null=True),
        ),
    ]