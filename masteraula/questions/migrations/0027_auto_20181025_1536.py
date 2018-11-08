# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-10-25 18:36
from __future__ import unicode_literals

from django.db import migrations, models
import masteraula.questions.models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0026_remove_learningobject_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningobject',
            name='folder_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='learningobject',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=masteraula.questions.models.LearningObject.get_upload_file_name),
        ),
    ]