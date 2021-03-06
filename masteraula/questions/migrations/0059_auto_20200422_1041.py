# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-04-22 13:41
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('questions', '0058_faq_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentOnline',
            fields=[
                ('link', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('start_date', models.DateTimeField()),
                ('finish_date', models.DateTimeField()),
                ('duration', models.PositiveIntegerField(blank=True, null=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Document')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Document Online',
                'verbose_name_plural': 'Documents Online',
            },
        ),
        migrations.CreateModel(
            name='DocumentQuestionOnline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveIntegerField(blank=True, null=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.DocumentOnline')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Question')),
            ],
            options={
                'verbose_name': 'Document Question Online',
                'verbose_name_plural': 'Document Question Online',
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=200)),
                ('student_levels', models.CharField(max_length=200)),
                ('start', models.DateTimeField()),
                ('finish', models.DateTimeField()),
                ('total_score', models.PositiveIntegerField(blank=True, null=True)),
                ('results', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='questions.DocumentOnline', verbose_name='document')),
            ],
        ),
        migrations.CreateModel(
            name='StudentAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField(blank=True, null=True)),
                ('score_answer', models.PositiveIntegerField(blank=True, null=True)),
                ('student_answer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_answer', to='questions.Result')),
                ('student_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_question', to='questions.DocumentQuestionOnline')),
            ],
        ),
        migrations.AddField(
            model_name='documentonline',
            name='questions_document',
            field=models.ManyToManyField(related_name='questions_document', through='questions.DocumentQuestionOnline', to='questions.Question'),
        ),
    ]
