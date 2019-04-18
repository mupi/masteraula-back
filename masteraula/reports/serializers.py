from rest_framework import serializers

from masteraula.questions.models import Question

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