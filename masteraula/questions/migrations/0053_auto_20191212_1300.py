# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-12-12 16:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0052_auto_20191204_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='label',
            name='color',
            field=models.CharField(blank=True, choices=[('', 'None'), ('#FFFF33', 'Yellow'), ('#A849F7', 'Purple'), ('#F9442E', 'Red'), ('#BABEBF', 'Grey'), ('#050505', 'Black'), ('#FC1979', 'Pink'), ('#FC7320', 'Orange'), ('#82C2FB', 'Blue'), ('#9AEE2E', 'Light Green'), ('#569505', 'Dark Green')], max_length=7, null=True),
        ),
        migrations.AlterField(
            model_name='label',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
