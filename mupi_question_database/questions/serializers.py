from rest_framework import serializers
from rest_framework.exceptions import ParseError

from mupi_question_database.users.models import User

from .models import Question, Answer, Question_List, QuestionQuestion_List, Profile

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

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            'credit_balance',
        )

class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='mupi_question_database:users-detail')

    class Meta:
        model = User
        fields = (
            'url',
            'id',
            'username',
            'name',
            'email',
            'password'
        )
        extra_kwargs = {'password': {'write_only': True, 'required' : True},
                        'username': {'required' : False}}

    def create(self, validated_data):
        user = User(username=validated_data['username'],
                    name=validated_data['name'],
                    email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()

        Profile.objects.create(user=user)

        return user

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='mupi_question_database:users-detail')
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'url',
            'id',
            'username',
            'name',
            'email',
            'profile'
        )
        extra_kwargs = {'profile' : {'read_only' : True},
                        'username': {'read_only' : True}}

class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=200)
    previous_password = serializers.CharField(max_length=200)

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = (
            'id',
            'answer_text',
            'is_correct'
        )
        extra_kwargs =  {'id': {'read_only': False, 'required' : False},
                        'answer_text' : {'required' : True},
                        'is_correct' : {'required' : True}
                        }


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    answers = AnswerSerializer(many=True, read_only=False)
    tags = TagListSerializer(read_only=False)
    author = serializers.HyperlinkedRelatedField(view_name='mupi_question_database:users-detail', read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='mupi_question_database:questions-detail')

    class Meta:
        model = Question
        fields = (
            'url',
            'id',
            'question_header',
            'question_text',
            'resolution',
            'level',
            'author',
            'create_date',
            'credit_cost',
            'tags',
            'answers'
        )
        extra_kwargs = {'tags': {'required' : True}, 'answers' : {'required' : True}}

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        answers = validated_data.pop('answers')

        # Verifica se ha duas questoes corretas na mesma pergunta
        has_correct = False
        error = None
        for answer in answers:
            if answer["is_correct"]:
                if has_correct:
                    error = 'The question has two correct answers'
                    break
                has_correct = True

        # Verifica se ha ao menos uma resposta correta
        if not has_correct:
            error = 'The question does not have any correct answer'
        if error is not None:
            raise ParseError(error)

        question = Question.objects.create(question_header=validated_data['question_header'],
                                            question_text=validated_data['question_text'],
                                            resolution=validated_data['resolution'],
                                            level=validated_data['level'],
                                            author=validated_data['author'])

        for tag in tags:
            question.tags.add(tag)

        for answer in answers:
            answer['id'] = None
            new_answer = Answer.objects.create(question=question, **answer)
            question.answers.add(new_answer)

        return question

    def update(self, instance, validated_data):
        # Verifica se existe answer para partial_update (PATCH)
        if 'answers' in validated_data:
            answers = validated_data.pop('answers')

            # Verifica se ha duas questoes corretas na mesma pergunta
            has_correct = False
            error = None
            for answer in answers:
                if answer["is_correct"]:
                    if has_correct:
                        error = 'The question has two correct answers'
                        break
                    has_correct = True

            # Verifica se ha ao menos uma resposta correta
            if not has_correct:
                error = 'The question does not have any correct answer'

            # Prepara listas para exclusao de respostas que nao fazem mais parte da pergunta
            dbanswer = [answer.id for answer in list(instance.answers.all())]
            answer_aux = [answer['id'] for answer in answers if 'id' in answer]
            to_delete = list(set(dbanswer) - set(answer_aux))
            to_create = list(set(answer_aux) - set(dbanswer))

            # Nao pode haver ids 'to_create' para nao gerar inconsistencia no banco de dados
            if to_create:
                error = 'There is a question with a new id that did not exist before'
            if error is not None:
                raise ParseError(error)

            # Deleta as respostas que nao estao mais sendo usadas
            for id_answer in to_delete:
                removed_answer = Answer.objects.get(id=id_answer)
                removed_answer.delete()
                # instance.answers.remove(removed_answer)

            # Atualiza as respostas
            for answer in answers:
                if 'id' in answer:
                    # Atualiza as questoes ja existentes
                    dbanswer = Answer.objects.get(id=answer['id'])
                    dbanswer.answer_text = answer['answer_text']
                    dbanswer.is_correct = answer['is_correct']
                    dbanswer.save()
                else:
                    # Cria uma nova questao caso ela nao exista
                    new_answer = Answer.objects.create(question=instance, **answer)
                    instance.answers.add(new_answer)


        # Verifica se existe tags para partial_update (PATCH)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')

            # Cria lista para a criacao de novas tags e exclusao de tags que nao fazem mais parte
            dbtags = [tag.name for tag in list(instance.tags.all())]
            to_delete = list(set(dbtags) - set(tags))
            to_create = list(set(tags) - set(dbtags))

            for tag in to_create:
                instance.tags.add(tag)
            for tag in to_delete:
                instance.tags.remove(tag)

        return super().update(instance, validated_data)

class QuestionOrderSerializer(serializers.ModelSerializer):
    question = serializers.HyperlinkedRelatedField(view_name='mupi_question_database:questions-detail', read_only=True)

    class Meta:
        model = QuestionQuestion_List
        fields = (
            'question',
            'order',
        )

class Question_ListSerializer(serializers.HyperlinkedModelSerializer):
    questions = QuestionOrderSerializer(many=True, source='questionquestion_list_set', read_only=False)
    owner = serializers.HyperlinkedRelatedField(view_name='mupi_question_database:users-detail', read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='mupi_question_database:question_lists-detail')

    class Meta:
        model = Question_List
        fields = (
            'url',
            'id',
            'owner',
            'question_list_header',
            'private',
            'create_date',
            'questions'
        )


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
