# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-07-10 12:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0015_documentheader_owner'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Describer',
            new_name='Descriptor',
        ),
        migrations.RenameModel(
            old_name='Subject',
            new_name='Discipline',
        ),
        migrations.RenameModel(
            old_name='EducationLevel',
            new_name='TeachingLevel',
        ),
        migrations.RenameField(
            model_name='alternative',
            old_name='answer_text',
            new_name='text',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='level',
            new_name='difficulty',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='subjects',
            new_name='disciplines',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='education_level',
            new_name='teaching_level',
        ),
        migrations.AddField(
            model_name='question',
            name='desciptors',
            field=models.ManyToManyField(blank=True, to='questions.Descriptor'),
        ),
    ]
