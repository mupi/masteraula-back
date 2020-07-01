# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-06-26 13:18
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '0002_auto_20150616_2121'),
        ('questions', '0062_auto_20200608_1300'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('difficulty', models.CharField(blank=True, choices=[('', 'None'), ('E', 'Easy'), ('M', 'Medium'), ('H', 'Hard')], max_length=1, null=True)),
                ('disabled', models.BooleanField(default=False)),
                ('secret', models.BooleanField(default=False)),
                ('disciplines', models.ManyToManyField(blank=True, to='questions.Discipline')),
                ('learning_objects', models.ManyToManyField(blank=True, related_name='activity_obj', to='questions.LearningObject')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
                ('teaching_levels', models.ManyToManyField(blank=True, to='questions.TeachingLevel')),
                ('topics', models.ManyToManyField(blank=True, to='questions.Topic')),
            ],
            options={
                'verbose_name': 'Activity',
                'verbose_name_plural': 'Activities',
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description_task', models.TextField(blank=True, null=True)),
                ('student_expectation', models.TextField(blank=True, null=True)),
                ('teacher_expectation', models.TextField(blank=True, null=True)),
                ('activity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='questions.Activity')),
            ],
        ),
    ]
