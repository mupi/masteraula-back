# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-02-03 13:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0054_auto_20200130_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classplan',
            name='disciplines',
            field=models.ManyToManyField(to='questions.Discipline'),
        ),
        migrations.AlterField(
            model_name='classplan',
            name='teaching_levels',
            field=models.ManyToManyField(to='questions.TeachingLevel'),
        ),
        migrations.AlterField(
            model_name='classplan',
            name='topics',
            field=models.ManyToManyField(to='questions.Topic'),
        ),
    ]
