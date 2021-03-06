# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-01-30 20:20
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import masteraula.questions.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('questions', '0053_auto_20191212_1300'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=200)),
                ('duration', models.PositiveIntegerField(blank=True, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('pdf', models.FileField(blank=True, null=True, upload_to='documents_pdf', validators=[masteraula.questions.models.ClassPlan.validate_pdf])),
                ('disciplines', models.ManyToManyField(blank=True, to='questions.Discipline')),
                ('documents', models.ManyToManyField(blank=True, related_name='plans_doc', to='questions.Document')),
                ('learning_objects', models.ManyToManyField(blank=True, related_name='plans_obj', to='questions.LearningObject')),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link', models.URLField()),
                ('description_url', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TeachingYear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='classplan',
            name='links',
            field=models.ManyToManyField(blank=True, related_name='plans_links', to='questions.Link'),
        ),
        migrations.AddField(
            model_name='classplan',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='classplan',
            name='teaching_levels',
            field=models.ManyToManyField(blank=True, to='questions.TeachingLevel'),
        ),
        migrations.AddField(
            model_name='classplan',
            name='teaching_years',
            field=models.ManyToManyField(blank=True, to='questions.TeachingYear'),
        ),
        migrations.AddField(
            model_name='classplan',
            name='topics',
            field=models.ManyToManyField(blank=True, to='questions.Topic'),
        ),
    ]
