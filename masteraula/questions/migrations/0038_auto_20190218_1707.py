# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2019-02-18 20:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0037_auto_20190214_1457'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
