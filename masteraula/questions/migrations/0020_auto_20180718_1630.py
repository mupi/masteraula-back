# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-07-18 19:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0019_auto_20180712_1411'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='teaching_levels',
            field=models.ManyToManyField(blank=True, to='questions.TeachingLevel'),
        ),
    ]
