# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-07-16 13:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0064_auto_20200706_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningobject',
            name='disabled',
            field=models.BooleanField(default=False),
        ),
    ]
