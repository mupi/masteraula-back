from rest_framework import serializers

from masteraula.questions.models import Question, LearningObject, Alternative

class QuestionStatementEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = (
            'id',
            'statement'
        )

    def validate_statement(self, value):
        if value.strip() != '':
            return value
        raise serializers.ValidationError("Question does not exist")

class LearningObjectEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningObject
        fields = (
            'id',
            'text',
            'source',
        )

    def validate(self, data):
        if data['source'] == None:
            data.pop('source')

        return data

class AlternativeEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternative
        fields = (
            'id',
            'text',
        )

    def validate_text(self, value):
        if value.strip() != '':
            return value
        raise serializers.ValidationError("Question does not exist")