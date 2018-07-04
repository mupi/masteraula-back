# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-05-24 18:37
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('questions', '0009_question_question_parent'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alternative',
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
            name='Describer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('secret', models.BooleanField()),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DocumentHeader',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('institution_name', models.CharField(max_length=200)),
                ('subject_name', models.CharField(max_length=50)),
                ('professor_name', models.CharField(max_length=200)),
                ('student_indicator', models.BooleanField()),
                ('class_indicator', models.BooleanField()),
                ('score_indicator', models.BooleanField()),
                ('date_indicator', models.BooleanField()),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Document')),
            ],
        ),
        migrations.CreateModel(
            name='DocumentQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField()),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Document')),
            ],
            options={
                'ordering': ['document', 'order'],
            },
        ),
        migrations.CreateModel(
            name='EducationLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='LearningObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('image', models.ImageField(blank=True, null=True, upload_to='')),
                ('text', models.TextField(blank=True, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
        ),
        migrations.RemoveField(
            model_name='answer',
            name='question',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='avaiable_questions',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='user',
        ),
        migrations.RemoveField(
            model_name='question_list',
            name='cloned_from',
        ),
        migrations.RemoveField(
            model_name='question_list',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='question_list',
            name='questions',
        ),
        migrations.RemoveField(
            model_name='questionquestion_list',
            name='question',
        ),
        migrations.RemoveField(
            model_name='questionquestion_list',
            name='question_list',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='question_statement',
            new_name='statement',
        ),
        migrations.RenameField(
            model_name='subject',
            old_name='subject_name',
            new_name='name',
        ),
        migrations.RemoveField(
            model_name='question',
            name='question_parent',
        ),
        migrations.AlterField(
            model_name='question',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='question',
            name='credit_cost',
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='question',
            name='education_level',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='questions.EducationLevel'),
        ),
        migrations.AlterField(
            model_name='question',
            name='level',
            field=models.CharField(blank=True, choices=[('', 'Nenhuma opção'), ('E', 'Easy'), ('M', 'Medium'), ('H', 'Hard')], max_length=1, null=True),
        ),
        migrations.DeleteModel(
            name='Answer',
        ),
        migrations.DeleteModel(
            name='Profile',
        ),
        migrations.DeleteModel(
            name='Question_List',
        ),
        migrations.DeleteModel(
            name='QuestionQuestion_List',
        ),
        migrations.AddField(
            model_name='documentquestion',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questions.Question'),
        ),
        migrations.AddField(
            model_name='document',
            name='questions',
            field=models.ManyToManyField(related_name='questions', through='questions.DocumentQuestion', to='questions.Question'),
        ),
        migrations.AddField(
            model_name='alternative',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alternatives', to='questions.Question'),
        ),
        migrations.AddField(
            model_name='question',
            name='learning_object',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='questions.LearningObject'),
        ),
    ]