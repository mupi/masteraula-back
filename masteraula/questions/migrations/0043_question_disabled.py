# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-06-04 14:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0042_documentdownload_answers'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='disabled',
            field=models.BooleanField(default=False),
        ),
    ]