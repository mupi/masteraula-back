# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-01-30 13:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.TextField()),
                ('is_correct', models.BooleanField()),
            ],
            options={
                'ordering': ['question', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credit_balance', models.PositiveIntegerField(blank=True, default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_header', models.CharField(max_length=50)),
                ('question_text', models.TextField()),
                ('resolution', models.TextField(blank=True, null=True)),
                ('level', models.CharField(blank=True, choices=[('', 'Nenhuma opção'), ('E', 'Fácil'), ('M', 'Médio'), ('H', 'Difícil')], max_length=1, null=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('credit_cost', models.PositiveIntegerField(default=0)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
        ),
        migrations.CreateModel(
            name='Question_List',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_list_header', models.CharField(max_length=200, verbose_name='Nome da Lista')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('private', models.BooleanField(verbose_name='Lista privada')),
                ('cloned_from', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='questions.Question_List')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='QuestionQuestion_List',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Question')),
                ('question_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Question_List')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AddField(
            model_name='question_list',
            name='questions',
            field=models.ManyToManyField(related_name='questions', through='questions.QuestionQuestion_List', to='questions.Question'),
        ),
        migrations.AddField(
            model_name='profile',
            name='avaiable_questions',
            field=models.ManyToManyField(blank=True, to='questions.Question'),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='questions.Question'),
        ),
    ]
