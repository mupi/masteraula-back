# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-07-06 14:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0013_auto_20180704_1132'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentheader',
            name='document',
        ),
        migrations.AddField(
            model_name='document',
            name='document_header',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='questions.DocumentHeader'),
        ),
    ]
