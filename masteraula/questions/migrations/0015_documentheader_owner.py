# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-07-06 14:50
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('questions', '0014_auto_20180706_1144'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentheader',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
