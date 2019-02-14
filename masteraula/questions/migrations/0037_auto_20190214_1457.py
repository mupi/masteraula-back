# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2019-02-14 16:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0036_question_topics'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='discipline',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Discipline'),
        ),
    ]
