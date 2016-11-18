# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-07 13:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0014_auto_20161101_1649'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionQuestion_List',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(blank=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Question')),
            ],
        ),
        migrations.RemoveField(
            model_name='question_list',
            name='questions',
        ),
        migrations.AddField(
            model_name='question_list',
            name='questions',
            field=models.ManyToManyField(through='questions.QuestionQuestion_List', to='questions.Question'),
        ),
        migrations.AddField(
            model_name='questionquestion_list',
            name='question_list',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Question_List'),
        ),
    ]