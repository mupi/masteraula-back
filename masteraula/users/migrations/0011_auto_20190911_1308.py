# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-09-11 18:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_user_disciplines'),
    ]

    operations = [
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='schools',
            field=models.ManyToManyField(blank=True, related_name='teachers', to='users.School'),
        ),
    ]
