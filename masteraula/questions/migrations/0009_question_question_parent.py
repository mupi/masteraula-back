# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-03 15:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0008_auto_20170411_1047'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='question_parent',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='questions.Question'),
        ),
    ]
