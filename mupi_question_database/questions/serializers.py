from rest_framework import serializers
from rest_framework.exceptions import ParseError

import ast

from .models import Question, Answer, Question_List

class TagListSerializer(serializers.Field):
    '''
    TagListSerializer para tratar o App taggit, ja que nao possui suporte para
    rest_framework
    '''
    def to_internal_value(self, data):
        if  type(data) is list:
            return data
        try:
            taglist = ast.literal_eval(data)
            return taglist
        except BaseException as e:
            raise serializers.ValidationError("expected a list of data")


    def to_representation(self, obj):
        if type(obj) is not list:
            return [tag.name for tag in obj.all()]
        return obj


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('id', 'answer_text', 'is_correct')


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    tags = TagListSerializer(read_only=True)
    id = serializers.IntegerField()

    class Meta:
        model = Question
        fields = ('id', 'question_header', 'question_text', 'resolution', 'level', 'author', 'create_date', 'tags', 'answers')

    def create(self, validated_data):
        '''
        Override para tratar jsutamente o taggit
        '''
        question = Question.objects.create(question_header=validated_data['question_header'],
                                            question_text=validated_data['question_text'],
                                            resolution=validated_data['resolution'],
                                            level=validated_data['level'],
                                            author=validated_data['author'])

        for tag in validated_data['tags']:
            question.tags.add(tag)

        return question


    def update(self, instance, validated_data):
        '''
        Override para tratar jsutamente o taggit
        '''
        dbtags = [auxtag.name for auxtag in list(instance.tags.all())]
        to_delete = list(set(dbtags) - set(validated_data['tags']))
        to_create = list(set(validated_data['tags']) - set(dbtags))

        for tag in to_create:
            instance.tags.add(tag)
        for tag in to_delete:
            instance.tags.remove(tag)

        return super().update(instance, validated_data)

class SimpleQuestion_ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question_List
        fields = ('question_list_header', 'owner', 'questions', 'private')


class Question_ListSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=False)

    class Meta:
        model = Question_List
        fields = ('id', 'question_list_header', 'owner', 'private', 'create_date', 'questions')


    def update(self, instance, validated_data):

        question_ids = [item['id'] for item in validated_data['questions']]
        dbquestions = [question.id for question in list(instance.questions.all())]
        to_add = list(set(question_ids) - set(dbquestions))

        for question in instance.questions.all():
            if question.id not in question_ids:
                instance.questions.remove(question)

        for question_id in to_add:
            question = Question.objects.filter(id=question_id)
            instance.questions.add(question)

        return instance
