# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-05 13:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0003_auto_20161005_1043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='resolution',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
